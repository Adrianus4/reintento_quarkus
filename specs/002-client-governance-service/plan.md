# Implementation Plan: Spec 002 — client-governance-service

**Branch**: `002-client-governance-service` | **Date**: 2026-10-21 | **Spec**: [specs/002-client-governance-service/spec.md](specs/002-client-governance-service/spec.md)

**Input**: Feature specification from `specs/002-client-governance-service/spec.md`

## Summary

Implement the dedicated `client-governance-service` microservice running on port `8002` for the **TCS Intelligent Microservice Factory**. It provides dynamic management of enterprise client profiles (Java/Quarkus versions, package namespaces), technical architectural directives with deterministic checks, OpenAPI/Swagger contract parsing and storage, and delivers the consolidated governance bundle for AI microservice generation, enforcing strict multi-tenant client isolation with **zero hardcoded clients**.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (0.111+), Uvicorn, Pydantic v2, PyYAML, SQLAlchemy 2.0, PyJWT, httpx, python-dotenv
**Storage**: SQLAlchemy 2.0 with SQLite (`governance_factory_local.db`) / PostgreSQL via `DATABASE_URL`
**Testing**: pytest, pytest-asyncio, httpx
**Target Platform**: Linux / Windows / Azure Container Apps (Port 8002)
**Project Type**: Microservice (REST API)
**Performance Goals**: Governance bundle compilation < 50ms, CRUD operations < 100ms
**Constraints**: Zero hardcoded clients (BCP is purely a seed/test profile); Developer isolation strictly enforced

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post-design.*

| Principle | Compliance Assessment | Status |
|---|---|---|
| **III. Cumplimiento Normativo** | Directivas técnicas versionadas formalmente por cliente con categorías y severidades deterministas. | PASS |
| **IV. Control de Accesos (RBAC)** | Validación de tokens contra `auth-access-service` e inspección de clientes asignados (`assigned_clients`). | PASS |
| **V. Plataforma Agnóstica** | Zero hardcoding. Los perfiles de clientes son 100% dinámicos en base de datos. Ningún cliente quemado. | PASS |
| **VI. Calidad Verificable** | Suite completa de pruebas unitarias y de integración con SQLite en memoria y TestClient. | PASS |
| **XIII. Arquitectura Fábrica** | Puerto formal 8002, microservicio independiente en `services/client-governance-service/`. | PASS |
| **XIV. Veracidad y Estado Limpio** | Zero preloaded data. Arranque limpio sin datos simulados obligatorios. | PASS |

## Project Structure

### Documentation (this feature)

```text
specs/002-client-governance-service/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (entities, ERD, and schemas)
├── quickstart.md        # Phase 1 output (local execution & test guide)
├── contracts/           # Phase 1 output (OpenAPI 3.1 specification)
│   └── openapi.json
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code Layout

```text
services/client-governance-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, CORS, tables creation on startup
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Auth verification & tenant access authorization
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py          # Aggregator router
│   │       ├── clients.py      # /clients endpoints
│   │       ├── directives.py   # /clients/{code}/directives endpoints
│   │       ├── contracts.py    # /clients/{code}/contracts endpoints
│   │       └── governance.py   # /clients/{code}/governance-context endpoint
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Port 8002, DATABASE_URL, AUTH_SERVICE_VERIFY_URL
│   │   └── database.py         # SQLAlchemy engine & sessionmaker
│   ├── models/
│   │   ├── __init__.py
│   │   ├── client.py           # ClientProfile model
│   │   ├── directive.py        # TechnicalDirective model
│   │   └── contract.py         # OpenApiContract model
│   └── schemas/
│       ├── __init__.py
│       ├── client.py           # ClientCreate, ClientUpdate, ClientResponse
│       ├── directive.py        # DirectiveCreate, DirectiveResponse
│       ├── contract.py         # ContractUploadRequest, ContractResponse
│       └── governance.py       # GovernanceContextResponse
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Test fixtures & mock tokens
│   ├── test_clients.py         # Client CRUD & RBAC isolation tests
│   ├── test_directives.py      # Directives catalog & validation tests
│   ├── test_contracts.py       # OpenAPI contract upload & parsing tests
│   └── test_governance.py      # Governance context bundle tests
├── requirements.txt
├── Dockerfile
└── README.md
```

## Complexity Tracking

> **No Constitution violations detected.** Clean FastAPI service on Port 8002 with complete multi-tenant client isolation.
