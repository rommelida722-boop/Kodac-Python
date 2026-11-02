# Kodac Python Parity

This file tracks the Python port against the existing Java and TypeScript implementations.

## Implemented

- CLI:
  - `kodac`
  - `kodac -p`
  - `--provider`
  - `--model`
  - `--plain`
  - `--mode react|plan|team`
  - `--worker-mode react|plan`
  - `--json` usage/cost output
  - `--cwd`
  - `kodac doctor`
  - `kodac serve --http --port <port>`
- REPL:
  - `/help`
  - `/clear`
  - `/context`
  - `/memory`
  - `/save`
  - `/config`
  - `/tools`
  - `/hitl`
  - `/policy`
  - `/audit`
  - `/index`
  - `/search`
  - `/plan`
  - `/team`
  - `/model` Default/Custom Tab selector with live client switching
  - persisted BYOK DeepSeek/GLM/OpenAI-compatible custom models
  - `/usage`
  - `/task`
  - `/snapshot`
  - `/restore`
  - `/skill`
  - `/mcp`
  - `/exit`
- Agent:
  - OpenAI-compatible streaming LLM client
  - DeepSeek default
  - ReAct loop with text/thinking/tool-call/tool-result/done events
  - Plan-and-Execute agent with Planner-generated DAG, dependency ordering, and parallel executable batches
  - Multi-Agent orchestrator with Planner, Worker, Reviewer, dependency scheduling, parallel workers, review approval parsing, bounded retry, and per-worker `react|plan` mode
  - isolated Skill context per SubAgent and per parallel Plan task
  - SDK entrypoint with ReAct, Plan-and-Execute, and Multi-Agent methods
  - pre/post side-history snapshots around Agent runs
- Configuration:
  - defaults
  - user config
  - project config
  - project `.env`
  - CLI overrides
  - process env
  - provider-specific keys such as `DEEPSEEK_API_KEY`, `GLM_API_KEY`, `STEP_API_KEY`, `KIMI_API_KEY`
- Tools:
  - `read_file`
  - `write_file`
  - `list_dir`
  - `glob` / `glob_files`
  - `grep` / `grep_code`
  - `bash` / `execute_command`
  - `web_search`
  - `web_fetch`
  - `save_memory`
  - `search_memory`
  - `load_skill`
  - `save_skill` with mandatory HITL approval
  - `search_code`
  - `revert_turn`
- Safety:
  - PathGuard
  - CommandGuard
  - HITL approval
  - JSONL AuditLog
- Memory:
  - static project memory files `AGENTS.md`, `KODAC.md`, `.kodac/KODAC.md`, local variants
  - governed SQLite dynamic memory with metadata, normalized deduplication, TTL, quota, access tracking, and relevance recall
  - automatic request-specific Top-K recall plus model-initiated `search_memory`
  - bounded short-term history and deterministic context compression
  - cache-friendly static Prompt plus per-request dynamic Prompt
- Skills:
  - built-in/user/project skill layers
  - user/project `.kodac/skills/*/SKILL.md`
  - `~/.kodac/skills.json` disabled-state store
  - `load_skill` with one-shot SkillContextBuffer injection
  - current-query next-turn Skill injection (no one-request delay)
  - name/description/tag Top-K matcher with Chinese n-gram support
  - safe project/user create/update and model-proposed `save_skill`
  - `/skill list/show/on/off/reload`
- RAG:
  - SQLite local code index
  - `/index`
  - `/search`
  - `search_code`
- MCP:
  - official MCP Python SDK client
  - stdio MCP server connection
  - Streamable HTTP MCP server connection
  - dynamic `mcp__server__tool` registration
  - virtual resource tools
  - virtual prompt tools
  - `kodac mcp init-chrome`
  - `kodac mcp list`
  - Kodac MCP server over stdio/http for built-in tools
- Chrome DevTools MCP:
  - project/user config writer for `npx chrome-devtools-mcp@latest`
  - `--browser-url`
  - `--headless`
  - `--slim`
  - usage-statistics opt-out flag by default
- Runtime:
  - API key requirement
  - `POST /v1/threads`
  - `POST /v1/threads/{id}/turns`
  - `GET /v1/threads/{id}/events`
  - `POST /v1/tasks`
  - `GET /v1/tasks`
  - `GET /v1/tasks/{id}`
  - `POST /v1/tasks/{id}/cancel`
  - SQLite durable task queue
  - task modes `react|plan|team`
  - atomic claim, project scope, lease/heartbeat recovery, and cancellation-safe completion
  - standalone `kodac worker`
  - persisted Runtime thread history
- Snapshot:
  - `pre-turn` / `post-turn`
  - `/snapshot`
  - `/restore`
  - `revert_turn`
- Image input:
  - `@image:path`
  - `@image:file:///path`
  - `@image:https://...`
  - local image resize/compress
  - transparent PNG white background handling
  - provider/model capability fallback
- Diagnostics:
  - Python syntax diagnostics after `write_file`
- Usage and cost:
  - OpenAI-compatible streaming usage-only chunks
  - input/output/cache-hit/cache-miss/reasoning token aggregation
  - dated DeepSeek V4 Flash/Pro price profiles with config overrides
  - ReAct/Plan/Team SDK and CLI aggregation

## Live Dependencies

These features need external credentials or platform state for live verification:

- Real LLM calls need API keys.
- Chrome DevTools MCP needs Node.js LTS, npm/npx, and Chrome.
- Runtime API turn execution needs a working LLM key.
- WeChat iLink needs private iLink credentials and scan-login state.

## Known Remaining Java-Only Area

The Java implementation has a WeChat iLink channel. Python does not ship that private channel yet because it requires iLink account credentials and protocol details that should not be faked. All public/open protocol surfaces from the TypeScript baseline and the main Java Agent CLI surfaces have corresponding Python implementations.

## Verification

```bash
uv run --extra dev ruff check .
uv run --extra dev ruff format --check .
uv run --extra dev python -m pytest
uv build
uv run kodac --help
uv run kodac doctor --cwd .
uv run kodac mcp serve --transport http --port 3999
```


### 长上下文完整性升级

依据 docs1/phase-12-long-context.md，Python 压缩器在无用户消息时仍保留完整工具调用组，并深拷贝嵌套消息数据，避免污染原始历史。相关上下文回归测试共 7 项通过。


### 全量测试与持续集成

98 项本地测试通过；新增用户目录隔离与离线测试占位配置。GitHub Actions 工作流已配置全量测试矩阵、Ruff、打包及 CLI 验证，远端状态以 Actions 为准。每期记录参见 CHANGELOG.md，图文介绍参见 docs/project-showcase.md。


### 第四期：长上下文压缩质量（0.1.1）

Python 摘要支持目标、约束、待办、决定等分类抽取、重复压缩解包、去重、来源与历史顺序保留、完整边界及旧版完整摘要兼容。多模态历史抽取文字并省略图片字节。近期消息继续保持原文，预算不足时不保证保留全部历史。

新增 14 项回归用例，全量测试 112 项通过。公开入口集成用例和连续五轮离线示例均通过。详见 `docs/releases/phase-04-context-retention.md`。
