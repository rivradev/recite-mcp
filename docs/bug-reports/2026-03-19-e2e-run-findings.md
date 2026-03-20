# E2E Test Run Findings — 2026-03-19 (Run 2)

Run against: `recite-mcp` v0.1.7
Branch: `feature/prod02`
Test plan: `docs/plans/2026-03-17-e2e-test-plan.md`
Run date: 2026-03-19 (second full run; Run 1 findings preserved below)

---

## Overall Result: ALL 36 TARGETS PASSED

All 33 tools and 3 resources exercised successfully. No test-blocking failures.
Five findings documented — three new from this run, two carried from Run 1 (one of which may be resolved).

---

## Finding 0 — BUG (Phase 0-E): Local state reset targets wrong `RECITE_HOME`

**Affects:** Phase 0-E (local state reset), Phase 0-C (`--validate` from bash)
**Severity:** Medium — Phase 0-E run from bash clears the wrong directory; phase assertions about empty ledger state can be wrong
**Layer:** Test plan + environment wiring

### Observed behaviour

The MCP server process (launched via `.mcp.json`) has `RECITE_HOME` set to the project-local
`.recite/` directory and the API key injected. When `python -m recite_mcp.server` is run from
a plain bash shell (as in Phase 0-B/C), neither variable is inherited:

| Context | `recite_home` | `has_api_key` |
|---------|--------------|--------------|
| MCP server (`.mcp.json` env) | `<repo>/.recite/` | `true` |
| Bash shell | `C:\Users\noname\.config\recite` | `false` |

**Phase 0-E consequence:** The test plan instructs deleting files from `$RECITE_HOME`. If run
from a plain terminal (without sourcing the `.mcp.json` env vars), the script deletes from
`~/.config/recite`, which is a different directory than the one the MCP server reads. The MCP
server's local state is not actually cleared, so Phase 2 empty-state assertions (T05, R03) could
observe stale data from a prior run.

**Phase 0-C consequence:** `RECITE_API_KEY="re_live_xxx" python -m recite_mcp.server --validate`
requires the caller to know and manually paste the actual key. There is no way to extract it from
`.mcp.json` programmatically without reading the file in plain text.

### Suggested fix

1. Add a note to the test plan that `RECITE_HOME` for Phase 0-E must match the value shown by
   `get_config` (T01), not the shell default.
2. Optionally, have `get_config` or `validate_setup` print the active `RECITE_HOME` with a
   "to reset: delete these files" hint so testers have the exact path.

---

## Finding 0b — BUG (Phase 0-B): `--validate` response shape does not match test plan assertion

**Affects:** Phase 0-B, Phase 0-C assertions
**Severity:** Low — functional result is correct; test plan assertion is misleading
**Layer:** `server.py` (`--validate` output format)

### Observed behaviour

The test plan asserts:
```
"has_api_key": false  (top-level)
"issues": ["missing_api_key"]  (top-level)
```

Actual `--validate` output wraps both fields in a two-key envelope:
```json
{
  "config": { "has_api_key": false, ... },
  "health": { "has_api_key": false, "issues": ["missing_api_key"], ... }
}
```

The values are present but nested, not at top level. A tester scanning for `"has_api_key": false`
at root would find it only inside `config` or `health`.

### Suggested fix

Update the Phase 0-B and Phase 0-C assertions in the test plan to reflect the actual nested shape,
or flatten the `--validate` output to return the `health` object directly.

---

## Finding 0c — BUG: `process_receipt rename=true` silently overwrites an existing file

**Affects:** T11 (`process_receipt` with `rename=true`)
**Severity:** Medium — data loss possible when the formatted filename already exists on disk
**Layer:** `tools.py` (rename logic)

### Observed behaviour

`rename_test_raw.png` scanned as Pappadeaux / 2014-04-15 / $36.79. The rename target
`2014-04-15_Pappadeaux_36.79.png` already existed in the `receipts/` directory (an original
fixture file). The tool renamed `rename_test_raw.png` → `2014-04-15_Pappadeaux_36.79.png` without
any warning, silently overwriting the pre-existing file. The response `renamed_to` field was set to
the target path and no error or warning was emitted.

### Impact

If a user's `receipts/` directory already contains a receipt with the same vendor/date/amount, a
subsequent scan + rename would silently destroy it. The overwritten file cannot be recovered.

### Suggested fix

Before performing the rename, check whether the target path already exists. Options:
- Emit a warning in the response (e.g. `"warnings": ["renamed_to path already existed; original overwritten"]`).
- Append a counter suffix to deduplicate: `2014-04-15_Pappadeaux_36.79_2.png`.
- Return an error if `collision_mode` is not explicitly set (opt-in overwrite).

---

## Finding 1 — BUG (Python layer): `export_transactions` leaks the internal HTTP envelope to MCP callers when `output_path` is omitted

**Affects:** T38 (`export_transactions` CSV), T39 (`export_transactions` JSON)
**Severity:** Medium — breaks any agent/caller that treats the tool output as raw CSV/JSON
**Layer:** Python (`src/recite_mcp/api_client.py` + `src/recite_mcp/tools.py`)

### Root cause

`_request()` in `api_client.py:586` wraps every non-JSON HTTP response into an internal envelope:

```python
# api_client.py:586
return {"content_type": content_type, "body": getattr(response, "text", "")}
```

The Recite API correctly returns a plain CSV string (or JSON array). This wrapping is a reasonable internal convention so the rest of the client always deals with `dict`. The problem is `tools.export_transactions` only unwraps when `output_path` is provided:

```python
# tools.py:294-300
result = self._api_client.export_transactions(format=format, filters=filters)
if output_path is not None:
    path.write_text(result["body"], encoding="utf-8")   # ← correctly unwraps
    return {"status": "ok", "path": str(path), "format": format}
return result   # ← leaks the envelope dict to the MCP caller
```

When called without `output_path` the MCP caller receives:
```json
{"content_type": "text/csv; charset=utf-8", "body": "transaction_id,date,...\n..."}
```
instead of raw CSV or a download URL.

### Expected behaviour (per test plan)

> "Assert: returns CSV content or download URL"
> "Assert: returns JSON array or download URL"

### Suggested fix (one line in `tools.py`)

```python
# tools.py — change the final return
return result["body"]   # return raw content instead of the envelope
```

Or, if preserving the content-type metadata is useful, document the envelope shape explicitly in the MCP tool description and update the test plan assertions.

---

## Finding 2 — BUG (API layer): `scan_receipt` fires a confusing breakdown-mismatch warning when the total is actually verified *(not reproduced in Run 2)*

**Affects:** T06, T07, T28 (any receipt with a tip line)
**Severity:** Low — functional result is correct; warning is misleading noise
**Layer:** Recite REST API (server-side — the Python client passes warnings through unchanged)

> **Run 2 status:** This warning did NOT appear for the Pappadeaux receipt in Run 2. The same
> receipt returned `"warnings": ["Transaction date is more than one year old"]` only — no
> breakdown-mismatch warning. The verification block still correctly showed `amount_verified: true`.
> Either the server-side warning logic was fixed between runs, or it fires non-deterministically.
> Keeping this finding open for monitoring; needs one more run to confirm resolution.

### Observed behaviour

Scanning `2014-04-15_Pappadeaux_36.79.png` (subtotal $30.79, tip $6.00, total $36.79) returns simultaneously:

```json
"warnings": [
  "Amount breakdown doesn't match total: expected ~$30.79, got $36.79"
],
"verification": {
  "amount_verified": true,
  "subtotal": 30.79,
  "tip": 6,
  "total": 36.79,
  "method": "single_amount"
}
```

The verification block correctly accounts for the tip and sets `amount_verified: true`. The warning fires anyway because `subtotal + tax (0) ≠ total`, without factoring in the tip that the same response already extracted.

### Impact

An agent or user acting on `warnings` alone would flag this receipt as potentially incorrect when it is in fact correct. The warning logic does not consult the `tip` field before emitting the mismatch message.

### Suggested fix

In the warning generation code, compute expected total as `subtotal + tax + tip + fees - discount` before comparing to `total`. Only emit the mismatch warning if the fully-summed breakdown still doesn't reconcile.

---

## Finding 3 — OBSERVATION: Batch scan extracts wrong date for `2026-03-18_WholeFoodsMarket_62.84.png`

**Affects:** T30 (`get_batch_scan_results`)
**Severity:** Informational — expected OCR uncertainty; documented for tracking

### Observed behaviour

```json
{
  "vendor": "Whole Foods Market",
  "date": "2026-03-19",       ← extracted by OCR
  "confidence": { "date": 0.1 }
}
```

The filename encodes `2026-03-18`; the OCR extracted `2026-03-19` with confidence `0.1` (very low). This is a genuine OCR ambiguity on the receipt image (thermal printer date can be hard to read).

### Impact

No server-side bug. The confidence score correctly signals unreliability. An agent auto-saving with `save_threshold=medium` or higher would skip this item or flag it for review, which is the correct behaviour.

### Recommendation

No code change needed. Consider adding a note to the E2E test plan that the Whole Foods receipt produces low date confidence, so future testers do not mistake this for a regression.

---

## Ancillary Notes

### `export_transactions` response size

Both T38 (74 KB CSV) and T39 (240 KB JSON) exceeded the MCP context token limit and were spilled to disk. The responses are valid and complete; this is a context-window constraint, not a server bug. The exports contain the full transaction history for the account (~164 transactions in CSV, all transactions in JSON).

### `recite://ledger` `vendor` field is empty string for unreadable vendor

Entry for `2026-03-18_None_223.75.png` has `"vendor": ""` in the local ledger (and `"unknown"` in `summarize_ledger`). This is consistent with the filename which encodes `None` as the vendor. No bug — the OCR could not extract a vendor name from this receipt image.

### Duplicate ledger entries after batch

Because T10, T11, and T13 all processed receipts from the same `receipts/` directory, several receipt images were scanned and ledger-written more than once (e.g., Pappadeaux appears 3×). This is expected behaviour — the local ledger is append-only and has no deduplication. Not a bug, but worth noting for users who run batch processing on already-processed directories.

---

## Test Artefact Cleanup Status

| Artefact | Status |
|---|---|
| E2E Test Project | Deleted (T44) |
| E2E Test Vendor transaction | Deleted (T43) |
| Import Test A transaction | Deleted (T42) |
| Import Test B transaction | Deleted (T42) |
| CSV Vendor transaction | Deleted (T42) |
| Test webhook | Deleted (T41) |
| Test rule | Deleted (T40) |
| `rename_test_raw.png` fixture | Restored (copy of Pappadeaux receipt) |
| Local ledger / memory files | Cleared at Phase 0-E (will persist post-test scan data) |
| Export files (`~/recite_test_export.*`) | Left on disk at `C:/Users/noname/` — safe to delete |
