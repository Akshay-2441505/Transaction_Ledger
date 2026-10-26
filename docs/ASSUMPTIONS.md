# Key Assumptions and Design Decisions

**Project:** Transaction Ledger API  
**Status:** Baseline Documentation  
**Related Documents:** [`PRD.md`](./PRD.md), [`DESIGN.md`](./DESIGN.md), [`TECH_STACK.md`](./TECH_STACK.md)

---

## 1. Currency & Precision
- **Currency:** The ledger strictly models single-currency transactions in Indian Rupees (INR, ₹). Multi-currency conversions and foreign exchange are out of scope.
- **Monetary Precision:** All amounts and balances are stored as PostgreSQL `NUMERIC(18, 2)` and manipulated in Python using `decimal.Decimal` with two fractional digits. Floating-point arithmetic (`float`) is strictly prohibited.
- **API Wire Format:** Monetary values are serialized as decimal strings (e.g. `"1000.00"`) in JSON payloads to prevent precision loss in client environments that parse JSON numbers as IEEE-754 double precision floats.

## 2. Invariants & Consistency
- **Balance Invariant:** For every account, the stored balance strictly equals `sum(successful credits) - sum(successful debits)`.
- **Negative Balance Prevention:** An account balance must never fall below `0.00`. This is guarded by:
  1. Service-level checks under exclusive pessimistic row lock (`SELECT ... FOR UPDATE`).
  2. PostgreSQL database check constraint `CHECK (balance >= 0)`.
- **Atomic Operations:** Credit or debit writes and the resulting account balance update occur within the exact same database transaction.
- **Failure Non-Persistence:** Rejected transactions (e.g., overdraft attempts or invalid inputs) are never committed to the `transactions` table. Failed operations roll back completely.

## 3. Idempotency & Reference Uniqueness
- **Scope of Uniqueness:** The `reference_id` is unique per account (`UNIQUE (account_id, reference_id)`), not globally. A client may reuse the same reference ID across different accounts.
- **Conflict Handling:** Reusing a reference ID for the same account results in `409 DUPLICATE_REFERENCE`. The API does not silently replay previous transactions.
- **Sanitization:** `reference_id` strings are whitespace-trimmed and compared case-sensitively.

## 4. Immutability
- **Append-Only Ledger:** There are no `PUT`, `PATCH`, or `DELETE` endpoints for ledger records. Once committed, a transaction record is immutable.
- **Account Balance Field:** Account creation (`POST /accounts`) strictly forbids client-supplied `balance`. Initial balance is always `0.00`.

## 5. Security & Scope Limitations
- **Authentication & Authorization:** As explicitly scoped in the recruitment assessment specification, end-user authentication (JWT, OAuth) and account-owner authorization are excluded from the API contract. All endpoints are open for evaluation.
- **Data Protection:** Database credentials are never logged or exposed. Application error handlers sanitize exceptions and never return raw SQL, stack traces, or environment variables.
- **Input Sanitization:** Account names are trimmed and validated to contain non-whitespace text. Query limits are bounded between 1 and 100.
