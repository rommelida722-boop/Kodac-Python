# 第二期：全量测试基线与持续集成

## 基线

2026-11-02，在 Windows、Python 3.12.9 环境中执行完整测试集：98 项通过，0 失败，0 跳过。

测试在工作区源码副本运行；原桌面路径的上级目录访问受限，不据此判断 Git 对象损坏。

## 修复的测试环境问题

- 默认 pytest 临时目录不可访问：本地验证显式指定工作区中的 `--basetemp`。
- Windows 的用户目录读取 USERPROFILE：统一 fixture 同时隔离 HOME 与 USERPROFILE。
- 四项测试曾依赖用户已有模型配置：离线测试显式提供占位 API Key。

没有关闭生产环境的 API Key 校验，也没有跳过失败测试。

## 本地复现

在项目根目录执行：

```powershell
uv sync --frozen --extra dev
uv run --frozen --extra dev python -m pytest --junitxml=test-results/pytest.xml
uv run --frozen --extra dev ruff check src tests
uv run --frozen --extra dev ruff format --check src tests
uv build
uv run --frozen --extra dev kodac --version
```

若系统默认临时目录受限，可为 pytest 指定一个新的、专用的 `--basetemp` 路径。pytest 会清理该目录，请不要指向有个人文件的目录。

## GitHub Actions

配置位于 `.github/workflows/tests.yml`。每次推送均执行，没有分支或文件路径过滤；PR 和手动运行也会触发。

测试覆盖 Windows / Linux 与 Python 3.11 / 3.12 / 3.13 六组组合；每组上传 JUnit 报告。失败不会被忽略，某组失败也不会取消其他组合的测试。

运行记录位于仓库 Actions 页面。只有远端运行完成后，才能认定相应组合验证通过。本地通过不等于六组远端均已通过。

## 验证范围

当前完整测试集主要使用离线客户端、临时文件、SQLite 和本地 MCP 子进程，不需要真实模型凭据。真实 LLM 响应效果、Chrome DevTools MCP 与外网服务可用性仍需要对应环境另行验证。

配置依据：[uv 官方集成文档](https://docs.astral.sh/uv/guides/integration/github/)、[GitHub Actions 触发事件文档](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)。
