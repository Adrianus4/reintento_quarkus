from fastapi.testclient import TestClient
from app.core.vault import decrypt_secret
from app.models.credential import VaultCredential


def test_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ai-orchestrator-service"
    assert data["port"] == 8003


def test_admin_saves_vault_key(client: TestClient, admin_headers: dict, db_session):
    raw_api_key = "AIzaSyFakeKeyForUnitTestingOnly12345"
    payload = {
        "provider": "gemini",
        "api_key": raw_api_key
    }
    response = client.post("/api/v1/vault/keys", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "gemini"
    assert "..." in data["masked_key"]
    assert raw_api_key not in data["masked_key"]  # Never plain text

    # Verify encrypted in database
    cred = db_session.query(VaultCredential).filter(VaultCredential.provider == "gemini").first()
    assert cred is not None
    assert cred.encrypted_key != raw_api_key
    # Decryption recovers exact key
    assert decrypt_secret(cred.encrypted_key) == raw_api_key


def test_admin_rotates_vault_key(client: TestClient, admin_headers: dict, db_session):
    client.post(
        "/api/v1/vault/keys",
        json={"provider": "deepseek", "api_key": "sk-initialkey1234567890"},
        headers=admin_headers
    )
    # Rotate with new key
    new_raw = "sk-rotatedkey9876543210"
    resp = client.post(
        "/api/v1/vault/keys",
        json={"provider": "deepseek", "api_key": new_raw},
        headers=admin_headers
    )
    assert resp.status_code in [200, 201]
    cred = db_session.query(VaultCredential).filter(VaultCredential.provider == "deepseek").first()
    assert decrypt_secret(cred.encrypted_key) == new_raw


def test_developer_cannot_save_vault_key(client: TestClient, bcp_dev_headers: dict):
    payload = {
        "provider": "grok",
        "api_key": "xai-unauthorizedkey12345"
    }
    response = client.post("/api/v1/vault/keys", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 403


def test_test_connection_unconfigured_provider(client: TestClient, admin_headers: dict):
    response = client.post(
        "/api/v1/vault/test-connection",
        json={"provider": "grok"},
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["connected"] is False
    assert "No active credentials" in data["message"]
