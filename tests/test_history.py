import time
import uuid
import pytest


def test_history_all_types_and_ordering(client, created_account):
    account_id = created_account["id"]

    # Post 3 transactions in sequence
    client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "1000.00",
            "description": "Tx 1",
            "reference_id": "TX-01",
        },
    )
    time.sleep(0.01)
    client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "debit",
            "amount": "200.00",
            "description": "Tx 2",
            "reference_id": "TX-02",
        },
    )
    time.sleep(0.01)
    client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "500.00",
            "description": "Tx 3",
            "reference_id": "TX-03",
        },
    )

    response = client.get(f"/accounts/{account_id}/transactions")
    assert response.status_code == 200

    data = response.json()
    items = data["items"]
    pagination = data["pagination"]

    assert len(items) == 3
    assert pagination["total_records"] == 3
    assert pagination["total_pages"] == 1
    assert pagination["page"] == 1
    assert pagination["page_size"] == 20

    # Ordered newest first (Tx 3, Tx 2, Tx 1)
    assert items[0]["reference_id"] == "TX-03"
    assert items[1]["reference_id"] == "TX-02"
    assert items[2]["reference_id"] == "TX-01"


def test_history_filter_by_type(client, created_account):
    account_id = created_account["id"]

    client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "1000.00",
            "description": "Credit 1",
            "reference_id": "C-1",
        },
    )
    client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "debit",
            "amount": "100.00",
            "description": "Debit 1",
            "reference_id": "D-1",
        },
    )
    client.post(
        f"/accounts/{account_id}/transactions",
        json={
            "type": "credit",
            "amount": "200.00",
            "description": "Credit 2",
            "reference_id": "C-2",
        },
    )

    # Filter by credit
    res_credit = client.get(f"/accounts/{account_id}/transactions?type=credit")
    assert res_credit.status_code == 200
    credit_data = res_credit.json()
    assert credit_data["pagination"]["total_records"] == 2
    assert all(item["type"] == "credit" for item in credit_data["items"])

    # Filter by debit
    res_debit = client.get(f"/accounts/{account_id}/transactions?type=debit")
    assert res_debit.status_code == 200
    debit_data = res_debit.json()
    assert debit_data["pagination"]["total_records"] == 1
    assert debit_data["items"][0]["type"] == "debit"
    assert debit_data["items"][0]["reference_id"] == "D-1"


def test_history_pagination(client, created_account):
    account_id = created_account["id"]

    # Create 5 transactions
    for i in range(1, 6):
        client.post(
            f"/accounts/{account_id}/transactions",
            json={
                "type": "credit",
                "amount": "100.00",
                "description": f"Tx {i}",
                "reference_id": f"PAGE-TX-{i}",
            },
        )

    # Page 1 with limit 2
    res_p1 = client.get(f"/accounts/{account_id}/transactions?page=1&limit=2")
    data_p1 = res_p1.json()
    assert len(data_p1["items"]) == 2
    assert data_p1["pagination"]["total_records"] == 5
    assert data_p1["pagination"]["total_pages"] == 3
    assert data_p1["pagination"]["page"] == 1
    assert data_p1["pagination"]["page_size"] == 2

    # Page 3 (should have 1 item)
    res_p3 = client.get(f"/accounts/{account_id}/transactions?page=3&limit=2")
    data_p3 = res_p3.json()
    assert len(data_p3["items"]) == 1

    # Page beyond available items
    res_p4 = client.get(f"/accounts/{account_id}/transactions?page=4&limit=2")
    data_p4 = res_p4.json()
    assert len(data_p4["items"]) == 0
    assert data_p4["pagination"]["total_records"] == 5
    assert data_p4["pagination"]["total_pages"] == 3


def test_history_empty_results(client, created_account):
    account_id = created_account["id"]
    response = client.get(f"/accounts/{account_id}/transactions")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["pagination"]["total_records"] == 0
    assert data["pagination"]["total_pages"] == 0


def test_history_account_not_found(client):
    random_id = str(uuid.uuid4())
    response = client.get(f"/accounts/{random_id}/transactions")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ACCOUNT_NOT_FOUND"


@pytest.mark.parametrize(
    "invalid_query",
    [
        "page=0",
        "page=-1",
        "limit=0",
        "limit=101",
        "type=invalid_type",
    ],
)
def test_history_invalid_query_params(client, created_account, invalid_query):
    account_id = created_account["id"]
    response = client.get(f"/accounts/{account_id}/transactions?{invalid_query}")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
