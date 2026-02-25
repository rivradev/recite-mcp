# recite-mcp

`recite-mcp` is a local MCP server for receipt processing with the Recite API. It provides tools for single/batch receipt processing, ledger writes, corrections, memory instructions, and health/status resources.

## Install

### End users

```bash
uvx recite-mcp
```

Alternative:

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

Set API key:

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

Use `uvx` for the cleanest user install path:

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

## Main Features

- Single receipt processing and optional file rename
- Batch processing with dry-run preview
- Local CSV ledger append and audit-safe correction entries
- Memory instruction store for categorization rules
- Resource providers for ledger, memory, and health status

## Release and Distribution

For post-publish checklist, discoverability, and install guidance for end users:

- `docs/publishing_guide.md`

## Documentation

- Implementation and operations walkthrough: `docs/walkthrough.md`
