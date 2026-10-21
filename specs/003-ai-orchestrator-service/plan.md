# Implementation Plan: Spec 003 — ai-orchestrator-service

**Branch**: `003-ai-orchestrator-service` | **Date**: 2026-10-21 | **Spec**: [specs/003-ai-orchestrator-service/spec.md](specs/003-ai-orchestrator-service/spec.md)

**Input**: Feature specification from `specs/003-ai-orchestrator-service/spec.md`

## Summary

Implement the dedicated `ai-orchestrator-service` microservice running on port `8003` for the **TCS Intelligent Microservice Factory**. It delivers a Fernet-encrypted credential vault for Gemini/DeepSeek/Grok, an AI Model Gateway supporting hot provider switching and consumption modes (`economic`, `balanced`, `advanced`), a stateful LangGraph multi-agent generation pipeline (Blueprint -> Scaffolding -> Domain -> Tests) with resilient JSON parsing (`maxOutputTokens >= 8192`), token/cost telemetry, and Human-in-the-Loop inspection, editing, and approval compuertas.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI (0.111+), Uvicorn, Pydantic v2, SQLAlchemy 2.0, cryptography (Fernet), PyJWT, httpx, python-dotenv
**Storage**: SQLAlchemy 2.0 with SQLite (`orchestrator_factory_local.db`) / PostgreSQL via `DATABASE_URL`
**Testing**: pytest, pytest-asyncio, httpx
**Target Platform**: Linux / Windows / Azure Container Apps (Port 8003)
**Project Type**: Microservice (REST API + LangGraph engine)
**Performance Goals**: Vault retrieval < 10ms, Blueprint & Scaffolding generation with Mock engine < 200ms
**Constraints**: Zero plain text API keys in DB or responses; strictly enforce 2-role RBAC and client isolation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post-design.*

| Principle | Compliance Assessment | Status |
|---|---|---|
| **I. Estilos Adaptativos** | El nodo de Blueprint selecciona justificadamente entre Hexagonal, En Capas, Event-Driven, BFF y gRPC. | PASS |
| **II. Capacidades Bajo Demanda** | Sin dependencias ni persistencia forzada. Solo se añaden las extensiones justificadas por requerimientos/directivas. | PASS |
| **IV. Control de Accesos y Bóveda** | Bóveda Fernet cifrada en reposo. Cero secretos en texto plano. RBAC estricto para administración. | PASS |
| **VIII. LangGraph Resiliente** | Flujo con estado tipado `JobState`, acumulación de contexto, límites de presupuesto y parser robusto. | PASS |
| **IX. Capa Flexible de IA** | Conmutación en caliente entre Gemini, DeepSeek, Grok y Mock, con modos economic/balanced/advanced. | PASS |
| **XII. Supervisión Humana** | Human-in-the-loop: Endpoints para inspección de archivos, edición en caliente y aprobación manual. | PASS |
| **XIII. Arquitectura Fábrica** | Puerto formal 8003, microservicio independiente en `services/ai-orchestrator-service/`. | PASS |
| **XIV. Veracidad y Estado Limpio** | Cero credenciales ni proyectos precargados falsos. | PASS |

## Project Structure

### Source Code Layout

```text
services/ai-orchestrator-service/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py
│   │       ├── vault.py
│   │       ├── gateway.py
│   │       └── orchestrator.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── vault.py
│   │   └── parser.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── credential.py
│   │   ├── gateway_config.py
│   │   └── job.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── vault.py
│   │   ├── gateway.py
│   │   └── job.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── factory.py
│   │   ├── mock_client.py
│   │   ├── gemini_client.py
│   │   └── openai_compat.py
│   └── graph/
│       ├── __init__.py
│       ├── state.py
│       ├── nodes.py
│       └── workflow.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_vault.py
│   ├── test_gateway.py
│   ├── test_parser.py
│   └── test_orchestrator.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Complexity Tracking

> **No Constitution violations detected.** Follows clean service separation and stateful graph execution.
