from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "client-governance-service"
    assert data["port"] == 8002


def test_admin_creates_client(client: TestClient, admin_headers: dict):
    payload = {
        "code": "telecom-corp",
        "name": "Telecom Solutions",
        "description": "Telecom services architecture",
        "package_prefix": "com.telecom.microservices",
        "java_version": "21",
        "quarkus_version": "3.15.1"
    }
    response = client.post("/api/v1/clients", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "telecom-corp"
    assert data["package_prefix"] == "com.telecom.microservices"
    assert data["java_version"] == "21"


def test_create_client_duplicate_code(client: TestClient, admin_headers: dict, sample_bcp_client):
    payload = {
        "code": "bcp",
        "name": "Another BCP Name",
        "package_prefix": "com.bcp.other",
        "java_version": "17",
        "quarkus_version": "3.15.1"
    }
    response = client.post("/api/v1/clients", json=payload, headers=admin_headers)
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


def test_developer_cannot_create_client(client: TestClient, bcp_dev_headers: dict):
    payload = {
        "code": "unauthorized-client",
        "name": "Unauthorized Client",
        "package_prefix": "com.unauthorized",
        "java_version": "17",
        "quarkus_version": "3.15.1"
    }
    response = client.post("/api/v1/clients", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 403


def test_list_clients_isolation(
    client: TestClient,
    admin_headers: dict,
    bcp_dev_headers: dict,
    retail_dev_headers: dict,
    sample_bcp_client,
    sample_retail_client
):
    # Admin sees both clients
    admin_resp = client.get("/api/v1/clients", headers=admin_headers)
    assert admin_resp.status_code == 200
    admin_codes = [c["code"] for c in admin_resp.json()]
    assert "bcp" in admin_codes
    assert "retail-corp" in admin_codes

    # BCP dev sees ONLY bcp
    bcp_resp = client.get("/api/v1/clients", headers=bcp_dev_headers)
    assert bcp_resp.status_code == 200
    bcp_codes = [c["code"] for c in bcp_resp.json()]
    assert "bcp" in bcp_codes
    assert "retail-corp" not in bcp_codes

    # Retail dev sees ONLY retail-corp
    retail_resp = client.get("/api/v1/clients", headers=retail_dev_headers)
    assert retail_resp.status_code == 200
    retail_codes = [c["code"] for c in retail_resp.json()]
    assert "retail-corp" in retail_codes
    assert "bcp" not in retail_codes


def test_client_access_forbidden_for_unassigned_developer(
    client: TestClient,
    bcp_dev_headers: dict,
    sample_retail_client
):
    # BCP dev attempts to read retail-corp profile -> 403 Forbidden
    response = client.get("/api/v1/clients/retail-corp", headers=bcp_dev_headers)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_admin_updates_client(client: TestClient, admin_headers: dict, sample_bcp_client):
    response = client.patch(
        "/api/v1/clients/bcp",
        json={"package_prefix": "com.bcp.v2.core", "java_version": "21"},
        headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["package_prefix"] == "com.bcp.v2.core"
    assert data["java_version"] == "21"

