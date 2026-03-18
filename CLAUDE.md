# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install editable for development
python -m pip install -e ".[dev]"

# Run tests
pytest -q

# Run a single test file
pytest tests/test_tools.py -q

# Run a single test by name
pytest tests/test_tools.py::test_function_name -q

# Lint / format
ruff check src/ tests/
ruff format src/ tests/

# Type checking
mypy src/

# Run MCP server locally (stdio transport, dev smoke test)
python -m recite_mcp.server

# Validate config without hitting the API
python -m recite_mcp.server --validate
```

## Architecture

```
src/recite_mcp/
├── server.py       # MCP entry point — registers 33 tools + 3 resources via FastMCP
├── tools.py        # ReciteTools — orchestrates local + API operations
├── api_client.py   # ApiClient — all HTTP calls to the Recite REST API
├── config.py       # Settings — loads RECITE_API_KEY / RECITE_HOME
├── ledger.py       # LedgerRepository — append-only CSV at ~/.config/recite/bookkeeping_transactions.csv
├── memory.py       # MemoryRepository — JSON-lines file at ~/.config/recite/long_term_memory.md
├── models.py       # Dataclasses: ReceiptRecord, LedgerEntry, MemoryEntry, ProcessResult
└── resources.py    # ResourceProvider — exposes recite://ledger, recite://memory, recite://health
```

**Data flow:** `server.py` wires MCP calls → `ReciteTools` → either `ApiClient` (remote) or `LedgerRepository`/`MemoryRepository` (local files). Server starts without an API key; API tools fail at call time if the key is absent.

**Fallback server:** `_SimpleServer` in `server.py` provides a dict-based stub when FastMCP isn't installed, so `--validate` and health checks still work.

**Local persistence:** All files live under `~/.config/recite/` (or `$RECITE_HOME`). The ledger is a plain CSV with an audit-safe correction mechanism (new rows, never edits). Memory is JSON lines.

**MCP resources:** `recite://ledger`, `recite://memory`, `recite://health`.

## Testing Notes

- `tests/conftest.py` defines a custom `tmp_path` fixture that creates test directories inside the repo root (not `%TEMP%`) to avoid Windows ACL issues — use this fixture, not pytest's built-in `tmp_path`, in new tests.
- Mock all HTTP calls; never hit live Recite endpoints. The `_Response` / `_Session` helpers in `test_api_client.py` show the pattern.
- Use `monkeypatch` to set `RECITE_HOME` and `RECITE_API_KEY` in config/tool tests.

## Conventions

- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`).
- Keep modules single-purpose: transport in `api_client.py`, file logic in `ledger.py`/`memory.py`, MCP wiring in `server.py`.
- Type hints on all public functions; dataclasses for structured payloads.
- MCP registry line `# mcp-name: io.github.rivradev/recite-mcp` in `server.py` must not be removed.
