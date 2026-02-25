# Recite MCP Walkthrough

## 1. What Was Implemented

This repository now includes a complete local server package with TDD-first coverage for:

- Config resolution (`RECITE_API_KEY`, `RECITE_HOME`, `config.toml` fallback)
- Receipt API client wrapper
- Ledger persistence and summary/export utilities
- Memory instruction storage
- MCP-style tool and resource registration

Test status: `15 passed` using `pytest -q`.

## 2. Source File Map

- `src/recite_mcp/config.py`: settings model, config loading, precedence rules.
- `src/recite_mcp/models.py`: shared typed dataclasses for records/results.
- `src/recite_mcp/api_client.py`: HTTP client for Recite receipt processing endpoint.
- `src/recite_mcp/ledger.py`: CSV ledger repository, correction entries, summary, exports.
- `src/recite_mcp/memory.py`: append/list memory instructions.
- `src/recite_mcp/tools.py`: orchestration layer for all tool behaviors.
- `src/recite_mcp/resources.py`: ledger/memory/health resource providers.
- `src/recite_mcp/server.py`: server entrypoint and tool/resource registration.
- `tests/*.py`: unit tests and registration tests.

## 3. Tool Surface

Registered tools:

- `process_receipt(file_path, rename=False, category_hint=None, dry_run=False)`
- `process_receipts_batch(input_dir, rename=False, dry_run=True, recursive=True)`
- `update_memory(instruction, tags=None)`
- `list_memory()`
- `add_ledger_correction(original_entry_id, corrected_fields, reason)`
- `summarize_ledger(group_by="vendor")`
- `export_ledger(format, output_path)`
- `get_config()`
- `validate_setup()`

Registered resources:

- `recite://ledger`
- `recite://memory`
- `recite://health`

## 4. Local Development and Test (TDD Workflow)

1. Install dependencies:
   `python -m pip install -e .[dev]`
2. Write/modify tests in `tests/` first.
3. Run tests:
   `pytest -q`
4. Run server locally:
   `python -m recite_mcp.server`

## 5. Configuration

Priority order:

1. `RECITE_API_KEY` environment variable.
2. `RECITE_HOME/config.toml` key `api_key`.

Paths:

- `RECITE_HOME` default: `~/.config/recite/`
- Ledger: `bookkeeping_transactions.csv`
- Memory: `long_term_memory.md`
- Optional config: `config.toml`

Example `config.toml`:

```toml
api_key = "re_live_xxx"
api_base_url = "https://recite.rivra.dev/apiV1/api/v1"
request_timeout_sec = 30
```

Receipt scanning call used by this implementation:

- `POST {api_base_url}/scan`
- Headers: `Authorization: Bearer <key>`, `Content-Type: application/json`
- Body (local file mode): `{ "image_base64": "...", "auto_save": false }`

## 6. Deploy and Release

1. Build package:
   `python -m pip install build && python -m build`
2. Publish (PyPI workflow):
   `python -m pip install twine && python -m twine upload dist/*`
3. End-user run path:
   `uvx recite-mcp`

For MCP client integration, configure command execution with `uvx recite-mcp` and pass `RECITE_API_KEY` in environment settings.

## 7. Notes

- Current server module exposes MCP-like registration and CLI output for local verification.
- If the official MCP Python SDK is installed later, keep `src/recite_mcp/tools.py` and `src/recite_mcp/resources.py` as stable logic and swap only transport wiring.
