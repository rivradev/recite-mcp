# Recite API Reference

**Version:** v1
**Base URL:** `https://recite.rivra.dev/apiV1/api/v1`
**Last Updated:** March 2026

Recite's REST API lets you scan receipts, extract structured financial data, manage transactions and projects, run batch operations, and automate bookkeeping workflows — all programmatically. It is designed for AI agents, automation platforms, and custom integrations.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Authentication](#2-authentication)
3. [Request & Response Format](#3-request--response-format)
4. [Errors](#4-errors)
5. [Rate Limits](#5-rate-limits)
6. [Scopes](#6-scopes)
7. [Scan Quota](#7-scan-quota)
8. [Endpoints](#8-endpoints)
   - [POST /scan](#post-scan) — Scan a receipt
   - [GET /scan/:id](#get-scanid) — Retrieve scan result
   - [POST /transactions](#post-transactions) — Create transaction
   - [GET /transactions](#get-transactions) — List transactions
   - [GET /transactions/:id](#get-transactionsid) — Get transaction
   - [PATCH /transactions/:id](#patch-transactionsid) — Update transaction
   - [DELETE /transactions/:id](#delete-transactionsid) — Delete transaction
   - [POST /import/transactions](#post-importtransactions) — Bulk import
   - [POST /batch/scans](#post-batchscans) — Submit batch scan job
   - [GET /batch/scans/:jobId](#get-batchscansjobid) — Batch job status
   - [GET /batch/scans/:jobId/results](#get-batchscansjobidresults) — Batch results
   - [GET /projects](#get-projects) — List projects
   - [POST /projects](#post-projects) — Create project
   - [PATCH /projects/:id](#patch-projectsid) — Update project
   - [DELETE /projects/:id](#delete-projectsid) — Delete project
   - [GET /summary](#get-summary) — Financial summary
   - [POST /webhooks](#post-webhooks) — Register webhook
   - [GET /webhooks](#get-webhooks) — List webhooks
   - [DELETE /webhooks/:id](#delete-webhooksid) — Delete webhook
   - [POST /rules](#post-rules) — Create rule
   - [GET /rules](#get-rules) — List rules
   - [DELETE /rules/:id](#delete-rulesid) — Delete rule
   - [GET /usage](#get-usage) — Usage statistics
   - [POST /export](#post-export) — Export transactions
9. [Webhooks Guide](#9-webhooks-guide)
10. [Idempotency](#10-idempotency)
11. [Batch Processing](#11-batch-processing)
12. [AI Agent Integration](#12-ai-agent-integration)
13. [Code Examples](#13-code-examples)
14. [FAQ](#14-faq)

---

## 1. Quick Start

### Prerequisites

- **Recite account** — Sign up at [recite.rivra.dev](https://recite.rivra.dev)
- **API key** — Create one at **Settings → API Access**
- **Subscription** — API scan calls share your monthly quota

### Scan a receipt in 60 seconds

```bash
curl -X POST https://recite.rivra.dev/apiV1/api/v1/scan \
  -H "Authorization: Bearer sk_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/receipt.jpg",
    "auto_save": true,
    "save_threshold": "medium",
    "project_id": "your-project-id"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_id": "scan_8f3a2b1c-...",
    "extracted_data": {
      "date": "2026-02-14",
      "amount": 42.50,
      "subtotal": 39.81,
      "tax": 2.69,
      "vendor": "Starbucks Coffee",
      "category": "Food & Dining",
      "payment_method": "Credit Card",
      "confidence": {
        "amount": 0.98,
        "date": 0.95,
        "vendor": 0.92,
        "overall": 0.95
      }
    },
    "transaction_id": "txn_abc123",
    "summary": {
      "confidence_band": "high",
      "auto_save_eligible": true
    }
  },
  "meta": {
    "request_id": "req_550e8400-...",
    "api_version": "v1",
    "processing_time_ms": 1240,
    "quota_limit": 200,
    "quota_remaining": 157
  }
}
```

---

## 2. Authentication

All API requests require a Bearer token in the `Authorization` header.

```
Authorization: Bearer sk_live_YOUR_API_KEY
```

### Getting an API Key

1. Sign in to [recite.rivra.dev](https://recite.rivra.dev)
2. Go to **Settings → API Access**
3. Click **Create API Key**
4. Enter a name (e.g., `My Agent`, `Production`) and select scopes
5. Copy the key — **it is shown only once**

### API Key Format

```
sk_live_<name>_<32-char-hex-secret>
```

Example: `sk_live_myapp_f8a92b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a`

Keys may also use the `re_live_` prefix.

### Security Requirements

- Store keys in environment variables or secrets managers
- Never embed in client-side code or public repositories
- Rotate keys immediately if exposed
- Use the minimum set of scopes needed

### Key Lifecycle

| State | Behavior |
|-------|----------|
| `active` | Requests proceed normally |
| `revoked` | All requests immediately return `401 INVALID_API_KEY` |
| `expired` | Requests return `401 INVALID_API_KEY` once expiry timestamp passes |

---

## 3. Request & Response Format

### Base URL

```
https://recite.rivra.dev/apiV1/api/v1
```

### Request Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | `Bearer YOUR_API_KEY` |
| `Content-Type` | Yes (for POST/PATCH) | `application/json` or `text/csv` |
| `Idempotency-Key` | No | Deduplication key (see [Idempotency](#10-idempotency)) |

### Response Envelope

Every response, success or error, uses the same envelope structure.

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "request_id": "req_uuid",
    "api_version": "v1",
    "processing_time_ms": 320,
    "quota_limit": 200,
    "quota_remaining": 150
  }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Field 'amount' must be a positive number",
    "details": {
      "field": "amount",
      "provided": -10
    }
  },
  "meta": {
    "request_id": "req_uuid",
    "api_version": "v1",
    "processing_time_ms": 12
  }
}
```

### Response Formats

List endpoints support alternative formats via query parameter or `Accept` header.

```
GET /transactions?format=csv
GET /transactions?format=text
```

| Format | Content-Type | Use Case |
|--------|-------------|---------|
| `json` | `application/json` | Default — machine processing |
| `csv` | `text/csv` | Spreadsheet import |
| `text` | `text/plain` | Debug / human readable |

---

## 4. Errors

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Missing or invalid fields in request body/params |
| `INVALID_IMAGE` | 400 | Image cannot be decoded or is unsupported format |
| `INVALID_API_KEY` | 401 | API key is missing, malformed, revoked, or expired |
| `INSUFFICIENT_SCOPE` | 403 | API key lacks the scope needed for this endpoint |
| `NOT_FOUND` | 404 | Resource does not exist or belongs to a different user |
| `DUPLICATE` | 409 | Resource already exists (idempotency hit) |
| `FILE_TOO_LARGE` | 413 | Image or payload exceeds size limit |
| `EXTRACTION_FAILED` | 422 | LLM could not extract structured data from the input |
| `RATE_LIMITED` | 429 | Too many requests in the current time window |
| `QUOTA_EXCEEDED` | 429 | Monthly scan quota exhausted |
| `INTERNAL_ERROR` | 500 | Server-side error |

### Handling Errors

```javascript
const response = await fetch(url, options);
const body = await response.json();

if (!body.success) {
  switch (body.error.code) {
    case 'QUOTA_EXCEEDED':
      // Handle monthly limit exhausted
      break;
    case 'RATE_LIMITED':
      // Respect Retry-After header
      const retryAfter = response.headers.get('Retry-After');
      await sleep(parseInt(retryAfter) * 1000);
      break;
    case 'EXTRACTION_FAILED':
      // Image too unclear — ask user for better photo
      break;
  }
}
```

---

## 5. Rate Limits

Rate limits apply per API key using sliding window counters.

| Window | Default Limit |
|--------|--------------|
| Per minute | 100 requests |
| Per hour | 500 requests |
| Per day | 5,000 requests |

### Rate Limit Headers

Every response includes current rate limit status:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1709123456
Retry-After: 23   (only present when rate limited)
```

### Rate Limit Errors

When rate limited, the API returns `429 RATE_LIMITED`. Retry after the `Retry-After` header value (seconds).

> **Note:** `RATE_LIMITED` (window exceeded) is distinct from `QUOTA_EXCEEDED` (monthly scan limit). Rate limits reset within minutes; scan quota resets monthly.

---

## 6. Scopes

API keys are granted specific scopes at creation. Each endpoint requires one or more scopes.

| Scope | Grants Access To |
|-------|-----------------|
| `scan:create` | `POST /scan`, `POST /batch/scans` |
| `scan:read` | `GET /scan/:id`, `GET /batch/scans/:id/results` |
| `transactions:create` | `POST /transactions`, `POST /import/transactions` |
| `transactions:read` | `GET /transactions`, `GET /transactions/:id`, `GET /summary` |
| `transactions:update` | `PATCH /transactions/:id` |
| `transactions:delete` | `DELETE /transactions/:id` |
| `batch:create` | `POST /batch/scans` |
| `batch:read` | `GET /batch/scans/:id`, `GET /batch/scans/:id/results` |
| `projects:read` | `GET /projects` |
| `projects:write` | `POST /projects`, `PATCH /projects/:id`, `DELETE /projects/:id` |
| `usage:read` | `GET /usage` |
| `export:create` | `POST /export` |
| `webhooks:manage` | `POST /webhooks`, `GET /webhooks`, `DELETE /webhooks/:id` |
| `rules:read` | `GET /rules` |
| `rules:write` | `POST /rules`, `DELETE /rules/:id` |

### Default Scopes

New API keys created in Settings include these scopes by default:

`scan:create`, `scan:read`, `transactions:create`, `transactions:read`, `transactions:update`, `projects:read`, `usage:read`

---

## 7. Scan Quota

Scan quota is shared between the web app and the API. Both `POST /scan` and `POST /batch/scans` consume quota.

| Subscription | Monthly Scan Limit |
|-------------|-------------------|
| Free | 10 |
| Standard | 200 |
| Premium | 200 |
| Standard Pro | 500 |
| Premium Pro | 1,000+ |

Monitor remaining quota via:
- The `meta.quota_remaining` field on every scan response
- `GET /usage`

When quota is exhausted, all scan endpoints return `429 QUOTA_EXCEEDED` until the monthly reset date.

---

## 8. Endpoints

---

### POST /scan

Scan a receipt image or raw text and extract structured financial data. Optionally auto-create a transaction.

**Required scope:** `scan:create`

#### Request Body

```typescript
{
  // Input — provide exactly one of:
  image_url?: string;        // Publicly accessible HTTPS URL to image
  image_base64?: string;     // Base64-encoded image data
  raw_text?: string;         // Raw receipt text for LLM extraction

  // Auto-save behavior
  auto_save?: boolean;       // Create a transaction automatically (default: false)
  save_threshold?: 'high' | 'medium' | 'low';  // Confidence gate (default: 'high')
  project_id?: string;       // Project to assign transaction to (required when auto_save: true)
  status?: 'draft' | 'reviewed';  // Initial transaction status (default: 'reviewed')

  // Advanced
  image_type?: string;       // MIME type hint (e.g., 'image/jpeg')
  idempotency_key?: string;  // 24-hour dedup key (max 128 chars)
  metadata?: Record<string, string>;  // Custom key-value metadata
  ephemeral?: boolean;       // Skip Firestore writes; cannot combine with auto_save
}
```

**Constraints:**
- Exactly one of `image_url`, `image_base64`, or `raw_text` must be provided
- `image_url` must be a valid HTTPS URL
- `ephemeral` and `auto_save` cannot both be `true`
- `auto_save: true` requires `project_id`

#### Response `200 OK`

```typescript
{
  scan_id: string;
  extracted_data: {
    date: string | null;          // YYYY-MM-DD
    amount: number | null;        // Total amount
    subtotal: number | null;      // Pre-tax subtotal
    tax: number | null;
    tip: number | null;
    fees: number | null;
    fees_description: string | null;
    discount: number | null;
    discount_description: string | null;
    currency: string | null;      // e.g., "USD"
    vendor: string | null;
    category: string | null;      // e.g., "Food & Dining"
    description: string | null;
    payment_method: string | null;
    confidence: {
      amount: number;             // 0.0 – 1.0
      date: number;
      vendor: number;
      category: number;
      payment_method: number;
      tip: number;
      fees: number;
      discount: number;
      overall: number;            // Weighted composite score
    };
  };
  transaction_type: 'Expense' | 'Income' | 'Asset' | 'Liability' | 'Equity';
  transaction_id?: string;        // Present only when auto_save triggered
  image_source: 'url' | 'base64' | 'text';
  extraction_method: 'vision' | 'text_llm' | 'vision_fallback';
  raw_text: string;
  warnings: string[];
  verification?: {
    amount_verified: boolean;
    subtotal: number;
    tax: number;
    tip: number;
    fees: number;
    fees_description: string;
    discount: number;
    total: number;
    discrepancy: number;
    method: 'subtotal_tax' | 'single_amount' | 'unverifiable';
  };
  summary: {
    confidence_band: 'high' | 'medium' | 'low';
    is_blocked: boolean;
    blocked_reason?: 'missing_amount' | 'extraction_failed';
    auto_save_eligible: boolean;
    auto_save_skipped_reason?: 'below_threshold' | 'blocked' | 'auto_save_disabled';
  };
  suggestions?: string[];
}
```

#### Confidence Bands

| Band | Overall Score | Meaning |
|------|--------------|---------|
| `high` | ≥ 0.85 | High quality extraction; safe to auto-save |
| `medium` | 0.60 – 0.84 | Moderate quality; review recommended |
| `low` | < 0.60 | Poor extraction; manual review required |

#### `save_threshold` Behavior

When `auto_save: true`, a transaction is created only if the confidence band meets or exceeds the threshold:

| `save_threshold` | Transaction created when confidence is... |
|-----------------|------------------------------------------|
| `high` (default) | `high` only |
| `medium` | `medium` or `high` |
| `low` | Always (any band) |

#### Example

```bash
# Scan from URL with auto-save on high-confidence results
curl -X POST https://recite.rivra.dev/apiV1/api/v1/scan \
  -H "Authorization: Bearer sk_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://cdn.example.com/receipts/starbucks.jpg",
    "auto_save": true,
    "save_threshold": "high",
    "project_id": "proj_abc123"
  }'
```

```bash
# Ephemeral scan (no storage, no quota deduction for saved data)
curl -X POST https://recite.rivra.dev/apiV1/api/v1/scan \
  -H "Authorization: Bearer sk_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "iVBORw0KGgoAAAANSUhEUgA...",
    "ephemeral": true
  }'
```

---

### GET /scan/:id

Retrieve a previously created scan result by its ID.

**Required scope:** `scan:read`

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | Scan ID returned by `POST /scan` |

#### Response `200 OK`

Same schema as `POST /scan` response.

#### Errors

| Code | Condition |
|------|-----------|
| `NOT_FOUND` | Scan ID does not exist or belongs to a different user |

---

### POST /transactions

Create a transaction manually (without scanning).

**Required scope:** `transactions:create`

#### Request Body

```typescript
{
  // Required fields
  date: string;              // YYYY-MM-DD
  amount: number;            // Must be positive (> 0)
  transaction_type: 'Expense' | 'Income' | 'Asset' | 'Liability' | 'Equity';
  category: string;          // Non-empty string
  payment_method: string;    // Non-empty string

  // Optional fields
  scan_id?: string;          // Link to an existing scan result
  subtotal?: number;
  tax?: number;
  tip?: number;
  fees?: number;
  fees_description?: string;
  discount?: number;
  discount_description?: string;
  currency?: string;         // e.g., "USD"
  vendor?: string;
  description?: string;
  project_id?: string;
  metadata?: Record<string, string>;
}
```

#### Response `201 Created`

```typescript
{
  transaction_id: string;
  date: string;
  amount: number;
  subtotal?: number;
  tax?: number;
  tip?: number;
  fees?: number;
  fees_description?: string;
  discount?: number;
  discount_description?: string;
  currency?: string;
  transaction_type: string;
  category: string;
  vendor: string;
  description: string;
  payment_method: string;
  project_id?: string;
  receipt_url?: string;
  status: string;
  source: 'api';
  api_key_id: string;
  created_at: string;        // ISO 8601
  updated_at: string;
}
```

#### Validation Rules

| Field | Rule |
|-------|------|
| `date` | Must be valid YYYY-MM-DD date |
| `amount` | Must be numeric and greater than 0 |
| `transaction_type` | Must be one of the five enum values |
| `scan_id` | If provided, must exist and belong to this user |
| `project_id` | If provided, must exist and belong to this user |

---

### GET /transactions

List transactions with filtering, sorting, and pagination.

**Required scope:** `transactions:read`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | string | — | Filter from date (YYYY-MM-DD, inclusive) |
| `end_date` | string | — | Filter to date (YYYY-MM-DD, inclusive) |
| `transaction_type` | string | — | `Expense`, `Income`, `Asset`, `Liability`, `Equity` |
| `category` | string | — | Exact category match |
| `vendor` | string | — | Exact vendor match |
| `payment_method` | string | — | Exact payment method match |
| `amount_min` | number | — | Minimum amount (inclusive) |
| `amount_max` | number | — | Maximum amount (inclusive) |
| `status` | string | — | `draft` or `reviewed` |
| `project_id` | string | — | Filter to specific project |
| `source` | string | — | Filter by source (e.g., `api`, `web`) |
| `agent_name` | string | — | Filter by agent name |
| `sort_by` | string | `date` | `date`, `amount`, `created_at`, `category` |
| `sort_order` | string | `desc` | `asc` or `desc` |
| `limit` | integer | 50 | Max results per page (max: 200) |
| `offset` | integer | 0 | Pagination offset |
| `format` | string | `json` | `json`, `csv`, or `text` |

#### Response `200 OK`

```typescript
{
  transactions: Array<{
    transaction_id: string;
    date: string;
    amount: number;
    subtotal?: number;
    tax?: number;
    tip?: number;
    fees?: number;
    fees_description?: string;
    discount?: number;
    discount_description?: string;
    currency?: string;
    transaction_type: string;
    category: string;
    vendor: string;
    description: string;
    payment_method: string;
    project_id?: string;
    receipt_url?: string;
    status: string;
    source: string;
    api_key_id: string;
    created_at: string;
    updated_at: string;
  }>;
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
}
```

#### Example — Filter by date range and export as CSV

```bash
curl "https://recite.rivra.dev/apiV1/api/v1/transactions?\
start_date=2026-01-01&end_date=2026-01-31&format=csv" \
  -H "Authorization: Bearer sk_live_YOUR_KEY"
```

---

### GET /transactions/:id

Retrieve a single transaction by its ID.

**Required scope:** `transactions:read`

#### Response `200 OK`

Returns a single transaction object (same schema as list items above).

#### Errors

| Code | Condition |
|------|-----------|
| `NOT_FOUND` | Transaction does not exist or belongs to different user |

---

### PATCH /transactions/:id

Update one or more fields of an existing transaction.

**Required scope:** `transactions:update`

All fields are optional. Only provided fields are updated; unspecified fields remain unchanged.

#### Request Body

```typescript
{
  date?: string;              // YYYY-MM-DD
  amount?: number;            // Must be positive
  subtotal?: number;
  tax?: number;
  tip?: number;
  fees?: number;
  fees_description?: string;
  discount?: number;
  discount_description?: string;
  currency?: string;
  transaction_type?: 'Expense' | 'Income' | 'Asset' | 'Liability' | 'Equity';
  category?: string;
  vendor?: string;
  description?: string;
  payment_method?: string;
  project_id?: string;
  receipt_url?: string;       // Must use https://
}
```

#### Response `200 OK`

Returns the updated transaction object.

#### Validation Rules

| Field | Rule |
|-------|------|
| `amount` | If provided, must be > 0 |
| `receipt_url` | If provided, must start with `https://` |

---

### DELETE /transactions/:id

Permanently delete a transaction. This action cannot be undone.

**Required scope:** `transactions:delete`

#### Response `204 No Content`

Empty body on success.

#### Side Effects

- If any webhook is subscribed to `transaction.deleted`, the event fires asynchronously after the delete succeeds.

#### Errors

| Code | Condition |
|------|-----------|
| `NOT_FOUND` | Transaction does not exist or belongs to different user |

---

### POST /import/transactions

Bulk import up to 500 transactions from JSON or CSV in a single request.

**Required scope:** `transactions:create`

#### Request Body (JSON)

```typescript
{
  transactions: Array<{
    date?: string;              // YYYY-MM-DD
    amount?: number | string;   // Converted to float
    subtotal?: number | string;
    discount?: number | string;
    discount_description?: string;
    tax?: number | string;
    tip?: number | string;
    fees?: number | string;
    fees_description?: string;
    currency?: string;
    transaction_type?: string;  // Or use 'type' alias
    type?: string;              // Alias for transaction_type
    category?: string;
    vendor?: string;
    description?: string;
    payment_method?: string;
    project_id?: string;
    project?: string;           // Alias for project_id (name lookup)
  }>;
  all_or_nothing?: boolean;     // Reject all rows if any row fails (default: false)
  project_id?: string;          // Default project for all rows
}
```

#### Request Body (CSV)

Set `Content-Type: text/csv` and send raw CSV. Supported column headers:

```
date, amount, subtotal, discount, discount_description, tax, tip, fees,
fees_description, currency, type, transaction_type, category, vendor,
description, payment_method, project, project_id
```

Headers are case-insensitive. Columns can be in any order.

#### Response `200 OK`

```typescript
{
  total: number;              // Total rows submitted
  imported: number;           // Successfully imported
  failed: number;             // Rows that failed validation
  transactions: Array<{
    row: number;
    transaction_id: string;
  }>;
  errors: Array<{
    row: number;
    field: string;
    message: string;
  }>;
}
```

#### Validation Rules (per row)

| Field | Rule |
|-------|------|
| `date` | Required, must be YYYY-MM-DD |
| `amount` | Required, must be positive number |
| `transaction_type` | Required, must be one of the five enum values |
| `category` | Required, non-empty |
| `payment_method` | Required, non-empty |

#### `all_or_nothing` Mode

When `all_or_nothing: true`, the entire import is rejected if any row fails validation. The response returns a non-empty `errors` array and `imported: 0`.

#### Example — CSV import

```bash
curl -X POST https://recite.rivra.dev/apiV1/api/v1/import/transactions \
  -H "Authorization: Bearer sk_live_YOUR_KEY" \
  -H "Content-Type: text/csv" \
  --data-binary @transactions.csv
```

---

### POST /batch/scans

Submit a batch of up to 20 receipt images for asynchronous processing.

**Required scopes:** `batch:create`, `scan:create`

#### Request Body

```typescript
{
  items: Array<{
    image_url?: string;         // HTTPS URL to image
    image_base64?: string;      // Base64-encoded image
    metadata?: Record<string, string>;
  }>;
  auto_save?: boolean;          // Auto-create transactions for results
  save_threshold?: 'high' | 'medium' | 'low';
  project_id?: string;
  webhook_url?: string;         // HTTPS URL to notify on completion
  webhook_secret?: string;      // HMAC secret for signature verification
}
```

**Constraints:**
- Maximum 20 items per batch
- Each item must provide exactly one of `image_url` or `image_base64`
- `webhook_url` must use HTTPS

#### Response `202 Accepted`

```typescript
{
  job_id: string;
  status: 'processing';
  total_items: number;
  status_url: string;           // Polling URL
  created_at: string;
}
```

Processing happens asynchronously. Poll `GET /batch/scans/:jobId` or wait for the webhook.

---

### GET /batch/scans/:jobId

Get the current status of a batch scan job.

**Required scope:** `batch:read`

#### Response `200 OK`

```typescript
{
  job_id: string;
  status: 'processing' | 'completed' | 'partially_failed' | 'failed';
  total_items: number;
  processed_count: number;
  successful_count: number;
  failed_count: number;
  created_at: string;
  completed_at?: string;
  summary?: {
    total_amount: number;
    avg_confidence: number;
    auto_saved_count: number;
  };
}
```

#### Job Status Lifecycle

```
processing → completed
           → partially_failed  (some items failed)
           → failed            (all items failed)
```

---

### GET /batch/scans/:jobId/results

Get full extraction results for each item in a completed batch job.

**Required scopes:** `batch:read`, `scan:read`

#### Response `200 OK`

```typescript
{
  job_id: string;
  status: string;
  results: Array<{
    index: number;              // 0-based position in original items array
    status: 'success' | 'failed';
    scan_id?: string;
    extracted_data?: ScanExtractedData;  // Same as POST /scan response
    confidence_band?: 'high' | 'medium' | 'low';
    auto_saved?: boolean;
    transaction_id?: string;    // Present if auto_saved
    error?: string;             // Present if status is 'failed'
  }>;
  summary?: BatchSummary;
}
```

---

### GET /projects

List all projects belonging to the authenticated user.

**Required scope:** `projects:read`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | `all` | `active`, `archived`, or `all` |
| `limit` | integer | 50 | Max results (max: 200) |
| `offset` | integer | 0 | Pagination offset |
| `format` | string | `json` | `json`, `csv`, or `text` |

#### Response `200 OK`

```typescript
{
  projects: Array<{
    project_id: string;
    name: string;
    description: string;
    status: 'active' | 'archived';
    transaction_count: number;
    created_at: string;
    updated_at: string;
  }>;
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
  };
}
```

---

### POST /projects

Create a new project.

**Required scope:** `projects:write`

#### Request Body

```typescript
{
  name: string;         // Required, non-empty, max 100 characters
  description?: string; // Optional, max 500 characters
}
```

#### Response `201 Created`

Returns the created project object with `transaction_count: 0`.

---

### PATCH /projects/:id

Update a project's name, description, or archive status.

**Required scope:** `projects:write`

#### Request Body

```typescript
{
  name?: string;
  description?: string;
  status?: 'active' | 'archived';
}
```

#### Response `200 OK`

Returns the updated project object.

---

### DELETE /projects/:id

Delete a project. Transactions referencing the deleted project are **not** deleted; their `project_id` field is left intact.

**Required scope:** `projects:write`

#### Response `204 No Content`

#### Errors

| Code | Condition |
|------|-----------|
| `NOT_FOUND` | Project does not exist or belongs to different user |

---

### GET /summary

Get aggregated financial statistics for a time period. Useful for dashboards and reports.

**Required scope:** `transactions:read`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | `current_month` | `current_month`, `last_30_days`, `last_90_days`, `ytd`, `all_time` |
| `start_date` | string | — | Override period start (YYYY-MM-DD) |
| `end_date` | string | — | Override period end (YYYY-MM-DD) |
| `project_id` | string | — | Limit to single project |
| `group_by` | string | — | `category`, `vendor`, `payment_method`, `month` |

> **Note:** If `start_date` or `end_date` is provided, it overrides the `period` parameter.

#### Response `200 OK`

```typescript
{
  period: {
    start: string;    // ISO date
    end: string;
  };
  totals: {
    income: number;
    expense: number;
    net: number;       // income - expense
    transaction_count: number;
  };
  breakdown: Array<{
    label: string;     // Category/vendor/month name
    total: number;
    count: number;
    percentage: number;  // Share of total expense or income
  }>;
}
```

#### Example — Monthly category breakdown

```bash
curl "https://recite.rivra.dev/apiV1/api/v1/summary?\
period=last_30_days&group_by=category" \
  -H "Authorization: Bearer sk_live_YOUR_KEY"
```

---

### POST /webhooks

Register a webhook endpoint to receive real-time event notifications.

**Required scope:** `webhooks:manage`

#### Request Body

```typescript
{
  url: string;          // Required, must be HTTPS
  events: string[];     // Required, non-empty array of event types
  secret?: string;      // HMAC secret; auto-generated if omitted
}
```

#### Available Events

| Event | Triggered When |
|-------|---------------|
| `transaction.created` | A transaction is created (including auto-save from scan) |
| `transaction.updated` | A transaction field is updated |
| `transaction.deleted` | A transaction is deleted |
| `batch.completed` | A batch scan job finishes processing |

#### Response `201 Created`

```typescript
{
  webhook_id: string;
  url: string;
  events: string[];
  active: boolean;
  secret: string;       // Store this — used to verify signatures
  created_at: string;
}
```

> **Important:** Save the `secret` from this response. It is not retrievable later. Use it to verify the `X-Recite-Signature` on incoming webhook requests.

---

### GET /webhooks

List all registered webhooks.

**Required scope:** `webhooks:manage`

#### Response `200 OK`

Returns an array of webhook objects ordered by `created_at` descending. The `secret` field is **not** included in list responses.

---

### DELETE /webhooks/:id

Delete a webhook registration. No further events will be sent to its URL.

**Required scope:** `webhooks:manage`

#### Response `204 No Content`

---

### POST /rules

Create an automation rule. Rules are applied automatically when transactions are saved from scans, overriding extracted values based on matching conditions.

**Required scope:** `rules:write`

#### Request Body

```typescript
{
  rule_type: 'vendor_category' | 'default_project' | 'processing_preference';
  condition: {
    vendor?: string;              // Exact vendor match
    category_contains?: string;   // Case-insensitive substring match on category
  };
  action: {
    set_category?: string;        // Override category
    set_project_id?: string;      // Assign to project
    set_payment_method?: string;  // Override payment method
  };
  priority?: number;              // Execution order (default: 0, lower runs first)
}
```

#### Response `201 Created`

```typescript
{
  rule_id: string;
  rule_type: string;
  condition: object;
  action: object;
  priority: number;
  created_at: string;
}
```

#### Rule Evaluation

When a transaction is auto-saved from a scan, all matching rules execute in ascending priority order. Later rules can override earlier ones if they set the same field.

#### Example Rule

```json
{
  "rule_type": "vendor_category",
  "condition": { "vendor": "Starbucks" },
  "action": { "set_category": "Coffee & Beverages", "set_project_id": "proj_expenses" },
  "priority": 1
}
```

---

### GET /rules

List all automation rules.

**Required scope:** `rules:read`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 50 | Max results (max: 200) |
| `offset` | integer | 0 | Pagination offset |

#### Response `200 OK`

Returns an array of rule objects ordered by `priority` ascending, then `created_at` ascending.

---

### DELETE /rules/:id

Delete an automation rule.

**Required scope:** `rules:write`

#### Response `204 No Content`

---

### GET /usage

Get detailed usage statistics for your API key.

**Required scope:** `usage:read`

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `period` | string | `current_month` | `current_month`, `last_30_days`, `today` |
| `breakdown` | string | `total` | `total` or `daily` |

#### Response `200 OK`

```typescript
{
  api_key_id: string;
  period: string;
  quota: {
    monthly_scan_limit: number;
    monthly_scan_count: number;
    remaining: number;
    reset_date: string;         // ISO date when count resets
  };
  usage: {
    total_requests: number;
    scans_count: number;
    scans_successful: number;
    scans_failed: number;
    transactions_created: number;
    batch_jobs_submitted: number;
  };
  daily_breakdown?: Array<{     // Present when breakdown=daily
    date: string;
    requests: number;
    scans: number;
    transactions: number;
  }>;
}
```

---

### POST /export

Export all matching transactions to CSV or JSON for download.

**Required scope:** `export:create`

#### Request Body

```typescript
{
  format: 'csv' | 'json';   // Required
  filters?: {
    start_date?: string;    // YYYY-MM-DD
    end_date?: string;      // YYYY-MM-DD
    source?: string;
    agent_name?: string;
    project_id?: string;
  };
}
```

#### Response `200 OK`

- **JSON format:** Standard API response envelope with a `transactions` array
- **CSV format:** `text/csv` with `Content-Disposition: attachment; filename="transactions.csv"`

**Exported CSV columns:**
`transaction_id`, `date`, `amount`, `transaction_type`, `category`, `vendor`, `description`, `payment_method`, `project_id`, `source`

---

## 9. Webhooks Guide

### How It Works

1. Register a webhook with `POST /webhooks`, specifying the HTTPS URL and events you want
2. When an event occurs, Recite sends a `POST` request to your URL within seconds
3. Verify the request signature to ensure it came from Recite
4. Respond with any `2xx` status to acknowledge receipt

### Payload Structure

```json
{
  "event": "transaction.created",
  "timestamp": "2026-03-01T14:32:00.000Z",
  "data": {
    "transaction_id": "txn_abc123"
  }
}
```

For `batch.completed`:
```json
{
  "event": "batch.completed",
  "timestamp": "2026-03-01T14:32:00.000Z",
  "data": {
    "job_id": "job_xyz789"
  }
}
```

### Signature Verification

Every webhook request includes a `X-Recite-Signature` header:

```
X-Recite-Signature: sha256=a1b2c3d4e5f6...
```

Verify the signature using HMAC-SHA256 over the raw request body:

```javascript
const crypto = require('crypto');

function verifyWebhook(rawBody, signature, secret) {
  const expected = 'sha256=' + crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signature)
  );
}

// In your Express handler:
app.post('/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  const sig = req.headers['x-recite-signature'];

  if (!verifyWebhook(req.body, sig, process.env.WEBHOOK_SECRET)) {
    return res.status(401).send('Invalid signature');
  }

  const event = JSON.parse(req.body);
  // Handle event...
  res.status(200).send('OK');
});
```

### Delivery Behavior

- Webhooks are delivered as fire-and-forget (best effort)
- Delivery failures are not automatically retried in the current version
- Always respond with `2xx` within 10 seconds to avoid timeouts

---

## 10. Idempotency

Use idempotency keys to safely retry failed scan requests without risk of double-processing.

### How to Use

Include an `idempotency_key` field in any `POST /scan` request body:

```json
{
  "image_url": "https://example.com/receipt.jpg",
  "idempotency_key": "order-12345-scan-attempt-1"
}
```

Or use the `Idempotency-Key` request header:

```
Idempotency-Key: order-12345-scan-attempt-1
```

### Behavior

- If a request with the same key (and same API key) is received within **24 hours**, the cached response is returned immediately without re-processing
- Idempotency keys are scoped per API key — the same key value used by different API keys does not conflict
- Cache TTL is 24 hours

### When to Use

- After a network timeout where you don't know if the request reached the server
- In retry loops for important scan operations
- When processing the same receipt in multiple code paths

---

## 11. Batch Processing

### Workflow

```
POST /batch/scans          → job_id, status: 'processing'
     ↓
GET /batch/scans/:jobId    → Poll for status change
     ↓ (or webhook)
GET /batch/scans/:jobId/results  → Full extraction results
```

### Best Practices

**Poll with exponential backoff:**
```javascript
async function waitForBatch(jobId, apiKey) {
  let delay = 2000;
  for (let i = 0; i < 15; i++) {
    await sleep(delay);
    const status = await getJobStatus(jobId, apiKey);
    if (status !== 'processing') return status;
    delay = Math.min(delay * 1.5, 30000);
  }
  throw new Error('Batch timed out');
}
```

**Use webhooks for large batches** instead of polling. Register a webhook for `batch.completed` and include the `webhook_url` in your batch request.

### Concurrency

Batch items are processed with a concurrency of 5 items at a time. A batch of 20 items typically completes in 20–60 seconds depending on image complexity.

### Auto-Save in Batches

When `auto_save: true`, each item that meets the `save_threshold` will automatically create a transaction. The `results[n].transaction_id` field indicates which items were saved.

---

## 12. AI Agent Integration

Recite's API is designed for seamless use by AI agents and LLM-powered systems.

### Recommended Workflow for Receipt Processing Agents

```
1. User sends receipt image/URL
2. Agent calls POST /scan with ephemeral: true to preview extraction
3. If confidence_band is 'low', ask user to provide a clearer image
4. If confidence_band is 'medium' or 'high', call POST /scan with auto_save: true
5. Report extracted data and transaction_id to user
```

### Suggested System Prompt Snippet

```
You have access to the Recite API for scanning receipts and managing financial transactions.
Base URL: https://recite.rivra.dev/apiV1/api/v1
Authentication: Bearer token in Authorization header

Available capabilities:
- POST /scan: Extract data from receipt images or text
- POST /transactions: Create transactions manually
- GET /transactions: Search and filter existing transactions
- GET /summary: Get financial aggregations
- GET /projects: List available project categories
- GET /usage: Check remaining scan quota before processing

Always check GET /usage before batch operations to ensure sufficient quota.
Use save_threshold: 'high' for automatic saves; present low-confidence results to user for review.
Use idempotency_key when retrying failed requests.
```

### Handling Extraction Failures

When `EXTRACTION_FAILED` (422) is returned, the image was too unclear for the LLM to parse. Suggested response to users: "I couldn't read this receipt clearly. Please try a well-lit photo with the receipt flat and fully visible."

### Quota Management for Agents

```javascript
async function scanWithQuotaCheck(imageUrl, apiKey) {
  // Check quota first for batch operations
  const usage = await getUsage(apiKey);
  if (usage.quota.remaining < 5) {
    throw new Error(`Low scan quota: ${usage.quota.remaining} remaining. Resets ${usage.quota.reset_date}`);
  }

  return await scan({ image_url: imageUrl }, apiKey);
}
```

---

## 13. Code Examples

### JavaScript / TypeScript

```typescript
const BASE_URL = 'https://recite.rivra.dev/apiV1/api/v1';

class ReciteClient {
  constructor(private apiKey: string) {}

  private async request(method: string, path: string, body?: object) {
    const response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    const data = await response.json();
    if (!data.success) throw new Error(`${data.error.code}: ${data.error.message}`);
    return data;
  }

  scan(params: object) {
    return this.request('POST', '/scan', params);
  }

  listTransactions(params?: object) {
    const qs = params ? '?' + new URLSearchParams(params as any).toString() : '';
    return this.request('GET', `/transactions${qs}`);
  }

  createTransaction(data: object) {
    return this.request('POST', '/transactions', data);
  }

  getUsage() {
    return this.request('GET', '/usage');
  }
}

// Usage
const client = new ReciteClient(process.env.RECITE_API_KEY!);

const result = await client.scan({
  image_url: 'https://cdn.example.com/receipt.jpg',
  auto_save: true,
  save_threshold: 'high',
  project_id: 'proj_abc123',
});

console.log(`Saved as transaction: ${result.data.transaction_id}`);
```

### Python

```python
import os
import requests

BASE_URL = "https://recite.rivra.dev/apiV1/api/v1"

class ReciteClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _request(self, method, path, **kwargs):
        resp = self.session.request(method, f"{BASE_URL}{path}", **kwargs)
        data = resp.json()
        if not data.get("success"):
            raise Exception(f"{data['error']['code']}: {data['error']['message']}")
        return data

    def scan(self, **kwargs):
        return self._request("POST", "/scan", json=kwargs)

    def list_transactions(self, **kwargs):
        return self._request("GET", "/transactions", params=kwargs)

    def create_transaction(self, **kwargs):
        return self._request("POST", "/transactions", json=kwargs)

    def get_summary(self, **kwargs):
        return self._request("GET", "/summary", params=kwargs)

    def get_usage(self):
        return self._request("GET", "/usage")


# Usage
client = ReciteClient(os.environ["RECITE_API_KEY"])

# Scan receipt
result = client.scan(
    image_url="https://cdn.example.com/receipt.jpg",
    auto_save=True,
    save_threshold="high",
    project_id="proj_abc123",
)
print(f"Transaction ID: {result['data']['transaction_id']}")

# Get monthly summary by category
summary = client.get_summary(period="current_month", group_by="category")
for item in summary["data"]["breakdown"]:
    print(f"{item['label']}: ${item['total']:.2f} ({item['percentage']:.1f}%)")
```

### cURL — Common Operations

```bash
# List transactions from the last 30 days
curl "https://recite.rivra.dev/apiV1/api/v1/transactions?\
start_date=2026-02-01&end_date=2026-02-28&sort_by=amount&sort_order=desc" \
  -H "Authorization: Bearer sk_live_YOUR_KEY"

# Create a manual transaction
curl -X POST https://recite.rivra.dev/apiV1/api/v1/transactions \
  -H "Authorization: Bearer sk_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2026-03-01",
    "amount": 125.00,
    "transaction_type": "Expense",
    "category": "Office Supplies",
    "vendor": "Staples",
    "payment_method": "Corporate Card",
    "project_id": "proj_abc123"
  }'

# Submit batch of 3 receipts
curl -X POST https://recite.rivra.dev/apiV1/api/v1/batch/scans \
  -H "Authorization: Bearer sk_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {"image_url": "https://example.com/r1.jpg"},
      {"image_url": "https://example.com/r2.jpg"},
      {"image_url": "https://example.com/r3.jpg"}
    ],
    "auto_save": true,
    "save_threshold": "high",
    "project_id": "proj_abc123",
    "webhook_url": "https://myserver.com/webhooks/recite"
  }'

# Export January transactions as CSV
curl -X POST https://recite.rivra.dev/apiV1/api/v1/export \
  -H "Authorization: Bearer sk_live_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "format": "csv",
    "filters": {
      "start_date": "2026-01-01",
      "end_date": "2026-01-31"
    }
  }' -o january.csv
```

---

## 14. FAQ

**Q: Does the API count against the same quota as the web app?**
Yes. All scan calls (web and API) share the same monthly quota pool. Monitor via `GET /usage` or `meta.quota_remaining` on scan responses.

**Q: What image formats are supported?**
JPEG, PNG, WebP, and PDF. Images should be under 10MB. Use high-resolution, well-lit photos for best extraction accuracy.

**Q: Can I use `image_base64` for large images?**
Yes, but prefer `image_url` when possible to minimize request payload size. Base64 encoding increases payload size by ~33%.

**Q: Is auto-save atomic with scanning?**
Yes. The transaction is created within the same scan request. If transaction creation fails, `transaction_id` is absent from the response and `auto_save_skipped_reason` explains why.

**Q: Can I scan PDFs?**
PDF files can be provided as base64. Multi-page PDFs are processed using the first page only.

**Q: How do I get the highest extraction accuracy?**
- Use clear, high-resolution images (minimum 1000px on the shorter side)
- Ensure the receipt is flat and fully visible in the frame
- Avoid glare, blur, and shadows
- `extraction_method: 'vision'` (with image input) is more accurate than `text_llm` (raw text input)

**Q: What happens when `ephemeral: true`?**
The scan runs through the LLM pipeline normally, but nothing is written to Firestore (no scan history, no idempotency record). Quota is still consumed. Use this for preview/validation flows where you don't want to persist raw scan records.

**Q: How are rules applied?**
Rules are evaluated on every auto-saved transaction, in ascending `priority` order. Rules with the same priority run in creation order. Each matching rule can override `category`, `project_id`, and/or `payment_method` of the transaction.

**Q: Can I delete a transaction that was auto-saved from a scan?**
Yes. `DELETE /transactions/:id` deletes the transaction. The original scan record in `api_scans` is not deleted.

**Q: What's the difference between `RATE_LIMITED` and `QUOTA_EXCEEDED`?**
`RATE_LIMITED` (429) means too many requests in the current minute/hour/day window — retry after the `Retry-After` header value. `QUOTA_EXCEEDED` (429) means your monthly scan limit is exhausted — this resets on your billing cycle date and is visible in `GET /usage`.

**Q: Does the API support multi-currency?**
The `currency` field is extracted and stored but Recite does not perform currency conversion. All amounts are stored as-extracted.

---

## Endpoint Reference Summary

| Method | Path | Scope(s) | Description |
|--------|------|----------|-------------|
| `POST` | `/scan` | `scan:create` | Scan receipt and extract data |
| `GET` | `/scan/:id` | `scan:read` | Get scan result |
| `POST` | `/transactions` | `transactions:create` | Create transaction |
| `GET` | `/transactions` | `transactions:read` | List transactions |
| `GET` | `/transactions/:id` | `transactions:read` | Get transaction |
| `PATCH` | `/transactions/:id` | `transactions:update` | Update transaction |
| `DELETE` | `/transactions/:id` | `transactions:delete` | Delete transaction |
| `POST` | `/import/transactions` | `transactions:create` | Bulk import |
| `POST` | `/batch/scans` | `batch:create`, `scan:create` | Submit batch job |
| `GET` | `/batch/scans/:jobId` | `batch:read` | Batch job status |
| `GET` | `/batch/scans/:jobId/results` | `batch:read`, `scan:read` | Batch results |
| `GET` | `/projects` | `projects:read` | List projects |
| `POST` | `/projects` | `projects:write` | Create project |
| `PATCH` | `/projects/:id` | `projects:write` | Update project |
| `DELETE` | `/projects/:id` | `projects:write` | Delete project |
| `GET` | `/summary` | `transactions:read` | Financial aggregation |
| `POST` | `/webhooks` | `webhooks:manage` | Register webhook |
| `GET` | `/webhooks` | `webhooks:manage` | List webhooks |
| `DELETE` | `/webhooks/:id` | `webhooks:manage` | Delete webhook |
| `POST` | `/rules` | `rules:write` | Create automation rule |
| `GET` | `/rules` | `rules:read` | List rules |
| `DELETE` | `/rules/:id` | `rules:write` | Delete rule |
| `GET` | `/usage` | `usage:read` | Usage statistics |
| `POST` | `/export` | `export:create` | Export transactions |
