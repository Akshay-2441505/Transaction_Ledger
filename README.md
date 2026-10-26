# Transaction Ledger API & Financial Dashboard

A reliable, atomic REST API and real-time browser-based financial dashboard for managing accounts and immutable simulated financial transactions, backed by PostgreSQL, FastAPI, SQLAlchemy, Alembic, and Pydantic.

---

> [!NOTE] **Assessment Scope Notice:**  
> This application is a simulated ledger demonstration built for technical evaluation. In accordance with the assignment specifications, external payment gateways (UPI, Stripe, banking rails) and end-user authentication (JWT/OAuth) are intentionally excluded. All transactions represent internal ledger events.

---

## 🌐 Verified Live Deployment Links

The application is deployed on Vercel serverless compute with a managed PostgreSQL database on Supabase:

| Resource | Live URL | Status | Description |
| :---- | :---- | :---- | :---- |
| **Financial Dashboard** | [https://transaction-ledger-pi.vercel.app](https://transaction-ledger-pi.vercel.app) | `200 OK` | Interactive dark-charcoal Financial Dashboard with INR formatting |
| **Swagger UI** | [https://transaction-ledger-pi.vercel.app/docs](https://transaction-ledger-pi.vercel.app/docs) | `200 OK` | Interactive OpenAPI 3.0 documentation and request runner |
| **OpenAPI Schema** | [https://transaction-ledger-pi.vercel.app/openapi.json](https://transaction-ledger-pi.vercel.app/openapi.json) | `200 OK` | Raw OpenAPI 3.0 JSON specification |
| **Health Check** | [https://transaction-ledger-pi.vercel.app/health](https://transaction-ledger-pi.vercel.app/health) | `200 OK` | Service operational health endpoint (`{"status": "ok"}`) |
| **Database Probe** | [https://transaction-ledger-pi.vercel.app/health/db](https://transaction-ledger-pi.vercel.app/health/db) | `200 OK` | Live PostgreSQL connectivity check (`{"status": "ok", "database": "connected"}`) |

*GitHub Repository:* [https://github.com/Akshay-2441505/Transaction_Ledger](https://github.com/Akshay-2441505/Transaction_Ledger)

---

## ⚡ Quick-Start Guide (Local Setup in 60 Seconds)

### Option A: Run with Docker Compose (Recommended)

**Prerequisites:** Docker Desktop or Docker Engine with Docker Compose.

\```bash
# 1. Clone the repository
git clone https://github.com/Akshay-2441505/Transaction_Ledger.git
cd Transaction_Ledger

# 2. Build and launch the application and database
docker compose up --build
```

The PostgreSQL database initializes with a health check, Alembic migrations apply automatically on container startup, and the FastAPI application starts on port `8000`.

- **Local Dashboard:** [http://localhost:8000/](http://localhost:8000/)  
- **Local Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)  
- **Local Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

To stop the services:

```bash
docker compose down
```

---

### Option B: Run Locally with Python (Without Docker for API)

**Prerequisites:** Python 3.10+ (tested on Python 3.13) and an accessible PostgreSQL 15+ database.

\```bash
# 1. Clone and enter directory
git clone https://github.com/Akshay-2441505/Transaction_Ledger.git
cd Transaction_Ledger

# 2. Create and activate a virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env to set your DATABASE_URL (e.g. postgresql+psycopg://postgres:postgres@localhost:5432/ledger_db)

# 5. Run database migrations
alembic upgrade head

# 6. Start the development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📋 Features

### 1. Account Management

- **Automatic Identifier Generation:** Accounts are assigned a standard server-generated UUIDv4 upon creation (`POST /accounts`).  
- **Zero Initial Balance Guarantee:** Accounts always initialize with a strictly enforced balance of `₹0.00`. Any attempt to supply a client-defined initial balance is rejected with `422 Unprocessable Entity`.  
- **Input Validation:** Account names are trimmed of leading/trailing whitespace, cannot be blank or whitespace-only, and are limited to 150 characters. Extra unrecognized request fields are strictly forbidden.

### 2. Atomic Credit & Debit Transactions

- **Dual Transaction Types:** Supports `credit` (inflow) and `debit` (outflow) via `POST /accounts/{account_id}/transactions`.  
- **Strict Monetary Precision:** All monetary amounts are validated and calculated using Python's `decimal.Decimal` and stored as PostgreSQL `NUMERIC(18, 2)`. Binary floats are strictly prohibited.  
- **Two-Decimal Validation:** Transaction amounts must be strictly positive numbers with at most 2 decimal places. Non-positive numbers (`0.00`, negative values), invalid representations (`NaN`, `Infinity`), and excess decimal precision (e.g. `10.555`) are rejected with `422 Unprocessable Entity`.  
- **Atomic Balance Updates:** The transaction write and the account balance mutation occur within the exact same database transaction, ensuring no ledger record exists without an updated balance.

### 3. Concurrency Control & Invariant Enforcement

- **Pessimistic Row-Level Locking:** Every transaction acquires an exclusive row lock (`SELECT ... FOR UPDATE`) on the target account before calculating the new balance, preventing lost updates and race conditions during high-concurrency requests.  
- **Negative Balance Prevention:** An account balance is prohibited from dropping below zero. If a debit exceeds the available balance, the operation is rejected with `409 Conflict` (`INSUFFICIENT_BALANCE`), rolling back the database session.  
- **Database-Level Check Constraint:** As a defense-in-depth safeguard, PostgreSQL enforces `CHECK (balance >= 0)` on the `accounts` table.  
- **Ledger Invariant:** At all times, the stored balance satisfies: $$\text{Account Balance} = \sum(\text{Credits}) - \sum(\text{Debits}) \ge 0$$

### 4. Idempotency & Duplicate Prevention

- **Account-Scoped Reference Uniqueness:** Each transaction must supply a client-defined `reference_id` (1–128 characters). The database enforces `UNIQUE (account_id, reference_id)`.  
- **Replay Protection:** Submitting a duplicate `reference_id` for the same account is rejected with `409 Conflict` (`DUPLICATE_REFERENCE`), and the account balance remains unmodified.  
- **Cross-Account Reuse Allowed:** The same `reference_id` may legitimately be used across distinct accounts.

### 5. Deterministic Transaction History & Filtering

- **Append-Only Immutability:** Transactions are immutable. The API exposes no `PUT`, `PATCH`, or `DELETE` endpoints for ledger records.  
- **Type Filtering:** Query transactions with `GET /accounts/{account_id}/transactions?type=credit` or `?type=debit`, or omit the parameter for all records.  
- **Pagination:** Controlled via `page` (1-indexed) and `limit` (1–100, default 20), returning pagination metadata (`page`, `page_size`, `total_records`, `total_pages`).  
- **Deterministic Ordering:** Results are deterministically sorted newest-first by `created_at DESC, id DESC`.

### 6. In-Browser Financial Dashboard

- **Modern Dark Financial SaaS UI:** Built with dark charcoal background (`#0B0E14`), subtle cards (`#161C28`), and emerald accents (`#10B981`).  
- **Indian Rupee Formatting:** All monetary displays use canonical INR formatting (e.g. `₹50,000.00`).  
- **Decoupled Overview & History:** The Overview tab always calculates total inflow, outflow, and net balance across the entire account ledger, completely independent of the filters applied in the Transaction History tab.  
- **Embedded Swagger Access:** Direct button in topbar and sidebar linking to interactive API docs.

---

## 💻 Technology Stack

| Component | Technology | Version | Purpose |
| :---- | :---- | :---- | :---- |
| **Language** | Python | `3.13` (3.10+ compatible) | Core backend programming language |
| **Web Framework** | FastAPI | `0.115.2` | High-performance ASGI framework with automatic OpenAPI documentation |
| **ASGI Server** | Uvicorn | `0.32.0` | Production ASGI web server |
| **Data Validation** | Pydantic / Pydantic Settings | `2.9.2` / `2.6.0` | Strict schema validation, extra field rejection, and environment config |
| **ORM & Database Toolkit** | SQLAlchemy | `2.0.36` | Database access, parameterized queries, and `SELECT ... FOR UPDATE` row locks |
| **Database** | PostgreSQL | `16-alpine` | ACID-compliant relational storage, check constraints, and composite indexes |
| **Database Driver** | psycopg (v3, binary) | `3.2.3` | Modern, asynchronous/synchronous PostgreSQL adapter for Python |
| **Migrations** | Alembic | `1.14.0` | Version-controlled schema migrations with automated startup execution |
| **Testing** | Pytest / pytest-asyncio | `8.3.3` / `0.24.0` | Comprehensive integration and concurrency test suite |
| **HTTP Test Client** | HTTPX | `0.27.2` | Async/sync HTTP client for FastAPI `TestClient` |
| **Containerization** | Docker & Docker Compose | Compose Spec v3.8 | Reproducible multi-container local and test environment |
| **Frontend** | Vanilla HTML5, CSS3, ES6 JS | Browser Native | Zero-dependency, lightweight, high-performance financial dashboard |
| **Cloud Deployment** | Vercel + Supabase | Serverless / Managed PG | Serverless frontend/API hosting with remote managed PostgreSQL |

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    Client["Browser Dashboard / Swagger UI / cURL Client"] --> Router["FastAPI Routing Layer (app/main.py)"]
    
    subgraph "FastAPI Server Layer"
        Router --> VercelMW["VercelRewriterMiddleware (ASGI Normalizer)"]
        VercelMW --> Schema["Pydantic Validation Layer (app/schemas)"]
        Schema --> Service["Business Logic & Invariants (app/services)"]
    end
    
    subgraph "Database Transaction Boundary"
        Service --> RowLock["Pessimistic Row Lock (SELECT ... FOR UPDATE)"]
        RowLock --> CheckBalance{"Sufficient Balance?"}
        CheckBalance -- "No" --> Rollback["Rollback Session -> 409 INSUFFICIENT_BALANCE"]
        CheckBalance -- "Yes" --> InsertTx["Insert Transaction Record (Immutable)"]
        InsertTx --> UpdateAcc["Update Account Stored Balance"]
        UpdateAcc --> Commit["Atomic Commit"]
    end

    subgraph "PostgreSQL Storage (app/models)"
        Commit --> DB_Acc["accounts Table (CHECK balance >= 0)"]
        Commit --> DB_Tx["transactions Table (UNIQUE account_id + ref_id)"]
    end
```

---

## ⚙️ Environment Configuration

Configuration is managed via Pydantic Settings in `app/core/config.py` and read from `.env`.

| Variable | Type | Default Value | Description |
| :---- | :---- | :---- | :---- |
| `DATABASE_URL` | string | `postgresql+psycopg://postgres:postgres@localhost:5432/ledger_db` | Primary application database connection string |
| `TEST_DATABASE_URL` | string | `postgresql+psycopg://postgres:postgres@localhost:5432/ledger_test_db` | Dedicated test database for automated test suite |
| `ENVIRONMENT` | string | `development` | Deployment environment identifier (`development`, `production`, `test`) |
| `LOG_LEVEL` | string | `INFO` | Application logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `APP_HOST` | string | `0.0.0.0` | Host interface for Uvicorn binding |
| `APP_PORT` | integer | `8000` | Port for Uvicorn binding |

> [!TIP] The configuration automatically normalizes `postgres://` and `postgresql://` URIs to `postgresql+psycopg://` and automatically appends `sslmode=require` when connecting to hosted cloud providers such as Supabase (`*.supabase.co`).

---

## 🗄️ Database Migrations

Schema migrations are managed with Alembic.

### Apply Migrations

```bash
# In Docker Compose (runs automatically on startup, or manually):
docker compose exec api alembic upgrade head

# Locally with virtualenv active:
alembic upgrade head
```

### Inspect Current Revision

```bash
alembic current
```

### Rollback Last Migration

```bash
alembic downgrade -1
```

Migration `0001_initial_schema.py` defines:

1. `accounts` table with primary key UUID, name, numeric balance, server default timestamp, and constraint `check_account_balance_non_negative`.  
2. `transactions` table with primary key UUID, foreign key referencing `accounts.id` (`ON DELETE RESTRICT`), type check constraint, positive amount constraint, composite index on `(account_id, created_at DESC, id DESC)`, and unique constraint `uq_account_reference` on `(account_id, reference_id)`.

---

## 🧪 Automated Testing & Verification

The test suite runs against a live PostgreSQL database and asserts validation rules, aggregate balance invariants, race condition handling, and edge cases.

### Run Tests in Docker Compose

```bash
docker compose exec api pytest -v
```

### Run Tests Locally

```bash
# Ensure local PostgreSQL test database (ledger_test_db) is running:
pytest -v
```

---

## 📡 API Overview

Detailed documentation for every request and response schema is available in [`docs/API_DOCUMENTATION.md`](docs/API_DOCUMENTATION.md).

| Method | Endpoint | Description | Success Status | Error Statuses |
| :---- | :---- | :---- | :---- | :---- |
| `GET` | `/health` | Service health check | `200 OK` | — |
| `GET` | `/health/db` | Database connectivity probe | `200 OK` | `503 Service Unavailable` |
| `POST` | `/accounts` | Create a new account with zero balance | `201 Created` | `422 Unprocessable Entity` |
| `GET` | `/accounts/{account_id}/balance` | Retrieve current available balance | `200 OK` | `404 Not Found`, `422 Unprocessable Entity` |
| `POST` | `/accounts/{account_id}/transactions` | Execute atomic credit or debit | `201 Created` | `404 Not Found`, `409 Conflict`, `422 Unprocessable Entity` |
| `GET` | `/accounts/{account_id}/transactions` | Query paginated and filtered history | `200 OK` | `404 Not Found`, `422 Unprocessable Entity` |
| `GET` | `/` | Serve Financial Dashboard UI | `200 OK` | — |

---

## 🛠️ Complete Verification Workflow (cURL)

You can copy and execute this sequence against either local (`http://localhost:8000`) or production (`https://transaction-ledger-pi.vercel.app`).

```bash
BASE_URL="https://transaction-ledger-pi.vercel.app"
```

### 1. Verify Health

```bash
curl -s "$BASE_URL/health"
```
```json
{"status":"ok"}
```

### 2. Create an Account

```bash
CREATE_RES=$(curl -s -X POST "$BASE_URL/accounts" \
  -H "Content-Type: application/json" \
  -d '{"name": "Priya Sharma"}')

echo "$CREATE_RES"
```
```json
{
  "id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "name": "Priya Sharma",
  "balance": "0.00",
  "created_at": "2026-10-26T21:40:00Z"
}
```

*(Extract the generated UUID for subsequent commands)*
```bash
ACCOUNT_ID="e4d08e15-bb30-4e13-9287-22fd9b41587f"
```

### 3. Credit the Account with ₹5,000.00

```bash
curl -s -X POST "$BASE_URL/accounts/$ACCOUNT_ID/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "credit",
    "amount": "5000.00",
    "description": "Consulting invoice payout",
    "reference_id": "INV-2026-001"
  }'
```
```json
{
  "id": "6bd8701a-2d9c-40d7-bb7a-7a1cab5557d9",
  "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "type": "credit",
  "amount": "5000.00",
  "description": "Consulting invoice payout",
  "reference_id": "INV-2026-001",
  "created_at": "2026-10-26T21:41:00Z",
  "account_balance": "5000.00"
}
```

### 4. Debit the Account by ₹1,500.00

```bash
curl -s -X POST "$BASE_URL/accounts/$ACCOUNT_ID/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "debit",
    "amount": "1500.00",
    "description": "Cloud hosting renewal",
    "reference_id": "INV-2026-002"
  }'
```
```json
{
  "id": "7ae9201b-3f8a-41d6-8b2c-9a2dfa4441e8",
  "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "type": "debit",
  "amount": "1500.00",
  "description": "Cloud hosting renewal",
  "reference_id": "INV-2026-002",
  "created_at": "2026-10-26T21:42:00Z",
  "account_balance": "3500.00"
}
```

### 5. Check Updated Balance (Should Be ₹3,500.00)

```bash
curl -s "$BASE_URL/accounts/$ACCOUNT_ID/balance"
```
```json
{
  "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "balance": "3500.00"
}
```

### 6. Verify Overdraft Rejection (Attempt to Debit ₹10,000.00)

```bash
curl -i -s -X POST "$BASE_URL/accounts/$ACCOUNT_ID/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "debit",
    "amount": "10000.00",
    "description": "Overdraft purchase",
    "reference_id": "INV-2026-003"
  }'
```
```json
HTTP/1.1 409 Conflict

{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Debit of 10000.00 exceeds current balance of 3500.00",
    "details": {}
  }
}
```

### 7. Confirm Balance Did Not Change After Failed Debit

```bash
curl -s "$BASE_URL/accounts/$ACCOUNT_ID/balance"
```
```json
{
  "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
  "balance": "3500.00"
}
```

### 8. Verify Idempotency (Re-attempt Credit with Duplicate Reference)

```bash
curl -i -s -X POST "$BASE_URL/accounts/$ACCOUNT_ID/transactions" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "credit",
    "amount": "5000.00",
    "description": "Duplicate payment",
    "reference_id": "INV-2026-001"
  }'
```
```json
HTTP/1.1 409 Conflict

{
  "error": {
    "code": "DUPLICATE_REFERENCE",
    "message": "A transaction with reference_id 'INV-2026-001' already exists for this account",
    "details": {}
  }
}
```

### 9. Retrieve Paginated Transaction History (Newest-First)

```bash
curl -s "$BASE_URL/accounts/$ACCOUNT_ID/transactions?page=1&limit=20"
```
```json
{
  "items": [
    {
      "id": "7ae9201b-3f8a-41d6-8b2c-9a2dfa4441e8",
      "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
      "type": "debit",
      "amount": "1500.00",
      "description": "Cloud hosting renewal",
      "reference_id": "INV-2026-002",
      "created_at": "2026-10-26T21:42:00Z"
    },
    {
      "id": "6bd8701a-2d9c-40d7-bb7a-7a1cab5557d9",
      "account_id": "e4d08e15-bb30-4e13-9287-22fd9b41587f",
      "type": "credit",
      "amount": "5000.00",
      "description": "Consulting invoice payout",
      "reference_id": "INV-2026-001",
      "created_at": "2026-10-26T21:41:00Z"
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

## 🔒 Security Boundaries & Limitations

1. **Authentication & Authorization:** Consistent with the assignment prompt, end-user authentication (JWT/session tokens) and account ownership authorization are intentionally excluded. All endpoints are open for reviewer evaluation.  
2. **Synthetic Data Only:** The live deployment is publicly accessible for demonstration purposes. Only fictitious test data should be submitted.  
3. **Pessimistic Row Locking:** Prevents race conditions during simultaneous requests.  
4. **Input Defense:** String parameters are sanitarily trimmed; extra fields are rejected; UUID formats are validated; monetary inputs are bound to 2 decimal places.  
5. **Information Leakage Prevention:** Database connection strings, credentials, and internal stack traces are never exposed in responses or logs.

---

## 📂 Repository Structure

```text
Transaction_Ledger/
├── README.md                      # Primary reviewer entry point and project overview
├── requirements.txt               # Locked production and test Python dependencies
├── .env.example                   # Template for environment configuration
├── .gitignore                     # Git ignore rules
├── Dockerfile                     # Multi-stage production container build
├── compose.yaml                   # Multi-container orchestration (API + PostgreSQL 16)
├── alembic.ini                    # Alembic migration configuration
├── vercel.json                    # Vercel serverless routing and rewrite rules
├── main.py                        # Root serverless entrypoint
│
├── api/                           # Vercel Serverless Function entrypoints
│   └── index.py                   # ASGI app export for @vercel/python runtime
│
├── app/                           # Core FastAPI Application package
│   ├── __init__.py
│   ├── main.py                    # Application factory, middleware & exception handlers
│   ├── api/                       # API Route Controllers
│   │   ├── __init__.py
│   │   ├── accounts.py            # /accounts endpoints (creation, balance, routes)
│   │   ├── health.py              # /health and /health/db endpoints
│   │   └── transactions.py        # /accounts/{id}/transactions endpoints
│   ├── core/                      # Application Configuration & Error Envelopes
│   │   ├── config.py              # Pydantic Settings & database URL normalization
│   │   └── errors.py              # Domain exceptions (AppException hierarchy)
│   ├── db/                        # Database Connection & Session Management
│   │   ├── base.py                # Declarative base class
│   │   └── session.py             # Engine, SessionLocal, NullPool for serverless
│   ├── models/                    # SQLAlchemy ORM Domain Models
│   │   ├── __init__.py
│   │   ├── account.py             # Account model (UUID PK, balance, CHECK constraint)
│   │   └── transaction.py         # Transaction model (type, amount, reference unique)
│   ├── schemas/                   # Pydantic Request & Response Contracts
│   │   ├── __init__.py
│   │   ├── account.py             # Account request/response models
│   │   ├── errors.py              # Unified error envelope model
│   │   └── transaction.py         # Transaction models, Decimal validators, pagination
│   └── services/                  # Business Logic & Transaction Management
│       ├── __init__.py
│       ├── accounts.py            # Account creation & balance retrieval
│       └── transactions.py        # Row-locked credit/debit processing & history query
│
├── static/                        # In-Browser Dashboard Assets
│   └── index.html                 # Complete, self-contained dashboard UI
│
├── migrations/                    # Alembic Database Migrations
│   ├── env.py                     # Alembic migration environment
│   ├── script.py.mako             # Migration template
│   └── versions/
│       └── 0001_initial_schema.py # Initial accounts and transactions tables
│
├── tests/                         # Comprehensive Automated Test Suite (48 tests)
│   ├── conftest.py                # Test fixtures, test DB setup, and clean tables
│   ├── test_accounts.py           # Account creation, validation, whitespace trimming
│   ├── test_concurrency.py        # Concurrent debits, race conditions, duplicate refs
│   ├── test_dashboard.py          # Dashboard routes, static serving, developer docs
│   ├── test_history.py            # Filtering by type, pagination bounds, deterministic sort
│   └── test_transactions.py       # Credits, debits, overdraft checks, immutability
│
├── docs/                          # Detailed Technical Documentation
│   ├── PRD.md                     # Product requirements document
│   ├── TECH_STACK.md              # Technical stack evaluation and design rationale
│   ├── DESIGN.md                  # Comprehensive technical design document
│   ├── ASSUMPTIONS.md             # Key assumptions and engineering decisions
│   └── API_DOCUMENTATION.md       # Comprehensive API contract and endpoint reference
│
├── scripts/                       # Developer Utilities
│   └── init-db.sql                # Auxiliary database initialization script
│
└── postman/                       # Postman Integration Collection
    └── collection.json            # Importable test collection with preconfigured requests
```

---

## 🔧 Troubleshooting

### 1. Database Connection Refused (`localhost:5432`)

- **Symptom:** `psycopg.OperationalError: connection to server at "localhost", port 5432 failed`.  
- **Solution:** Verify that your PostgreSQL server is running. If using Docker Compose, ensure the database container is healthy:  

```bash
docker compose ps
```

### 2. Port Already in Use (`8000` or `5432`)

- **Symptom:** `Bind for 0.0.0.0:8000 failed: port is already allocated`.  
- **Solution:** Check for running services occupying port 8000 or 5432:  

```bash
# Windows:
netstat -ano | findstr :8000

# Linux / macOS:
lsof -i :8000
```

Adjust the port mapping in `compose.yaml` (e.g. `"8080:8000"`) or stop the conflicting service.

### 3. Vercel Serverless IPv6 Connection Issue

- **Symptom:** `Cannot assign requested address` when connecting to Supabase from Vercel.  
- **Cause:** Vercel serverless runs in an IPv4 network, while Supabase direct hostnames resolve to IPv6 only.  
- **Solution:** Always use the Supabase **Session Pooler** host (`aws-0-[region].pooler.supabase.com:5432`) with user `postgres.[project-ref]` in Vercel's `DATABASE_URL` environment variable.
