# Recite Public API - Complete Reference Guide

**Version:** 1.0
**Base URL:** `https://recite.rivra.dev/apiV1/api/v1`
**Last Updated:** February 2026

This is the comprehensive reference for the Recite Public API. It enables AI agents, applications, and automation systems to scan receipts, extract financial data, and manage transactions programmatically.

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Authentication](#2-authentication)
3. [Base URL and Headers](#3-base-url-and-headers)
4. [Response Format](#4-response-format)
5. [Error Codes](#5-error-codes)
6. [Rate Limits](#6-rate-limits)
7. [Scopes and Permissions](#7-scopes-and-permissions)
8. [Endpoints](#8-endpoints)
   - 8.1 POST /scan · 8.2 GET /scan/:id
   - 8.3 POST /transactions · 8.4 GET /transactions · 8.5 GET /transactions/:id · 8.6 PATCH /transactions/:id
   - **8.13 POST /import/transactions** ← _new_
   - 8.7 POST /batch/scans · 8.8 GET /batch/scans/:id · 8.9 GET /batch/scans/:id/results
   - 8.10 GET /usage · 8.11 POST /export · 8.12 GET /projects
9. [Webhooks](#9-webhooks)
10. [Best Practices](#10-best-practices)
11. [Code Examples](#11-code-examples)
12. [FAQ](#12-faq)

---

## 1. Quick Start

### Prerequisites

1. **Recite Account** - Sign up at [recite.rivra.dev](https://recite.rivra.dev)
2. **API Key** - Create one at Settings > API Access
3. **Active Subscription** - API shares monthly scan quota with web app

### Your First API Call

```bash
curl -X POST https://recite.rivra.dev/apiV1/api/v1/scan \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_url": "https://example.com/receipt.jpg"}'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_id": "uuid-here",
    "extracted_data": {
      "date": "2026-02-07",
      "amount": 42.50,
      "subtotal": 39.81,
      "tax": 2.69,
      "vendor": "Starbucks Coffee",
      "category": "Food & Dining",
      "payment_method": "Credit Card",
      "confidence": {"overall": 0.92}
    },
    "transaction_type": "Expense"
  }
}
```

---

## 2. Authentication

### Getting an API Key

1. Sign in to Recite
2. Navigate to **Settings > API Access**
3. Click **Create API Key**
4. Provide:
   - **Key Name** - Human-readable label (e.g., "Production Scanner")
   - **Agent Name** (optional) - Identifies your AI agent or app
5. **Copy the key immediately** - It's shown only once

**Key Format:** `sk_live_{5-char-prefix}_{32-hex-chars}`
**Example:** `sk_live_abc12_f8a92b1c4d5e6f7a8b9c0d1e2f3a4b5c`

### Using the Key

Include in every request as a Bearer token:

```http
Authorization: Bearer sk_live_abc12_f8a92b1c4d5e6f7a8b9c0d1e2f3a4b5c
```

### Security Best Practices

- ✅ Store keys in environment variables or secret managers
- ✅ Use different keys for development and production
- ✅ Rotate keys periodically (24-hour grace period supported)
- ❌ Never commit keys to version control
- ❌ Never expose keys in client-side code

---

## 3. Base URL and Headers

### Base URL

```
https://recite.rivra.dev/apiV1/api/v1
```

All endpoint paths in this document are relative to this base URL.

### Standard Request Headers

```http
Authorization: Bearer YOUR_API_KEY       # Required
Content-Type: application/json            # Required for POST/PATCH
Accept: application/json                  # Optional (default: JSON)
X-Request-ID: your-unique-uuid            # Optional (auto-generated if omitted)
```

### Response Headers

Every response includes:

```http
X-Request-ID: uuid                        # Request identifier
X-API-Version: v1                         # API version
X-RateLimit-Limit: 30                     # Requests per minute limit
X-RateLimit-Remaining: 28                 # Remaining requests
X-RateLimit-Reset: 1706140860             # Unix timestamp when limit resets
```

---

## 4. Response Format

### Success Response

```json
{
  "success": true,
  "data": {
    // ... endpoint-specific data
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "api_version": "v1",
    "processing_time_ms": 1234
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Human-readable error description",
    "details": {}
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "api_version": "v1",
    "processing_time_ms": 5
  }
}
```

### Alternative Formats

The API supports three response formats:

1. **JSON** (default) - `?format=json` or `Accept: application/json`
2. **CSV** - `?format=csv` or `Accept: text/csv`
3. **Text** - `?format=text` or `Accept: text/plain`

---

## 5. Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request, missing fields, invalid values |
| 400 | `INVALID_IMAGE` | Image unreachable, unsupported format, timeout |
| 401 | `INVALID_API_KEY` | Missing, malformed, revoked, or expired key |
| 403 | `INSUFFICIENT_SCOPE` | Key lacks required permission scope |
| 404 | `NOT_FOUND` | Resource not found or not owned by you |
| 409 | `DUPLICATE` | Idempotency key already used (returns cached response) |
| 413 | `FILE_TOO_LARGE` | Image exceeds 5MB limit |
| 422 | `EXTRACTION_FAILED` | No text detected in image |
| 429 | `RATE_LIMITED` | Rate limit exceeded |
| 429 | `QUOTA_EXCEEDED` | Monthly scan quota exhausted |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## 6. Rate Limits

Rate limits apply per API key using sliding windows:

| Window | Limit |
|--------|-------|
| Per minute | 30 requests |
| Per hour | 500 requests |
| Per day | 5,000 requests |

### Handling Rate Limits

When rate limited (HTTP 429):

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded (30 requests per minute).",
    "details": {"window": "minute", "limit": 30}
  }
}
```

Response includes:
```http
Retry-After: 60                           # Seconds to wait
X-RateLimit-Remaining: 0
```

**Best Practice:** Check `X-RateLimit-Remaining` header and throttle before hitting limit.

---

## 7. Scopes and Permissions

Each API key has scopes that control endpoint access:

| Scope | Description | Default? |
|-------|-------------|----------|
| `scan:create` | Create scans (POST /scan, batch) | ✅ |
| `scan:read` | Read scan results (GET /scan/:id) | ✅ |
| `transactions:create` | Create transactions | ✅ |
| `transactions:read` | Read/list transactions | ✅ |
| `transactions:update` | Update transactions | ✅ |
| `batch:create` | Submit batch jobs | ❌ |
| `batch:read` | Read batch status/results | ❌ |
| `projects:read` | List and read project details | ✅ |
| `usage:read` | Read usage statistics | ✅ |
| `export:create` | Export transactions | ❌ |

**Insufficient Scope Error:**

```json
{
  "error": {
    "code": "INSUFFICIENT_SCOPE",
    "message": "API key lacks required scope: batch:create",
    "details": {
      "required_scopes": ["batch:create"],
      "key_scopes": ["scan:create", "scan:read"]
    }
  }
}
```

---

## 8. Endpoints

### 8.1 POST /api/v1/scan

Scan a receipt image and extract structured financial data using AI.

**Required Scope:** `scan:create`

**Request Body:**

```json
{
  "image_url": "https://example.com/receipt.jpg",
  "image_base64": "base64-encoded-data",
  "image_type": "image/jpeg",
  "raw_text": "extracted text if you have it",
  "auto_save": false,
  "project_id": "project-uuid",
  "idempotency_key": "unique-string",
  "metadata": {"source": "email"}
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image_url` | string | One of: url/base64/raw_text | Publicly accessible image URL. Max 5MB, 10s timeout. |
| `image_base64` | string | One of: url/base64/raw_text | Base64-encoded image. Supports data URI format. |
| `image_type` | string | No | MIME type hint (auto-detected if omitted). |
| `raw_text` | string | One of: url/base64/raw_text | Pre-extracted text to process with LLM. |
| `auto_save` | boolean | No | If true, auto-creates transaction. Default: false. |
| `project_id` | string | **Required with auto_save** | Project UUID. REQUIRED when auto_save=true. Use GET /api/v1/projects to retrieve your project IDs. |
| `idempotency_key` | string | No | Prevent duplicate processing (24h cache). |
| `metadata` | object | No | Custom key-value metadata. |

**Important:** Provide exactly **one** of: `image_url`, `image_base64`, or `raw_text`.

**Important - Auto-Save:** When `auto_save: true`, you MUST provide a valid `project_id`. The API validates that:
1. The project exists
2. You own the project

Use `GET /api/v1/projects` to retrieve your project IDs.

**Supported Formats:** JPEG, PNG, WebP, PDF

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "scan_id": "uuid",
    "extracted_data": {
      "date": "2026-02-07",
      "amount": 42.50,
      "subtotal": 39.81,
      "tax": 2.69,
      "discount": null,
      "discount_description": null,
      "vendor": "Starbucks Coffee",
      "category": "Food & Dining",
      "description": "Grande Latte",
      "payment_method": "Credit Card",
      "confidence": {
        "date": 0.95,
        "amount": 0.98,
        "vendor": 0.90,
        "category": 0.85,
        "payment_method": 0.80,
        "overall": 0.92
      }
    },
    "warnings": [],
    "extraction_method": "vision",
    "transaction_type": "Expense",
    "verification": {
      "amount_verified": true,
      "subtotal": 39.81,
      "discount": null,
      "discount_description": null,
      "tax": 2.69,
      "total": 42.50,
      "discrepancy": 0,
      "method": "subtotal_tax"
    },
    "suggestions": ["Consider categorizing coffee purchases under 'Business Meals'"],
    "raw_text": "STARBUCKS COFFEE\n123 Main St...",
    "image_source": "url",
    "transaction_id": "txn-uuid-if-auto-save-was-true"
  }
}
```

**Extraction Methods:**

- `vision` - Gemini Flash Vision (direct image → JSON)
- `vision_fallback` - Vision API OCR → text LLM (fallback if vision fails)
- `text_llm` - LLM text extraction (when `raw_text` provided)

**Verification Object:**

- `amount_verified` - Whether subtotal + discount + tax = total
- `subtotal` - Pre-tax subtotal amount
- `discount` - Pre-tax discount/savings as a negative number (null if none)
- `discount_description` - Comma-separated list of discounts with amounts (null if none)
- `tax` - Tax amount
- `total` - Final total after all adjustments
- `method` - Verification approach: `subtotal_tax`, `single_amount`, or `unverifiable`
- `discrepancy` - Difference between calculated and stated total (if any)

**Errors:**

| Scenario | Error Code |
|----------|------------|
| No input provided | `INVALID_REQUEST` |
| Multiple inputs provided | `INVALID_REQUEST` |
| auto_save without project_id | `INVALID_REQUEST` - "project_id is required when auto_save is true" |
| Invalid or unowned project_id | `INVALID_REQUEST` - "Project {id} not found" |
| Image unreachable | `INVALID_IMAGE` |
| Image too large (>5MB) | `FILE_TOO_LARGE` |
| No text detected | `EXTRACTION_FAILED` |
| Quota exhausted | `QUOTA_EXCEEDED` |

---

### 8.2 GET /api/v1/scan/:scanId

Retrieve a previously scanned receipt by ID.

**Required Scope:** `scan:read`

**Path Parameter:** `scanId` - UUID from POST /scan response

**Response:** Same structure as POST /scan

**Important:** Scan results expire after **24 hours**.

---

### 8.3 POST /api/v1/transactions

Create a transaction manually (without scanning).

**Required Scope:** `transactions:create`

**Request Body:**

```json
{
  "date": "2026-02-07",
  "amount": 42.50,
  "subtotal": 39.81,
  "discount": null,
  "discount_description": null,
  "tax": 2.69,
  "transaction_type": "Expense",
  "category": "Food & Dining",
  "vendor": "Starbucks",
  "description": "Team coffee",
  "payment_method": "Credit Card",
  "project_id": "project-uuid",
  "scan_id": "scan-uuid",
  "metadata": {"department": "engineering"}
}
```

**Parameters:**

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `date` | string | **Yes** | Must be YYYY-MM-DD format |
| `amount` | number | **Yes** | Must be positive (> 0) |
| `subtotal` | number | No | Positive number |
| `discount` | number | No | Pre-tax discount as negative number (e.g., -4.74), or null |
| `discount_description` | string | No | Comma-separated discount list, or null |
| `tax` | number | No | Positive number or 0 |
| `transaction_type` | string | **Yes** | Must be "Income" or "Expense" (capitalized) |
| `category` | string | **Yes** | Non-empty string |
| `payment_method` | string | **Yes** | Non-empty string |
| `vendor` | string | No | Defaults to empty string |
| `description` | string | No | Defaults to empty string |
| `project_id` | string | No | Must be valid project UUID you own |
| `scan_id` | string | No | Must be valid scan UUID you own |
| `metadata` | object | No | Custom key-value data |

**Response (201 Created):**

```json
{
  "success": true,
  "data": {
    "transaction_id": "uuid",
    "date": "2026-02-07",
    "amount": 42.50,
    "subtotal": 39.81,
    "discount": null,
    "discount_description": null,
    "tax": 2.69,
    "transaction_type": "Expense",
    "category": "Food & Dining",
    "vendor": "Starbucks",
    "description": "Team coffee",
    "payment_method": "Credit Card",
    "project_id": "project-uuid",
    "source": "api",
    "api_key_id": "key-uuid",
    "agent_name": "my-agent",
    "created_at": "2026-02-07T10:30:00.000Z",
    "updated_at": "2026-02-07T10:30:00.000Z"
  }
}
```

All API-created transactions have:
- `source: "api"`
- `status: "reviewed"` (finalized, not draft)
- Auto-tagged with `api_key_id` and `agent_name`

---

### 8.4 GET /api/v1/transactions

List transactions with filters and pagination.

**Required Scope:** `transactions:read`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_id` | string | - | Filter by project |
| `start_date` | string | - | YYYY-MM-DD (inclusive) |
| `end_date` | string | - | YYYY-MM-DD (inclusive) |
| `transaction_type` | string | - | "Income" or "Expense" |
| `source` | string | - | "api" or "web" |
| `agent_name` | string | - | Filter by agent |
| `sort_by` | string | `"date"` | "date", "amount", or "created_at" |
| `sort_order` | string | `"desc"` | "asc" or "desc" |
| `limit` | number | 50 | 1-200 results per page |
| `offset` | number | 0 | Pagination offset |
| `format` | string | `"json"` | "json", "csv", or "text" |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "transaction_id": "uuid",
        "date": "2026-02-07",
        "amount": 42.50,
        // ... full transaction object
      }
    ],
    "pagination": {
      "total": 150,
      "limit": 50,
      "offset": 0,
      "has_more": true
    }
  }
}
```

**CSV Format:** When `?format=csv`, returns CSV file with headers.

---

### 8.5 GET /api/v1/transactions/:id

Get a single transaction by ID.

**Required Scope:** `transactions:read`

**Path Parameter:** `id` - transaction UUID

**Response:** Single transaction object (same as list item)

---

### 8.6 PATCH /api/v1/transactions/:id

Update specific fields on a transaction.

**Required Scope:** `transactions:update`

**Path Parameter:** `id` - transaction UUID

**Request Body (all fields optional):**

```json
{
  "date": "2026-02-08",
  "amount": 45.00,
  "subtotal": 42.00,
  "discount": null,
  "discount_description": null,
  "tax": 3.00,
  "transaction_type": "Expense",
  "category": "Office Supplies",
  "vendor": "Staples",
  "description": "Updated description",
  "payment_method": "Debit Card",
  "project_id": "new-project-uuid"
}
```

Only provided fields are updated; omitted fields remain unchanged.

**Response (200 OK):** Full updated transaction object

---

### 8.7 POST /api/v1/batch/scans

Submit multiple receipts for asynchronous processing.

**Required Scopes:** `batch:create` AND `scan:create`

**Request Body:**

```json
{
  "items": [
    {"image_url": "https://example.com/receipt1.jpg"},
    {"image_url": "https://example.com/receipt2.jpg"},
    {"image_base64": "base64-data", "metadata": {"note": "from email"}},
    {"image_url": "https://example.com/receipt4.png"}
  ],
  "auto_save": true,
  "project_id": "project-uuid",
  "webhook_url": "https://your-server.com/webhook",
  "webhook_secret": "whsec_secret123"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `items` | array | **Yes** | 1-20 items. Each needs `image_url` or `image_base64` |
| `auto_save` | boolean | No | Auto-create transactions for successful scans |
| `project_id` | string | No | Apply to all auto-saved transactions |
| `webhook_url` | string | No | POST webhook when job completes |
| `webhook_secret` | string | No | HMAC-SHA256 signature secret |

**Response (202 Accepted):**

```json
{
  "success": true,
  "data": {
    "job_id": "batch-uuid",
    "status": "processing",
    "total_items": 4,
    "status_url": "/api/v1/batch/scans/batch-uuid"
  }
}
```

**Processing Details:**
- Items processed in chunks of 3 concurrently
- Each item counts toward scan quota
- Progress updated in real-time in Firestore
- Results expire after 24 hours

---

### 8.8 GET /api/v1/batch/scans/:jobId

Get batch job status.

**Required Scope:** `batch:read`

**Path Parameter:** `jobId` - UUID from POST response

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "job_id": "batch-uuid",
    "status": "completed",
    "total_items": 4,
    "processed_count": 4,
    "successful_count": 3,
    "failed_count": 1,
    "created_at": "2026-02-07T10:30:00.000Z",
    "completed_at": "2026-02-07T10:31:15.000Z"
  }
}
```

**Status Values:**
- `processing` - In progress
- `completed` - All succeeded
- `partially_failed` - Some succeeded, some failed
- `failed` - All failed

**Polling:** Poll every 3-5 seconds until status != "processing"

---

### 8.9 GET /api/v1/batch/scans/:jobId/results

Get detailed results for each item in a batch.

**Required Scopes:** `batch:read` AND `scan:read`

**Path Parameter:** `jobId` - batch UUID

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "job_id": "batch-uuid",
    "status": "partially_failed",
    "results": [
      {
        "index": 0,
        "status": "success",
        "scan_id": "scan-uuid-1",
        "extracted_data": {
          "date": "2026-02-07",
          "amount": 42.50,
          "vendor": "Starbucks",
          // ... full extracted data
        }
      },
      {
        "index": 1,
        "status": "failed",
        "error": "No text detected in image"
      }
    ]
  }
}
```

---

### 8.10 GET /api/v1/usage

Get usage statistics and quota information.

**Required Scope:** `usage:read`

**Query Parameters:**

| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| `period` | string | `"current_month"` | "current_month", "last_30_days", "today" |
| `breakdown` | string | `"total"` | "total" or "daily" |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "api_key_id": "key-uuid",
    "period": "current_month",
    "quota": {
      "monthly_scan_limit": 200,
      "monthly_scan_count": 45,
      "remaining": 155,
      "reset_date": "2026-03-01T00:00:00.000Z"
    },
    "usage": {
      "total_requests": 120,
      "scans_count": 45,
      "scans_successful": 42,
      "scans_failed": 3,
      "transactions_created": 38,
      "batch_jobs_submitted": 2
    },
    "daily_breakdown": [
      {"date": "2026-02-05", "requests": 15, "scans": 5, "transactions": 4},
      {"date": "2026-02-06", "requests": 22, "scans": 8, "transactions": 7}
    ]
  }
}
```

**Quota:** API shares scan quota with web app.

---

### 8.11 POST /api/v1/export

Export transactions as CSV or JSON file.

**Required Scope:** `export:create`

**Request Body:**

```json
{
  "format": "csv",
  "filters": {
    "start_date": "2026-01-01",
    "end_date": "2026-01-31",
    "source": "api",
    "agent_name": "my-agent",
    "project_id": "project-uuid"
  }
}
```

**CSV Response:** Returns downloadable CSV with `Content-Disposition: attachment`

**JSON Response:**

```json
{
  "success": true,
  "data": {
    "transactions": [...],
    "total_count": 42,
    "exported_at": "2026-02-07T10:30:00.000Z"
  }
}
```

---

### 8.13 POST /api/v1/import/transactions

Bulk-create transactions from a JSON array or a CSV file. No image scanning occurs — you supply the field values directly. For full details and sample files see [`Import_API_Reference.md`](./Import_API_Reference.md).

**Required Scope:** `transactions:create`

**Limits:** Max 500 rows · Max 10MB body

#### JSON request

```http
POST /api/v1/import/transactions
Content-Type: application/json
```

```json
{
  "transactions": [
    {
      "date": "2025-01-15",
      "amount": 42.50,
      "subtotal": 39.81,
      "tax": 2.69,
      "transaction_type": "Expense",
      "category": "Food & Dining",
      "vendor": "Starbucks",
      "description": "Team coffee",
      "payment_method": "Credit Card",
      "currency": "USD"
    },
    {
      "date": "2025-01-18",
      "amount": 1200.00,
      "transaction_type": "Income",
      "category": "Consulting",
      "vendor": "Acme Corp",
      "description": "Invoice #INV-0042",
      "payment_method": "Bank Transfer"
    },
    {
      "date": "2025-01-22",
      "amount": 89.99,
      "subtotal": 84.90,
      "discount": 10.00,
      "discount_description": "10% loyalty discount",
      "tax": 5.09,
      "transaction_type": "Expense",
      "category": "Software & Tools",
      "vendor": "Adobe Creative Cloud",
      "payment_method": "Credit Card"
    }
  ],
  "all_or_nothing": false,
  "project_id": "a3b2c1d4-e5f6-7890-1234-567890abcdef"
}
```

#### CSV request

```http
POST /api/v1/import/transactions?all_or_nothing=false&project_id=a3b2c1d4-e5f6-7890-1234-567890abcdef
Content-Type: text/csv
```

```csv
Date,Amount,Subtotal,Tax,Discount,Discount Description,Fees,Fees Description,Currency,Type,Category,Vendor,Description,Payment Method,Project
2025-01-15,42.50,39.81,2.69,,,,,USD,Expense,Food & Dining,Starbucks,Team coffee,Credit Card,My Project
2025-01-18,1200.00,1200.00,,,,,,USD,Income,Consulting,Acme Corp,Invoice #INV-0042,Bank Transfer,My Project
2025-01-22,89.99,84.90,5.09,10.00,10% loyalty discount,,,USD,Expense,Software & Tools,Adobe Creative Cloud,Monthly subscription,Credit Card,My Project
```

**Parameters:**

| Field | Type | Required (JSON) | Required (CSV query) | Description |
|-------|------|-----------------|----------------------|-------------|
| `transactions` | array | **Yes** | — | Array of transaction objects |
| `all_or_nothing` | boolean | No | No | Default `false`. If `true`, any error aborts the entire import |
| `project_id` | string | No | No | Default project for rows that don't specify one |

**Transaction field requirements:**

| Field | Required | Notes |
|-------|----------|-------|
| `date` | **Yes** | `YYYY-MM-DD` |
| `amount` | **Yes** | Positive number. Strips `$`, `,` from strings. |
| `transaction_type` | **Yes** | `Expense`, `Income`, `Asset`, `Liability`, `Equity` |
| `category` | **Yes** | Non-empty string |
| `payment_method` | **Yes** | Non-empty string |
| All other fields | No | See Import_API_Reference.md for full field list |

**Response — Partial success (200 OK):**

```json
{
  "success": true,
  "data": {
    "total": 5,
    "imported": 3,
    "failed": 2,
    "transactions": [
      { "row": 1, "transaction_id": "7f3a1bc2-d4e5-6789-0abc-def012345678" },
      { "row": 2, "transaction_id": "9c2b4de3-f6g7-890a-1bcd-ef2345678901" },
      { "row": 4, "transaction_id": "a1b2c3d4-e5f6-7890-abcd-ef0123456789" }
    ],
    "errors": [
      { "row": 3, "field": "amount", "message": "Amount must be a positive number" },
      { "row": 5, "field": "date",   "message": "Invalid date format, expected YYYY-MM-DD" }
    ]
  },
  "meta": {
    "request_id": "550e8400-e29b-41d4-a716-446655440000",
    "api_version": "v1",
    "processing_time_ms": 312
  }
}
```

**Response — all_or_nothing rejection (400 Bad Request):**

```json
{
  "success": false,
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Validation failed for 2 of 5 rows. No transactions were imported (all_or_nothing=true).",
    "details": {
      "total": 5,
      "error_count": 2,
      "errors": [
        { "row": 3, "field": "amount", "message": "Amount must be a positive number" },
        { "row": 5, "field": "date",   "message": "Invalid date format, expected YYYY-MM-DD" }
      ]
    }
  }
}
```

**All imported transactions get:** `status: "reviewed"`, `scan_source: "manual"`, `source: "api"`

> **Note:** Import does **not** consume scan quota. Use this endpoint freely for migrating data from spreadsheets or other systems.

---

### 8.12 GET /api/v1/projects

List all projects for the authenticated user with transaction counts.

**Required Scope:** `projects:read`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | `"all"` | Filter by status: "active", "archived", or "all" |
| `limit` | number | 50 | Results per page (1-200) |
| `offset` | number | 0 | Pagination offset |
| `format` | string | `"json"` | Response format: "json", "csv", or "text" |

**Response (200 OK):**

```json
{
  "success": true,
  "data": {
    "projects": [
      {
        "project_id": "a3b2c1d4-e5f6-7890-1234-567890abcdef",
        "name": "Personal Expenses",
        "description": "My personal spending",
        "status": "active",
        "transaction_count": 42,
        "created_at": "2024-01-15T10:30:00.000Z",
        "updated_at": "2026-02-10T14:20:00.000Z"
      },
      {
        "project_id": "b4c3d2e1-f6g7-8901-2345-678901bcdefg",
        "name": "Business 2024",
        "description": "Q1-Q4 business expenses",
        "status": "archived",
        "transaction_count": 127,
        "created_at": "2024-01-01T00:00:00.000Z",
        "updated_at": "2024-12-31T23:59:59.000Z"
      }
    ],
    "pagination": {
      "total": 5,
      "limit": 50,
      "offset": 0,
      "has_more": false
    }
  },
  "meta": {
    "request_id": "req-uuid",
    "api_version": "v1",
    "processing_time_ms": 124
  }
}
```

**CSV Format:** When `?format=csv`, returns CSV with headers: project_id, name, description, status, transaction_count, created_at, updated_at

**Examples:**

**Python:**
```python
import requests

response = requests.get(
    "https://recite.rivra.dev/apiV1/api/v1/projects",
    headers={"Authorization": f"Bearer {api_key}"},
    params={"status": "active", "limit": 20}
)

projects = response.json()["data"]["projects"]
for project in projects:
    print(f"{project['name']}: {project['transaction_count']} transactions")
```

**Node.js:**
```javascript
const response = await fetch(
  'https://recite.rivra.dev/apiV1/api/v1/projects?status=active',
  {
    headers: {
      'Authorization': `Bearer ${apiKey}`
    }
  }
);

const {data} = await response.json();
data.projects.forEach(project => {
  console.log(`${project.name}: ${project.transaction_count} transactions`);
});
```

**Bash:**
```bash
curl -X GET "https://recite.rivra.dev/apiV1/api/v1/projects?status=active" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**PowerShell:**
```powershell
$headers = @{
    "Authorization" = "Bearer YOUR_API_KEY"
}
$response = Invoke-RestMethod -Uri "https://recite.rivra.dev/apiV1/api/v1/projects?status=active" -Headers $headers
$response.data.projects | Format-Table name, transaction_count, status
```

**Errors:**

| Scenario | Error Code |
|----------|------------|
| Invalid status parameter | `INVALID_REQUEST` - "Status must be 'active', 'archived', or 'all'" |

---

## 9. Webhooks

### Batch Completion Webhook

When submitting a batch with `webhook_url` and `webhook_secret`, the API POSTs to your URL on completion.

**Request:**

```http
POST https://your-server.com/webhook
Content-Type: application/json
X-Recite-Signature: sha256=a1b2c3d4e5f6...
```

```json
{
  "event": "batch.completed",
  "job_id": "batch-uuid",
  "status": "completed",
  "summary": {
    "total": 5,
    "successful": 4,
    "failed": 1
  },
  "timestamp": "2026-02-07T10:31:15.000Z"
}
```

### Signature Verification

The `X-Recite-Signature` header contains HMAC-SHA256 hex digest:

**Python:**
```python
import hmac
import hashlib

def verify_webhook(body_bytes, signature_header, secret):
    expected = hmac.new(
        secret.encode('utf-8'),
        body_bytes,
        hashlib.sha256
    ).hexdigest()
    return signature_header == f"sha256={expected}"
```

**Node.js:**
```javascript
const crypto = require('crypto');

function verifyWebhook(bodyBuffer, signatureHeader, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(bodyBuffer)
    .digest('hex');
  return signatureHeader === `sha256=${expected}`;
}
```

**Behavior:**
- 10-second timeout
- Best-effort (no retries)
- Failure logged but job still completes

---

## 10. Best Practices

### 1. Use Idempotency Keys

Prevent duplicate processing during retries:

```json
{
  "image_url": "https://example.com/receipt.jpg",
  "idempotency_key": "receipt-email-123-2026-02-07"
}
```

Keys are scoped per API key and cached for 24 hours.

### 2. Handle Rate Limits Gracefully

```python
import time

def api_call_with_retry(url, headers, data):
    resp = requests.post(url, headers=headers, json=data)

    if resp.status_code == 429:
        retry_after = int(resp.headers.get('Retry-After', 60))
        time.sleep(retry_after)
        return api_call_with_retry(url, headers, data)

    return resp.json()
```

### 3. Check Quota Before Bulk Operations

```python
def check_quota():
    resp = requests.get(f"{BASE_URL}/usage", headers=headers)
    quota = resp.json()['data']['quota']
    return quota['scans_remaining']

remaining = check_quota()
if remaining < len(receipt_urls):
    print("Not enough quota!")
```

### 4. Use Batch API for Multiple Receipts

For 2+ receipts, use batch API instead of multiple single scans:

```python
# Good: Single batch request
batch_response = requests.post(
    f"{BASE_URL}/batch/scans",
    headers=headers,
    json={"items": [{"image_url": url} for url in urls]}
)

# Less optimal: Multiple single requests
for url in urls:
    requests.post(f"{BASE_URL}/scan", ...)
```

### 5. Validate Images Before Sending

- Ensure images are < 5MB
- Verify URLs are publicly accessible
- Use supported formats (JPEG, PNG, WebP, PDF)

### 6. Tag API-Created Data

Use `metadata` to add context:

```json
{
  "metadata": {
    "source_system": "email_parser",
    "email_id": "msg-12345",
    "processed_by": "automation-v2.1"
  }
}
```

### 7. Monitor Confidence Scores

```python
extracted = response['data']['extracted_data']
if extracted['confidence']['overall'] < 0.7:
    # Flag for manual review
    print(f"Low confidence: {extracted['confidence']}")
```

---

## 11. Code Examples

### Python - Complete Workflow

```python
import requests
import base64

BASE_URL = "https://recite.rivra.dev/apiV1/api/v1"
API_KEY = "sk_live_YOUR_KEY"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Scan with base64 image
with open("receipt.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode('utf-8')

scan_resp = requests.post(
    f"{BASE_URL}/scan",
    headers=HEADERS,
    json={
        "image_base64": image_base64,
        "auto_save": True,
        "project_id": "my-project-uuid"
    }
)

scan_data = scan_resp.json()
if scan_data['success']:
    extracted = scan_data['data']['extracted_data']
    print(f"Vendor: {extracted['vendor']}")
    print(f"Amount: ${extracted['amount']:.2f}")
    print(f"Transaction ID: {scan_data['data'].get('transaction_id')}")
```

### Node.js/TypeScript - Batch Processing

```typescript
const BASE_URL = "https://recite.rivra.dev/apiV1/api/v1";
const API_KEY = "sk_live_YOUR_KEY";

async function processBatch(imageUrls: string[]) {
  // Submit batch
  const batchResp = await fetch(`${BASE_URL}/batch/scans`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      items: imageUrls.map(url => ({image_url: url})),
      auto_save: true
    })
  });

  const batch = await batchResp.json();
  const jobId = batch.data.job_id;
  console.log(`Batch submitted: ${jobId}`);

  // Poll for completion
  while (true) {
    const statusResp = await fetch(`${BASE_URL}/batch/scans/${jobId}`, {
      headers: {"Authorization": `Bearer ${API_KEY}`}
    });
    const status = await statusResp.json();

    if (status.data.status !== "processing") {
      console.log(`Batch complete: ${status.data.status}`);
      console.log(`Success: ${status.data.successful_count}/${status.data.total_items}`);
      break;
    }

    await new Promise(r => setTimeout(r, 3000)); // Wait 3s
  }

  // Get results
  const resultsResp = await fetch(`${BASE_URL}/batch/scans/${jobId}/results`, {
    headers: {"Authorization": `Bearer ${API_KEY}`}
  });
  const results = await resultsResp.json();

  return results.data.results;
}
```

### Bash/curl - Local Image Upload

```bash
#!/bin/bash

BASE_URL="https://recite.rivra.dev/apiV1/api/v1"
API_KEY="sk_live_YOUR_KEY"

# Convert local image to base64
BASE64_IMAGE=$(base64 -w 0 receipt.jpg)

# Scan and auto-save
curl -X POST "$BASE_URL/scan" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$BASE64_IMAGE\",
    \"auto_save\": true,
    \"project_id\": \"my-project-uuid\"
  }" | jq .
```

### PowerShell - Windows

```powershell
$BASE_URL = "https://recite.rivra.dev/apiV1/api/v1"
$API_KEY = "sk_live_YOUR_KEY"

# Convert image to base64
$imageBytes = [System.IO.File]::ReadAllBytes("receipt.jpg")
$base64Image = [Convert]::ToBase64String($imageBytes)

# Scan receipt
$body = @{
    image_base64 = $base64Image
    auto_save = $true
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "$BASE_URL/scan" `
    -Method POST `
    -Headers @{Authorization="Bearer $API_KEY"} `
    -Body $body `
    -ContentType "application/json"

Write-Host "Vendor: $($response.data.extracted_data.vendor)"
Write-Host "Amount: $($response.data.extracted_data.amount)"
```

---

## 12. FAQ

### Q: How do I get an API key?

**A:** Sign in to Recite → Settings → API Access → Create API Key. Copy the full key immediately (shown only once).

### Q: Can I use the API without a subscription?

**A:** Yes, but the free tier has a 10 scans/month limit. The API shares this quota with the web app.

### Q: What's the difference between image_url and image_base64?

**A:**
- `image_url` - API downloads from public URL (10s timeout, 5MB limit)
- `image_base64` - Send image data directly in request body (no download needed)

Use `image_base64` for local files or when images aren't publicly accessible.

### Q: Why use raw_text instead of image?

**A:** If you already have OCR text (from another system), use `raw_text` to skip image processing and go straight to LLM extraction. Faster and uses less quota.

### Q: What happens if auto_save is true but amount is null?

**A:** The transaction is **not** created. Only the scan result is returned. You can manually create a transaction using POST /transactions.

### Q: How accurate is the extraction?

**A:** The API uses Gemini Flash Vision AI with typical accuracy of 90-95% for clear receipts. Check `confidence.overall` in responses. Values < 0.7 may need review.

### Q: Can I delete transactions via API?

**A:** Not yet. Delete transactions from the Recite web dashboard.

### Q: What's the maximum batch size?

**A:** 20 items per batch. For larger volumes, submit multiple batches.

### Q: How long do scan results persist?

**A:** Scan results (from POST /scan) expire after 24 hours. Transactions persist permanently.

### Q: Is there a test/sandbox environment?

**A:** No. Use your production API key with the free tier for testing (10 scans/month).

### Q: Can I rotate API keys without downtime?

**A:** Yes. Click the rotate icon on a key. The old key works for 24 hours while you update systems.

### Q: What if I exceed my quota?

**A:** API returns `QUOTA_EXCEEDED` error. Upgrade your subscription or wait until next month.

### Q: How do I filter transactions by agent?

**A:** Use `agent_name` query parameter: `GET /transactions?agent_name=my-agent`

### Q: Why "Income" and not "income"?

**A:** `transaction_type` is case-sensitive. Must be "Income" or "Expense" with capital first letter.

### Q: Can I use this from a browser?

**A:** Yes, CORS is enabled. But exposing API keys in client-side code is insecure. Use a backend proxy.

---

## Support

- **Documentation:** [recite.rivra.dev/docs](https://recite.rivra.dev/docs)
- **Dashboard:** [recite.rivra.dev](https://recite.rivra.dev)
- **Issues:** [GitHub Issues](https://github.com/rivradev/recite/issues)

---

**Last Updated:** February 2026
**API Version:** v1
**Document Version:** 1.0
