# Recite MCP Reference

This document describes the MCP surface implemented by `recite-mcp` today.

It is an implementation reference for the server in `src/recite_mcp/server.py`, not a generic product overview. If there is any conflict between this file and older planning notes, this file should be treated as the current MCP behavior.

## Overview

`recite-mcp` exposes:

- 33 MCP tools
- 3 MCP resources

The server combines two kinds of capability:

- Recite API tools that call the public Recite REST API
- Local agent tools that write to or read from files under `RECITE_HOME`

## Runtime Behavior

### API key behavior

- The server can start without `RECITE_API_KEY`.
- `get_config`, `validate_setup`, and the read-only resources work without an API key.
- Any tool that talks to the Recite API fails with `Missing API key.` if `RECITE_API_KEY` is not set.

### Data locations

By default, local files live under `RECITE_HOME`:

- Ledger CSV: `bookkeeping_transactions.csv`
- Memory Markdown: `long_term_memory.md`

### Response behavior

- JSON API responses are returned to the MCP client largely unchanged.
- Non-JSON API responses, such as CSV export responses, are returned as:

```json
{
  "content_type": "text/csv",
  "body": "..."
}
```

- Delete-style tools return a small MCP-friendly status object such as:

```json
{
  "status": "deleted",
  "transaction_id": "txn_123"
}
```

### Local convenience inputs

The MCP layer adds a few agent-friendly inputs on top of the raw REST API:

- `scan_receipt` accepts `file_path` and converts the file to base64 before calling `/scan`
- `submit_batch_scans` batch items may use `file_path`, which is converted to base64 per item
- `import_transactions` accepts `csv_file_path` and reads the CSV from disk before calling `/import/transactions`

### Validation performed locally before API calls

`recite-mcp` performs the following checks before sending requests:

- `scan_receipt` requires exactly one of `file_path`, `image_url`, `image_base64`, or `raw_text`
- `scan_receipt` rejects `ephemeral=true` together with `auto_save=true`
- `scan_receipt` requires `project_id` when `auto_save=true`
- `scan_receipt` requires `image_url` to start with `https://`
- `import_transactions` requires exactly one of `transactions`, `csv_text`, or `csv_file_path`
- `submit_batch_scans` requires each item to contain exactly one of `file_path`, `image_url`, or `image_base64`
- `submit_batch_scans` requires each `image_url` item to start with `https://`
- Local file-based inputs fail early if the referenced file does not exist

## Tool Index

| Tool | Kind | Backed By | Purpose |
| --- | --- | --- | --- |
| `process_receipt` | Local + API | `POST /scan` + local ledger | Scan one local receipt file and optionally write it to the local ledger |
| `process_receipts_batch` | Local + API | repeated `process_receipt` | Scan a local folder of receipt files |
| `scan_receipt` | API | `POST /scan` | Call the Recite scan API directly |
| `get_scan` | API | `GET /scan/:id` | Fetch a previously created scan |
| `create_transaction` | API | `POST /transactions` | Create a manual transaction |
| `list_transactions` | API | `GET /transactions` | List transactions with filters |
| `get_transaction` | API | `GET /transactions/:id` | Fetch one transaction |
| `update_transaction` | API | `PATCH /transactions/:id` | Update selected transaction fields |
| `delete_transaction` | API | `DELETE /transactions/:id` | Delete a transaction |
| `import_transactions` | API | `POST /import/transactions` | Bulk import transactions from JSON or CSV |
| `submit_batch_scans` | API | `POST /batch/scans` | Submit asynchronous batch scan jobs |
| `get_batch_scan_status` | API | `GET /batch/scans/:jobId` | Fetch batch job status |
| `get_batch_scan_results` | API | `GET /batch/scans/:jobId/results` | Fetch batch job results |
| `list_projects` | API | `GET /projects` | List projects |
| `create_project` | API | `POST /projects` | Create a project |
| `update_project` | API | `PATCH /projects/:id` | Update a project |
| `delete_project` | API | `DELETE /projects/:id` | Delete a project |
| `get_summary` | API | `GET /summary` | Fetch aggregated financial summary |
| `create_webhook` | API | `POST /webhooks` | Register a webhook |
| `list_webhooks` | API | `GET /webhooks` | List webhooks |
| `delete_webhook` | API | `DELETE /webhooks/:id` | Delete a webhook |
| `create_rule` | API | `POST /rules` | Create an automation rule |
| `list_rules` | API | `GET /rules` | List rules |
| `delete_rule` | API | `DELETE /rules/:id` | Delete a rule |
| `get_usage` | API | `GET /usage` | Fetch usage and quota information |
| `export_transactions` | API | `POST /export` | Export transactions as JSON or CSV |
| `update_memory` | Local | memory file | Append an instruction to long-term memory |
| `list_memory` | Local | memory file | Return parsed memory entries |
| `add_ledger_correction` | Local | ledger CSV | Append an audit correction row |
| `summarize_ledger` | Local | ledger CSV | Group and total local ledger rows |
| `export_ledger` | Local | ledger CSV | Export local ledger as CSV or JSON |
| `get_config` | Local | runtime settings | Return non-secret configuration details |
| `validate_setup` | Local | runtime settings | Return installation and health status |

## Tool Reference

### `process_receipt`

Purpose: Scan one local receipt file through Recite and optionally persist the result to the local ledger.

Parameters:

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `file_path` | `str` | Yes | - | Path to a local receipt file |
| `rename` | `bool` | No | `false` | Rename the source file after processing |
| `category_hint` | `str \| null` | No | `null` | Override the detected category locally |
| `dry_run` | `bool` | No | `false` | Scan only, do not write ledger or rename file |

Behavior:

- Expands the provided path.
- Calls the Recite scan API with the file encoded as base64 and `auto_save=false`.
- Converts the response into a local `ReceiptRecord`.
- If `category_hint` is set, the returned category is overridden before any local write.
- If `dry_run=true`, returns the parsed receipt without writing the ledger.
- Otherwise appends one row to the local ledger CSV.
- If `rename=true`, renames the file to `{date}_{safe_vendor}_{total:.2f}{ext}`.

Return shape:

```json
{
  "status": "ok",
  "message": "processed",
  "ledger_entry": {
    "entry_id": "...",
    "timestamp_utc": "...",
    "entry_type": "receipt",
    "vendor": "...",
    "date": "YYYY-MM-DD",
    "total": 0.0,
    "tax": 0.0,
    "currency": "USD",
    "category": "...",
    "source_file": "..."
  },
  "receipt": {
    "vendor": "...",
    "date": "YYYY-MM-DD",
    "total": 0.0,
    "tax": 0.0,
    "currency": "USD",
    "category": "..."
  },
  "renamed_to": "..."
}
```

### `process_receipts_batch`

Purpose: Process a local directory of receipt files using `process_receipt`.

Parameters:

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `input_dir` | `str` | Yes | - | Folder containing receipt files |
| `rename` | `bool` | No | `false` | Rename files after successful processing |
| `dry_run` | `bool` | No | `true` | Preview only by default |
| `recursive` | `bool` | No | `true` | Recurse into subdirectories |

Behavior:

- Scans for files ending in `.png`, `.jpg`, `.jpeg`, or `.pdf`.
- In `dry_run` mode, returns a preview list and does not call the API.
- In write mode, processes each file one by one.
- Records per-file success or error in the returned `items` list.

Return shape:

```json
{
  "status": "ok",
  "processed": 0,
  "failed": 0,
  "preview_count": 0,
  "items": []
}
```

### `scan_receipt`

Purpose: Direct MCP wrapper for the Recite `POST /scan` endpoint.

Parameters:

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `file_path` | `str \| null` | No | `null` | Local file convenience input |
| `image_url` | `str \| null` | No | `null` | Public HTTPS image URL |
| `image_base64` | `str \| null` | No | `null` | Base64 image payload |
| `raw_text` | `str \| null` | No | `null` | Raw receipt text |
| `auto_save` | `bool` | No | `false` | Ask Recite to auto-create a transaction |
| `save_threshold` | `str \| null` | No | `null` | Confidence threshold passed through to Recite |
| `project_id` | `str \| null` | No | `null` | Required when `auto_save=true` |
| `status` | `str \| null` | No | `null` | Transaction status passed through to Recite |
| `image_type` | `str \| null` | No | `null` | MIME type hint |
| `idempotency_key` | `str \| null` | No | `null` | Idempotency key |
| `metadata` | `dict \| null` | No | `null` | Metadata object |
| `ephemeral` | `bool` | No | `false` | Ask Recite not to persist the scan record |

Behavior:

- Requires exactly one input source.
- Converts `file_path` to base64 before sending.
- Guesses `image_type` from the file extension if `file_path` is used and `image_type` is omitted.
- Rejects `ephemeral=true` together with `auto_save=true`.
- Rejects `auto_save=true` without `project_id`.
- Rejects non-HTTPS `image_url`.

Returns:

- The Recite JSON response envelope for JSON responses.
- This is the preferred tool for agents that want full Recite scan output instead of the simplified local `ReceiptRecord`.

### `get_scan`

Purpose: Fetch a scan result by scan ID.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `scan_id` | `str` | Yes | Scan identifier returned by `scan_receipt` |

Returns:

- The JSON response from `GET /scan/:id`.

### `create_transaction`

Purpose: Create a transaction manually through Recite.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `transaction` | `dict` | Yes | Transaction payload to send to `POST /transactions` |

Behavior:

- Removes keys whose values are `null` before sending.

Returns:

- The JSON response from `POST /transactions`.

### `list_transactions`

Purpose: List transactions with filters and pagination.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `start_date` | `str \| null` | No | `null` |
| `end_date` | `str \| null` | No | `null` |
| `transaction_type` | `str \| null` | No | `null` |
| `category` | `str \| null` | No | `null` |
| `vendor` | `str \| null` | No | `null` |
| `payment_method` | `str \| null` | No | `null` |
| `amount_min` | `float \| int \| null` | No | `null` |
| `amount_max` | `float \| int \| null` | No | `null` |
| `status` | `str \| null` | No | `null` |
| `project_id` | `str \| null` | No | `null` |
| `source` | `str \| null` | No | `null` |
| `agent_name` | `str \| null` | No | `null` |
| `sort_by` | `str \| null` | No | `null` |
| `sort_order` | `str \| null` | No | `null` |
| `limit` | `int \| null` | No | `null` |
| `offset` | `int \| null` | No | `null` |
| `format` | `str \| null` | No | `null` |

Behavior:

- Only sends parameters whose values are not `null`.

Returns:

- The JSON response from `GET /transactions`.

### `get_transaction`

Purpose: Fetch one transaction by ID.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `transaction_id` | `str` | Yes | Transaction identifier |

Returns:

- The JSON response from `GET /transactions/:id`.

### `update_transaction`

Purpose: Update selected transaction fields.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `transaction_id` | `str` | Yes | Transaction identifier |
| `changes` | `dict` | Yes | Patch payload |

Behavior:

- Removes keys whose values are `null` before sending.

Returns:

- The JSON response from `PATCH /transactions/:id`.

### `delete_transaction`

Purpose: Delete a transaction.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `transaction_id` | `str` | Yes | Transaction identifier |

Returns:

```json
{
  "status": "deleted",
  "transaction_id": "..."
}
```

### `import_transactions`

Purpose: Bulk import transactions through Recite.

Parameters:

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `transactions` | `list[dict] \| null` | No | `null` | JSON import payload |
| `csv_text` | `str \| null` | No | `null` | Raw CSV content |
| `csv_file_path` | `str \| null` | No | `null` | Local CSV convenience input |
| `all_or_nothing` | `bool \| null` | No | `null` | Passed through to Recite |
| `project_id` | `str \| null` | No | `null` | Default project for imported rows |

Behavior:

- Requires exactly one of `transactions`, `csv_text`, or `csv_file_path`.
- If `csv_file_path` is used, reads the file from disk first.
- JSON imports are sent as `application/json`.
- CSV imports are sent as `text/csv`.
- For CSV imports, `all_or_nothing` is sent as the lowercase query string value `true` or `false`.

Returns:

- The JSON response from `POST /import/transactions`.

### `submit_batch_scans`

Purpose: Submit a batch scan job to Recite.

Parameters:

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `items` | `list[dict]` | Yes | - | Batch items |
| `auto_save` | `bool` | No | `false` | Ask Recite to auto-save passing scans |
| `save_threshold` | `str \| null` | No | `null` | Confidence threshold |
| `project_id` | `str \| null` | No | `null` | Project for auto-saved transactions |
| `webhook_url` | `str \| null` | No | `null` | Batch completion webhook URL |
| `webhook_secret` | `str \| null` | No | `null` | Webhook signing secret |

Each item may contain:

- `file_path`
- `image_url`
- `image_base64`
- `metadata`
- `image_type`

Behavior:

- Each item must contain exactly one of `file_path`, `image_url`, or `image_base64`.
- `file_path` items are converted to base64 before sending.
- For `file_path` items, `image_type` is guessed from the filename when not supplied.
- `image_url` items must use `https://`.

Returns:

- The JSON response from `POST /batch/scans`.

### `get_batch_scan_status`

Purpose: Fetch the status of a batch job.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `job_id` | `str` | Yes | Batch job identifier |

Returns:

- The JSON response from `GET /batch/scans/:jobId`.

### `get_batch_scan_results`

Purpose: Fetch batch scan results.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `job_id` | `str` | Yes | Batch job identifier |

Returns:

- The JSON response from `GET /batch/scans/:jobId/results`.

### `list_projects`

Purpose: List projects.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `status` | `str \| null` | No | `null` |
| `limit` | `int \| null` | No | `null` |
| `offset` | `int \| null` | No | `null` |
| `format` | `str \| null` | No | `null` |

Returns:

- The JSON response from `GET /projects`.

### `create_project`

Purpose: Create a project.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `name` | `str` | Yes | - |
| `description` | `str \| null` | No | `null` |

Returns:

- The JSON response from `POST /projects`.

### `update_project`

Purpose: Update a project.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `project_id` | `str` | Yes | - |
| `name` | `str \| null` | No | `null` |
| `description` | `str \| null` | No | `null` |
| `status` | `str \| null` | No | `null` |

Behavior:

- Removes keys whose values are `null` before sending.

Returns:

- The JSON response from `PATCH /projects/:id`.

### `delete_project`

Purpose: Delete a project.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `project_id` | `str` | Yes | Project identifier |

Returns:

```json
{
  "status": "deleted",
  "project_id": "..."
}
```

### `get_summary`

Purpose: Fetch an aggregated financial summary.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `period` | `str \| null` | No | `null` |
| `start_date` | `str \| null` | No | `null` |
| `end_date` | `str \| null` | No | `null` |
| `project_id` | `str \| null` | No | `null` |
| `group_by` | `str \| null` | No | `null` |

Returns:

- The JSON response from `GET /summary`.

### `create_webhook`

Purpose: Register a webhook.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `url` | `str` | Yes | - |
| `events` | `list[str]` | Yes | - |
| `secret` | `str \| null` | No | `null` |

Returns:

- The JSON response from `POST /webhooks`.

Note:

- If Recite returns a webhook secret, this tool passes it through to the MCP client. Treat it as sensitive.

### `list_webhooks`

Purpose: List registered webhooks.

Parameters: none

Returns:

- The JSON response from `GET /webhooks`.

### `delete_webhook`

Purpose: Delete a webhook.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `webhook_id` | `str` | Yes | Webhook identifier |

Returns:

```json
{
  "status": "deleted",
  "webhook_id": "..."
}
```

### `create_rule`

Purpose: Create an automation rule.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `rule_type` | `str` | Yes | - |
| `condition` | `dict` | Yes | - |
| `action` | `dict` | Yes | - |
| `priority` | `int \| null` | No | `null` |

Returns:

- The JSON response from `POST /rules`.

### `list_rules`

Purpose: List automation rules.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `limit` | `int \| null` | No | `null` |
| `offset` | `int \| null` | No | `null` |

Returns:

- The JSON response from `GET /rules`.

### `delete_rule`

Purpose: Delete an automation rule.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `rule_id` | `str` | Yes | Rule identifier |

Returns:

```json
{
  "status": "deleted",
  "rule_id": "..."
}
```

### `get_usage`

Purpose: Fetch API usage and quota information.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `period` | `str \| null` | No | `null` |
| `breakdown` | `str \| null` | No | `null` |

Returns:

- The JSON response from `GET /usage`.

### `export_transactions`

Purpose: Export transactions from Recite.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `format` | `str` | Yes | - |
| `filters` | `dict \| null` | No | `null` |

Returns:

- For JSON exports, the JSON response from `POST /export`
- For CSV exports, a two-field object:

```json
{
  "content_type": "text/csv",
  "body": "transaction_id,amount,..."
}
```

### `update_memory`

Purpose: Append one long-term memory instruction to the local memory file.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `instruction` | `str` | Yes | - |
| `tags` | `list[str] \| null` | No | `null` |

Behavior:

- Writes to `long_term_memory.md` under `RECITE_HOME`.

Returns:

```json
{
  "timestamp_utc": "...",
  "instruction": "...",
  "tags": ["..."]
}
```

### `list_memory`

Purpose: Return parsed local memory entries.

Parameters: none

Returns:

- A list of memory entries.

### `add_ledger_correction`

Purpose: Append an audit correction row to the local ledger.

Parameters:

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `original_entry_id` | `str` | Yes | Entry being corrected |
| `corrected_fields` | `dict` | Yes | Corrected values |
| `reason` | `str` | Yes | Human-readable reason |

Behavior:

- Does not overwrite the original ledger row.
- Appends a new row with `entry_type="correction"` and `ref_entry_id` set to the original entry.

Returns:

- The newly created correction row.

### `summarize_ledger`

Purpose: Group and total local receipt rows.

Parameters:

| Name | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `group_by` | `str` | No | `"vendor"` | Attribute name from local ledger rows |

Behavior:

- Only includes rows with `entry_type="receipt"`.
- Ignores correction rows.

Returns:

```json
{
  "Some Group": {
    "count": 2,
    "total": 50.0
  }
}
```

### `export_ledger`

Purpose: Export the local ledger to a file.

Parameters:

| Name | Type | Required | Default |
| --- | --- | --- | --- |
| `format` | `str` | Yes | - |
| `output_path` | `str` | Yes | - |

Behavior:

- Supports `csv` and `json`.
- Creates parent directories for the output path if needed.

Returns:

```json
{
  "status": "ok",
  "path": "..."
}
```

### `get_config`

Purpose: Return non-secret runtime configuration.

Parameters: none

Returns:

```json
{
  "recite_home": "...",
  "api_base_url": "https://recite.rivra.dev/apiV1/api/v1",
  "request_timeout_sec": 30,
  "has_api_key": true
}
```

Notes:

- The API key itself is not returned.

### `validate_setup`

Purpose: Return local health and setup information.

Parameters: none

Returns:

```json
{
  "status": "ok",
  "recite_home": "...",
  "ledger_path": "...",
  "memory_path": "...",
  "has_api_key": true,
  "issues": []
}
```

Possible `status` values:

- `ok`
- `degraded`

Possible `issues` values:

- `missing_api_key`

## Resource Reference

### `recite://ledger`

Read-only resource returning local ledger rows as a list of objects.

Source:

- `bookkeeping_transactions.csv` under `RECITE_HOME`

### `recite://memory`

Read-only resource returning the raw contents of the memory markdown file as a string.

Source:

- `long_term_memory.md` under `RECITE_HOME`

If the file does not exist yet, the resource returns an empty string.

### `recite://health`

Read-only resource returning the same health payload as `validate_setup`.

## Privacy and Security Notes

- `scan_receipt` supports `ephemeral=true` for flows where the agent should avoid creating a persisted scan record in Recite.
- `process_receipt` and `process_receipts_batch` always call the scan API with `auto_save=false`; they do not create Recite transactions.
- `get_config` intentionally returns only `has_api_key`, not the key value.
- `create_webhook` may return a secret from Recite. Treat that return value as sensitive.
- Local ledger exports and memory tools write only to `RECITE_HOME`.

## Error Handling

Errors are surfaced as MCP tool failures by raising `ApiClientError` or standard Python exceptions.

Common failure cases include:

- `Missing API key.`
- `Receipt file does not exist: ...`
- `Import file does not exist: ...`
- `Provide exactly one of file_path, image_url, image_base64, or raw_text.`
- `ephemeral and auto_save cannot both be true.`
- `project_id is required when auto_save is true.`
- `image_url must use https://.`
- `Each batch item must provide exactly one of file_path, image_url, or image_base64.`

HTTP errors from Recite are converted into readable messages when possible by parsing the API error body.
