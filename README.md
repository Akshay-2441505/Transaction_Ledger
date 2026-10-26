# Transaction Ledger API & Financial Dashboard

A reliable, atomic REST API and browser-based financial dashboard for managing accounts and immutable simulated financial transactions, backed by PostgreSQL and FastAPI.

---

> [!NOTE]
> **Assessment Scope Notice:**  
> This service is a simulated ledger implementation designed for technical evaluation. In accordance with the assessment specifications, end-user authentication (JWT/OAuth), multi-user authorization, and external payment processor integrations are intentionally excluded.

---

## 🎨 System & Architecture Sketch

```text
Browser Client / Swagger UI / curl / Postman
                 │
                 ▼
     FastAPI Web Server (app/main.py)
     ├── GET /              -> Financial Dashboard (HTML/CSS/JS)
     ├── GET /docs          -> Swagger UI Documentation
     ├── GET /health        -> Health Check
     └── /accounts/...      -> REST API Endpoints
                 │
                 ▼
       Pydantic Validation (app/schemas)
                 │
                 ▼
   Service / Invariant Enforcement (app/services)
   - SELECT ... FOR UPDATE (pessimistic row lock)
   - Decimal precision & non-negative balance checks
                 │
                 ▼
       SQLAlchemy Unit of Work (app/db)
                 │
                 ▼
      PostgreSQL 16 Database
      - accounts (balance >= 0)
      - transactions (immutable, unique per account_id + reference_id)
```

---

## 🚀 Quick Start (Docker Compose)

### Prerequisites
- Docker & Docker Compose plugin (Docker Desktop or Docker Engine)

### Launch Service
Run the following single command from the project root:

```bash
docker compose up --build
```

The database container will start, run health checks, apply Alembic migrations automatically, and start the FastAPI application at port `8000`.

- **Web Financial Dashboard:** [`http://localhost:8000/`](http://localhost:8000/)
- **Interactive API Documentation (Swagger UI):** [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **ReDoc Documentation:** [`http://localhost:8000/redoc`](http://localhost:8000/redoc)
- **OpenAPI Schema:** [`http://localhost:8000/openapi.json`](http://localhost:8000/openapi.json)
- **Health Check:** [`http://localhost:8000/health`](http://localhost:8000/health)

---

## 📊 Browser Dashboard Features

The dashboard is served directly from the FastAPI application using vanilla HTML5, CSS3, and modern JavaScript:

1. **Overview View:**
   - Real-time live stored account balance in INR (`₹`).
   - Total credits (inflows) and debits (outflows) calculated honestly from actual ledger records.
   - Total transaction count from API pagination metadata.
   - Compact activity visualization derived from real transaction volume.
   - Recent transaction activity table.

2. **Accounts View:**
   - Account creation form (`POST /accounts`). Initial balance is always ₹0.00 (client-supplied balance is rejected by the backend).
   - Session account switcher and direct UUID lookup input.

3. **Transactions View:**
   - Intuitive Credit / Debit transaction execution form.
   - Built-in "Auto Generate" unique reference button to easily avoid duplicate reference conflicts.
   - Inline feedback for validation errors (`422`), insufficient balance (`409`), and duplicate references (`409`).
   - Paginated transaction history with type filtering (`All`, `Credits`, `Debits`) and deterministic ordering (`created_at DESC, id DESC`).

---

## 🧪 Running Automated Tests

All tests run directly against PostgreSQL, asserting row-level locking, race conditions, idempotency, dashboard route serving, and aggregate balance invariants.

### In Docker Compose
```bash
docker compose run --rm api pytest -v
```

### Locally (with local Python virtualenv & running Postgres)
```bash
# 1. Activate your virtual environment (.venv)
# 2. Run pytest:
pytest -v
```

**Actual Passing Result:**
```text
======================== 48 passed in ~2.5s ========================
```

---

## 🛠️ Step-by-Step Walkthrough (cURL)

Below is an end-to-end verification sequence demonstrating account creation, atomic credit/debit operations, overdraw protection, and duplicate reference conflict rejection.

### 1. Health Check
```bash
curl -s http://localhost:8000/health
```
```json
{"status":"ok"}
```

### 2. Create an Account
```bash
curl -s -X POST http://localhost:8000/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Akshay Kumar"}'
```
```json
{
  "id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "name": "Akshay Kumar",
  "balance": "0.00",
  "created_at": "2026-10-26T18:00:00Z"
}
```
*(Export the returned `id` as `ACCOUNT_ID` for subsequent calls)*

### 3. Apply Credit of ₹1,000.00
```bash
curl -s -X POST http://localhost:8000/accounts/$ACCOUNT_ID/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "credit",
    "amount": "1000.00",
    "description": "Salary deposit",
    "reference_id": "REF-001"
  }'
```
```json
{
  "id": "6bd8701a-2d9c-40d7-bb7a-7a1cab5557d9",
  "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "type": "credit",
  "amount": "1000.00",
  "description": "Salary deposit",
  "reference_id": "REF-001",
  "created_at": "2026-10-26T18:01:00Z",
  "account_balance": "1000.00"
}
```

### 4. Apply Debit of ₹300.00
```bash
curl -s -X POST http://localhost:8000/accounts/$ACCOUNT_ID/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "debit",
    "amount": "300.00",
    "description": "Books purchase",
    "reference_id": "REF-002"
  }'
```
```json
{
  "id": "7ac9812b-3e8f-41e8-8b9a-8b2def6648a1",
  "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "type": "debit",
  "amount": "300.00",
  "description": "Books purchase",
  "reference_id": "REF-002",
  "created_at": "2026-10-26T18:02:00Z",
  "account_balance": "700.00"
}
```

### 5. Attempt Overdraft of ₹800.00 (Rejected with 409)
```bash
curl -s -i -X POST http://localhost:8000/accounts/$ACCOUNT_ID/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "debit",
    "amount": "800.00",
    "description": "Overdraft attempt",
    "reference_id": "REF-003"
  }'
```
**HTTP Status:** `409 Conflict`
```json
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "The account does not have sufficient funds for this debit.",
    "details": {}
  }
}
```

### 6. Verify Balance Remains Intact (₹700.00)
```bash
curl -s http://localhost:8000/accounts/$ACCOUNT_ID/balance
```
```json
{
  "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "balance": "700.00"
}
```

### 7. Duplicate Reference Attempt (Rejected with 409)
```bash
curl -s -i -X POST http://localhost:8000/accounts/$ACCOUNT_ID/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "type": "credit",
    "amount": "500.00",
    "description": "Reusing REF-001",
    "reference_id": "REF-001"
  }'
```
**HTTP Status:** `409 Conflict`
```json
{
  "error": {
    "code": "DUPLICATE_REFERENCE",
    "message": "A transaction with this reference ID already exists for the account.",
    "details": {}
  }
}
```

### 8. View Paginated Transaction History
```bash
curl -s "http://localhost:8000/accounts/$ACCOUNT_ID/transactions?page=1&limit=20"
```
```json
{
  "items": [
    {
      "id": "7ac9812b-3e8f-41e8-8b9a-8b2def6648a1",
      "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
      "type": "debit",
      "amount": "300.00",
      "description": "Books purchase",
      "reference_id": "REF-002",
      "created_at": "2026-10-26T18:02:00Z"
    },
    {
      "id": "6bd8701a-2d9c-40d7-bb7a-7a1cab5557d9",
      "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
      "type": "credit",
      "amount": "1000.00",
      "description": "Salary deposit",
      "reference_id": "REF-001",
      "created_at": "2026-10-26T18:01:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_records": 2,
    "total_pages": 1
  }
}
```

---

## 📁 Key Design Documentation

- [`docs/PRD.md`](docs/PRD.md): Product requirements document.
- [`docs/DESIGN.md`](docs/DESIGN.md): Technical architecture and database schema.
- [`docs/TECH_STACK.md`](docs/TECH_STACK.md): Technology decisions and concurrency rationale.
- [`docs/ASSUMPTIONS.md`](docs/ASSUMPTIONS.md): Assumptions regarding currency, idempotency, and bounds.
- [`postman/collection.json`](postman/collection.json): Importable Postman test collection.
