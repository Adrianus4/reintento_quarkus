# Implementation Plan: Spec 004 — sandbox-verifier-service

**Branch**: `004-sandbox-verifier-service` | **Date**: 2026-10-21 | **Spec**: [specs/004-sandbox-verifier-service/spec.md](specs/004-sandbox-verifier-service/spec.md)

**Input**: Feature specification from `specs/004-sandbox-verifier-service/spec.md`

## Summary

Implement the dedicated `sandbox-verifier-service` microservice running on port `8004` for the **TCS Intelligent Microservice Factory**. It delivers an isolated ephemeral execution workspace, executes real Maven compilation (`mvn -B clean test-compile`) or resilient deterministic syntax checks, generates the cryptographic SHA-256 manifest (`VERIFICATION_MANIFEST.json`) adhering to Constitution Principle XIV, and packages the complete microservice as a downloadable `.zip`.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (0.111+), Uvicorn, Pydantic v2, SQLAlchemy 2.0, PyJWT, python-dotenv
**Storage**: SQLAlchemy 2.0 with SQLite (`verifier_factory_local.db`) / PostgreSQL via `DATABASE_URL`
**Testing**: pytest, pytest-asyncio, httpx
**Target Platform**: Linux / Windows / Azure Container Apps (Port 8004)
**Project Type**: Microservice (REST API + Compiler execution)
**Performance Goals**: File materialization & SHA-256 generation < 200ms
**Constraints**: Absolute path traversal security; zero fake verification outcomes

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post-design.*

| Principle | Compliance Assessment | Status |
|---|---|---|
| **VI. Calidad Verificable** | Ejecución real de compilación y pruebas en sandbox efímero aislado sin mocks. | PASS |
| **XIII. Arquitectura Fábrica** | Puerto formal 8004, microservicio desacoplado en `services/sandbox-verifier-service/`. | PASS |
| **XIV. Manifiesto Criptográfico** | Generación determinista de `VERIFICATION_MANIFEST.json` con SHA-256 de todos los archivos fuente. | PASS |

## Project Structure

### Source Code Layout

```text
services/sandbox-verifier-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py
│   │       └── verifier.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── compiler.py
│   │   ├── manifest.py
│   │   └── packager.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── run.py
│   └── schemas/
│       ├── __init__.py
│       └── verifier.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_security.py
│   ├── test_compiler.py
│   ├── test_manifest.py
│   └── test_verifier.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Complexity Tracking

> **No Constitution violations detected.** Clean isolation for compiler execution and zip archiving.
