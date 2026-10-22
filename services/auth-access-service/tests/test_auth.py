from datetime import timedelta
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.models.user import User


def test_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "auth-access-service"
    assert data["port"] == 8001


def test_setup_admin_clean_state_and_idempotency_block(client: TestClient):
    # Initial setup on clean database
    payload = {
        "email": "bootstrap.admin@tcs.com",
        "password": "Password123!",
        "full_name": "Bootstrap Admin"
    }
    response = client.post("/api/v1/auth/setup-admin", json=payload)
    assert response.status_code == 201
    token_response = response.json()
    assert token_response["access_token"]
    data = token_response["user"]
    assert data["email"] == "bootstrap.admin@tcs.com"
    assert data["role"] == "ADMIN"
    assert data["is_active"] is True

    # Second call must be blocked with 409 Conflict
    response_blocked = client.post("/api/v1/auth/setup-admin", json=payload)
    assert response_blocked.status_code == 409
    assert "already been completed" in response_blocked.json()["detail"]


def test_login_success(client: TestClient, admin_user: User):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "AdminPass123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == admin_user.email
    assert data["user"]["role"] == "ADMIN"


def test_register_cannot_reset_existing_password(client: TestClient, admin_user: User):
    response=client.post('/api/v1/auth/register',json={
        'email':admin_user.email,'password':'Replacement123!','full_name':'Replacement','role':'ADMIN'})
    assert response.status_code==409
    assert client.post('/api/v1/auth/login',json={
        'email':admin_user.email,'password':'AdminPass123!'}).status_code==200
    assert client.post('/api/v1/auth/login',json={
        'email':admin_user.email,'password':'Replacement123!'}).status_code==401


def test_public_registration_cannot_add_admin(client: TestClient, admin_user: User):
    response=client.post('/api/v1/auth/register',json={
        'email':'new@example.com','password':'Password123!','full_name':'New User','role':'ADMIN'})
    assert response.status_code==201
    assert response.json()['user']['role']=='DEVELOPER'


def test_login_invalid_password(client: TestClient, admin_user: User):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": admin_user.email, "password": "WrongPassword123"}
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_non_existent_email(client: TestClient):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@tcs.com", "password": "AnyPassword123"}
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_inactive_user(client: TestClient, db_session, dev_user: User):
    dev_user.is_active = False
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": dev_user.email, "password": "DevPass123!"}
    )
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


def test_get_current_user_profile(client: TestClient, dev_user: User, dev_token: str):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {dev_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == dev_user.id
    assert data["email"] == dev_user.email
    assert data["role"] == "DEVELOPER"
    assert "bcp" in data["assigned_clients"]


def test_get_current_user_unauthorized(client: TestClient):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_verify_token_valid(client: TestClient, dev_user: User, dev_token: str):
    response = client.post(
        "/api/v1/auth/verify",
        json={"token": dev_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["user_id"] == dev_user.id
    assert data["role"] == "DEVELOPER"
    assert data["assigned_clients"] == ["bcp"]
    assert data["reason"] is None


def test_verify_token_expired(client: TestClient, dev_user: User):
    expired_token = create_access_token(
        subject=dev_user.id,
        email=dev_user.email,
        role=dev_user.role.value,
        expires_delta=timedelta(seconds=-10)
    )
    response = client.post(
        "/api/v1/auth/verify",
        json={"token": expired_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["reason"] == "INVALID_OR_EXPIRED_TOKEN"


def test_verify_token_inactive_user(client: TestClient, db_session, dev_user: User, dev_token: str):
    dev_user.is_active = False
    db_session.commit()

    response = client.post(
        "/api/v1/auth/verify",
        json={"token": dev_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["reason"] == "USER_INACTIVE"

