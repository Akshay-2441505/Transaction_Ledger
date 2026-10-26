import concurrent.futures
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.session import get_db
from app.main import app
from app.models.account import Account
from app.models.transaction import Transaction

# Dedicated PostgreSQL connection pool for concurrency test workers
concurrency_engine = create_engine(
    settings.TEST_DATABASE_URL or settings.DATABASE_URL,
    pool_size=15,
    max_overflow=25,
)
ConcurrencySessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=concurrency_engine
)


def override_concurrency_db():
    db = ConcurrencySessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def concurrency_app(is_postgres):
    if not is_postgres:
        pytest.skip("PostgreSQL is required for concurrency and row-locking tests.")

    app.dependency_overrides[get_db] = override_concurrency_db
    yield app
    app.dependency_overrides.clear()


def test_concurrent_debits_prevent_negative_balance(concurrency_app):
    """
    Simulates two concurrent debits of 700.00 against an account with 1000.00 balance.
    PostgreSQL FOR UPDATE row lock must serialize the requests such that:
    - Exactly one debit succeeds (HTTP 201)
    - The second debit sees remaining balance of 300.00 and is rejected (HTTP 409 INSUFFICIENT_BALANCE)
    - Final balance is strictly 300.00
    """
    with TestClient(concurrency_app) as client:
        # Create account
        acc_res = client.post("/accounts", json={"name": "Race Condition Test"})
        assert acc_res.status_code == 201
        account_id = acc_res.json()["id"]

        # Credit 1000.00
        client.post(
            f"/accounts/{account_id}/transactions",
            json={
                "type": "credit",
                "amount": "1000.00",
                "description": "Initial 1000",
                "reference_id": f"INIT-{uuid.uuid4()}",
            },
        )

    def attempt_debit(ref_suffix: str):
        with TestClient(concurrency_app) as thread_client:
            return thread_client.post(
                f"/accounts/{account_id}/transactions",
                json={
                    "type": "debit",
                    "amount": "700.00",
                    "description": f"Parallel debit {ref_suffix}",
                    "reference_id": f"DEBIT-RACE-{ref_suffix}",
                },
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_debit, "A")
        f2 = executor.submit(attempt_debit, "B")
        res1 = f1.result()
        res2 = f2.result()

    statuses = [res1.status_code, res2.status_code]
    assert 201 in statuses, "At least one debit should have succeeded"
    assert 409 in statuses, "One debit should have failed with 409 INSUFFICIENT_BALANCE"

    with TestClient(concurrency_app) as client:
        bal_res = client.get(f"/accounts/{account_id}/balance")
        assert bal_res.status_code == 200
        assert bal_res.json()["balance"] == "300.00"


def test_concurrent_duplicate_references(concurrency_app):
    """
    Simulates concurrent requests submitting the identical reference_id for the same account.
    Exactly one request must succeed and the other must be rejected with 409 DUPLICATE_REFERENCE.
    """
    with TestClient(concurrency_app) as client:
        acc_res = client.post("/accounts", json={"name": "Idempotency Race Test"})
        account_id = acc_res.json()["id"]

    fixed_ref = f"DUPLICATE-RACE-{uuid.uuid4()}"

    def attempt_credit():
        with TestClient(concurrency_app) as thread_client:
            return thread_client.post(
                f"/accounts/{account_id}/transactions",
                json={
                    "type": "credit",
                    "amount": "250.00",
                    "description": "Race credit",
                    "reference_id": fixed_ref,
                },
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(attempt_credit) for _ in range(3)]
        results = [f.result() for f in futures]

    successes = [r for r in results if r.status_code == 201]
    conflicts = [r for r in results if r.status_code == 409]

    assert len(successes) == 1, "Exactly one request with this reference must succeed"
    assert len(conflicts) == 2, "All other duplicate submissions must receive 409"
    for c in conflicts:
        assert c.json()["error"]["code"] == "DUPLICATE_REFERENCE"

    with TestClient(concurrency_app) as client:
        bal_res = client.get(f"/accounts/{account_id}/balance")
        assert bal_res.json()["balance"] == "250.00"


def test_concurrency_aggregate_invariant(concurrency_app):
    """
    Executes multiple concurrent transactions and verifies that stored balance
    strictly matches sum(credits) - sum(debits).
    """
    with TestClient(concurrency_app) as client:
        acc_res = client.post("/accounts", json={"name": "Aggregate Invariant Test"})
        account_id = acc_res.json()["id"]

        # Initial seed
        client.post(
            f"/accounts/{account_id}/transactions",
            json={
                "type": "credit",
                "amount": "1000.00",
                "description": "Seed deposit",
                "reference_id": f"SEED-{uuid.uuid4()}",
            },
        )

    def random_operation(idx: int):
        with TestClient(concurrency_app) as thread_client:
            is_credit = idx % 2 == 0
            ttype = "credit" if is_credit else "debit"
            amount = "50.00" if is_credit else "40.00"
            return thread_client.post(
                f"/accounts/{account_id}/transactions",
                json={
                    "type": ttype,
                    "amount": amount,
                    "description": f"Concurrent op {idx}",
                    "reference_id": f"CONC-{idx}-{uuid.uuid4()}",
                },
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(random_operation, i) for i in range(10)]
        results = [f.result() for f in futures]

    for r in results:
        assert r.status_code in [201, 409]

    # Recompute ledger total directly from transactions table
    with ConcurrencySessionLocal() as session:
        account = session.get(Account, uuid.UUID(account_id))
        transactions = (
            session.execute(
                select(Transaction).where(
                    Transaction.account_id == uuid.UUID(account_id)
                )
            )
            .scalars()
            .all()
        )

        calculated_balance = Decimal("0.00")
        for tx in transactions:
            if tx.type == "credit":
                calculated_balance += tx.amount
            elif tx.type == "debit":
                calculated_balance -= tx.amount

        assert (
            account.balance == calculated_balance
        ), "Stored balance must equal sum(credits) - sum(debits)"
