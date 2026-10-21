# Phase 0 Research: Spec 002 — client-governance-service

## 1. Technical Decisions & Trade-Offs

### 1.1 Architecture & Service Boundaries
- **Decision**: Standalone FastAPI service running on port `8002`.
- **Rationale**: Isolates client configuration, enterprise architectural standards, and OpenAPI specifications from generation engines, strictly respecting Constitution Principle XIII.
- **Port**: `8002`
- **Swagger Documentation**: `http://localhost:8002/docs`

### 1.2 Inter-Service Authentication & Tenant Isolation
- **Decision**: Validate authorization tokens against `auth-access-service` (`PORT 8001`) via `POST /api/v1/auth/verify` or via shared symmetric JWT verification (`JWT_SECRET_KEY`) with role and assigned client claims inspection.
- **Access Rule**:
  - `ADMIN`: Access to all clients (`["*"]`).
  - `DEVELOPER`: Access restricted strictly to client codes listed in `assigned_clients`. Any attempt to read or modify a client not in `assigned_clients` returns `403 Forbidden`.

### 1.3 OpenAPI / Swagger Ingestion & Validation
- **Decision**: Support both JSON and YAML OpenAPI specifications.
- **Validation**:
  - Requires `openapi: 3.x.x` (or `swagger: 2.0` rejected with upgrade advice).
  - Validates `info.title`, `info.version`, and `paths` dictionary.
  - Automatically computes endpoints/operations count.
  - Stores the raw content for faithful reproduction during microservice scaffolding.

### 1.4 Directives & Deterministic Standards
- **Decision**: Categorize technical rules into `SECURITY`, `ARCHITECTURE`, `NAMING`, `TESTING`, and `OBSERVABILITY`.
- **Severity Levels**:
  - `MANDATORY`: Non-negotiable rules; must be checked deterministically.
  - `RECOMMENDED`: Strong suggestions injected into AI prompts.
  - `OPTIONAL`: User-selectable capabilities.
- **Zero Client Hardcoding (Principio V)**:
  - BCP is purely a test/seed account. All rules, naming conventions, and package prefixes are dynamically fetched from the database.

---

## 2. Directory Layout Decision

```text
services/client-governance-service/
├── app/
│   ├── api/
│   │   ├── deps.py               # Token verification & client access check dependencies
│   │   └── v1/
│   │       ├── api.py            # Aggregated router
│   │       ├── clients.py        # /clients (CRUD)
│   │       ├── directives.py     # /clients/{code}/directives (Catalog & Versioning)
│   │       ├── contracts.py      # /clients/{code}/contracts (OpenAPI storage & validation)
│   │       └── governance.py     # /clients/{code}/governance-context (Consolidated bundle)
│   ├── core/
│   │   ├── config.py             # Port 8002, DB_URL, Auth service URL, JWT Secret
│   │   └── database.py           # SQLAlchemy 2.0 engine & SessionLocal
│   ├── models/
│   │   ├── client.py             # ClientProfile model
│   │   ├── directive.py          # TechnicalDirective model
│   │   └── contract.py           # OpenApiContract model
│   ├── schemas/
│   │   ├── client.py             # ClientCreate, ClientUpdate, ClientResponse
│   │   ├── directive.py          # DirectiveCreate, DirectiveResponse
│   │   ├── contract.py           # ContractUploadRequest, ContractResponse
│   │   └── governance.py         # GovernanceContextResponse
│   └── main.py                   # FastAPI app entrypoint
├── tests/
│   ├── conftest.py               # In-memory DB, mocked auth helpers, test client
│   ├── test_clients.py           # Client profile CRUD and isolation tests
│   ├── test_directives.py        # Directives catalog and validation tests
│   ├── test_contracts.py         # OpenAPI upload, parsing and validation tests
│   └── test_governance.py        # Consolidated governance context bundle tests
├── requirements.txt
├── Dockerfile
└── README.md
```

