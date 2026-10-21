from fastapi.testclient import TestClient
from app.models.user import User


def test_list_users_as_admin(client: TestClient, admin_token: str, admin_user: User):
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    emails = [u["email"] for u in data]
    assert admin_user.email in emails


def test_list_users_as_developer_forbidden(client: TestClient, dev_token: str):
    response = client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert response.status_code == 403
    assert "Administrative privileges required" in response.json()["detail"]


def test_create_user_as_admin(client: TestClient, admin_token: str):
    payload = {
        "email": "new.dev@tcs.com",
        "password": "Password123!",
        "full_name": "New Developer",
        "role": "DEVELOPER"
    }
    response = client.post(
        "/api/v1/users",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new.dev@tcs.com"
    assert data["role"] == "DEVELOPER"
    assert data["is_active"] is True


def test_create_user_as_developer_forbidden(client: TestClient, dev_token: str):
    payload = {
        "email": "hack.dev@tcs.com",
        "password": "Password123!",
        "full_name": "Hack Developer",
        "role": "DEVELOPER"
    }
    response = client.post(
        "/api/v1/users",
        json=payload,
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert response.status_code == 403


def test_create_user_duplicate_email(client: TestClient, admin_token: str, admin_user: User):
    payload = {
        "email": admin_user.email,
        "password": "Password123!",
        "full_name": "Duplicate Admin",
        "role": "ADMIN"
    }
    response = client.post(
        "/api/v1/users",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_create_user_invalid_role(client: TestClient, admin_token: str):
    payload = {
        "email": "invalid.role@tcs.com",
        "password": "Password123!",
        "full_name": "Invalid Role",
        "role": "SUPERUSER"  # Only ADMIN and DEVELOPER allowed
    }
    response = client.post(
        "/api/v1/users",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 422


def test_admin_cannot_deactivate_self_if_sole_admin(client: TestClient, admin_user: User, admin_token: str):
    response = client.patch(
        f"/api/v1/users/{admin_user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert "sole active Administrator" in response.json()["detail"]


def test_admin_cannot_demote_self_if_sole_admin(client: TestClient, admin_user: User, admin_token: str):
    response = client.patch(
        f"/api/v1/users/{admin_user.id}",
        json={"role": "DEVELOPER"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert "sole active Administrator" in response.json()["detail"]


def test_admin_can_update_other_user(client: TestClient, admin_token: str, dev_user: User):
    response = client.patch(
        f"/api/v1/users/{dev_user.id}",
        json={"full_name": "Updated Dev Name", "is_active": False},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Dev Name"
    assert data["is_active"] is False

