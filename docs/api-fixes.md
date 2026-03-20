# API-Level Issues — recite-mcp (2026-03-18)

This document records issues that were discovered during E2E testing and that
**cannot be fixed in the Python client code**. Each item describes what was
observed, the root cause (server-side), and the recommended API change.

---

## API-01: `create_rule` rejects `vendor_contains` condition key

**Severity:** Medium
**Discovered in:** E2E Phase 9, T33

### Observed behaviour

Calling `create_rule` with `condition={"vendor_contains": "Coffee"}` returns an
HTTP 4xx error:

```
Error: Invalid condition key(s) for rule_type "vendor_category": vendor_contains.
Valid keys: vendor.
```

### Root cause

The API only supports exact-match vendor conditions (`vendor`). The E2E test plan
(and likely documentation) mentioned `vendor_contains` as a valid key, but the
server rejects it. No substring or prefix matching is currently implemented.

### Recommended API changes

Option A — **Add `vendor_contains` as a valid condition key** supporting
case-insensitive substring matching (the most useful behaviour for end-users).

Option B — **Document clearly** that only exact `vendor` matching is supported,
and remove `vendor_contains` from any documentation or examples.

### Workaround (already applied)

The E2E test plan (`docs/plans/2026-03-17-e2e-test-plan.md`) has been updated to
use `{"vendor": "Coffee"}` instead of `{"vendor_contains": "Coffee"}`.

---

## API-02: `process_receipts_batch` live response includes non-zero `preview_count`

**Severity:** Low
**Discovered in:** E2E Phase 4, T13

### Observed behaviour

When calling `process_receipts_batch` with `dry_run=false`, the API response
contained `"preview_count": 6` instead of `0`. The Python source code correctly
sets `preview_count=0` in live mode.

### Root cause

The running MCP server was executing an **older cached/installed version** of the
package rather than the current source. This is a deployment/packaging issue, not
a client code bug. The current source (`tools.py`) is correct.

### Recommended fix

Ensure that `uvx recite-mcp` (or the installed package) is always up to date
before running E2E tests. Consider pinning the version in `.mcp.json` or adding a
version check in the validation step.

No API-server change is required.

---

## API-03: No substring/pattern matching in rule conditions

**Severity:** Low (related to API-01)
**Discovered in:** E2E Phase 9, T33

### Observed behaviour

The `create_rule` endpoint only supports `vendor` (exact string match) for
`vendor_category` rules. Real-world use cases almost always require partial
matching (e.g., all receipts where vendor contains "Starbucks", "Coffee", etc.).

### Recommended API changes

Extend the `vendor_category` condition schema to support:

| Key | Semantics |
|-----|-----------|
| `vendor` | Exact match (already exists) |
| `vendor_contains` | Case-insensitive substring match |
| `vendor_starts_with` | Case-insensitive prefix match |
| `vendor_regex` | Regular-expression match (advanced) |

---

## API-04: Large `export_transactions` responses exceed inline display limits

**Severity:** Very Low / UX
**Discovered in:** E2E Phase 10, T38–T39

### Observed behaviour

`export_transactions` with `format="csv"` returned ~78 KB of CSV text and
`format="json"` returned ~257 KB of JSON — too large to display inline in Claude
Code or most MCP clients. The data was accessible but required writing to a
temporary file for review.

### Recommended API changes

Option A — **Return a pre-signed download URL** instead of (or in addition to)
the raw content for large exports, consistent with how cloud storage export
endpoints typically behave.

Option B — **Add a `limit`/`offset` or `page` parameter** to export endpoints
so that large datasets can be fetched in chunks.

Option C — **Return only a download URL** and a metadata summary (row count, byte
size) in the MCP tool response. The full payload is then fetched separately.

---

## Notes

- Python client code fixes (validation, tests, Windows `rename` bug) are tracked
  in the commit history on branch `feature/prod02`.
- Items in this document require changes to the **Recite REST API server**, not
  the Python MCP client.
