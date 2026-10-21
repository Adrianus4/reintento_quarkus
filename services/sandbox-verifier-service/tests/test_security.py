from fastapi.testclient import TestClient


def test_path_traversal_detection_parent_dir(client: TestClient, bcp_dev_headers: dict):
    payload = {
        "client_code": "bcp",
        "files": {
            "../../etc/passwd": "malicious content",
            "pom.xml": "<project></project>"
        }
    }
    response = client.post("/api/v1/verifier/runs", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 400
    assert "Path traversal detected" in response.json()["detail"]


def test_path_traversal_detection_absolute_path(client: TestClient, bcp_dev_headers: dict):
    payload = {
        "client_code": "bcp",
        "files": {
            "/root/secret.txt": "malicious content"
        }
    }
    response = client.post("/api/v1/verifier/runs", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 400
    assert "Path traversal detected" in response.json()["detail"] or "Absolute paths" in response.json()["detail"]
