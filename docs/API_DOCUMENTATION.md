# Transaction Ledger API — API Documentation & Contract Reference

**Version:** `1.0.0`  
**OpenAPI Specification:** `3.0.0`  
---

## 1. Overview

The Transaction Ledger API is a deterministic, atomic RESTful web service designed to manage accounts and immutable financial credit and debit transactions. It enforces monetary precision in Indian Rupees (INR, `₹`), prevents overdrafts through database constraints and pessimistic row locks, and guarantees transaction idempotency through account-scoped reference identifiers.

### Interactive Exploration Links

| Interface | Production URL | Local URL | Description |
| :---- | :---- | :---- | :---- |
| **Swagger UI** | [https://transaction-ledger-pi.vercel.app/docs](https://transaction-ledger-pi.vercel.app/docs) | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API runner and schema explorer |
| **ReDoc** | [https://transaction-ledger-pi.vercel.app/redoc](https://transaction-ledger-pi.vercel.app/redoc) | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Human-friendly technical documentation |
| **OpenAPI Schema** | [https://transaction-ledger-pi.vercel.app/openapi.json](https://transaction-ledger-pi.vercel.app/openapi.json) | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) | Machine-readable OpenAPI 3.0 specification |
| **Web Dashboard** | [https://transaction-ledger-pi.vercel.app](https://transaction-ledger-pi.vercel.app) | [http://localhost:8000/](http://localhost:8000/) | Live browser financial dashboard |

---

## 2. Base URLs & Conventions

- **Production Environment:** `https://transaction-ledger-pi.vercel.app`  
- **Local Development Environment:** `http://localhost:8000`

### Headers & Content Types

- Request headers for mutating requests: `Content-Type: application/json`  
- Response headers: `Content-Type: application/json` (except `/` and `/docs` which serve HTML)  
- Date and time formatting: ISO 8601 extended format with UTC timezone offset (e.g. `2026-10-26T21:40:00.123456Z`).  
- Monetary values: Expressed as strings with two fractional digits (e.g. `"1000.00"`) to avoid floating-point rounding errors in client runtimes.

---

## 3. Error Handling Envelope

Every failed request returns a consistent, structured JSON error response:

```json
{
  "error": {
    "code": "STRING_ERROR_CODE",
    "message": "Human-readable explanation of the error condition.",
    "details": {}
  }
}
```

### Standard Error Codes

| HTTP Status | Error Code | Trigger Condition |
| :---- | :---- | :---- |
| `400 Bad Request` | `INVALID_REQUEST` | Malformed request syntax or unparseable JSON payload |
| `404 Not Found` | `ACCOUNT_NOT_FOUND` | The specified account UUID does not exist in the ledger |
| `404 Not Found` | `RESOURCE_NOT_FOUND` | The requested route or static file path does not exist |
| `405 Method Not Allowed` | `METHOD_NOT_ALLOWED` | HTTP method not supported on the target endpoint |
| `409 Conflict` | `INSUFFICIENT_BALANCE` | Attempted debit exceeds available account balance |
| `409 Conflict` | `DUPLICATE_REFERENCE` | The reference ID has already been recorded for this account |
| `422 Unprocessable Entity` | `VALIDATION_ERROR` | Schema validation error (e.g. missing fields, negative amounts, extra fields) |
| `500 Internal Server Error` | `INTERNAL_ERROR` | Unhandled server exception |
| `503 Service Unavailable` | `SERVICE_UNAVAILABLE` | Database connectivity failure |

---

## 4. Endpoint Reference

---

### 1. Health Check

#### `GET /health`

Validates that the API service is alive and accepting incoming requests.

- **Authentication:** None  
- **Query Parameters:** None  
- **Request Body:** None

**Success Response (`200 OK`):**

```json
{
  "status": "ok"
}
```

---

### 2. Database Connectivity Probe

#### `GET /health/db`

Executes an active query (`SELECT 1`) against the PostgreSQL database to verify connection health.

- **Authentication:** None  
- **Query Parameters:** None  
- **Request Body:** None

**Success Response (`200 OK`):**

```json
{
  "status": "ok",
  "database": "connected"
}
```

**Failure Response (`503 Service Unavailable`):**

```json
{
  "status": "error",
  "database": "disconnected",
  "detail": "connection failed: server does not support SSL..."
}
```

---

### 3. Create Account

#### `POST /accounts`

Registers a new account in the ledger.

- **Business Rules:**  
  - Accounts always initialize with a verified balance of `₹0.00`.  
  - Clients **cannot** supply a starting balance. Supplying `balance` or any extra field is rejected.  
  - The `name` field is trimmed of leading and trailing whitespace.  
  - The `id` is a server-generated UUIDv4.  
- **Request Body Schema (`AccountCreateRequest`):**

| Field | Type | Required | Constraints | Description |
| :---- | :---- | :---- | :---- | :---- |
| `name` | string | **Yes** | Min 1 char, Max 150 chars, non-blank | The full name of the account holder |

*Note: `extra="forbid"` is enforced. Any unlisted field will trigger validation failure.*

**Example Request:**

```bash
curl -X POST "https://transaction-ledger-pi.vercel.app/accounts" \
-H "Content-Type: application/json" \
-d '{"name": "Aarav Patel"}'
```

**Success Response (`201 Created`):**

```json
{
  "id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "name": "Aarav Patel",
  "balance": "0.00",
  "created_at": "2026-10-26T21:40:00.123456Z"
}
```

**Error Responses:**

- `422 Unprocessable Entity` (Empty name or whitespace-only):  
    
```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Validation failed for request parameters or payload.",
      "details": {
        "errors": [
          {
            "field": "body -> name",
            "message": "Account holder name cannot be empty or blank",
            "type": "value_error"
          }
        ]
      }
    }
  }
```

    
- `422 Unprocessable Entity` (Client attempted to inject initial balance):  
    
```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Validation failed for request parameters or payload.",
      "details": {
        "errors": [
          {
            "field": "body -> balance",
            "message": "Extra inputs are not permitted",
            "type": "extra_forbidden"
          }
        ]
      }
    }
  }
```

---

### 4. Get Account Balance

#### `GET /accounts/{account_id}/balance`

Retrieves the current available balance for an existing account.

- **Path Parameters:**

| Parameter | Type | Required | Constraints | Description |
| :---- | :---- | :---- | :---- | :---- |
| `account_id` | string (UUID) | **Yes** | Valid RFC 4122 UUID | Unique identifier of the account |

**Example Request:**

```bash
curl "https://transaction-ledger-pi.vercel.app/accounts/e4d08e15-bb30-4e13-9287-22fd9b41587f/balance"
```

**Success Response (`200 OK`):**

```json
{
  "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "balance": "5000.00"
}
```

**Error Responses:**

- `404 Not Found` (Account does not exist):  
    
```json
  {
    "error": {
      "code": "ACCOUNT_NOT_FOUND",
      "message": "The requested account was not found.",
      "details": {}
    }
  }
```

    
- `422 Unprocessable Entity` (Malformed UUID):  
    
```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Validation failed for request parameters or payload.",
      "details": {
        "errors": [
          {
            "field": "path -> account_id",
            "message": "Input should be a valid UUID, invalid character: expected an optional prefix of \`urn:uuid:\` followed by [0-9a-fA-F-], found \`n\` at 1",
            "type": "uuid_parsing"
          }
        ]
      }
    }
  }
```

---

### 5. Create Transaction (Credit or Debit)

#### `POST /accounts/{account_id}/transactions`

Executes an atomic credit or debit operation on an account.

- **Business Rules:**  
  - Acquires an exclusive row lock (`SELECT ... FOR UPDATE`) on the target account.  
  - For `credit`: Stored balance increases by `amount`.  
  - For `debit`: Verifies `current_balance >= amount`. If insufficient, the transaction is rejected with `409 INSUFFICIENT_BALANCE` and the database session rolls back.  
  - Verifies that `reference_id` has not been previously used for this account. If duplicated, rejected with `409 DUPLICATE_REFERENCE`.  
  - Appends an immutable record to the `transactions` table.  
- **Path Parameters:**

| Parameter | Type | Required | Constraints | Description |
| :---- | :---- | :---- | :---- | :---- |
| `account_id` | string (UUID) | **Yes** | Valid RFC 4122 UUID | Unique identifier of the target account |

- **Request Body Schema (`TransactionCreateRequest`):**

| Field | Type | Required | Constraints | Description |
| :---- | :---- | :---- | :---- | :---- |
| `type` | string | **Yes** | Must be `"credit"` or `"debit"` | Transaction classification |
| `amount` | string or number | **Yes** | Number \> 0, max 2 decimals | Monetary amount in INR |
| `description` | string | **Yes** | Min 1 char, Max 500 chars | Human-readable explanation of transaction |
| `reference_id` | string | **Yes** | Min 1 char, Max 128 chars | Idempotency key, unique per account |

*Note: `extra="forbid"` is enforced. Any unlisted field will trigger validation failure.*

**Example Credit Request:**

```bash
curl -X POST "https://transaction-ledger-pi.vercel.app/accounts/e4d08e15-bb30-4e13-9287-22fd9b41587f/transactions" \
-H "Content-Type: application/json" \
-d '{
"type": "credit",
```

    "amount": "2500.00",

    "description": "Consulting stipend",

    "reference_id": "STIPEND-2026-OCT"

  }'

**Success Response (`201 Created`):**

```json
{
  "id": "6bd8701a-2d9c-40d7-bb7a-7a1cab5557d9",
  "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "type": "credit",
  "amount": "2500.00",
  "description": "Consulting stipend",
  "reference_id": "STIPEND-2026-OCT",
  "created_at": "2026-10-26T21:41:00.654321Z",
  "account_balance": "2500.00"
}
```

**Example Debit Request:**

```bash
curl -X POST "https://transaction-ledger-pi.vercel.app/accounts/e4d08e15-bb30-4e13-9287-22fd9b41587f/transactions" \
-H "Content-Type: application/json" \
-d '{
"type": "debit",
```

    "amount": "500.00",

    "description": "Web hosting fee",

    "reference_id": "HOSTING-INV-001"

  }'

**Success Response (`201 Created`):**

```json
{
  "id": "7ac9812b-3e8f-41e8-8b9a-8b2def6648a1",
  "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "type": "debit",
  "amount": "500.00",
  "description": "Web hosting fee",
  "reference_id": "HOSTING-INV-001",
  "created_at": "2026-10-26T21:42:00.123456Z",
  "account_balance": "2000.00"
}
```

**Error Responses:**

- `404 Not Found` (Account does not exist):  
    
```json
  {
    "error": {
      "code": "ACCOUNT_NOT_FOUND",
      "message": "The requested account was not found.",
      "details": {}
    }
  }
```

    
- `409 Conflict` (Insufficient funds for debit):  
    
```json
  {
    "error": {
      "code": "INSUFFICIENT_BALANCE",
      "message": "The account does not have sufficient funds for this debit.",
      "details": {}
    }
  }
```

    
- `409 Conflict` (Duplicate reference ID for this account):  
    
```json
  {
    "error": {
      "code": "DUPLICATE_REFERENCE",
      "message": "A transaction with this reference ID already exists for the account.",
      "details": {}
    }
  }
```

    
- `422 Unprocessable Entity` (Invalid amount with \>2 decimal places):  
    
```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Validation failed for request parameters or payload.",
      "details": {
        "errors": [
          {
            "field": "body -> amount",
            "message": "Amount must have at most 2 decimal places",
            "type": "value_error"
          }
        ]
      }
    }
  }
```

    
- `422 Unprocessable Entity` (Non-positive amount):  
    
```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Validation failed for request parameters or payload.",
      "details": {
        "errors": [
          {
            "field": "body -> amount",
            "message": "Amount must be greater than zero",
            "type": "value_error"
          }
        ]
      }
    }
  }
```

---

### 6. Get Transaction History

#### `GET /accounts/{account_id}/transactions`

Retrieves a paginated list of transactions for the specified account, sorted newest-first.

- **Path Parameters:**

| Parameter | Type | Required | Constraints | Description |
| :---- | :---- | :---- | :---- | :---- |
| `account_id` | string (UUID) | **Yes** | Valid RFC 4122 UUID | Unique identifier of the target account |

- **Query Parameters:**

| Parameter | Type | Required | Default | Constraints | Description |
| :---- | :---- | :---- | :---- | :---- | :---- |
| `type` | string | No | `null` | Must be `"credit"` or `"debit"` | Filter transactions by type |
| `page` | integer | No | `1` | Minimum `1` | 1-based page number |
| `limit` | integer | No | `20` | Minimum `1`, Maximum `100` | Number of records per page |

- **Ordering Guarantee:** Deterministically sorted by `created_at DESC, id DESC`.

**Example Request:**

```bash
curl "https://transaction-ledger-pi.vercel.app/accounts/e4d08e15-bb30-4e13-9287-22fd9b41587f/transactions?page=1&limit=10&type=debit"
```

**Success Response (`200 OK`):**

```json
{
  "items": [
    {
      "id": "7ac9812b-3e8f-41e8-8b9a-8b2def6648a1",
      "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
      "type": "debit",
      "amount": "500.00",
      "description": "Web hosting fee",
      "reference_id": "HOSTING-INV-001",
      "created_at": "2026-10-26T21:42:00.123456Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 10,
    "total_records": 1,
    "total_pages": 1
  }
}
```

**Empty History (`200 OK`):** If an account exists but has recorded no transactions (or none matching the filter):

```json
{
  "items": [],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_records": 0,
    "total_pages": 0
  }
}
```

**Error Responses:**

- `404 Not Found` (Account does not exist):  
    
```json
  {
    "error": {
      "code": "ACCOUNT_NOT_FOUND",
      "message": "The requested account was not found.",
      "details": {}
    }
  }
```

    
- `422 Unprocessable Entity` (Invalid page number `page=0`):  
    
```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Validation failed for request parameters or payload.",
      "details": {
        "errors": [
          {
            "field": "query -> page",
            "message": "Input should be greater than or equal to 1",
            "type": "greater_than_equal"
          }
        ]
      }
    }
  }
```

    
- `422 Unprocessable Entity` (Exceeded maximum limit `limit=101`):  
    
```json
  {
    "error": {
      "code": "VALIDATION_ERROR",
      "message": "Validation failed for request parameters or payload.",
      "details": {
        "errors": [
          {
            "field": "query -> limit",
            "message": "Input should be less than or equal to 100",
            "type": "less_than_equal"
          }
        ]
      }
    }
  }
```

---

## 5. End-to-End Workflow Demonstration

The following shell sequence executes a complete testing lifecycle against the live service:

```bash
BASE_URL="https://transaction-ledger-pi.vercel.app"

# 1. Check health
curl -s "$BASE_URL/health"

# 2. Create account
ACCOUNT_JSON=$(curl -s -X POST "$BASE_URL/accounts" \
  -H "Content-Type: application/json" \
  -d '{"name": "Rohan Mehra"}')
echo "$ACCOUNT_JSON"

# Extract ID
ACCOUNT_ID=$(echo "$ACCOUNT_JSON" | grep -o '"id":"[^"]*' | cut -d'"' -f4)

# 3. Credit account
curl -s -X POST "$BASE_URL/accounts/$ACCOUNT_ID/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "credit",
    "amount": "10000.00",
    "description": "Initial capital",
    "reference_id": "CAP-001"
  }'

# 4. Debit account
curl -s -X POST "$BASE_URL/accounts/$ACCOUNT_ID/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "debit",
    "amount": "2500.00",
    "description": "Equipment purchase",
    "reference_id": "PUR-001"
  }'

# 5. Verify balance (Should be 7500.00)
curl -s "$BASE_URL/accounts/$ACCOUNT_ID/balance"

# 6. Attempt Overdraft (Debit 10000.00 -> Rejection 409)
curl -i -s -X POST "$BASE_URL/accounts/$ACCOUNT_ID/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "debit",
    "amount": "10000.00",
    "description": "Excessive withdrawal",
    "reference_id": "PUR-002"
  }'

# 7. Attempt Duplicate Reference (Credit 1000.00 with CAP-001 -> Rejection 409)
curl -i -s -X POST "$BASE_URL/accounts/$ACCOUNT_ID/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "credit",
    "amount": "1000.00",
    "description": "Replay attempt",
    "reference_id": "CAP-001"
  }'

# 8. Retrieve transaction history
curl -s "$BASE_URL/accounts/$ACCOUNT_ID/transactions?page=1&limit=20"
```
