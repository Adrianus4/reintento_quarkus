from fastapi.testclient import TestClient

SAMPLE_VALID_POM = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.bcp</groupId>
  <artifactId>sample-service</artifactId>
  <version>1.0.0</version>
</project>
"""

SAMPLE_VALID_JAVA = """package com.bcp;

public class SampleAccount {
    private String id;
    public SampleAccount(String id) {
        this.id = id;
    }
}
"""

SAMPLE_INVALID_JAVA = """package com.bcp;

public class BrokenAccount {
    // Missing closing brace
    public void execute() {
        System.out.println("broken");
"""


def test_compiler_success(client: TestClient, bcp_dev_headers: dict, monkeypatch):
    # HTTP contract fixture; native Java compilation is exercised separately.
    from app.core import compiler
    from unittest.mock import Mock
    monkeypatch.setattr(compiler,'get_maven_binary',lambda:'/usr/bin/mvn')
    monkeypatch.setattr(compiler.subprocess,'run',Mock(return_value=Mock(returncode=0,stdout='BUILD SUCCESS',stderr='')))
    payload = {
        "client_code": "bcp",
        "files": {
            "pom.xml": SAMPLE_VALID_POM,
            "src/main/java/com/bcp/SampleAccount.java": SAMPLE_VALID_JAVA
        }
    }
    response = client.post("/api/v1/verifier/runs", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "BUILD SUCCESS" in data["compilation_output"]


def test_compiler_missing_pom_fails(client: TestClient, bcp_dev_headers: dict):
    payload = {
        "client_code": "bcp",
        "files": {
            "src/main/java/com/bcp/SampleAccount.java": SAMPLE_VALID_JAVA
        }
    }
    response = client.post("/api/v1/verifier/runs", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPILATION_FAILED"
    assert "pom.xml not found" in data["compilation_output"]


def test_compiler_syntax_error_fails(client: TestClient, bcp_dev_headers: dict):
    payload = {
        "client_code": "bcp",
        "files": {
            "pom.xml": SAMPLE_VALID_POM,
            "src/main/java/com/bcp/BrokenAccount.java": SAMPLE_INVALID_JAVA
        }
    }
    response = client.post("/api/v1/verifier/runs", json=payload, headers=bcp_dev_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPILATION_FAILED"
    assert "unbalanced braces" in data["compilation_output"]

