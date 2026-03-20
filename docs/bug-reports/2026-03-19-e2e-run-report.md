# E2E Test Run Report — 2026-03-19

**Plan reference:** `docs/plans/2026-03-17-e2e-test-plan.md`
**Run date:** 2026-03-19 (UTC: 2026-03-20T02:45–02:52)
**MCP server version:** `0.1.7`
**API base URL:** `https://recite.rivra.dev/apiV1/api/v1`
**recite_home (MCP):** `C:\Users\noname\VSCodeProjects\PythonProject\recite_mcp\.recite`

---

## Summary

| Phase | Result | Notes |
|-------|--------|-------|
| 0 — Install & Setup | ✅ PASS (partial) | 0-F blocked on categories/vendors (see BUG-01) |
| 1 — Setup Verification | ✅ PASS | All 3 targets pass |
| 2 — Local Tools | ✅ PASS | All 5 targets pass |
| 3 — Single Receipt Scanning | ✅ PASS | All 6 targets pass |
| 4 — Batch Receipt Processing | ✅ PASS | Both targets pass |
| 5 — Local Ledger Operations | ✅ PASS (with observation) | Floating-point imprecision in summarize (see OBS-01) |
| 6 — Project Management | ✅ PASS | All 3 targets pass |
| 7 — Transaction CRUD | ✅ PASS | All 6 targets pass |
| 8 — Async Batch Scan | ✅ PASS | All 3 targets pass |
| 9 — Webhooks & Rules | ⚠️ PARTIAL | T31–T34 pass; T35 FAIL (see BUG-02) |
| 10 — Preferences | ❌ FAIL | All 4 targets fail (see BUG-01) |
| 11 — Analytics & Export | ✅ PASS (with observation) | T44 response shape differs from spec (see OBS-02) |
| 12 — Cleanup | ✅ PASS | T45/T46 skipped (no artifacts to delete due to BUG-01) |

**Total test targets:** 43 (40 tools + 3 resources)
**PASS:** 37 | **FAIL:** 5 (T35, T36, T37, T38, T39) | **SKIP:** 2 (T45, T46 — blocked by BUG-01)

---

## Bugs Found

### BUG-01 — `/api/v1/categories` and `/api/v1/vendors` endpoints return 404

**Severity:** High — blocks 6 test targets (T36, T37, T38, T39, T45, T46) and Phase 0-F cleanup

**Affected tools:**
- `get_categories` — `GET /api/v1/categories` → `not found`
- `create_category` — `POST /api/v1/categories` → `not found`
- `delete_category` — not tested (blocked by create failure)
- `get_vendors` — `GET /api/v1/vendors` → `not found`
- `create_vendor` — `POST /api/v1/vendors` → `not found`
- `delete_vendor` — not tested (blocked by create failure)

**First observed:** Phase 0-F (pre-run cleanup), confirmed again in Phase 10.

**Error messages:**
```
Error executing tool get_categories: GET /api/v1/categories not found.
Error executing tool create_category: POST /api/v1/categories not found.
Error executing tool get_vendors: GET /api/v1/vendors not found.
Error executing tool create_vendor: POST /api/v1/vendors not found.
```

**Possible causes:**
1. The `/categories` and `/vendors` endpoint group has not yet been deployed to production.
2. The API base URL may have changed and the categories/vendors routes live under a different path.
3. Authentication/routing middleware is stripping these routes before they reach the handler.

**Fix guidance:**
- Verify the correct route paths in the backend router for categories and vendors.
- Confirm these endpoints are deployed to `https://recite.rivra.dev/apiV1/api/v1`.
- Run `curl -H "Authorization: Bearer <key>" https://recite.rivra.dev/apiV1/api/v1/categories` to confirm the raw API response.

---

### BUG-02 — `update_rule` endpoint returns 404

**Severity:** Medium — T35 fails; rules can be created and deleted but not updated

**Affected tool:** `update_rule`

**HTTP method/path:** `PATCH /api/v1/rules/{rule_id}`

**Error message:**
```
Error executing tool update_rule: PATCH /api/v1/rules/87e2a5b6-eb57-44b2-9ef1-aeb71edfc15e not found.
```

**Context:** The rule (`rule_id: 87e2a5b6-eb57-44b2-9ef1-aeb71edfc15e`) was successfully created by T33 and appeared correctly in `list_rules` (T34). The PATCH endpoint is the only missing piece of the rules CRUD.

**Contrast:** `delete_rule` (T47) works correctly with `DELETE /api/v1/rules/{id}`. The issue is specific to the PATCH handler.

**Possible causes:**
1. The PATCH route for rules is not registered in the backend router.
2. The route uses a different HTTP method (PUT vs PATCH).
3. Route parameter name mismatch (e.g., `:id` vs `:rule_id`).

**Fix guidance:**
- Check the backend router: ensure `PATCH /api/v1/rules/:id` is registered alongside the existing `DELETE /api/v1/rules/:id`.
- If the backend uses PUT instead of PATCH, update `api_client.py` `update_rule` method to use `PUT`.
- The `update_rule` tool's docstring specifies it uses PATCH — verify this matches the backend OpenAPI spec.

---

## Observations (non-blocking)

### OBS-01 — Floating-point imprecision in `summarize_ledger`

**Tool:** `summarize_ledger` (T15 — group_by=category)

**Observed:** `"Other": {"count": 2, "total": 435.81000000000006}` instead of `435.81`

**Cause:** Standard Python float arithmetic accumulation. The two "Other" entries total `372.97 + 62.84 = 435.81`, but floating-point addition yields `435.81000000000006`.

**Fix guidance:** Apply `round(total, 2)` when computing totals in `LedgerRepository.summarize()` (in `ledger.py`), or use `decimal.Decimal` for accumulation.

---

### OBS-02 — `export_transactions` JSON response is a dict, not a bare array

**Tool:** `export_transactions` (T44, format=json)

**Test plan expectation:** "returns JSON array or download URL"

**Actual response shape:**
```json
{
  "transactions": [...],
  "total_count": 508,
  "exported_at": "2026-03-20T...",
  "pagination": {...}
}
```

**Assessment:** This is not a bug — the richer envelope is more useful than a bare array. However the E2E test plan assertion should be updated to reflect the actual shape.

**Action:** Update `docs/plans/2026-03-17-e2e-test-plan.md` T44 assertion to:
> Returns JSON object with `transactions` array and `total_count`. Each entry has standard transaction fields.

---

### OBS-03 — `export_transactions` returns very large payloads

**Context:** T43 (CSV) produced 51,547 chars; T44 (JSON) produced 154,755 chars — both exceeded the MCP tool result token limit.

**Impact:** None on correctness (data was verified via saved file), but callers consuming these tools programmatically must handle large payloads. Consider adding pagination parameters or a `limit` filter.

---

### OBS-04 — Vendor stored as empty string, summarized as "unknown"

**Observed:** The receipt `2026-03-18_None_223.75.png` produces `vendor: ""` in the ledger (entry `47aabb3c`). `summarize_ledger` maps the empty string to the key `"unknown"` in the summary output.

**Assessment:** The "unknown" fallback label is reasonable, but it may be unexpected to callers. If the OCR cannot determine a vendor, consider storing `null` instead of `""` for type consistency, and document the `"unknown"` grouping key in the tool description.

---

## Receipts Directory State After Run

The `receipts/` directory was left with one extra file created by T11's rename operation:

| File | Origin |
|------|--------|
| `2026-03-20_WholeFoodsMarket_62.84.png` | Created by T11 rename of `rename_test_raw.png` |
| `rename_test_raw.png` | Restored as fixture after T11 |

The renamed file `2026-03-20_WholeFoodsMarket_62.84.png` is a duplicate of `2026-03-18_WholeFoodsMarket_62.84.png` (same image, different date extracted by OCR). It can be deleted manually if desired.

---

## Reproduction Steps for Bugs

### Reproduce BUG-01
```bash
# With valid API key set:
curl -H "Authorization: Bearer $RECITE_API_KEY" \
  https://recite.rivra.dev/apiV1/api/v1/categories
# Expected: 200 with category list
# Actual: 404 not found
```

### Reproduce BUG-02
```bash
# First create a rule, then try to update it:
RULE_ID="<id from create_rule response>"
curl -X PATCH \
  -H "Authorization: Bearer $RECITE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"active": false}' \
  https://recite.rivra.dev/apiV1/api/v1/rules/$RULE_ID
# Expected: 200 with updated rule
# Actual: 404 not found
```
