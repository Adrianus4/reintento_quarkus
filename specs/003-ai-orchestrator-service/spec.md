# Feature Specification: Spec 003 — ai-orchestrator-service

**Feature Branch**: `003-ai-orchestrator-service`  
**Created**: 2026-10-21  
**Status**: Draft  
**Version Alignment**: Constitution `v1.3.0` (Principio I: Estilos Adaptativos, Principio II: Capacidades Bajo Demanda & 100% Stateless sin BD forzada, Principio IV: Bóveda Fernet, Principio VIII: LangGraph Resiliente, Principio IX: Bóveda Cifrada e IA Desacoplada sin intermediarios, Principio XI: Observabilidad y Telemetría en Tiempo Real de Tokens y Costos, Principio XII: Human-in-the-Loop, Principio XIII: Puerto 8003, Principio XIV: Mandato de Generación Sin Errores en Quarkus según Pedido)

---

## 1. Executive Summary & Purpose

Implementar el microservicio **`ai-orchestrator-service`** (Puerto `8003`) para **TCS Intelligent Microservice Factory**. Este servicio centraliza:
1. La **Bóveda de Credenciales Cifradas** (Fernet) para almacenar llaves de API de los proveedores de IA sin exponer secretos en texto plano.
2. El **Gateway de Modelos de IA** compatible con Google Gemini, DeepSeek, Grok y Mock, con conmutación en caliente e ingesta directa de proveedor y modelo LLM (`model_name`) sin intermediarios ni tiers de consumo artificiales.
3. El **Motor de Orquestación Multi-Agente con LangGraph** para generar microservicios en Quarkus **sin errores según el pedido del usuario**, respetando estrictamente los inputs técnicos (o Blueprint JSON ingestada): si no se solicita persistencia, el servicio es **100% stateless** (cero Hibernate, cero Panache).
4. Las compuertas de **Supervisión Humana (Human-in-the-Loop - HITL)** para que el desarrollador inspeccione las propuestas de la IA, configure, edite el código en pantalla y apruebe antes de la verificación.
5. La **Telemetría y Observabilidad de Tokens** (`GET /api/v1/orchestrator/consumption`) con registro en tiempo real de tokens de entrada/salida y costos monetarios USD desglosados por proyecto y por proveedor de modelo.

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

### User Story 2 - Gateway de Modelos de IA con Selección Directa de API y Modelo (Priority: P1)

* **Como**: Administrador o Desarrollador de TCS.
* **Quiero**: Configurar directamente la API Key del proveedor (Gemini, DeepSeek, Grok, Mock) y especificar el modelo deseado sin intermediación de modos o niveles de consumo artificiales.
* **Para**: Tener control explícito sobre el modelo de lenguaje invocado y simplificar la gestión operativa sin romper la compatibilidad hacia atrás del código.
* **Prueba Independiente**: Se actualiza la configuración vía `PUT /api/v1/ai-gateway/config` enviando `active_provider` y `model_name`; la siguiente petición de generación invoca directamente dicho modelo.

**Criterios de Aceptación**:
1. **Given** una configuración enviada a `PUT /api/v1/ai-gateway/config`, **Then** los agentes actualizan su proveedor y modelo activo directamente.
2. **Given** la eliminación de los niveles o modos de consumo (`economic`, `balanced`, `advanced`), **Then** el sistema permite ingestar directamente la API Key y el nombre de modelo (ej. `gemini-2.5-flash`, `deepseek-chat`, `grok-beta`) conservando valores por defecto tolerantes para compatibilidad de esquemas previos.
3. **Given** el proveedor `mock`, **Then** opera offline de forma determinista para desarrollo y pruebas locales.

---

### User Story 3 - Motor de Generación Multi-Agente LangGraph con Ingestión de Blueprint o Redacción Libre (Priority: P1)

* **Como**: Desarrollador de TCS autorizado para un cliente (ej. `ibk`, `bcp`).
* **Quiero**: Al inicio, elegir entre redactar libremente lo que deseo construir o ingestar un Blueprint JSON existente para pre-poblar y sincronizar todas las fases técnicas del microservicio (arquitectura, seguridad, endpoints, base de datos y extensiones), pudiendo editarlas libremente; o en su defecto, ir dando forma paso a paso conforme avanzo por las fases.
* **Para**: Adecuar con precisión milimétrica el microservicio en Quarkus sin fallas, con total flexibilidad de entrada y control de ingeniería.

---

### User Story 5 - Módulo de Telemetría de Consumo de Tokens y Costos por Proyecto y Proveedor (Priority: P1)

* **Como**: Colaborador o Administrador de TCS.
* **Quiero**: Consultar el registro detallado de tokens consumidos acumulados y por proyecto/microservicio, así como el desglose consolidado por proveedor de modelo de IA (Gemini, DeepSeek, Grok, Mock).
* **Para**: Auditar el gasto en tokens (entrada/salida), costos en USD y volumen de generación de la plataforma.
* **Prueba Independiente**: Se invoca `GET /api/v1/orchestrator/consumption` y el sistema retorna un resumen consolidado con KPIs globales, desglose por proveedor y lista histórica de consumos por proyecto.

---

### User Story 3 - Motor de Generación Multi-Agente LangGraph con Libertad Total de Inputs y Configuración (Priority: P1)

* **Como**: Desarrollador de TCS autorizado para un cliente (ej. `ibk`, `bcp`).
* **Quiero**: Ingresar libremente mis requerimientos y parametrizar cada dimensión técnica del microservicio mediante campos de entrada (*inputs*) editables:
  - **Inputs de Proyecto & Herramienta de Construcción**: Cliente (`client_code`), herramienta de compilación (`build_tool`: Maven vs Gradle), nombre del microservicio (`artifact_id`), prefijo de paquete (`package_prefix`), puerto HTTP (`http_port`), versión Java (`java_version`: 21 / 17 LTS) y versión Quarkus (`quarkus_version`: 3.15.1).
  - **Inputs de Arquitectura & Patrones de Diseño**: Arquetipo (`architecture_style`: Hexagonal, Clean, Layered, EDA), patrones seleccionables (`design_patterns`: Repository, Builder, Saga, Outbox, Strategy, Factory) y convenciones de código (`naming_conventions`: camelCase, PascalCase, sufijos UseCase, Port, Adapter).
  - **Inputs de Seguridad**: Mecanismo de autenticación (`security_option`), emisor JWT/OIDC (`jwt_issuer`) y roles autorizados (`security_roles`).
  - **Inputs de Endpoints**: Lista de endpoints HTTP personalizados (`custom_endpoints`) con método, ruta, código de estado y descripción.
  - **Inputs de Persistencia**: Motor de base de datos (`database_option`), nombre de base de datos (`database_name`) y definición dinámica de entidades y campos tipados (`entities`).
  - **Inputs de Extensiones y Propiedades**: Inyección de extensiones Quarkus predefinidas y libres (`custom_extensions`), y propiedades clave-valor adicionales (`custom_properties`).
  - **Input de Reglas de Negocio**: Especificación funcional en lenguaje natural (`requirements`).
* **Para**: Adecuar con precisión milimétrica el microservicio en Quarkus a los requerimientos de la cuenta bancaria sin fallas, sin suposiciones no justificadas y con total control del desarrollador.
* **Prueba Independiente**: Se inicia un trabajo de generación vía `POST /api/v1/orchestrator/jobs` enviando el payload completo con los inputs personalizados; el grafo LangGraph inyecta estas especificaciones en el blueprint, `pom.xml`, `application.properties`, clases de dominio, adaptadores REST y pruebas unitarias/integración.

**Criterios de Aceptación**:
1. **Given** una solicitud con los inputs personalizados del desarrollador, **When** se crea el trabajo, **Then** el orquestador valida el acceso al cliente y almacena la configuración completa en `JobState` y en `generation_jobs.blueprint_json`.
2. **Given** la existencia de endpoints personalizados (`custom_endpoints`) y entidades (`entities`), **Then** el generador produce los recursos REST correspondientes con sus paths exactos, DTOs y persistencia asociada.
3. **Given** extensiones libres (`custom_extensions`) y propiedades (`custom_properties`), **Then** el generador las incorpora en `pom.xml` y `application.properties` sin generar conflictos de dependencias.
4. **Given** la finalización de los nodos, **Then** el trabajo queda en estado `AWAITING_REVIEW` con telemetría de tokens consumidos, tiempo y costo estimado en USD, listo para inspección en el CodeViewer (HITL).

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
