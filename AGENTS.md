# Repository Guidelines

## Project Structure & Module Organization
This repository is currently plan-first. Active content lives in `docs/`, especially `docs/mcp_plan.md`.

As implementation lands, keep a standard Python layout:
- `src/recite_mcp/`: package code (`server.py`, API client, ledger utilities)
- `tests/`: unit/integration tests mirroring `src/`
- `docs/`: design notes and operational docs

Keep modules small and single-purpose (API transport, file/ledger logic, MCP tool wiring).

## Build, Test, and Development Commands
Today, there is no packaged runtime in this repo yet. After scaffolding (`pyproject.toml`), use:
- `python -m pip install -e .` : install editable package locally
- `pytest -q` : run test suite
- `python -m recite_mcp.server` : run local MCP server over stdio (dev check)
- `uvx recite-mcp` : run published CLI as users will

If you add tooling (ruff/black/mypy), document exact commands in `README.md` and keep them consistent here.

## Coding Style & Naming Conventions
Use Python 3.10+ idioms and 4-space indentation.
- Modules/files: `snake_case.py`
- Functions/variables: `snake_case`
- Classes: `PascalCase`
- Constants/env vars: `UPPER_SNAKE_CASE` (for example `RECITE_API_KEY`)

Prefer type hints on public functions and dataclasses/TypedDicts for receipt payloads. Keep side effects (file writes, API calls) isolated behind small interfaces.

## Testing Guidelines
Use `pytest` with tests in `tests/test_<module>.py`.
- Cover API key resolution, request/response parsing, CSV append behavior, and file rename logic.
- Add regression tests for every bug fix.
- For integrations, mock external HTTP calls; do not hit live Recite endpoints in CI.

## Commit & Pull Request Guidelines
This workspace has no local Git history yet, so adopt Conventional Commits from now on:
- `feat: add process_receipt tool`
- `fix: handle missing RECITE_API_KEY`
- `docs: update MCP setup example`

PRs should include:
- Clear summary and scope
- Linked issue/task (if available)
- Test evidence (`pytest` output or rationale if tests are deferred)
- Config impact notes (env vars, file paths, migration steps)

## Security & Configuration Tips
Never commit API keys or user receipt data. Use environment variables (`RECITE_API_KEY`) and sanitize logs to avoid exposing PII.
