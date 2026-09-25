def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    # /health is lightweight liveness and does not claim connected dependencies
    assert data["database"] in ("not_checked", "connected")
    assert data["storage"] in ("not_checked", "connected")


def test_ready_endpoint(client):
    response = client.get("/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "storage" in data["services"]
    assert "models" in data["services"]
    assert "gpu" in data["services"]


def test_standardized_error_structure(client):
    # Trigger 404
    response = client.get("/api/v1/images/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "trace_id" in data["error"]
