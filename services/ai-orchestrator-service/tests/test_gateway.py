from fastapi.testclient import TestClient


def test_get_gateway_config(client: TestClient, bcp_dev_headers: dict):
    response = client.get("/api/v1/ai-gateway/config", headers=bcp_dev_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["active_provider"] == "mock"
    assert data["consumption_mode"] == "balanced"
    assert data["max_tokens"] >= 8192


def test_admin_updates_gateway_config(client: TestClient, admin_headers: dict):
    payload = {
        "active_provider": "gemini",
        "consumption_mode": "advanced",
        "temperature": 0.1,
        "max_tokens": 12000
    }
    response = client.put("/api/v1/ai-gateway/config", json=payload, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["active_provider"] == "gemini"
    assert data["consumption_mode"] == "advanced"
    assert data["temperature"] == 0.1
    assert data["max_tokens"] == 12000


def test_developer_cannot_update_gateway_config(client: TestClient, bcp_dev_headers: dict):
    payload = {
        "active_provider": "grok"
    }
    response = client.put("/api/v1/ai-gateway/config", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 403

