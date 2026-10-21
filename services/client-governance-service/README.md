# TCS Intelligent Microservice Factory — Client Governance Service

Microservice dedicated to managing dynamic client account profiles, cataloging versioned technical directives, and ingesting OpenAPI contracts.

- **Port**: `8002`
- **Swagger Documentation**: `http://localhost:8002/docs`
- **Constitution Version**: `1.2.0`

## Features

1. **Client Account Governance**: Dynamic management of client configurations (package prefixes, Java 17/21, Quarkus 3.x BOM versions).
2. **Deterministic Directives**: Formal catalog of architectural, security, testing, and naming policies with severity categorization (`MANDATORY`, `RECOMMENDED`, `OPTIONAL`).
3. **OpenAPI/Swagger Ingestion**: Parsing, endpoints count calculation, and structural validation of OpenAPI 3.x specifications (JSON/YAML).
4. **Tenant Isolation**: Developer access is hermetically restricted to authorized clients via inter-service token validation (`auth-access-service:8001`).
5. **Zero Client Hardcoding**: Neutral platform core with no hardcoded client rules or namespaces.

## Quickstart

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --port 8002 --reload
```

## Running Tests

```bash
pytest -v
```

