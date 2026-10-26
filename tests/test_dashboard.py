def test_dashboard_root_serves_html(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Transaction Ledger" in response.text
    assert "Financial Overview" in response.text


def test_dashboard_static_css_accessible(client):
    response = client.get("/static/css/dashboard.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]
    assert "--accent-green" in response.text


def test_dashboard_static_js_accessible(client):
    response = client.get("/static/js/dashboard.js")
    assert response.status_code == 200
    assert (
        "javascript" in response.headers["content-type"]
        or "text/plain" in response.headers["content-type"]
    )
    assert "fetchTransactionHistory" in response.text


def test_developer_docs_and_health_remain_accessible(client):
    # Verify developer docs routes are preserved and functional
    docs_res = client.get("/docs")
    assert docs_res.status_code == 200

    openapi_res = client.get("/openapi.json")
    assert openapi_res.status_code == 200
    assert openapi_res.json()["info"]["title"] == "Transaction Ledger API"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json() == {"status": "ok"}
