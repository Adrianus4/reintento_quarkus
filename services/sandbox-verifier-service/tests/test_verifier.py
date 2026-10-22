from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "sandbox-verifier-service"
    assert data["port"] == 8004


def test_end_to_end_verification_and_download(client: TestClient, bcp_dev_headers: dict, monkeypatch):
    # Exercise the HTTP/ZIP contract with an explicit successful native-process stub.
    from app.core import compiler
    from unittest.mock import Mock
    monkeypatch.setattr(compiler,'get_maven_binary',lambda:'/usr/bin/mvn')
    monkeypatch.setattr(compiler.subprocess,'run',Mock(return_value=Mock(returncode=0,stdout='BUILD SUCCESS',stderr='')))
    payload = {
        "client_code": "bcp",
        "files": {
            "pom.xml": """<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.bcp</groupId>
  <artifactId>sample-service</artifactId>
  <version>1.0.0</version>
</project>""",
            "src/main/java/com/bcp/App.java": "package com.bcp;\npublic class App {}"
        }
    }
    create_resp = client.post("/api/v1/verifier/runs", json=payload, headers=bcp_dev_headers)
    assert create_resp.status_code == 201
    run_id = create_resp.json()["id"]

    # Check run status
    get_resp = client.get(f"/api/v1/verifier/runs/{run_id}", headers=bcp_dev_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == run_id

    # Download ZIP
    dl_resp = client.get(f"/api/v1/verifier/runs/{run_id}/download", headers=bcp_dev_headers)
    assert dl_resp.status_code == 200
    assert dl_resp.headers["content-type"] == "application/zip"
    assert len(dl_resp.content) > 0


def test_download_blocked_by_veto_on_defect(client: TestClient, bcp_dev_headers: dict):
    """Verify that a broken project triggers Sandbox Veto and blocks download with HTTP 403."""
    payload = {
        "client_code": "bcp",
        "files": {
            "pom.xml": """<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.bcp</groupId>
  <artifactId>sample-service</artifactId>
  <version>1.0.0</version>
</project>""",
            "src/main/java/com/bcp/BrokenApp.java": "package com.bcp;\npublic class BrokenApp { // missing brace"
        }
    }
    create_resp = client.post("/api/v1/verifier/runs", json=payload, headers=bcp_dev_headers)
    assert create_resp.status_code == 201
    run_data = create_resp.json()
    assert run_data["status"] == "COMPILATION_FAILED"
    assert run_data["verdict"] == "FAILED"
    assert run_data["veto_applied"] is True

    # Attempt download should be forbidden by Veto
    dl_resp = client.get(f"/api/v1/verifier/runs/{run_data['id']}/download", headers=bcp_dev_headers)
    assert dl_resp.status_code == 403
    assert "ARTEFACTO VETADO" in dl_resp.json()["detail"]


def test_client_isolation_forbidden(client: TestClient, bcp_dev_headers: dict, retail_dev_headers: dict):
    # BCP dev creates run
    payload = {
        "client_code": "bcp",
        "files": {
            "pom.xml": "<project></project>"
        }
    }
    create_resp = client.post("/api/v1/verifier/runs", json=payload, headers=bcp_dev_headers)
    run_id = create_resp.json()["id"]

    # Retail dev tries reading BCP run -> 403
    forbidden_resp = client.get(f"/api/v1/verifier/runs/{run_id}", headers=retail_dev_headers)
    assert forbidden_resp.status_code == 403
