import hashlib
from fastapi.testclient import TestClient


def test_sha256_manifest_integrity(client: TestClient, bcp_dev_headers: dict):
    pom_content = "<project>hello</project>"
    java_content = "package com.bcp;\npublic class A {}"

    expected_pom_sha = hashlib.sha256(pom_content.encode("utf-8")).hexdigest()
    expected_java_sha = hashlib.sha256(java_content.encode("utf-8")).hexdigest()

    payload = {
        "client_code": "bcp",
        "files": {
            "pom.xml": pom_content,
            "src/main/java/com/bcp/A.java": java_content
        }
    }
    response = client.post("/api/v1/verifier/runs", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 201
    run_id = response.json()["id"]

    manifest_resp = client.get(f"/api/v1/verifier/runs/{run_id}/manifest", headers=bcp_dev_headers)
    assert manifest_resp.status_code == 200
    manifest = manifest_resp.json()

    files_map = {f["path"]: f["sha256"] for f in manifest["files"]}
    assert files_map["pom.xml"] == expected_pom_sha
    assert files_map["src/main/java/com/bcp/A.java"] == expected_java_sha

