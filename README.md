# recite-mcp

`mcp-name: io.github.rivradev/recite-mcp`

`recite-mcp` is a local MCP server for receipt processing with the Recite API. It provides tools for single/batch receipt processing, ledger writes, corrections, memory instructions, and health/status resources.

## Install

### End users

Recommended:

```bash
uvx recite-mcp
```

Alternative (`pipx`):

```bash
pipx install recite-mcp
```

Alternative (`pip`):

```bash
python -m pip install recite-mcp
```

### Contributors

```bash
python -m pip install -e .[dev]
pytest -q
python -m recite_mcp.server
```

## Required Environment

Get an API key at `https://recite.rivra.dev/settings/api` (includes 30 free scans per month), then set `RECITE_API_KEY` (required to process receipts; server can still start without it so `validate_setup()` can report what's missing):

```bash
# Windows PowerShell
$env:RECITE_API_KEY="re_live_xxx"
```

```bash
# macOS/Linux
export RECITE_API_KEY="re_live_xxx"
```

Optional home override:

```bash
# Windows PowerShell
$env:RECITE_HOME="C:\path\to\recite-home"
```

```bash
# macOS/Linux
export RECITE_HOME="$HOME/.config/recite"
```

## MCP Client Config

Copy-paste this config:

```json
{
  "mcpServers": {
    "recite": {
      "command": "uvx",
      "args": ["recite-mcp"],
      "env": {
        "RECITE_API_KEY": "re_live_xxx"
      }
    }
  }
}
```

If installed via `pipx` or `pip`, use:

```json
{
  "mcpServers": {
    "recite": {
      "command": "recite-mcp",
      "args": [],
      "env": {
        "RECITE_API_KEY": "re_live_xxx"
      }
    }
  }
}
```

## Troubleshooting

### MCP Registry ownership validation failed

- Symptom: Registry publish returns a PyPI ownership/README validation error.
- Fix: keep this exact line in packaged README: `mcp-name: io.github.rivradev/recite-mcp`, then bump version and upload new PyPI release before publishing to Registry.

### `RECITE_API_KEY` missing or invalid

- Symptom: `validate_setup()` reports `missing_api_key` or API requests are rejected.
- Fix: set `RECITE_API_KEY` in MCP client `env` config (preferred) or shell environment.

### `uvx` command not found

- Symptom: terminal says `uvx` is not recognized.
- Fix: install `uv` first, or use one of the alternatives:
  - `pipx install recite-mcp`
  - `python -m pip install recite-mcp`

### `recite-mcp` command not found after install

- Symptom: command not recognized after `pipx`/`pip` install.
- Fix:
  - For `pipx`: run `pipx ensurepath`, then reopen terminal.
  - For `pip`: run with module entrypoint: `python -m recite_mcp.server`

### MCP client starts but tools are unavailable

- Symptom: server appears configured but no tools/resources are listed.
- Fix:
  - Confirm MCP config JSON is valid.
  - Confirm command and args match your install method (`uvx` vs `recite-mcp`).
  - Restart MCP client after config changes.

### Can't download from PyPI (uvx/pip)

- Symptom: install/run fails with network/proxy errors.
- Fix: ensure your environment can reach PyPI (or configure your proxy / custom index). If you're on a locked-down network, you may need to allowlist PyPI or use an internal mirror.

### Quick local validation (no MCP client)

- Run `recite-mcp --validate` (or `uvx recite-mcp --validate`) to print local config/health JSON. Exit code is `0` if an API key is present, otherwise `1`.

## Main Features

- Single receipt processing and optional file rename
- Batch processing with dry-run preview
- Local CSV ledger append and audit-safe correction entries
- Memory instruction store for categorization rules
- Resource providers for ledger, memory, and health status

## Documentation

- User guide: `docs/user_guide.md`
