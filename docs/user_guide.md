# Recite MCP User Guide

This guide is for end users who want to install and use `recite-mcp` with an MCP client.

## 1. What this MCP does

`recite-mcp` helps you process receipt images through Recite, keep a local ledger, and manage memory instructions for categorization.

Main capabilities:

- Process one receipt or a full folder of receipts
- Append entries to a local CSV ledger
- Add correction records for audit-safe fixes
- Store and read long-term memory instructions
- Expose health, ledger, and memory resources

## 2. Install

Recommended:

```bash
uvx recite-mcp
```

Alternative:

```bash
pipx install recite-mcp
```

Alternative:

```bash
python -m pip install recite-mcp
```

## 3. Required setup

You must provide `RECITE_API_KEY`.

PowerShell:

```powershell
$env:RECITE_API_KEY="re_live_xxx"
```

macOS/Linux:

```bash
export RECITE_API_KEY="re_live_xxx"
```

Optional custom data directory:

PowerShell:

```powershell
$env:RECITE_HOME="C:\path\to\recite-home"
```

macOS/Linux:

```bash
export RECITE_HOME="$HOME/.config/recite"
```

## 4. MCP client config

Use this if you run with `uvx`:

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

Use this if you installed with `pipx` or `pip`:

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

## 5. Common tools you can call

- `validate_setup()`: check if API key and local paths are ready.
- `process_receipt(file_path, rename=False, category_hint=None, dry_run=False)`
- `process_receipts_batch(input_dir, rename=False, dry_run=True, recursive=True)`
- `summarize_ledger(group_by="vendor")`
- `export_ledger(format, output_path)`
- `update_memory(instruction, tags=None)`
- `list_memory()`

## 6. Local files created

By default (`RECITE_HOME` not set), files are under `~/.config/recite/`:

- `bookkeeping_transactions.csv` (ledger)
- `long_term_memory.md` (memory instructions)
- `config.toml` (optional configuration)

## 7. First-run checklist

1. Start MCP client with your config.
2. Call `validate_setup()`.
3. Run one `process_receipt(...)` call with `dry_run=True`.
4. Run again with `dry_run=False` after validation.

## 8. Troubleshooting

- API rejected: check `RECITE_API_KEY` and token validity.
- Command not found: use the matching config for `uvx` vs `recite-mcp`.
- No tools in client: validate JSON config and restart MCP client.
