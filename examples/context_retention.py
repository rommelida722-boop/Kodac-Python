"""离线演示连续五轮压缩后的任务线索保留，不需要模型 API Key。"""

from __future__ import annotations

from kodac.context import ContextBudget, ContextWindowManager
from kodac.types import Message


def main() -> None:
    # 用消息数量触发压缩，避免示例依赖具体模型的分词器或网络服务。
    manager = ContextWindowManager(
        ContextBudget(100_000, 1000), max_history_messages=6, min_recent_messages=2
    )
    facts = {
        "目标": "目标：升级命令行助手",
        "约束": "必须使用 Python",
        "决定": "决定：采用 SQLite",
        "待办": "待办：修复任务取消竞态",
    }
    history = [
        Message(role="user", content="\n".join(list(facts.values())[:2])),
        Message(role="assistant", content="\n".join(list(facts.values())[2:])),
    ]
    for round_number in range(1, 6):
        for index in range(5):
            history.extend(
                [
                    Message(role="user", content=f"进度回报 {round_number}/{index}"),
                    Message(role="assistant", content="普通日志 " + "x" * 600),
                ]
            )
        result = manager.prepare(history)
        summary = str(result.messages[0].content)
        retained = {name: fact in summary for name, fact in facts.items()}
        # 示例必须根据实际结果输出；任何线索丢失都以非零退出码结束。
        if not result.compressed or not all(retained.values()):
            raise RuntimeError(f"第 {round_number} 轮未保留预期线索：{retained}")
        status = " / ".join(f"{name}：保留" for name in retained)
        print(f"第 {round_number} 轮压缩 | {status}")
        history = result.messages
    print("验证通过：连续五轮压缩，四项任务线索均被保留。")
    print("说明：这是固定离线样例的验证，不代表所有长任务都不会丢失信息。")


if __name__ == "__main__":
    main()
