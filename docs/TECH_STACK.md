# Technology Stack and Rationale

**Project:** Transaction Ledger API  
**Status:** Proposed baseline  
**Related documents:** [`PRD.md`](./PRD.md), [`DESIGN.md`](./DESIGN.md)

## 1. Stack overview

| Layer | Choice | Why this choice |
|---|---|---|
| Language | Python 3.11+ | Familiar to the candidate and suitable for a focused backend assignment. |
| HTTP/API framework | FastAPI | Typed request/response models, dependency injection, validation and generated OpenAPI documentation. |
| Schema validation | Pydantic 2.x | Defines and validates request and response contracts. |
| Relational database | PostgreSQL | Transactions, foreign keys, unique constraints, checks, and row-level locking support the ledger's integrity requirements. |
| Local database runtime | PostgreSQL in Docker Compose | A reviewer can run the project without creating a hosted database account. It also permits tests against real PostgreSQL locking behavior. |
| Optional hosted database | Supabase PostgreSQL | Can be used by setting `DATABASE_URL` if a hosted database is useful; it is not required for local evaluation. |
| ORM and DB access | SQLAlchemy 2.x | Explicit transaction scopes, parameterized queries and a maintainable separation between persistence and API code. |
| PostgreSQL driver | Psycopg 3 | PostgreSQL driver compatible with the SQLAlchemy stack. |
| Schema migrations | Alembic | Versioned, reviewable database schema changes. |
| Tests | pytest + HTTPX | Unit/service tests and HTTP-level integration tests. Critical integration tests run against PostgreSQL. |
| Local orchestration | Docker + Docker Compose | Reproducible startup for the API and database. |
| API exploration | FastAPI `/docs` | Interactive OpenAPI/Swagger UI generated from the API definitions. |
| Configuration | Environment variables + `.env.example` | Keeps environment-specific values and secrets out of source code. |
| Formatting/linting (recommended) | Ruff | Fast, simple Python linting and formatting for a consistent repository. |

## 2. Why PostgreSQL, not SQLite, for the main test target?

The assignment explicitly requires atomic balance updates and data consistency. PostgreSQL provides transaction semantics and row-level locking that can be used to serialize mutations on a particular account. Because SQLite has materially different concurrency and locking behavior, PostgreSQL should be the primary integration-test database for concurrency-sensitive behavior. SQLite may be used for small isolated tests only if it does not create a false impression that PostgreSQL locking has been tested.

## 3. Money and identifiers

- Use Python `Decimal` in application logic; never use Python `float` for amounts or balances.
- Store amounts and balances as PostgreSQL `NUMERIC(18,2)`.
- Reject amounts less than or equal to zero, values with more than two fractional digits, non-finite values, and values outside the database precision.
- Represent money as a decimal string in API examples and JSON responses (for example, `"1000.00"`). This makes the external contract clear for clients that might otherwise parse money as binary floating-point.
- Use UUIDs generated server-side for account and transaction IDs.
- Use timezone-aware timestamps; store `TIMESTAMPTZ` values and return ISO 8601 timestamps in UTC.

## 4. Runtime and dependency approach

Use a supported Python 3.11+ runtime. Use current compatible stable releases of FastAPI, Pydantic 2.x, SQLAlchemy 2.x, Alembic, Psycopg 3, pytest and HTTPX. When implementation begins, pin the selected versions in `requirements.txt` (or use a lock file) so another person can reproduce the tested environment. Do not rely on an unpinned `latest` install for the final submission.

Suggested direct dependencies:

- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `pydantic-settings` (if used for typed configuration)
- `sqlalchemy`
- `alembic`
- `psycopg[binary]` for a simple local setup, or a deployment-appropriate Psycopg installation
- `pytest`
- `httpx`
- `ruff` (development tool)

Avoid adding a frontend framework, message broker, cache, microservice framework, or external payment SDK. None is necessary for the mandatory assessment.

## 5. Database configuration

The default local path uses PostgreSQL from Compose. The application reads `DATABASE_URL` from the environment. It should not hard-code or print connection strings.

- `.env.example` contains placeholders or safe local-only sample values.
- `.env` is ignored by Git.
- The README explains how to set configuration without publishing actual credentials.
- If Supabase is used, configure its connection string through the same environment variable and use the appropriate connection settings for that environment.
- Do not point tests at a database containing personal or production data.

## 6. Local reviewer workflow

The target reviewer workflow is:

1. Clone or download the repository.
2. Copy `.env.example` to `.env` if needed and review the safe local defaults.
3. Run `docker compose up --build`.
4. Open `http://localhost:8000/docs`.
5. Run the documented test command against a dedicated test database.

The final Compose configuration must wait for PostgreSQL readiness before applying migrations and starting the API. The README should state prerequisites (Docker Desktop or Docker Engine with the Compose plugin) and the exact commands validated by the author.

## 7. Deployment position

Local execution is the canonical evaluation path. A hosted demonstration is optional and should never be the only way to evaluate the project. If a public deployment is added, do not expose unrestricted account-creation and transaction-writing endpoints without access controls and abuse protections. Use disposable demonstration data and no real financial information. A public demo must not contain database credentials or secrets in client-visible code or documentation.

## 8. Relevant references

- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Pydantic documentation](https://docs.pydantic.dev/latest/)
- [SQLAlchemy 2.x documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLAlchemy session and transaction basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html)
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [PostgreSQL `SELECT` and row locking](https://www.postgresql.org/docs/current/sql-select.html)
- [Alembic documentation](https://alembic.sqlalchemy.org/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
- [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
