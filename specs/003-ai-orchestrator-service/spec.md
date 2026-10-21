# Feature Specification: Spec 003 — ai-orchestrator-service

**Feature Branch**: `003-ai-orchestrator-service`  
**Created**: 2026-10-21  
**Status**: Draft  
**Version Alignment**: Constitution `v1.2.0` (Principio I: Estilos Adaptativos, Principio II: Capacidades Bajo Demanda, Principio IV: Bóveda de Credenciales Cifradas, Principio VIII: LangGraph Resiliente, Principio IX: Capa Flexible de IA con Gemini/DeepSeek/Grok, Principio XII: Human-in-the-Loop, Principio XIII: Puerto 8003)

---

## 1. Executive Summary & Purpose

Implementar el microservicio **`ai-orchestrator-service`** (Puerto `8003`) para **TCS Intelligent Microservice Factory**. Este servicio centraliza:
1. La **Bóveda de Credenciales Cifradas** (Fernet) para gestionar con seguridad las API Keys de los proveedores de IA sin exponer secretos en texto plano.
2. El **Gateway de Modelos de IA** compatible con Google Gemini, DeepSeek y Grok, con conmutación en caliente y modos de consumo (`economic`, `balanced`, `advanced`).
3. El **Motor de Orquestación Multi-Agente con LangGraph** con contexto acumulativo, selección de arquitectura no monolítica (Hexagonal, En Capas, Event-Driven, BFF, gRPC), generación de Java/Quarkus con pruebas automatizadas, control de presupuesto de tokens y parser JSON resiliente.
4. Las compuertas de **Supervisión Humana (Human-in-the-Loop)** para que los colaboradores de TCS puedan inspeccionar, editar código generado y aprobarlo antes de la verificación.

---

## 2. User Scenarios & Prioritized User Stories

### User Story 1 - Bóveda de Credenciales Cifradas y Conectividad Multi-Proveedor (Priority: P1)

* **Como**: Administrador de TCS.
* **Quiero**: Guardar, rotar y verificar el estado de las credenciales de los proveedores de IA (Gemini, DeepSeek, Grok) mediante cifrado en reposo.
* **Para**: Garantizar que las llaves corporativas nunca se expongan en texto plano, logs ni interfaces.
* **Prueba Independiente**: Se registra una API Key vía `POST /api/v1/vault/keys`; se guarda cifrada con Fernet; la consulta `GET /api/v1/vault/keys` retorna la llave enmascarada (`sk-****1234`), y `POST /api/v1/vault/test-connection` valida la comunicación.

**Criterios de Aceptación**:
1. **Given** un token `ADMIN`, **When** envía `POST /api/v1/vault/keys` con `provider` y `api_key`, **Then** la llave se cifra con Fernet usando `VAULT_MASTER_KEY` y se guarda en base de datos.
2. **Given** cualquier consulta al endpoint de la bóveda, **Then** la API Key NUNCA se expone completa en respuestas JSON ni logs (únicamente prefijo y sufijo: `AIza...98a`).
3. **Given** un intento de probar conectividad (`POST /api/v1/vault/test-connection`), **Then** el gateway envía una sonda ligera al proveedor y retorna `{ "status": "connected", "latency_ms": 120 }`.
4. **Given** un Desarrollador no administrador, **When** intenta modificar credenciales en la bóveda, **Then** responde `403 Forbidden`.

---

### User Story 2 - Gateway de Modelos de IA con Conmutación en Caliente (Priority: P1)

* **Como**: Administrador o Desarrollador de TCS.
* **Quiero**: Seleccionar el proveedor activo (Gemini, DeepSeek o Grok) y el modo de consumo (`economic`, `balanced`, `advanced`) sin reiniciar el servicio.
* **Para**: Adaptar el rendimiento y los costos de generación según la complejidad del microservicio.
* **Prueba Independiente**: Se actualiza la configuración a proveedor `deepseek` y modo `balanced`; la siguiente petición de generación utiliza el modelo asignado a ese perfil de consumo.

**Criterios de Aceptación**:
1. **Given** una configuración enviada a `PUT /api/v1/ai-gateway/config`, **Then** los agentes actualizan su proveedor y modelo activo en caliente.
2. **Given** el modo `economic`, **Then** se asignan modelos rápidos y económicos (ej. `gemini-2.5-flash-lite`, `deepseek-chat`).
3. **Given** el modo `balanced`, **Then** se asigna el modelo estándar balanceado (ej. `gemini-2.5-flash`, `deepseek-chat`).
4. **Given** el modo `advanced`, **Then** se asigna el modelo de razonamiento superior (ej. `gemini-2.5-pro`, `deepseek-reasoner`).

---

### User Story 3 - Motor de Generación Multi-Agente LangGraph (Priority: P1)

* **Como**: Desarrollador de TCS autorizado para un cliente.
* **Quiero**: Ingresar requerimientos funcionales y el ID de un contrato OpenAPI catalogado en `client-governance-service:8002` para generar un microservicio Quarkus completo.
* **Para**: Obtener código modular, estructurado, con pruebas unitarias (`JUnit 5`), pruebas de integración (`@QuarkusTest` / RestAssured), dependencias limpias y workflow de CI/CD.
* **Prueba Independiente**: Se inicia un trabajo de generación vía `POST /api/v1/orchestrator/jobs`; el grafo LangGraph ejecuta los nodos (Blueprint -> Scaffolding -> Dominio -> Pruebas), acumulando contexto y entregando un árbol de archivos completo con telemetría de tokens y costo en USD.

**Criterios de Aceptación**:
1. **Given** una solicitud con `client_code`, `requirements` y `contract_id`, **When** se crea el trabajo, **Then** el orquestador consulta la gobernanza consolidada en `client-governance-service:8002` y rechaza la ejecución si el desarrollador no está asignado al cliente.
2. **Given** el nodo de Blueprint, **Then** el motor selecciona justificadamente el estilo arquitectónico (`Hexagonal`, `Layered`, `Event-Driven`, `BFF` o `gRPC`) según las directivas y requerimientos, prohibiendo forzar librerías o persistencia no solicitadas (Principio I y II).
3. **Given** respuestas del modelo de IA, **Then** el parser resiliente extrae bloques JSON válidos, auto-completa delimitadores si ocurren truncamientos y garantiza `maxOutputTokens >= 8192`.
4. **Given** la finalización de los nodos, **Then** el trabajo queda en estado `AWAITING_REVIEW` con telemetría de tokens consumidos, tiempo y costo estimado en USD.

---

### User Story 4 - Supervisión Humana (Human-in-the-Loop) y Aprobación (Priority: P2)

* **Como**: Desarrollador de TCS.
* **Quiero**: Inspeccionar el código generado, editar directamente cualquier archivo Java/configuración en la plataforma y aprobar el microservicio antes de enviarlo a verificación.
* **Para**: Mantener el control de ingeniería y corregir cualquier detalle antes de la compilación en sandbox efímero.
* **Prueba Independiente**: El desarrollador consulta los archivos con `GET /api/v1/orchestrator/jobs/{id}`, modifica un archivo con `PATCH /api/v1/orchestrator/jobs/{id}/files` y aprueba el resultado con `POST /api/v1/orchestrator/jobs/{id}/approve`.

**Criterios de Aceptación**:
1. **Given** un trabajo en estado `AWAITING_REVIEW`, **When** el Desarrollador envía `PATCH /api/v1/orchestrator/jobs/{id}/files` con `{ "path": "src/...", "content": "..." }`, **Then** el archivo se actualiza en el estado del trabajo.
2. **Given** un trabajo revisado, **When** el Desarrollador invoca `POST /api/v1/orchestrator/jobs/{id}/approve`, **Then** el estado pasa a `APPROVED`, quedando listo para el `sandbox-verifier-service:8004`.
3. **Given** un Desarrollador no asignado al cliente del trabajo, **When** intenta consultar o modificar el trabajo, **Then** responde `403 Forbidden`.

---

## 3. Requerimientos Funcionales y No Funcionales

* **FR-001**: Microservicio en puerto `8003` con Swagger en `/docs` y salud en `GET /api/v1/health`.
* **FR-002**: Bóveda criptográfica usando `cryptography.fernet.Fernet` para almacenar credenciales de IA.
* **FR-003**: Adaptadores desacoplados de LLM para Google Gemini, DeepSeek y Grok.
* **FR-004**: Parser JSON robusto con tolerancia a bloques markdown (````json ... ````) y auto-reparación de llaves/corchetes incompletos.
* **FR-005**: Estado tipado de LangGraph: `JobState` con `requirements`, `governance`, `blueprint`, `files`, `telemetry`, `status`.
* **FR-006**: Modo Simulado / Mock Provider para pruebas automatizadas herméticas sin consumir API Keys reales en tests.
* **NFR-001**: Respuesta de la bóveda de credenciales < 10 ms.
* **NFR-002**: Persistencia SQLite (`orchestrator_factory_local.db`) / PostgreSQL conmutables vía `DATABASE_URL`.
* **NFR-003**: Cero credenciales expuestas en texto plano.
