import uuid
import pytest
from unittest.mock import patch


def test_credit_transaction_success(client, created_account):
    account_id = created_account["id"]
    payload = {
        "type": "credit",
        "amount": "1000.00",
        "description": "Salary deposit",
        "reference_id": "REF-001",
    }
    response = client.post(f"/accounts/{account_id}/transactions", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["account_id"] == account_id
    assert data["type"] == "credit"
    assert data["amount"] == "1000.00"
    assert data["description"] == "Salary deposit"
    assert data["reference_id"] == "REF-001"
    assert data["account_balance"] == "1000.00"
    assert "id" in data
    assert "created_at" in data

    # Verify balance endpoint confirms updated balance
    bal_res = client.get(f"/accounts/{account_id}/balance")
    assert bal_res.status_code == 200
    assert bal_res.json()["balance"] == "1000.00"


def test_debit_transaction_success(client, created_account):
    account_id = created_account["id"]

    # Initial credit of 1000.00
    client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "1000.00",
            "description": "Initial funding",
            "reference_id": "FUND-01",
        },
    )

    # Valid debit of 300.00
    response = client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "debit",
            "amount": "300.00",
            "description": "Books purchase",
            "reference_id": "DEBIT-01",
        },
    )
    assert response.status_code == 201
    assert response.json()["account_balance"] == "700.00"

    # Verify balance is 700.00
    bal_res = client.get(f"/accounts/{account_id}/balance")
    assert bal_res.json()["balance"] == "700.00"


def test_debit_insufficient_balance_rejected(client, created_account):
    account_id = created_account["id"]

    # Credit 100.00
    client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "100.00",
            "description": "Seed money",
            "reference_id": "SEED-01",
        },
    )

    # Attempt debit of 150.00
    response = client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "debit",
            "amount": "150.00",
            "description": "Overdraft attempt",
            "reference_id": "OVERDRAFT-01",
        },
    )
    assert response.status_code == 409
    body = response.json()
    assert body["error"]["code"] == "INSUFFICIENT_BALANCE"

    # Verify balance remained exactly 100.00
    bal_res = client.get(f"/accounts/{account_id}/balance")
    assert bal_res.json()["balance"] == "100.00"

    # Verify rejected transaction was NOT saved in history
    hist_res = client.get(f"/accounts/{account_id}/transactions")
    assert hist_res.json()["pagination"]["total_records"] == 1


def test_transaction_nonexistent_account(client):
    fake_id = str(uuid.uuid4())
    payload = {
        "type": "credit",
        "amount": "100.00",
        "description": "Ghost deposit",
        "reference_id": "GHOST-01",
    }
    response = client.post(f"/accounts/{fake_id}/transactions", json=payload)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


def test_duplicate_reference_same_account_rejected(client, created_account):
    account_id = created_account["id"]
    payload = {
        "type": "credit",
        "amount": "500.00",
        "description": "First payment",
        "reference_id": "DUPLICATE-REF-TEST",
    }

    # First request succeeds
    res1 = client.post(f"/accounts/{account_id}/transactions", json=payload)
    assert res1.status_code == 201

    # Second request with identical reference on same account is rejected
    res2 = client.post(f"/accounts/{account_id}/transactions", json=payload)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "DUPLICATE_REFERENCE"

    # Verify balance was updated only once (500.00, not 1000.00)
    bal_res = client.get(f"/accounts/{account_id}/balance")
    assert bal_res.json()["balance"] == "500.00"


def test_duplicate_reference_different_accounts_accepted(client):
    # Create two distinct accounts
    acc1 = client.post("/accounts", json={"name": "User 1"}).json()["id"]
    acc2 = client.post("/accounts", json={"name": "User 2"}).json()["id"]

    payload = {
        "type": "credit",
        "amount": "500.00",
        "description": "Shared reference test",
        "reference_id": "SHARED-REF-100",
    }

    # Acc 1 succeeds
    res1 = client.post(f"/accounts/{acc1}/transactions", json=payload)
    assert res1.status_code == 201

    # Acc 2 also succeeds with same reference_id
    res2 = client.post(f"/accounts/{acc2}/transactions", json=payload)
    assert res2.status_code == 201


@pytest.mark.parametrize(
    "invalid_amount",
    ["0.00", "-50.00", "0", "-0.01", "100.555", "abc", "NaN", "Infinity", ""],
)
def test_reject_invalid_amounts(client, created_account, invalid_amount):
    account_id = created_account["id"]
    payload = {
        "type": "credit",
        "amount": invalid_amount,
        "description": "Testing invalid amount",
        "reference_id": f"TEST-AMT-{uuid.uuid4()}",
    }
    response = client.post(f"/accounts/{account_id}/transactions", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    "invalid_type", ["deposit", "withdrawal", "transfer", "CREDIT", ""]
)
def test_reject_invalid_transaction_types(client, created_account, invalid_type):
    account_id = created_account["id"]
    payload = {
        "type": invalid_type,
        "amount": "100.00",
        "description": "Invalid type test",
        "reference_id": f"TEST-TYPE-{uuid.uuid4()}",
    }
    response = client.post(f"/accounts/{account_id}/transactions", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_transaction_immutability_no_mutations_allowed(client, created_account):
    account_id = created_account["id"]
    tx_res = client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "100.00",
            "description": "Immutable tx",
            "reference_id": "IMMUTABLE-01",
        },
    )
    tx_id = tx_res.json()["id"]

    # Verify PUT, PATCH, DELETE are not allowed
    for method in ["put", "patch", "delete"]:
        res = getattr(client, method)(f"/accounts/{account_id}/transactions/{tx_id}")
        assert res.status_code in [404, 405]


def test_atomic_rollback_on_commit_failure(client, created_account, db):
    account_id = created_account["id"]

    # Mock db.commit to raise an exception during transaction creation
    with patch.object(
        db, "commit", side_effect=RuntimeError("Database failure simulation")
    ):
        with pytest.raises(RuntimeError):
            client.post(
                f"/accounts/{account_id}/transactions",
                json={
                    "type": "credit",
                    "amount": "500.00",
                    "description": "Failed commit",
                    "reference_id": "FAIL-COMMIT-01",
                },
            )

    # Verify no transaction was recorded and balance remains 0.00
    bal_res = client.get(f"/accounts/{account_id}/balance")
    assert bal_res.json()["balance"] == "0.00"

    hist_res = client.get(f"/accounts/{account_id}/transactions")
    assert hist_res.json()["pagination"]["total_records"] == 0
