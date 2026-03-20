# E2E Test Run Report — 2026-03-20

**Branch:** `feature/prod02`
**Run date:** 2026-03-20
**Coverage:** 40 tools + 3 resources (43 targets, Phases 0–12)
**Overall result:** All phases passed. Two code-level bugs and one documentation discrepancy found.

---

## Pass / Fail Summary

| Phase | Result | Notes |
|-------|--------|-------|
| 0 — Install & Setup | ✅ | Local state cleared, API pre-cleaned |
| 1 — Setup Verification | ✅ | `get_config`, `validate_setup`, `recite://health` |
| 2 — Local Tools | ✅ | Memory, ledger empty-state assertions |
| 3 — Single Receipt Scanning | ⚠️ PASS (with bug) | T11 failed on first attempt — see BUG-001 |
| 4 — Batch Receipt Processing | ✅ | |
| 5 — Local Ledger Operations | ✅ | Correction, CSV/JSON export |
| 6 — Project Management | ✅ | |
| 7 — Transaction CRUD | ✅ | list, get, update, import (list + CSV) |
| 8 — Async Batch Scan | ✅ | Completed in ~24 s |
| 9 — Webhooks & Rules | ✅ | Create, list, update (deactivate + re-enable) |
| 10 — Preferences | ✅ | Categories and vendors |
| 11 — Analytics & Export | ✅ | See DOC-001 for JSON export shape discrepancy |
| 12 — Cleanup | ✅ | All E2E artifacts deleted, pre-existing data intact |

---

## BUG-001 — Partial failure in `process_receipt` rename path

**Severity:** Medium
**Component:** `src/recite_mcp/tools.py` — `process_receipt`
**Discovered in:** T11 (Phase 3)

### What happened

`rename_test_raw.png` was scanned as `Best Buy / 2026-03-20 / $372.97`, so the
rename target would be `2026-03-20_BestBuy_372.97.png`. That file already existed
in `receipts/` (left by a prior run). The tool raised a rename collision and returned:

```json
{
  "status": "error",
  "message": "Cannot rename: destination already exists: 2026-03-20_BestBuy_372.97.png",
  "ledger_entry": { "entry_id": "da8d09b5-...", "entry_type": "receipt", ... },
  "renamed_to": null
}
```

### The bug

The tool **wrote a ledger entry even though the overall status is `"error"`**.
This is a partial failure that leaves the system in an inconsistent state:

- The receipt IS processed and saved to the local ledger.
- The file rename DID NOT happen.
- The caller sees `status: "error"` but there is no way to know whether the scan
  itself failed or whether only the rename failed.

### Impact

- Duplicate ledger entries accumulate across re-runs (each failed T11 attempt adds
  one `entry_type: "receipt"` row for the same source file).
- Any caller that treats `status: "error"` as "nothing was saved" will miss the
  written ledger entry.

### Suggested fix

Two possible approaches:

**Option A — Atomic semantics:** Only write the ledger entry if rename succeeds
(when `rename=True`). Return `status: "error"`, no `ledger_entry`. Force the caller
to retry.

**Option B — Partial-success semantics:** Keep the ledger write, but return a
distinct `status: "partial"` (or `"ok"` with a non-null `rename_error` field) so
the caller knows the scan succeeded but the rename failed. This is friendlier to
callers that care about the data even if the file wasn't renamed.

Either way, the current `status: "error"` + populated `ledger_entry` combination
is misleading and should not be left as-is.

### Reproduction

```
1. Run process_receipt with rename=True on a file whose OCR-derived rename target
   already exists in the same directory.
2. Observe: status="error" in response, but ledger CSV gains a new row.
```

---

## BUG-002 — Test plan gap: stale renamed files not cleaned up in Phase 0-F

**Severity:** Low (test infrastructure only)
**Component:** `docs/plans/2026-03-17-e2e-test-plan.md` — Phase 0-F
**Discovered in:** T11 first attempt (caused by prior run artifact)

### What happened

T11 renames `rename_test_raw.png` → `2026-03-20_BestBuy_372.97.png`.
The plan's Phase 0-F cleanup section does not include a step to remove this output
file before the next run. The plan's post-T11 "Restore fixture" step re-creates
`rename_test_raw.png` but does NOT delete the already-renamed output file.

On the next run, when T11 tries to rename again, the destination already exists,
triggering BUG-001.

### Suggested fix

Add to Phase 0-F (or to the post-T11 restore instructions):

```bash
# Remove stale T11 rename output (adjust pattern if fixture vendor changes)
rm -f receipts/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]_BestBuy_*.png
# Keep the 2026-03-18 baseline; only delete today-dated outputs:
# or more precisely: delete any file whose name matches the rename_test_raw scan result
```

A more robust approach is for `process_receipt` to handle collisions gracefully
(see BUG-001 Option B), which would make T11 less fragile regardless of leftover files.

---

## DOC-001 — `export_transactions` JSON format mismatch in test plan

**Severity:** Low (documentation only)
**Component:** `docs/plans/2026-03-17-e2e-test-plan.md` — T44

### What happened

The plan asserts:
> **Assert:** returns JSON array or download URL.

The actual API response is a wrapper object:
```json
{"transactions": [...]}
```
Not a bare JSON array. The data is present and correct; only the assertion shape
is wrong in the plan.

### Suggested fix

Update the T44 assertion in the plan:
```
**Assert:** returns object with "transactions" key containing a JSON array of
transaction records, or a download URL.
```

---

## Observations (not bugs)

### `list_rules` response format

The API returns two parallel representations of rule logic:
- Legacy: top-level `condition` / `action` objects (simple rules).
- New: `conditions` array + `condition_operator` + `actions` array
  (`transaction_rule` type).

The pre-existing Whole Foods rule uses the new format (`rule_type: "transaction_rule"`,
`conditions: [{"type": "vendor_contains", "value": "Whole "}]`).
The E2E test rule uses the legacy format (`rule_type: "vendor_category"`,
`condition: {"vendor": "Coffee"}`).

Both are valid. The test plan (T33/T34) does not exercise the new `transaction_rule`
format — worth adding in a future test iteration.

### `export_transactions` output size

Both CSV and JSON exports returned the full account history (70+ transactions),
not just the current-month E2E transactions. The CSV was ~52 KB and the JSON ~155 KB.
Consider whether a filtered export (e.g., `start_date` / `end_date`) would be more
appropriate for the E2E assertion, reducing noise and making the assertion
("includes Phase 7 transactions") easier to verify.

---

## Handover: Public API Behaviours

The following are confirmed public API behaviours (not local bugs) observed during
this run. No code changes are needed, but they are worth knowing for future test
and documentation work.

| Item | Behaviour |
|------|-----------|
| `scan_receipt` warnings | Returns `"Transaction date is more than one year old"` for old receipts. Expected. |
| `get_summary period=month` | Returns period `start` = first of current month, `end` = today. |
| `get_usage period=month` | Quota resets on `2026-04-01`; 33 scans used this month. |
| `list_rules` rule types | Two formats coexist: `vendor_category` (legacy) and `transaction_rule` (new). |
| Batch scan turnaround | `submit_batch_scans` → `status: "completed"` in ~24 seconds for 2 images. |
| `export_transactions` JSON | Wrapped as `{"transactions": [...]}`, not a bare array. |
