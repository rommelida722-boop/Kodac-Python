"""验证租约失效、同名 Worker 重领与跨进程竞争。"""

from __future__ import annotations

import multiprocessing
import sqlite3
from concurrent.futures import ProcessPoolExecutor

import pytest

from kodac.runtime import DurableTaskManager


def expire(manager, task_id):
    # 直接推进数据库中的租约状态，避免依赖真实等待和调度速度。
    with sqlite3.connect(manager.db_path) as connection:
        connection.execute(
            "update tasks set lease_expires_at = ? where id = ?", ("2000-01-01", task_id)
        )


def apply(manager, operation, task_id, worker, attempt):
    if operation == "heartbeat":
        return manager.heartbeat(task_id, worker, attempt=attempt)
    return getattr(manager, operation)(task_id, "旧结果", worker_id=worker, attempt=attempt)


@pytest.mark.parametrize("operation", ["heartbeat", "complete", "fail"])
def test_expired_owner_cannot_mutate_running_task(tmp_path, operation):
    manager = DurableTaskManager(tmp_path / "tasks.db")
    task_id = manager.add("测试任务")
    task = manager.claim_next("worker")
    expire(manager, task_id)
    assert not apply(manager, operation, task_id, "worker", task.attempts)
    assert manager.get(task_id).status == "running"


@pytest.mark.parametrize("operation", ["heartbeat", "complete", "fail"])
def test_previous_attempt_cannot_mutate_same_worker_reclaim(tmp_path, operation):
    manager = DurableTaskManager(tmp_path / "tasks.db")
    task_id = manager.add("测试任务")
    first = manager.claim_next("worker")
    expire(manager, task_id)
    second = manager.claim_next("worker")
    assert second.attempts == first.attempts + 1
    assert not apply(manager, operation, task_id, "worker", first.attempts)
    assert manager.complete(task_id, "新结果", worker_id="worker", attempt=second.attempts)
    assert manager.get(task_id).result == "新结果"


@pytest.mark.parametrize("operation", ["complete", "fail"])
def test_named_worker_requires_explicit_owner(tmp_path, operation):
    manager = DurableTaskManager(tmp_path / "tasks.db")
    task_id = manager.add("测试任务")
    task = manager.claim_next("worker")
    assert not getattr(manager, operation)(task_id, "无所有者结果")
    assert manager.complete(task_id, "完成", worker_id="worker", attempt=task.attempts)


def test_heartbeat_keeps_live_lease_owned(tmp_path):
    manager = DurableTaskManager(tmp_path / "tasks.db")
    task_id = manager.add("测试任务")
    task = manager.claim_next("worker", lease_seconds=10)
    assert manager.heartbeat(task_id, "worker", lease_seconds=100, attempt=task.attempts)
    assert manager.get(task_id).lease_expires_at > task.lease_expires_at
    assert manager.claim_next("other") is None


def test_restart_reclaims_abandoned_task(tmp_path):
    path = tmp_path / "tasks.db"
    first = DurableTaskManager(path)
    task_id = first.add("测试任务")
    first.claim_next("old")
    expire(first, task_id)
    restarted = DurableTaskManager(path)
    assert restarted.requeue_expired() == 1
    recovered = restarted.claim_next("new")
    assert recovered.id == task_id and recovered.attempts == 2
    assert restarted.complete(task_id, "恢复完成", worker_id="new", attempt=2)


def test_cancellation_rejects_all_late_writes(tmp_path):
    manager = DurableTaskManager(tmp_path / "tasks.db")
    task_id = manager.add("测试任务")
    task = manager.claim_next("worker")
    assert manager.cancel(task_id)
    for operation in ["heartbeat", "complete", "fail"]:
        assert not apply(manager, operation, task_id, "worker", task.attempts)
    assert manager.get(task_id).status == "canceled"


def consume(arguments):
    path, worker = arguments
    manager = DurableTaskManager(path)
    claimed = []
    while task := manager.claim_next(worker):
        assert manager.complete(task.id, "完成", worker_id=worker, attempt=task.attempts)
        claimed.append(task.id)
    return claimed


def test_four_processes_claim_twelve_tasks_once(tmp_path):
    path = tmp_path / "tasks.db"
    manager = DurableTaskManager(path)
    expected = {manager.add(f"任务 {index}") for index in range(12)}
    # spawn 与 Windows 保持一致，确保不是仅验证同一进程中的线程锁。
    with ProcessPoolExecutor(
        max_workers=4, mp_context=multiprocessing.get_context("spawn")
    ) as pool:
        groups = list(pool.map(consume, [(path, f"worker-{index}") for index in range(4)]))
    claimed = [task_id for group in groups for task_id in group]
    assert len(claimed) == len(set(claimed)) == 12
    assert set(claimed) == expected
    assert all(task.status == "completed" and task.attempts == 1 for task in manager.list())


@pytest.mark.parametrize("operation", ["heartbeat", "complete", "fail"])
def test_named_worker_without_attempt_is_rejected(tmp_path, operation):
    manager = DurableTaskManager(tmp_path / "tasks.db")
    task_id = manager.add("任务")
    manager.claim_next("worker")
    assert not apply(manager, operation, task_id, "worker", None)


def test_legacy_anonymous_call_cannot_finish_reclaimed_task(tmp_path):
    manager = DurableTaskManager(tmp_path / "tasks.db")
    task_id = manager.add("任务")
    manager.claim_next()
    expire(manager, task_id)
    current = manager.claim_next()
    assert not manager.complete(task_id, "旧调用")
    assert manager.complete(
        task_id, "新调用", worker_id=current.worker_id, attempt=current.attempts
    )


def test_runtime_worker_supplies_claim_attempt(tmp_path):
    import threading

    from kodac.runtime.api import RuntimeApiServer

    # 真实 Worker 循环执行离线任务，验证所有者与领取序号已经接入回写链路。
    server = object.__new__(RuntimeApiServer)
    server.task_manager = DurableTaskManager(tmp_path / "tasks.db")
    server._stop = threading.Event()
    task_id = server.task_manager.add("任务")

    async def run_task(task):
        server._stop.set()
        return "离线任务完成"

    server._run_task = run_task
    server._worker_loop("runtime-worker")
    assert server.task_manager.get(task_id).status == "completed"
