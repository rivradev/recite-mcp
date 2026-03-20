# E2E Test Run Findings — 2026-03-20

Run against: `recite-mcp` E2E plan (`docs/plans/2026-03-17-e2e-test-plan.md`)
Environment: Windows 11, recite_home = `.recite/` (project-local)
Server: `https://recite.rivra.dev/apiV1/api/v1`

---

## Overall Result: PASS (43/43 targets)

All 40 tools and 3 resources passed their assertions. One API-side bug was observed
that does not block the test but is documented below for the server team.

---

## Phase Results

| Phase | Result | Notes |
|-------|--------|-------|
| 0 — Install & Setup | PASS | `.mcp.json` pre-configured; 0-E/0-F clean slate confirmed |
| 1 — Setup | PASS | T01/T02/R01 all ok |
| 2 — Local | PASS | Memory + ledger empty-state assertions correct |
| 3 — Single scan | PASS | T06–T11 including rename fixture restore |
| 4 — Batch local | PASS | T12 preview_count=9, T13 processed=9, failed=0 |
| 5 — Ledger ops | PASS | Correction entry written; CSV (13 lines) + JSON (12 entries) exported |
| 6 — Projects | PASS | Create/list/update all confirmed |
| 7 — Transactions | PASS | CRUD + import-list + import-CSV all confirmed |
| 8 — Async batch | PASS | Completed in ~23 s, 2/2 successful |
| 9 — Webhooks/Rules | PASS | Rule schema difference noted (see Bug #1 context) |
| 10 — Preferences | PASS | Category/vendor create + verify confirmed |
| 11 — Analytics | PASS | T40–T44 all returned data |
| 12 — Cleanup | PASS | All test artifacts deleted and verified |

---

## Bug #1 — `get_categories`: `custom_categories` mirrors `default_categories`

**Severity:** Medium
**Type:** Public API bug (server-side)
**Affects:** `GET /api/v1/categories` → `custom_categories` field

### Description

`get_categories` returns a `custom_categories` array that contains all 17 built-in
default categories, even when the user has not added any custom categories. The field
should contain only user-defined additions.

### Observed response (before creating any custom category)

```json
{
  "default_categories": ["Advertising & Marketing", "Office Supplies", ...],  // 17 items
  "custom_categories": ["Advertising & Marketing", "Office Supplies", ...],   // same 17 items
  "all_categories": [...]  // sorted union — correct
}
```

After calling `create_category` with `"E2E Custom Category"`, the new entry appeared
as item 18 in `custom_categories`, confirming the 17 defaults are always injected:

```json
"custom_categories": [
  "Advertising & Marketing", ..., "Other",  // 17 defaults
  "E2E Custom Category"                      // user-added (correct)
]
```

### Expected behaviour

```json
{
  "default_categories": ["Advertising & Marketing", ...],  // 17 built-ins
  "custom_categories": ["E2E Custom Category"],            // user-added only
  "all_categories": [...]                                  // sorted union of both
}
```

### Impact

- Code that iterates `custom_categories` to list **only user-added** categories
  will include all 17 defaults — it cannot distinguish them.
- `all_categories` (sorted union) is correct and unaffected.
- Deleting a default category name from `custom_categories` is blocked by the API
  ("Default categories cannot be deleted"), so there is no workaround via the API.

### Reproduction steps

```
1. Call get_categories on any account with no custom categories.
2. Observe custom_categories contains all 17 default categories.
```

### Workaround (client-side)

Compute the true custom list by subtracting defaults:

```python
true_custom = set(resp["custom_categories"]) - set(resp["default_categories"])
```

---

## Observation — `rules` schema: two formats coexist on the server

Not a bug in the MCP server itself, but worth noting for future test assertions.

The server returns rules in two distinct formats depending on `rule_type`:

**`vendor_category` (created via `create_rule`):**
```json
{
  "rule_type": "vendor_category",
  "condition": {"vendor": "Coffee"},
  "action": {"set_category": "Meals & Entertainment"}
}
```

**`transaction_rule` (created via the web UI):**
```json
{
  "rule_type": "transaction_rule",
  "condition": {},
  "action": {},
  "conditions": [{"type": "vendor_contains", "value": "Whole "}],
  "condition_operator": "AND",
  "actions": [{"type": "set_category", "value": "Meals & Entertainment"}]
}
```

The E2E test plan's Phase 0-F cleanup step filters by `condition={"vendor":"Coffee"}`
which only matches `vendor_category` rules — this is correct. The pre-existing
`transaction_rule` format would not be matched by that filter.

**Recommendation:** Update T34 assertion and 0-F cleanup docs to acknowledge both
formats and match by `rule_id` rather than `condition` contents.

---

## Observation — T11 rename date uses OCR-extracted date, not file-name date

When `rename_test_raw.png` (a copy of `2026-03-18_BestBuy_372.97.png`) was processed
with `rename=true`, the file was renamed to `2026-03-20_BestBuy_372.97.png` (today's
date) rather than `2026-03-18_...`. The OCR extracted `2026-03-20` from the image,
not the date embedded in the source filename. This is expected behaviour — the rename
uses extracted data, not filename metadata. No action required.

---

## Handover: Bug #1 to Server Team

**File:** `docs/bug-reports/2026-03-20-e2e-findings.md` (this document)
**Tool:** `get_categories` / `mcp__recite__get_categories`
**Endpoint:** `GET /api/v1/categories`
**Field:** `custom_categories`

**Ask:** The `custom_categories` field in the API response should return **only
user-added** categories (those created via `POST /api/v1/categories`), not the full
set of 17 built-in defaults. The `default_categories` and `all_categories` fields
are correct.

**Test to confirm fix:**
```
1. Create a fresh account (or clear all custom categories).
2. Call get_categories.
3. Assert custom_categories is [] (empty).
4. Call create_category with name="Test Custom".
5. Call get_categories again.
6. Assert custom_categories == ["Test Custom"] (length 1, no defaults).
```
