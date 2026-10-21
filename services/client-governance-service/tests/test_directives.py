from fastapi.testclient import TestClient


def test_admin_creates_directive(client: TestClient, admin_headers: dict, sample_bcp_client):
    payload = {
        "rule_code": "SEC_SMALLRYE_JWT",
        "category": "SECURITY",
        "severity": "MANDATORY",
        "description": "All public endpoints must validate JWT using SmallRye JWT.",
        "deterministic_check": "has_quarkus_smallrye_jwt_dependency"
    }
    response = client.post("/api/v1/clients/bcp/directives", json=payload, headers=admin_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["rule_code"] == "SEC_SMALLRYE_JWT"
    assert data["category"] == "SECURITY"
    assert data["severity"] == "MANDATORY"
    assert data["version"] == 1


def test_create_directive_duplicate_rule_code(client: TestClient, admin_headers: dict, sample_bcp_client):
    payload = {
        "rule_code": "ARCH_HEXAGONAL",
        "category": "ARCHITECTURE",
        "severity": "RECOMMENDED",
        "description": "Favor Hexagonal Ports and Adapters."
    }
    r1 = client.post("/api/v1/clients/bcp/directives", json=payload, headers=admin_headers)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/clients/bcp/directives", json=payload, headers=admin_headers)
    assert r2.status_code == 409
    assert "already exists" in r2.json()["detail"]


def test_developer_cannot_create_directive(client: TestClient, bcp_dev_headers: dict, sample_bcp_client):
    payload = {
        "rule_code": "TEST_RESTASSURED",
        "category": "TESTING",
        "severity": "MANDATORY",
        "description": "Endpoints must have REST-assured integration tests."
    }
    response = client.post("/api/v1/clients/bcp/directives", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 403


def test_list_directives_isolation(
    client: TestClient,
    admin_headers: dict,
    bcp_dev_headers: dict,
    retail_dev_headers: dict,
    sample_bcp_client
):
    # Add a directive to BCP
    client.post(
        "/api/v1/clients/bcp/directives",
        json={
            "rule_code": "OBS_MICROMETER",
            "category": "OBSERVABILITY",
            "severity": "MANDATORY",
            "description": "Prometheus metrics enabled"
        },
        headers=admin_headers
    )

    # BCP dev can read BCP directives
    bcp_resp = client.get("/api/v1/clients/bcp/directives", headers=bcp_dev_headers)
    assert bcp_resp.status_code == 200
    assert len(bcp_resp.json()) >= 1

    # Retail dev CANNOT read BCP directives (403)
    retail_resp = client.get("/api/v1/clients/bcp/directives", headers=retail_dev_headers)
    assert retail_resp.status_code == 403

