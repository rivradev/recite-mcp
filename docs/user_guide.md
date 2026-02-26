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

You need `RECITE_API_KEY` to actually process receipts (call the Recite API). The MCP server can still start without it so you can run `validate_setup()` and see what's missing.

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

All tools this MCP provides (use these names when asking your MCP client/agent to call tools):

- `validate_setup()`: checks API key and local paths are ready.
- `get_config()`: shows effective configuration (without secrets).
- `process_receipt(file_path, rename=False, category_hint=None, dry_run=False)`: process one receipt image (use `dry_run=True` first).
- `process_receipts_batch(input_dir, rename=False, dry_run=True, recursive=True)`: process a folder of receipts (use `dry_run=True` first).
- `summarize_ledger(group_by="vendor")`: aggregates ledger totals by vendor/category/etc.
- `export_ledger(format, output_path)`: exports ledger to a file (`format` supports `csv` and `json`).
- `add_ledger_correction(original_entry_id, corrected_fields, reason)`: appends an audit-safe correction entry.
- `update_memory(instruction, tags=None)`: saves a long-term categorization rule/instruction.
- `list_memory()`: lists saved memory instructions.

## 6. Resources you can read

Some MCP clients can read resources directly (read-only):

- `recite://ledger`: ledger rows
- `recite://memory`: memory text
- `recite://health`: health/status

## 7. Local files created

By default (`RECITE_HOME` not set), files are under `~/.config/recite/`:

- `bookkeeping_transactions.csv` (ledger)
- `long_term_memory.md` (memory instructions)
- `config.toml` (optional configuration)

Notes:

- If you set `RECITE_HOME`, these files are created under that directory instead.
- Ledger corrections are appended as new records (audit-safe).

## 8. First-run checklist

1. Start MCP client with your config.
2. Call `validate_setup()`.
3. Run one `process_receipt(...)` call with `dry_run=True`.
4. Run again with `dry_run=False` after validation.

## 9. Troubleshooting

- API rejected: check `RECITE_API_KEY` and token validity.
- Command not found: use the matching config for `uvx` vs `recite-mcp`.
- No tools in client: validate JSON config and restart MCP client.
- Permissions errors: ensure `RECITE_HOME` points to a writable directory.
- Quick local check (no MCP client): run `recite-mcp --validate` (or `uvx recite-mcp --validate`) to print config/health JSON. Exit code is `0` if an API key is present, otherwise `1`.
- `uvx`/`pip` can’t download from PyPI: you may be on a locked-down network (proxy/firewall). Configure your proxy/index settings or use an environment that can reach PyPI.
