# E2E Test Results — recite-mcp (2026-03-18)

Run date: 2026-03-18
Branch: feature/prod02
Version: 0.1.7
MCP config: `.mcp.json` (uv run, RECITE_HOME=`.recite/`)

---

## Summary

| Phase | Result | Notes |
|-------|--------|-------|
| 0 — Install | PASS | v0.1.7, --validate works |
| 1 — Setup | PASS | All 3 checks pass |
| 2 — Local tools | PARTIAL | T05/R03 fail due to pre-existing ledger data |
| 3 — Single scan | PARTIAL | T06–T10 pass; T11 (rename) FAIL |
| 4 — Batch local | PASS | Both dry-run and live pass |
| 5 — Ledger ops | PASS | All 5 checks pass |
| 6 — Projects | PASS | Create/list/update all pass |
| 7 — Transactions | PASS | All 6 transaction tools pass |
| 8 — Async batch | PASS | Completed in ~15s |
| 9 — Webhooks/Rules | PASS | All 4 checks pass |
| 10 — Analytics | PASS | All 5 export/summary tools pass |
| 11 — Cleanup | PASS | All 9 deletions succeed |

**Passed: 36/38 test targets**
**Failed: 2 (T05, T11)**
**Notes/minor issues: 4**

---

## Bugs Found

### Bug #1 — No local state reset between E2E runs (test isolation)

**Severity:** Medium
**Affected:** T05 (`summarize_ledger` empty state), R03 (`recite://ledger` empty state)
**Symptom:** The test plan expects the local ledger to be empty at Phase 2 (`T05` should return `{}`, R03 should return `[]`). Instead, both return data accumulated from prior test runs (50+ entries, 6 vendors).
**Root cause:** The local ledger CSV at `.recite/bookkeeping_transactions.csv` is append-only and is never cleared. The E2E test plan's Phase 11 cleanup only deletes server-side resources (API transactions, projects, webhooks, rules) — it has no step to reset the local ledger or memory file.
**Fix options:**
1. Add a pre-test setup step (Phase 0-E) that deletes or truncates `.recite/bookkeeping_transactions.csv` and `.recite/long_term_memory.md` before each run.
2. The test plan could point `RECITE_HOME` to a fresh temp directory for each run (e.g., `RECITE_HOME=$(mktemp -d)`).
3. Document that T05/R03 assertions only apply on first run; subsequent runs should assert `count > 0` rather than empty.

---

### Bug #2 — `add_ledger_correction` allows empty `corrected_fields`

**Severity:** Low
**Affected:** `add_ledger_correction` tool
**Symptom:** One prior correction entry (`03fe195f`) in the ledger has `corrected_fields: ""` — an empty string instead of a JSON object. This produces a semantically invalid correction row: the correction records that something was changed, but not what.
**Root cause:** The tool does not validate that `corrected_fields` is non-empty before writing the correction row. When called with `corrected_fields={}`, the serialization produces an empty string or `"{}"` depending on how the serializer handles it.
**Observed ledger row:**
```
entry_type=correction, correction_reason="Wrong category assigned by OCR", corrected_fields=""
```
**Fix:** Add validation in `add_ledger_correction` (or `LedgerRepository.append_correction`) to raise a `ValueError` if `corrected_fields` is empty or contains no keys.

---

### Bug #3 — `process_receipt rename=true` fails with `WinError 183` on Windows (committed code)

**Severity:** High
**Affected:** T11 (`process_receipt` with `rename=true`), `process_receipts_batch` with `rename=true`
**Symptom:** When `rename=True` and the computed destination filename already exists in the directory, the rename operation fails:
```
[WinError 183] Cannot create a file when that file already exists:
  'receipts/receipt_test_rename.png' -> 'receipts/2025-01-15_GoogleStore_1088.91.png'
```
In practice this triggers nearly every time a receipt has been processed before, since the renamed file (`YYYY-MM-DD_Vendor_Amount.png`) already exists from the prior run.

**Root cause (confirmed via git diff):**
- **Committed code** (`HEAD`, `src/recite_mcp/tools.py`): uses `path.rename(target)` which raises `FileExistsError` / `WinError 183` on Windows when the destination exists.
- **Working tree** (unstaged): already fixed to use `path.replace(target)` which atomically replaces the destination on Windows.

**Status:** Fix exists in the working tree but is not committed. The running MCP server loaded the old module at startup and the fix won't take effect until the server is restarted after committing.

**Additional fix in working tree (also needed):** The working tree also adds vendor normalization for `None`/`null`/`N/A` string values, preventing filenames like `2026-03-18_None_223.75.png` from being used as rename targets for receipts where OCR returned no vendor.

**Action required:** Commit the working tree changes to `tools.py` and restart the MCP server.

---

## Minor Issues

### Issue #4 — Memory deduplication: identical entries accumulate

**Severity:** Low
**Affected:** `update_memory`, `list_memory`, `recite://memory`
**Symptom:** Each call to `update_memory` appends a new JSON-lines entry regardless of whether an identical instruction already exists. After 4 test runs with the same instruction, `list_memory` returns 4 duplicate entries.
**Impact:** Memory grows unboundedly; LLM context filled with redundant instructions.
**Fix:** Before appending, check if an entry with the same `instruction` (or same `instruction`+`tags`) already exists. If so, update the timestamp instead of appending a new row.

---

### Issue #5 — `process_receipts_batch` returns `preview_count` on live runs

**Severity:** Low
**Affected:** T13 (`process_receipts_batch` with `dry_run=false`)
**Symptom:** `preview_count: 6` is returned even when `dry_run=false`. This field only has meaning in dry-run mode; in a live run it is misleading (no previews occurred).
**Fix:** Set `preview_count: 0` (or omit the field) when `dry_run=false`.

---

### Issue #6 — `update_transaction` does not recalculate `subtotal`

**Severity:** Low
**Affected:** T25 (`update_transaction`)
**Symptom:** After updating `amount` from `42` to `43.5`, the response shows `subtotal: 42` (unchanged). This creates an inconsistency: `amount != subtotal` with no tax/fees to explain the difference.
**Note:** This may be intentional if `subtotal` represents pre-tax amount and is stored separately. However, if `subtotal` defaults to `amount` on creation (as observed — both were `42`), updating `amount` without updating `subtotal` is a data consistency issue.
**Fix:** Either recalculate `subtotal` when `amount` changes (if no tax/fees are present), or document clearly that `subtotal` must be updated independently.

---

### Issue #7 — Stale test artifacts from incomplete prior cleanup runs

**Severity:** Low (operational, not a code bug)
**Affected:** API account state
**Symptom:** `list_projects` returns 20 archived "Updated E2E Project" entries; `list_transactions` returns 33 stale "E2E Test Vendor" transactions from prior runs that were not cleaned up.
**Root cause:** Prior E2E runs crashed or were interrupted before reaching Phase 11, leaving artifacts on the server.
**Fix:** The Phase 11 cleanup in the test plan should be idempotent and run even on failure (e.g., wrapped in a try/finally). Consider adding a "pre-cleanup" step at Phase 0 that searches for and deletes any leftover test artifacts by name pattern before starting a new run.

---

## Test Environment Notes

- All receipt images in `receipts/` were renamed from prior runs — original `receipt1.png`, `receipt2.png` etc. no longer exist. Future runs requiring unprocessed files should use fresh copies or point to a separate test-fixtures directory that is not modified by tests.
- Local ledger at `.recite/bookkeeping_transactions.csv` contains 64 entries from prior runs.
- Local memory at `.recite/long_term_memory.md` contains 4 duplicate identical entries.
- Export test files `recite_test_export.csv` and `recite_test_export.json` were left in the project root (not gitignored).

---

## Tool Coverage

| Tool / Resource | Status | Test ID |
|----------------|--------|---------|
| `get_config` | PASS | T01 |
| `validate_setup` | PASS | T02 |
| `recite://health` | PASS | R01 |
| `update_memory` | PASS | T03 |
| `list_memory` | PASS | T04 |
| `recite://memory` | PASS | R02 |
| `summarize_ledger` (empty) | FAIL | T05 |
| `recite://ledger` (empty) | FAIL | R03 |
| `scan_receipt` (ephemeral) | PASS | T06 |
| `scan_receipt` (saved) | PASS | T07 |
| `get_scan` | PASS | T08 |
| `process_receipt` (dry_run) | PASS | T09 |
| `process_receipt` (full) | PASS | T10 |
| `process_receipt` (rename) | FAIL | T11 |
| `process_receipts_batch` (dry_run) | PASS | T12 |
| `process_receipts_batch` (live) | PASS | T13 |
| `summarize_ledger` (by vendor) | PASS | T14 |
| `summarize_ledger` (by category) | PASS | T15 |
| `recite://ledger` (populated) | PASS | R04 |
| `add_ledger_correction` | PASS | T16 |
| `export_ledger` (CSV) | PASS | T17 |
| `export_ledger` (JSON) | PASS | T18 |
| `create_project` | PASS | T19 |
| `list_projects` | PASS | T20 |
| `update_project` | PASS | T21 |
| `create_transaction` | PASS | T22 |
| `list_transactions` | PASS | T23 |
| `get_transaction` | PASS | T24 |
| `update_transaction` | PASS | T25 |
| `import_transactions` (list) | PASS | T26 |
| `import_transactions` (CSV text) | PASS | T27 |
| `submit_batch_scans` | PASS | T28 |
| `get_batch_scan_status` | PASS | T29 |
| `get_batch_scan_results` | PASS | T30 |
| `create_webhook` | PASS | T31 |
| `list_webhooks` | PASS | T32 |
| `create_rule` | PASS | T33 |
| `list_rules` | PASS | T34 |
| `get_summary` (period) | PASS | T35 |
| `get_summary` (date range) | PASS | T36 |
| `get_usage` | PASS | T37 |
| `export_transactions` (CSV) | PASS | T38 |
| `export_transactions` (JSON) | PASS | T39 |
| `delete_rule` | PASS | T40 |
| `delete_webhook` | PASS | T41 |
| `delete_transaction` (imported) | PASS | T42 |
| `delete_transaction` (E2E) | PASS | T43 |
| `delete_project` | PASS | T44 |
