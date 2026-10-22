from fastapi.testclient import TestClient
import pytest
import httpx


@pytest.fixture(autouse=True)
def sandbox_contract_stub(monkeypatch):
    """API contract tests use an explicit verifier stub, not offline success."""
    from app.graph import nodes
    original = nodes.httpx.Client
    def client(*args, **kwargs):
        def respond(request):
            if request.url.path.endswith('/runs'):
                return httpx.Response(201,json={'status':'SUCCESS','verdict':'PASSED','veto_applied':False,'failures':[]})
            return httpx.Response(503)
        return original(transport=httpx.MockTransport(respond))
    monkeypatch.setattr(nodes.httpx,'Client',client)


def test_start_generation_job_end_to_end(client: TestClient, bcp_dev_headers: dict):
    payload = {
        "client_code": "bcp",
        "requirements": "Microservicio de cuentas de ahorro en Java 17 y Quarkus con pruebas RestAssured."
    }
    response = client.post("/api/v1/orchestrator/jobs", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["client_code"] == "bcp"
    assert data["status"] == "AWAITING_REVIEW"
    assert data["architecture_style"] == "Hexagonal"
    assert "pom.xml" in data["files"]
    assert "src/main/resources/application.properties" in data["files"]
    assert data["prompt_tokens"] > 0
    assert data["completion_tokens"] > 0
    assert data["cost_usd"] >= 0.0

    job_id = data["id"]

    # Verify retrieval
    get_resp = client.get(f"/api/v1/orchestrator/jobs/{job_id}", headers=bcp_dev_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == job_id


def test_start_job_client_isolation_forbidden(client: TestClient, retail_dev_headers: dict):
    payload = {
        "client_code": "bcp",
        "requirements": "Unauthorized attempt on BCP account"
    }
    response = client.post("/api/v1/orchestrator/jobs", json=payload, headers=retail_dev_headers)
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_human_in_the_loop_edit_file(client: TestClient, bcp_dev_headers: dict):
    # Create job
    create_resp = client.post(
        "/api/v1/orchestrator/jobs",
        json={"client_code": "bcp", "requirements": "Servicio de transferencias"},
        headers=bcp_dev_headers
    )
    job_id = create_resp.json()["id"]

    # Developer edits a file
    custom_content = "// Custom human developer review adjustment\npackage com.tcs.factory;"
    edit_payload = {
        "files": {
            "src/main/java/com/tcs/factory/domain/model/Account.java": custom_content
        }
    }
    edit_resp = client.patch(
        f"/api/v1/orchestrator/jobs/{job_id}/files",
        json=edit_payload,
        headers=bcp_dev_headers
    )
    assert edit_resp.status_code == 200
    files = edit_resp.json()["files"]
    assert files["src/main/java/com/tcs/factory/domain/model/Account.java"] == custom_content


def test_human_in_the_loop_approve_job(client: TestClient, bcp_dev_headers: dict):
    create_resp = client.post(
        "/api/v1/orchestrator/jobs",
        json={"client_code": "bcp", "requirements": "Servicio de notificaciones"},
        headers=bcp_dev_headers
    )
    job_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "AWAITING_REVIEW"

    # Approve
    approve_resp = client.post(
        f"/api/v1/orchestrator/jobs/{job_id}/approve",
        headers=bcp_dev_headers
    )
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "APPROVED"

