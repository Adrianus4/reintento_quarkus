from fastapi.testclient import TestClient
from app.models.user import User


def test_admin_assigns_clients_to_developer(client: TestClient, admin_token: str, dev_user: User):
    payload = {
        "client_codes": ["bcp", "retail-corp", "telecom-x"]
    }
    response = client.put(
        f"/api/v1/users/{dev_user.id}/assigned-clients",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert set(data["assigned_clients"]) == {"bcp", "retail-corp", "telecom-x"}


def test_developer_cannot_assign_clients(client: TestClient, dev_token: str, dev_user: User):
    payload = {
        "client_codes": ["secret-bank"]
    }
    response = client.put(
        f"/api/v1/users/{dev_user.id}/assigned-clients",
        json=payload,
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert response.status_code == 403


def test_developer_retrieves_own_assigned_clients_isolation(client: TestClient, dev_token: str, dev_user: User):
    response = client.get(
        "/api/v1/auth/me/clients",
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "DEVELOPER"
    assert data["is_admin"] is False
    assert data["client_codes"] == ["bcp"]


def test_admin_receives_universal_client_access(client: TestClient, admin_token: str):
    response = client.get(
        "/api/v1/auth/me/clients",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "ADMIN"
    assert data["is_admin"] is True
    assert data["client_codes"] == ["*"]

