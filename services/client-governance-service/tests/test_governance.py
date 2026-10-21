from fastapi.testclient import TestClient


def test_get_governance_context_without_contract(
    client: TestClient,
    admin_headers: dict,
    bcp_dev_headers: dict,
    sample_bcp_client
):
    # Add directives with different severities
    client.post(
        "/api/v1/clients/bcp/directives",
        json={
            "rule_code": "SEC_JWT",
            "category": "SECURITY",
            "severity": "MANDATORY",
            "description": "JWT mandatory"
        },
        headers=admin_headers
    )
    client.post(
        "/api/v1/clients/bcp/directives",
        json={
            "rule_code": "ARCH_HEXA",
            "category": "ARCHITECTURE",
            "severity": "RECOMMENDED",
            "description": "Hexagonal recommended"
        },
        headers=admin_headers
    )

    response = client.get("/api/v1/clients/bcp/governance-context", headers=bcp_dev_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["client"]["code"] == "bcp"
    assert len(data["mandatory_directives"]) == 1
    assert data["mandatory_directives"][0]["rule_code"] == "SEC_JWT"
    assert len(data["recommended_directives"]) == 1
    assert data["recommended_directives"][0]["rule_code"] == "ARCH_HEXA"
    assert data["contract"] is None


def test_get_governance_context_with_contract(
    client: TestClient,
    bcp_dev_headers: dict,
    sample_bcp_client
):
    # Upload contract
    c_resp = client.post(
        "/api/v1/clients/bcp/contracts",
        json={
            "format": "json",
            "raw_content": '{"openapi": "3.0.1", "info": {"title": "Test API", "version": "1.0"}, "paths": {}}'
        },
        headers=bcp_dev_headers
    )
    contract_id = c_resp.json()["id"]

    response = client.get(
        f"/api/v1/clients/bcp/governance-context?contract_id={contract_id}",
        headers=bcp_dev_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["contract"] is not None
    assert data["contract"]["id"] == contract_id
    assert data["contract"]["title"] == "Test API"


def test_get_governance_context_cross_client_contract_rejected(
    client: TestClient,
    admin_headers: dict,
    bcp_dev_headers: dict,
    sample_bcp_client,
    sample_retail_client
):
    # Upload contract to retail-corp
    r_resp = client.post(
        "/api/v1/clients/retail-corp/contracts",
        json={
            "format": "json",
            "raw_content": '{"openapi": "3.0.1", "info": {"title": "Retail API", "version": "1.0"}, "paths": {}}'
        },
        headers=admin_headers
    )
    retail_contract_id = r_resp.json()["id"]

    # Try requesting BCP governance context pointing to retail-corp's contract
    response = client.get(
        f"/api/v1/clients/bcp/governance-context?contract_id={retail_contract_id}",
        headers=bcp_dev_headers
    )
    assert response.status_code == 404
    assert "not found for client 'bcp'" in response.json()["detail"]

