# Implementation Plan: Spec 001 — auth-access-service

**Branch**: `001-auth-access-service` | **Date**: 2026-10-21 | **Spec**: [specs/001-auth-access-service/spec.md](specs/001-auth-access-service/spec.md)

**Input**: Feature specification from `specs/001-auth-access-service/spec.md`

## Summary

Implement the dedicated `auth-access-service` microservice running on port `8001` for the **TCS Intelligent Microservice Factory**. It provides secure authentication, issues signed JWTs, enforces strictly **2 corporate roles** (`ADMIN` and `DEVELOPER`), isolates client account access per developer, exposes an inter-service token verification endpoint (`POST /api/v1/auth/verify`) for the factory microservices suite, and starts with zero preloaded data via an idempotent first-run `/setup-admin` endpoint.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (0.111+), Uvicorn, Pydantic v2, PyJWT, passlib[bcrypt], python-dotenv
**Storage**: SQLAlchemy 2.0 with SQLite (`auth_factory_local.db`) for local development; switchable to PostgreSQL via `DATABASE_URL`
**Testing**: pytest, pytest-asyncio, httpx
**Target Platform**: Linux / Windows / Azure Container Apps (Port 8001)
**Project Type**: Microservice (REST API)
**Performance Goals**: JWT issuance < 250ms, inter-service verification `/api/v1/auth/verify` < 20ms
**Constraints**: Zero hardcoding of client or user names; strictly 2 roles (`ADMIN`, `DEVELOPER`); zero fake preloaded data
**Scale/Scope**: Enterprise multi-tenant user and credential governance across all TCS client projects

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post-design.*

| Principle | Compliance Assessment | Status |
|---|---|---|
| **I. Estilos Adaptativos** | Microservicio REST desacoplado con FastAPI, OpenAPI 3.1 y separación limpia en capas (API, Core, Models, Schemas). | PASS |
| **II. Capacidades Bajo Demanda** | Dependencias mínimas y exactas (FastAPI + SQLAlchemy + PyJWT + Bcrypt). Sin sobreingeniería. | PASS |
| **III. Cumplimiento Normativo** | Verificación determinista de roles (`ADMIN` vs `DEVELOPER`) mediante dependencias inyectadas en FastAPI. | PASS |
| **IV. Control de Accesos (RBAC)** | Modelo estricto de exactamente 2 roles corporativos (`ADMIN` y `DEVELOPER`). Aislamiento de cuentas de clientes por colaborador. | PASS |
| **V. Plataforma Agnóstica** | Zero hardcoding. Los códigos de clientes (`client_code`) son dinámicos en base de datos. Ningún cliente o regla quemada en código. | PASS |
| **VI. Calidad Verificable** | Suite de pruebas unitarias y de integración completas con pytest + httpx. | PASS |
| **XIII. Arquitectura Fábrica** | Puerto formal 8001, microservicio independiente dentro de `services/auth-access-service/`. | PASS |
| **XIV. Veracidad y Estado Limpio** | Zero preloaded data. Arranque limpio con endpoint `/setup-admin` inicial. | PASS |

## Project Structure

### Documentation (this feature)

```text
specs/001-auth-access-service/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (architectural & technical decisions)
├── data-model.md        # Phase 1 output (entities, ERD, and Pydantic schemas)
├── quickstart.md        # Phase 1 output (local execution & test guide)
├── contracts/           # Phase 1 output (OpenAPI 3.1 specification)
│   └── openapi.json
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code Layout

```text
services/auth-access-service/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application setup, CORS, route inclusion
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Auth dependencies: get_current_user, require_admin
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py          # Central v1 router registration
│   │       ├── auth.py         # Endpoints: /login, /setup-admin, /verify, /me, /me/clients
│   │       └── users.py        # Endpoints: /users (list, create, update, assign clients)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # App settings (Pydantic BaseSettings: Port 8001, Secret, etc.)
│   │   ├── security.py         # Password hashing (bcrypt) & JWT operations (PyJWT)
│   │   └── database.py         # SQLAlchemy engine, session maker & declarative base
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User model & UserRole enum (ADMIN, DEVELOPER)
│   │   ├── assignment.py       # UserClientAssignment model
│   │   └── audit.py            # AuditLoginLog model
│   └── schemas/
│       ├── __init__.py
│       ├── auth.py             # Pydantic schemas for Login, Token, Verification
│       └── user.py             # Pydantic schemas for User create, update, list, clients
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # In-memory SQLite fixtures & TestClient
│   ├── test_auth.py            # Tests for /setup-admin, /login, /verify, /me
│   ├── test_users.py           # Tests for user creation, RBAC validation (403 for DEVELOPER)
│   └── test_client_access.py   # Tests for client isolation & assignment
├── requirements.txt            # Frozen Python dependencies
├── Dockerfile                  # Container definition for Port 8001
└── README.md                   # Operational guide
```

**Structure Decision**: Microservicio desacoplado en `services/auth-access-service/` acorde con el Principio XIII de la Constitución.

## Complexity Tracking

> **No Constitution violations detected.** The solution uses the simplest robust architecture (FastAPI + SQLAlchemy) with zero hardcoding and strict 2-role RBAC.
