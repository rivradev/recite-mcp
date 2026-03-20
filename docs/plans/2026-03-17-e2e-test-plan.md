# E2E Test Plan — recite-mcp (2026-03-17)

All 40 MCP tools + 3 resources are covered in sequence. Tests are ordered so each phase
leaves artifacts consumed by the next, and a final cleanup phase deletes everything created.

---

## What You Need to Provide

Before running any test, gather the following:

| Item | How to get it | Used in |
|------|--------------|---------|
| **`RECITE_API_KEY`** | https://recite.rivra.dev/settings/api | All API phases |
| **Receipt image × 2** (JPG/PNG) | Any real or sample receipt photo | Phase 3, 6 |
| **Receipt PDF × 1** | Optional third receipt as PDF | Phase 4 (batch) |
| **Receipt directory path** | Folder containing the images above | Phase 4, 5 |

**Receipt requirements:** Images must be readable (not blurry), contain a visible vendor
name, date, and total amount. A coffee shop or restaurant receipt works well.

---

## Phase 0 — Installation

### 0-A: Install the package

```bash
# Recommended
uvx recite-mcp --version

# Alternatively (editable local dev install)
python -m pip install -e ".[dev]"
python -m recite_mcp.server --version
```

**Pass:** version number printed (e.g., `0.1.7`)

### 0-B: Validate without API key

```bash
RECITE_API_KEY="" python -m recite_mcp.server --validate
```

**Pass:** JSON printed with the shape `{"config": {...}, "health": {...}}` where
`health.has_api_key` is `false` and `health.issues` contains `"missing_api_key"`; exit code 1.

> **Note:** The response wraps both `config` and `health` objects. The assertions below refer
> to fields inside `health`, not at the top level.

### 0-C: Validate with API key

```bash
RECITE_API_KEY="re_live_xxx" python -m recite_mcp.server --validate
```

Replace `re_live_xxx` with the actual key value from `.mcp.json` or your secrets store.

**Pass:** JSON printed where `health.has_api_key` is `true` and `health.issues` is `[]`; exit code 0.

> **Note:** The MCP server process reads `RECITE_API_KEY` and `RECITE_HOME` from `.mcp.json`'s
> `env` block. A plain bash shell does not inherit these. To run Phase 0-C from bash you must
> either source those values manually or read the key from `.mcp.json` before running.

### 0-D: Configure MCP client

Create `.mcp.json` in the project root (already in `.gitignore`):

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

Reload Claude Code and run `/mcp`. **Pass:** `recite` server listed as connected.

### 0-E: Reset local state (required before every run)

Clear the local ledger and memory files so Phase 2 empty-state assertions are reliable on every run.

> **Important:** Use the `recite_home` path reported by `get_config` (T01), **not** `$RECITE_HOME`
> from the shell. The MCP server sets its own home via `.mcp.json` env and it may differ from the
> shell default (`~/.config/recite`). Call `get_config` first to get the correct path.

```
Call get_config → note the recite_home value (e.g. C:\...\recite_mcp\.recite)
```

**Windows (PowerShell):**
```powershell
$home = "C:\...\recite_mcp\.recite"   # paste recite_home value from get_config
Remove-Item "$home\bookkeeping_transactions.csv" -ErrorAction SilentlyContinue
Remove-Item "$home\long_term_memory.md" -ErrorAction SilentlyContinue
```

**Unix / macOS:**
```bash
home="<recite_home from get_config>"
rm -f "$home/bookkeeping_transactions.csv"
rm -f "$home/long_term_memory.md"
```

**Pass:** Both files absent (the server recreates them on first use).

> **Why:** The ledger and memory files are append-only. Without this step, T05 (`summarize_ledger`) and R03 (`recite://ledger`) return stale data from prior runs instead of the expected empty state.

### 0-F: Pre-run API cleanup (recommended if prior runs may have been interrupted)

Search for and delete leftover test artifacts before starting a new run.

**Delete stale transactions:**
```
Call list_transactions with vendor="E2E Test Vendor", limit=50
→ For each transaction_id returned: Call delete_transaction with transaction_id="<id>"

Call list_transactions with vendor="Import Test A", limit=50
→ For each transaction_id returned: Call delete_transaction with transaction_id="<id>"

Call list_transactions with vendor="Import Test B", limit=50
→ For each transaction_id returned: Call delete_transaction with transaction_id="<id>"

Call list_transactions with vendor="CSV Vendor", limit=50
→ For each transaction_id returned: Call delete_transaction with transaction_id="<id>"
```

**Delete stale projects:**
```
Call list_projects
→ For each project where name="E2E Test Project": Call delete_project with project_id="<id>"
```

**Delete stale webhooks:**
```
Call list_webhooks
→ For each webhook where url contains "webhook.site": Call delete_webhook with webhook_id="<id>"
```

**Delete stale rules:**
```
Call list_rules
→ For each rule where condition={"vendor":"Coffee"}: Call delete_rule with rule_id="<id>"
```

**Delete stale rename outputs** (T11 leaves a dated file in `receipts/` after each run):
```bash
# Remove any dated rename output that matches the T11 fixture pattern.
# The fixture (rename_test_raw.png) scans as Best Buy; delete any output
# named YYYY-MM-DD_BestBuy_<amount>.png that is NOT the 2026-03-18 baseline.
ls receipts/ | grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}_BestBuy_" | grep -v "^2026-03-18_" | xargs -I{} rm -f "receipts/{}"
```
*(macOS / Linux — adjust path separator for Windows)*

**Windows (PowerShell):**
```powershell
Get-ChildItem receipts\*BestBuy*.png |
  Where-Object { $_.Name -notlike "2026-03-18_BestBuy*" } |
  Remove-Item
```

**Delete stale categories:**
```
Call get_categories
→ If "E2E Custom Category" appears in custom_categories: Call delete_category with name="E2E Custom Category"
```

**Delete stale vendors:**
```
Call get_vendors
→ If "E2E Test Vendor Co" appears in custom_vendors: Call delete_vendor with name="E2E Test Vendor Co"
```

**Pass:** All the above queries return empty lists (or lists containing only non-test data).

> **Why:** Prior runs that crash or are interrupted before Phase 11 leave projects, transactions, webhooks, and rules on the server. These accumulate across runs and pollute `list_projects`, `list_transactions`, and analytics responses.

---

## Phase 1 — Setup Verification (no API calls)

Run these tools via MCP (in Claude Code):

### T01 — `get_config`
```
Call get_config
```
**Assert:**
- `has_api_key: true`
- `recite_home` points to a real path (e.g., `C:/Users/.../AppData/Roaming/recite` or custom)

### T02 — `validate_setup`
```
Call validate_setup
```
**Assert:**
- `status: "ok"`
- `issues: []`

### R01 — Resource `recite://health`
```
Read resource recite://health
```
**Assert:** same shape as T02.

---

## Phase 2 — Local Tools (no API calls)

### T03 — `update_memory`
```
Call update_memory with instruction="Always categorize coffee receipts as Meals & Entertainment",
tags=["category", "coffee"]
```
**Assert:** response contains `timestamp_utc`, `instruction`, and `tags` fields.

### T04 — `list_memory`
```
Call list_memory
```
**Assert:** returns list with at least one entry matching T03.

### R02 — Resource `recite://memory`
```
Read resource recite://memory
```
**Assert:** raw text includes the instruction added in T03.

### T05 — `summarize_ledger` (empty state)
```
Call summarize_ledger with group_by="vendor"
```
**Assert:** returns `{}` or empty dict (ledger is empty at this point).

### R03 — Resource `recite://ledger` (empty state)
```
Read resource recite://ledger
```
**Assert:** returns `[]`.

---

## Phase 3 — Single Receipt Scanning

> **Requires:** `receipt_1.jpg` (your first receipt image)

### T06 — `scan_receipt` ephemeral (API call, no save)
```
Call scan_receipt with file_path="<path/to/receipt_1.jpg>", ephemeral=true
```
**Assert:**
- `extracted_data.vendor` is not empty
- `extracted_data.amount` is a positive number (field is `amount`, not `total`)
- `extracted_data.date` is present
- No `scan_id` in response (ephemeral)

### T07 — `scan_receipt` with save (capture scan_id)
```
Call scan_receipt with file_path="<path/to/receipt_1.jpg>", ephemeral=false
```
**Assert:**
- Same fields as T06
- Response includes a top-level `scan_id` (save for T08)

### T08 — `get_scan`
```
Call get_scan with scan_id="<id from T07>"
```
**Assert:** returns the same scan data as T07.

### T09 — `process_receipt` dry run
```
Call process_receipt with file_path="<path/to/receipt_1.jpg>", dry_run=true
```
**Assert:**
- `status: "ok"`, `message: "dry_run"`
- `receipt` object has vendor/date/total
- No ledger entry written (verify ledger still empty via R03)

### T10 — `process_receipt` full (write to ledger)
```
Call process_receipt with file_path="<path/to/receipt_1.jpg>",
rename=false, dry_run=false
```
**Assert:**
- `status: "ok"`, `message: "processed"`
- `ledger_entry` has `entry_id` (save for Phase 7)
- `ledger_entry.entry_type: "receipt"`

### T11 — `process_receipt` with rename

> **Important:** Use the dedicated rename fixture `receipts/rename_test_raw.png`,
> **not** a file already named in `YYYY-MM-DD_Vendor_Amount` format. Using a
> pre-named file makes `renamed_to` equal to the original path (no-op rename),
> which passes the assertions but does not exercise the rename code path.
> The fixture is a copy of an existing receipt saved under an unformatted name.

```
Call process_receipt with file_path="<repo_root>/receipts/rename_test_raw.png",
rename=true, dry_run=false
```
**Assert:**
- `renamed_to` field is not null
- `renamed_to` **differs from** the input path (actual rename occurred)
- Renamed file follows pattern `YYYY-MM-DD_Vendor_Amount.png`
- File exists at the `renamed_to` path
- Original path `rename_test_raw.png` no longer exists

**Restore fixture after test:**
```bash
# Re-create the fixture for the next run (copy any existing receipt)
cp receipts/<any_existing_receipt>.png receipts/rename_test_raw.png

# IMPORTANT: Also delete the dated rename output so the next run has a clean target.
# The output name matches whatever date/vendor/amount the fixture scans as.
# If the fixture is a Best Buy receipt, the output will be YYYY-MM-DD_BestBuy_NNN.png.
# Remove it (keep the 2026-03-18 baseline):
ls receipts/ | grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}_BestBuy_" | grep -v "^2026-03-18_" | xargs -I{} rm -f "receipts/{}"
```

---

## Phase 4 — Batch Receipt Processing

> **Requires:** a directory containing at least 2 receipt images (use the same receipts)

### T12 — `process_receipts_batch` dry run
```
Call process_receipts_batch with input_dir="<path/to/receipts/dir>",
dry_run=true, recursive=true
```
**Assert:**
- `status: "ok"`
- `preview_count >= 2`
- Each item has `status: "preview"`
- `processed: 0`, `failed: 0`

### T13 — `process_receipts_batch` live
```
Call process_receipts_batch with input_dir="<path/to/receipts/dir>",
dry_run=false, rename=false, recursive=false
```
**Assert:**
- `processed >= 1`
- `failed: 0`
- Each item has `entry_id`

---

## Phase 5 — Local Ledger Operations

After T10/T11/T13, the ledger has at least 3 entries.

### T14 — `summarize_ledger` by vendor
```
Call summarize_ledger with group_by="vendor"
```
**Assert:** at least one vendor key with `count >= 1` and `total > 0`.

### T15 — `summarize_ledger` by category
```
Call summarize_ledger with group_by="category"
```
**Assert:** keys reflect categories from scanned receipts.

### R04 — Resource `recite://ledger` (populated)
```
Read resource recite://ledger
```
**Assert:** returns list with at least 3 entries; each has `entry_id`, `vendor`, `total`.

### T16 — `add_ledger_correction`
```
Call add_ledger_correction with
  original_entry_id="<entry_id from T10>",
  corrected_fields={"category": "Office Supplies"},
  reason="Wrong category assigned by OCR"
```
**Assert:**
- `entry_type: "correction"`
- `ref_entry_id` matches the original entry_id
- `correction_reason` is set

### T17 — `export_ledger` CSV
```
Call export_ledger with format="csv", output_path="~/recite_test_export.csv"
```
**Assert:**
- `status: "ok"`
- File exists at the output path
- File is non-empty

### T18 — `export_ledger` JSON
```
Call export_ledger with format="json", output_path="~/recite_test_export.json"
```
**Assert:** valid JSON file containing all ledger entries including the correction from T16.

---

## Phase 6 — Project Management

### T19 — `create_project`
```
Call create_project with name="E2E Test Project", description="Created by automated E2E test"
```
**Assert:** returns a project object with `project_id` field (save as `test_project_id`).

### T20 — `list_projects`
```
Call list_projects
```
**Assert:** project from T19 appears in the list.

### T21 — `update_project`
```
Call update_project with project_id="<test_project_id>",
description="Updated by E2E test"
```
**Assert:** response shows updated description.

---

## Phase 7 — Transaction CRUD

### T22 — `create_transaction`
```
Call create_transaction with transaction={
  "vendor": "E2E Test Vendor",
  "date": "2026-03-17",
  "amount": 42.00,
  "currency": "USD",
  "category": "Testing",
  "transaction_type": "Expense",
  "payment_method": "Credit Card"
}
```
**Assert:** response has `transaction_id` (save as `test_transaction_id`).

### T23 — `list_transactions`
```
Call list_transactions with vendor="E2E Test Vendor", limit=10
```
**Assert:** the transaction from T22 appears.

### T24 — `get_transaction`
```
Call get_transaction with transaction_id="<test_transaction_id>"
```
**Assert:** returns the same data as T22.

### T25 — `update_transaction`
```
Call update_transaction with transaction_id="<test_transaction_id>",
changes={"category": "Updated Category", "amount": 43.50}
```
**Assert:** response reflects updated fields.

### T26 — `import_transactions` via list
```
Call import_transactions with transactions=[
  {"vendor": "Import Test A", "date": "2026-03-17", "amount": 10.00, "currency": "USD",
   "transaction_type": "Expense", "category": "Testing", "payment_method": "Credit Card"},
  {"vendor": "Import Test B", "date": "2026-03-17", "amount": 20.00, "currency": "USD",
   "transaction_type": "Expense", "category": "Testing", "payment_method": "Credit Card"}
], all_or_nothing=true
```
**Assert:** both transactions imported; response has success count.

### T27 — `import_transactions` via CSV text
```
Call import_transactions with csv_text="vendor,date,amount,currency,transaction_type,category,payment_method\nCSV Vendor,2026-03-17,15.00,USD,Expense,Testing,Credit Card"
```
**Assert:** 1 transaction imported.

---

## Phase 8 — Batch Scan (Async)

> **Requires:** 2 receipt images accessible as local files.
> **Important:** Use images that were NOT renamed by T11. If T11 used `receipt_2.jpg` for rename testing, pick different files here (e.g. `receipt_1.jpg` and a third image).

### T28 — `submit_batch_scans`
```
Call submit_batch_scans with items=[
  {"file_path": "<path/to/receipt_1.jpg>"},
  {"file_path": "<path/to/receipt_3.jpg>"}
], auto_save=false
```
**Assert:** response has `job_id` (save for T29/T30).

### T29 — `get_batch_scan_status` (poll until complete)
```
Call get_batch_scan_status with job_id="<job_id from T28>"
```
Repeat every ~5 seconds until `status` is `"completed"` or `"failed"`.
**Assert:** eventual `status: "completed"`.

### T30 — `get_batch_scan_results`
```
Call get_batch_scan_results with job_id="<job_id from T28>"
```
**Assert:**
- Returns list of results equal to items submitted
- Each result has `vendor` (may be `null` if unreadable), `amount`, `date`

---

## Phase 9 — Webhooks & Rules

### T31 — `create_webhook`
```
Call create_webhook with url="https://webhook.site/<your-test-id>",
events=["batch.completed", "transaction.created"]
```
> For `url`: use https://webhook.site to get a free test endpoint.
> Valid events: `transaction.created`, `transaction.updated`, `transaction.deleted`, `batch.completed`.

**Assert:** response has `webhook_id` (save as `test_webhook_id`).

### T32 — `list_webhooks`
```
Call list_webhooks
```
**Assert:** webhook from T31 appears in the list (matched by `webhook_id`).

### T33 — `create_rule`
```
Call create_rule with
  rule_type="vendor_category",
  condition={"vendor": "Coffee"},
  action={"set_category": "Meals & Entertainment"},
  priority=10
```
> Valid rule types: `vendor_category`, `default_project`, `processing_preference`.
> Valid condition keys for `vendor_category`: `vendor` (exact match only — the API does not support `vendor_contains`).

**Assert:** response has `rule_id` (save as `test_rule_id`).

### T34 — `list_rules`
```
Call list_rules
```
**Assert:** rule from T33 appears (matched by `rule_id`).

### T35 — `update_rule`
```
Call update_rule with rule_id="<test_rule_id from T33>",
changes={"active": false}
```
**Assert:**
- Response includes the full updated rule object
- `active: false` is reflected in the response
- `rule_id` matches `test_rule_id`

Re-enable for cleanup:
```
Call update_rule with rule_id="<test_rule_id from T33>",
changes={"active": true}
```
**Assert:** `active: true` in response.

---

## Phase 10 — Preferences (Categories & Vendors)

### T36 — `get_categories` (initial state)
```
Call get_categories
```
**Assert:**
- Response contains `default_categories`, `custom_categories`, and `all_categories`
- `default_categories` has exactly 17 entries (the built-in list)
- `all_categories` is the sorted union of both arrays

### T37 — `create_category`
```
Call create_category with name="E2E Custom Category"
```
**Assert:**
- Response has `name: "E2E Custom Category"`
- Calling `get_categories` again shows `"E2E Custom Category"` in `custom_categories` and `all_categories`

### T38 — `get_vendors` (initial state)
```
Call get_vendors
```
**Assert:**
- Response contains `custom_vendors` (may be empty or contain pre-existing vendors)

### T39 — `create_vendor`
```
Call create_vendor with name="E2E Test Vendor Co"
```
**Assert:**
- Response has `name: "E2E Test Vendor Co"`
- Calling `get_vendors` again shows `"E2E Test Vendor Co"` in `custom_vendors`

---

## Phase 11 — Analytics & Export

### T40 — `get_summary`
```
Call get_summary with period="month"
```
**Assert:** response has totals, count, or grouped breakdown.

### T41 — `get_summary` by date range
```
Call get_summary with start_date="2026-03-01", end_date="2026-03-31",
group_by="category"
```
**Assert:** response includes the transactions created in Phase 7.

### T42 — `get_usage`
```
Call get_usage with period="month"
```
**Assert:** shows scan count for current month (should be > 0 after Phase 3).

### T43 — `export_transactions` CSV
```
Call export_transactions with format="csv"
```
**Assert:** returns CSV content or download URL.

### T44 — `export_transactions` JSON
```
Call export_transactions with format="json"
```
**Assert:** returns JSON array or download URL.

---

## Phase 12 — Cleanup

Delete everything created during the test to keep the account clean.

### T45 — Delete test category
```
Call delete_category with name="E2E Custom Category"
```
**Assert:** `{"status": "deleted", "name": "E2E Custom Category"}` returned.
Verify: calling `get_categories` no longer shows it in `custom_categories`.

### T46 — Delete test vendor
```
Call delete_vendor with name="E2E Test Vendor Co"
```
**Assert:** `{"status": "deleted", "name": "E2E Test Vendor Co"}` returned.
Verify: calling `get_vendors` no longer shows it in `custom_vendors`.

### T47 — Delete test rule
```
Call delete_rule with rule_id="<test_rule_id from T33>"
```
**Assert:** success response.

### T48 — Delete test webhook
```
Call delete_webhook with webhook_id="<test_webhook_id from T31>"
```
**Assert:** success response.

### T49 — Delete imported transactions
```
Call list_transactions with vendor="Import Test A"
→ delete each returned transaction_id
Call list_transactions with vendor="Import Test B"
→ delete each returned transaction_id
Call list_transactions with vendor="CSV Vendor"
→ delete each returned transaction_id
```
**Assert:** all deletes succeed.

### T50 — Delete E2E test transaction
```
Call delete_transaction with transaction_id="<test_transaction_id from T22>"
```
**Assert:** success response.

### T51 — Delete test project
```
Call delete_project with project_id="<test_project_id from T19>"
```
**Assert:** success response.

---

## Test Coverage Summary

| Phase | Tools Covered | API Calls | Local Only |
|-------|--------------|-----------|------------|
| 0 — Install & Setup | CLI, local state reset, API pre-cleanup | — | ✓ |
| 1 — Setup | `get_config`, `validate_setup`, `recite://health` | — | ✓ |
| 2 — Local | `update_memory`, `list_memory`, `summarize_ledger`, `recite://memory`, `recite://ledger` | — | ✓ |
| 3 — Single scan | `scan_receipt`, `get_scan`, `process_receipt` | ✓ | — |
| 4 — Batch local | `process_receipts_batch` | ✓ | — |
| 5 — Ledger ops | `summarize_ledger`, `add_ledger_correction`, `export_ledger`, `recite://ledger` | — | ✓ |
| 6 — Projects | `create_project`, `list_projects`, `update_project` | ✓ | — |
| 7 — Transactions | `create_transaction`, `list_transactions`, `get_transaction`, `update_transaction`, `import_transactions` | ✓ | — |
| 8 — Async batch | `submit_batch_scans`, `get_batch_scan_status`, `get_batch_scan_results` | ✓ | — |
| 9 — Webhooks/Rules | `create_webhook`, `list_webhooks`, `create_rule`, `list_rules`, `update_rule` | ✓ | — |
| 10 — Preferences | `get_categories`, `create_category`, `get_vendors`, `create_vendor` | ✓ | — |
| 11 — Analytics | `get_summary`, `get_usage`, `export_transactions` | ✓ | — |
| 12 — Cleanup | `delete_category`, `delete_vendor`, `delete_rule`, `delete_webhook`, `delete_transaction`, `delete_project` | ✓ | — |

**Total: 40 tools + 3 resources = 43 test targets**

---

## Checklist Before Starting

- [ ] `RECITE_API_KEY` obtained from https://recite.rivra.dev/settings/api
- [ ] 2× receipt JPG/PNG images ready (real receipts or clear sample photos)
- [ ] 1× receipt PDF ready (optional, for batch testing)
- [ ] A folder containing those images, e.g., `~/receipts/`
- [ ] `receipts/rename_test_raw.png` fixture exists (copy of any receipt with an unformatted name — used by T11)
- [ ] A free webhook test URL from https://webhook.site
- [ ] `.mcp.json` created with your API key
- [ ] Claude Code reloaded and `recite` server showing as connected (`/mcp`)
- [ ] Phase 0-C passes (exit code 0 from `--validate`)
- [ ] Phase 0-E run: `bookkeeping_transactions.csv` and `long_term_memory.md` deleted from `$RECITE_HOME`
- [ ] Phase 0-F run (if re-running): no leftover "E2E Test" artifacts in list_projects / list_transactions / list_webhooks / list_rules / get_categories / get_vendors
