"""为每项测试隔离用户目录，避免读取真实配置或写入真实数据库。"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def isolated_user_directory(tmp_path, monkeypatch):
    # Windows 的 Path.home 使用 USERPROFILE，Linux/macOS 使用 HOME。
    # 同时设置两者，确保跨平台测试都只访问临时用户目录。
    user_directory = tmp_path / "user"
    user_directory.mkdir()
    monkeypatch.setenv("USERPROFILE", str(user_directory))
    monkeypatch.setenv("HOME", str(user_directory))
