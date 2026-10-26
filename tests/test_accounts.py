import uuid


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_account_success(client):
    payload = {"name": "Akshay Kumar"}
    response = client.post("/accounts", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    # Verify ID is a valid UUID
    account_uuid = uuid.UUID(data["id"])
    assert str(account_uuid) == data["id"]
    assert data["name"] == "Akshay Kumar"
    assert data["balance"] == "0.00"
    assert "created_at" in data


def test_create_account_name_whitespace_trimmed(client):
    payload = {"name": "   Jane Doe   "}
    response = client.post("/accounts", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "Jane Doe"


def test_create_account_reject_empty_or_whitespace_name(client):
    for invalid_name in ["", "   ", "\t\n"]:
        response = client.post("/accounts", json={"name": invalid_name})
        assert response.status_code == 422
        body = response.json()
        assert "error" in body
        assert body["error"]["code"] == "VALIDATION_ERROR"


def test_create_account_reject_missing_name(client):
    response = client.post("/accounts", json={})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_create_account_reject_client_supplied_balance(client):
    payload = {"name": "Hacker", "balance": "1000.00"}
    response = client.post("/accounts", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_create_account_reject_extra_unknown_fields(client):
    payload = {"name": "Valid Name", "extra_field": "disallowed"}
    response = client.post("/accounts", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"


def test_get_account_balance_success(client, created_account):
    account_id = created_account["id"]
    response = client.get(f"/accounts/{account_id}/balance")
    assert response.status_code == 200

    data = response.json()
    assert data["account_id"] == account_id
    assert data["balance"] == "0.00"


def test_get_account_balance_not_found(client):
    non_existent_id = str(uuid.uuid4())
    response = client.get(f"/accounts/{non_existent_id}/balance")
    assert response.status_code == 404

    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "ACCOUNT_NOT_FOUND"
    assert "not found" in body["error"]["message"].lower()
