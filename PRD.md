# Product Requirements Document (PRD)

**Project:** Transaction Ledger API  
**Status:** Draft for implementation  
**Primary source:** *Full Stack Developer Assessment* provided for the recruitment process  
**Related documents:** [`TECH_STACK.md`](./TECH_STACK.md), [`DESIGN.md`](./DESIGN.md)

## 1. Summary

Build a small, reliable REST API for a transaction ledger. The API lets a client create an account, apply credit or debit transactions, read the current account balance, and retrieve transaction history.

The core challenge is data integrity: a successful transaction must update the transaction history and account balance together; rejected operations must not change either; duplicate references must not process a transaction twice; and concurrent debit requests must not create an invalid balance.

This is an assessment-scale ledger simulation. It is **not** a live banking, payment-processing, or UPI integration.

## 2. Problem and opportunity

The assignment tests whether the candidate can implement a maintainable backend API with sound validation, persistence, error handling and transaction consistency. A technically correct implementation should also be easy for a reviewer to understand, launch, and test quickly.

## 3. Goals

1. Implement every mandatory behavior in the supplied assessment.
2. Preserve the account-balance and transaction-history invariants across successful, rejected, failed and concurrent operations.
3. Use database constraints as well as application validation.
4. Provide predictable HTTP responses and useful API documentation.
5. Make local setup and review fast and reproducible, ideally with a single documented Docker Compose command.
6. Keep the implementation small enough that a junior engineer can explain the architecture and key decisions during an interview.

## 4. Non-goals

The initial submission will not implement:

- Real bank, UPI, payment-gateway or external transaction APIs.
- A frontend or mobile application.
- User registration, login, multi-user identity, or account-owner authorization. This is a documented assessment limitation, not a claim that these are unnecessary in production.
- Deposits or withdrawals against real funds, settlement, reconciliation workflows, fraud detection, compliance controls, or banking-grade operational monitoring.
- Money transfers between accounts until every mandatory requirement and its tests pass. Transfers are a bonus in the assessment.
- Public account listing, transaction editing, transaction deletion, or manual balance-adjustment endpoints.

## 5. Users and use cases

### Primary user: API reviewer

The reviewer needs to understand the project, inspect its endpoints, run a repeatable example, execute the tests, and verify the difficult cases without extensive setup.

### API client use cases

- Create an account with a name and receive a server-generated account ID.
- Submit a credit to an existing account.
- Submit a debit if sufficient funds exist.
- Read the current balance.
- Retrieve transaction history, optionally filtered by type and paginated.
- Receive a clear error for invalid input, a missing account, insufficient funds or a duplicate reference.

## 6. Functional requirements

### FR-1: Create account

- Endpoint: `POST /accounts`.
- Request must include a non-empty account holder name.
- The server generates a unique account ID and creation timestamp.
- The initial balance is always zero.
- Clients cannot set the initial balance; requests containing unsupported fields such as `balance` are rejected rather than silently accepted.

### FR-2: Create a credit or debit transaction

- Endpoint: `POST /accounts/{account_id}/transactions`.
- Supported types are `credit` and `debit` only.
- Each transaction has a unique server-generated transaction ID, account ID, type, positive amount, description, reference ID and server-generated creation timestamp.
- Credit increases the account balance by the transaction amount.
- Debit decreases the balance only if sufficient funds exist.
- A transaction is recorded only if the operation succeeds.
- The ledger record and account-balance update are one atomic database operation.
- A failed or rejected transaction must not change the account balance or leave a committed transaction record.

### FR-3: Duplicate-reference protection

- `reference_id` is unique **within an account**, not globally.
- Submitting a reference already used by the same account must not create another transaction or change the balance.
- Return a documented conflict response indicating that the reference already exists.
- The database must enforce this rule with a unique constraint; an application-only pre-check is insufficient.

### FR-4: Read account balance

- Endpoint: `GET /accounts/{account_id}/balance`.
- Return `account_id` and the current balance.
- Return a suitable `404` response if the account does not exist.

### FR-5: Read transaction history

- Endpoint: `GET /accounts/{account_id}/transactions`.
- Optional `type` filter: `credit` or `debit`. If omitted, return both types.
- Support one-based `page` and a bounded `limit`.
- Return current page, page size, total record count and total pages.
- Sort newest first by `created_at`; use a deterministic secondary key when timestamps match.
- Return `404` if the account does not exist.

### FR-6: Transaction immutability

- Do not expose `PUT`, `PATCH` or `DELETE` operations for transactions.
- A committed transaction's type, amount, description, reference ID, account ID and creation timestamp must remain unchanged through the application API.

### FR-7: Validation and error handling

At minimum, validate account names, account existence, transaction type, amount, reference ID, duplicate references, available balance and pagination values. Return consistent, understandable error bodies and suitable HTTP status codes. Do not expose stack traces, SQL text, credentials or other internal details to the caller.

### FR-8: Optional transfer

Money transfer between two accounts is a stretch goal only. Implement it only after all mandatory behavior and tests are complete. If added, the debit and credit must commit atomically or both roll back.

## 7. Non-functional requirements

### Correctness and consistency

- Monetary values must use decimal-safe arithmetic and storage, not binary floating-point arithmetic.
- A mutation must be performed in one database transaction.
- Concurrent mutations affecting one account must be serialized or otherwise safely coordinated.
- Database constraints must protect critical invariants where possible.

### Security baseline

- Validate all client-controlled values on the server.
- Use parameterized ORM/database queries.
- Keep database credentials outside source code and version control.
- Use a least-privilege database credential suitable for the app's operations.
- Return sanitized error responses and avoid logging secrets.
- Document that ownership authorization and end-user authentication are not implemented in this assessment.
- Do not expose an unrestricted write-enabled demo to the public internet without adding appropriate access controls.

### Maintainability

- Separate route handlers, schemas, database models and business logic.
- Keep transaction boundaries visible and easy to reason about.
- Use database migrations rather than relying solely on ad-hoc schema creation.
- Include automated tests for happy paths, failure paths, and concurrency-sensitive behavior.

### Reviewer accessibility

- Place the quick-start instructions near the top of `README.md`.
- Prefer local PostgreSQL via Docker Compose so the reviewer does not need to create a third-party database account.
- Provide `/docs` (interactive Swagger UI), a health endpoint, a test command, sample requests and a seed/demo workflow.
- Include `.env.example` without real secrets, `.gitignore`, API documentation and assumptions.
- The project must be runnable locally using the README instructions.

## 8. Acceptance criteria

The submission is ready when all mandatory items below have been demonstrated:

- [ ] A valid account can be created; its ID and timestamp are server-generated and its balance is zero.
- [ ] Client-supplied initial balance is rejected.
- [ ] A credit increases the balance by the exact amount.
- [ ] A valid debit decreases the balance by the exact amount.
- [ ] A debit larger than the available balance is rejected and leaves the balance unchanged.
- [ ] A transaction cannot be created for a nonexistent account.
- [ ] Amounts that are non-positive, malformed or not representable to two decimal places are rejected.
- [ ] Invalid transaction types are rejected.
- [ ] Reusing a reference within the same account does not produce a second transaction or a second balance change.
- [ ] The same reference can be used for a different account.
- [ ] Balance and transaction record changes commit or roll back together.
- [ ] Concurrent debits cannot produce a negative balance or approve withdrawals based on the same stale balance.
- [ ] Transaction history filters by type, paginates, returns pagination metadata and sorts newest first deterministically.
- [ ] There is no transaction update or delete API.
- [ ] Missing accounts and invalid input produce consistent, useful errors.
- [ ] Automated tests pass against PostgreSQL, including the concurrency-sensitive cases.
- [ ] A reviewer can start the service using the documented local setup, open `/docs`, run tests and follow a sample workflow.
- [ ] Source code, README, API documentation and assumptions are included in the submission.

## 9. Assumptions and decisions to document

1. The ledger represents INR only; multi-currency support is out of scope.
2. Amounts must be greater than zero and have no more than two fractional digits.
3. API examples represent monetary amounts as decimal strings (for example, `"1000.00"`) to avoid ambiguity in clients that use binary floating-point values. Internally, values use Python `Decimal` and PostgreSQL `NUMERIC(18,2)`.
4. Reference IDs are trimmed, case-sensitive identifiers. Uniqueness applies to the pair `(account_id, reference_id)`.
5. Pagination is one-based, defaults to `page=1` and `limit=20`, and caps `limit` at `100`.
6. A duplicate reference is returned as a conflict (`409`); the API does not silently replay an earlier response.
7. Rejected debits are not persisted as financial transactions. Operational logs may record failures without recording secrets.
8. Authentication and account-owner authorization are not part of the assessment API contract. This must be called out clearly in the README and deployment notes.

## 10. Definition of done

The work is complete when the acceptance criteria are met, the tests pass, a fresh local environment can run the app from the README, the repository contains no credentials, and the reviewer can quickly find the design, API docs and test instructions.
