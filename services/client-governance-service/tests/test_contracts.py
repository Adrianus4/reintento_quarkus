from fastapi.testclient import TestClient

SAMPLE_OPENAPI_JSON = """
{
  "openapi": "3.0.3",
  "info": {
    "title": "BCP Card Verification API",
    "version": "1.0.0"
  },
  "paths": {
    "/cards/verify": {
      "post": {
        "summary": "Verify card number"
      }
    },
    "/cards/{id}/status": {
      "get": {
        "summary": "Get card status"
      }
    }
  }
}
"""

SAMPLE_OPENAPI_YAML = """
openapi: 3.1.0
info:
  title: YAML Payment API
  version: 2.1.0
paths:
  /payments:
    post:
      summary: Submit payment
"""


def test_upload_valid_json_contract(client: TestClient, bcp_dev_headers: dict, sample_bcp_client):
    payload = {
        "format": "json",
        "raw_content": SAMPLE_OPENAPI_JSON
    }
    response = client.post("/api/v1/clients/bcp/contracts", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "BCP Card Verification API"
    assert data["version"] == "1.0.0"
    assert data["endpoints_count"] == 2
    assert data["is_valid"] is True


def test_upload_valid_yaml_contract(client: TestClient, bcp_dev_headers: dict, sample_bcp_client):
    payload = {
        "format": "yaml",
        "raw_content": SAMPLE_OPENAPI_YAML
    }
    response = client.post("/api/v1/clients/bcp/contracts", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "YAML Payment API"
    assert data["endpoints_count"] == 1


def test_upload_invalid_swagger_2_rejected(client: TestClient, bcp_dev_headers: dict, sample_bcp_client):
    legacy_swagger = """
    {
      "swagger": "2.0",
      "info": {"title": "Old API", "version": "1.0"},
      "paths": {}
    }
    """
    response = client.post(
        "/api/v1/clients/bcp/contracts",
        json={"format": "json", "raw_content": legacy_swagger},
        headers=bcp_dev_headers
    )
    assert response.status_code == 422
    assert "Swagger 2.0" in response.json()["detail"]


def test_contracts_isolation_for_unassigned_developer(
    client: TestClient,
    retail_dev_headers: dict,
    sample_bcp_client
):
    response = client.get("/api/v1/clients/bcp/contracts", headers=retail_dev_headers)
    assert response.status_code == 403

