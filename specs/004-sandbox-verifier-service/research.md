# Phase 0 Research: Spec 004 — sandbox-verifier-service

## 1. Technical Decisions & Trade-Offs

### 1.1 Architecture & Boundaries
- **Decision**: Standalone FastAPI service running on port `8004`.
- **Rationale**: Keeps compiler execution, process spawning, file I/O, and disk storage completely isolated from the AI generation and user governance layers.
- **Port**: `8004`
- **Swagger Documentation**: `http://localhost:8004/docs`

### 1.2 Ephemeral Workspace & Path Traversal Security
- **Directory**: `sandbox_runs/{run_id}/` created per run.
- **Security Check**:
  ```python
  resolved = (base_dir / file_path).resolve()
  if not resolved.is_relative_to(base_dir.resolve()):
      raise ValueError("Path traversal attempt detected")
  ```
  Any attempt to write outside `sandbox_runs/{run_id}` is blocked with `400 Bad Request`.

### 1.3 Compilation Execution Strategy
- **Primary**: Native Maven command `mvn -B clean test-compile` via `subprocess.run` with a configurable timeout (120 seconds).
- **Resilient Fallback**: If Maven is not installed on the host or lightweight container, an internal deterministic Java syntax and Quarkus BOM validator parses the Java files and `pom.xml`, verifying syntactic correctness, valid package declarations, and dependency presence without failing on missing local JDKs.

### 1.4 Cryptographic Verification Manifest (`VERIFICATION_MANIFEST.json`)
- **Principio XIV**: Manifiesto Criptográfico con hashes SHA-256.
- **Algorithm**: `hashlib.sha256` applied to binary file content.
- **Location**: Written into `{workspace}/VERIFICATION_MANIFEST.json` and bundled in the `.zip`.

### 1.5 Packaging & Download
- **Format**: Standard ZIP archive using `zipfile.ZIP_DEFLATED`.
- **Serving**: Streaming or `fastapi.responses.FileResponse` with `Content-Disposition: attachment; filename="{client_code}-microservice.zip"`.

---

## 2. Directory Layout Decision

```text
services/sandbox-verifier-service/
├── app/
│   ├── api/
│   │   ├── deps.py               # Token verification & client authorization
│   │   └── v1/
│   │       ├── api.py            # Central router
│   │       └── verifier.py       # /verifier/runs (Create, Verify, Manifest, Download)
│   ├── core/
│   │   ├── config.py             # Port 8004, SANDBOX_BASE_PATH, DB_URL
│   │   ├── database.py           # SQLAlchemy 2.0
│   │   ├── compiler.py           # Maven runner & resilient syntax verifier
│   │   ├── manifest.py           # SHA-256 hash generator & manifest writer
│   │   └── packager.py           # Zip compression utility
│   ├── models/
│   │   ├── __init__.py
│   │   └── run.py                # VerificationRun model
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── verifier.py           # RunCreateRequest, RunResponse, ManifestResponse
│   └── main.py                   # FastAPI app entrypoint
├── tests/
│   ├── conftest.py               # Test fixtures & mock tokens
│   ├── test_security.py          # Path traversal security tests
│   ├── test_compiler.py          # Compilation runner tests
│   ├── test_manifest.py          # SHA-256 manifest tests
│   └── test_verifier.py          # End-to-end verification and download tests
├── requirements.txt
├── Dockerfile
└── README.md
```

