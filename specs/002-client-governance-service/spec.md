# Feature Specification: Spec 002 — client-governance-service

**Feature Branch**: `002-client-governance-service`  
**Created**: 2026-10-21  
**Status**: Draft  
**Version Alignment**: Constitution `v1.3.0` (Principio III: Cumplimiento Normativo y Verificación Determinista, Principio V: Plataforma 100% Agnóstica a Clientes - Zero Hardcoding, Principio XIII: Puerto 8002, Principio XIV: Mandato de Generación Sin Errores)

---

## 1. Executive Summary & Purpose

Implementar el microservicio **`client-governance-service`** (Puerto `8002`) para **TCS Intelligent Microservice Factory**. Este servicio gestiona dinámicamente los perfiles de clientes corporativos de TCS, versiona sus directivas técnicas y políticas de arquitectura, cataloga contratos OpenAPI/Swagger y suministra el contexto normativo consolidado a los agentes de IA de la fábrica, garantizando un aislamiento estricto entre cuentas y **cero código hardcodeado** (*zero hardcoding*).

---

## 2. User Scenarios & Prioritized User Stories

### User Story 1 - Gestión Dinámica de Perfiles de Cliente (Priority: P1)

* **Como**: Administrador de TCS.
* **Quiero**: Registrar, actualizar y consultar perfiles de cuentas de clientes (código, nombre, prefijo de paquete Java, versión de Java 17/21 y versión de Quarkus).
* **Para**: Parametrizar dinámicamente cualquier cuenta corporativa sin tocar el código fuente de la fábrica.
* **Por qué esta prioridad**: Es la base del principio multi-cliente y neutralidad de la plataforma.
* **Prueba Independiente**: Un Administrador registra o consulta el perfil del cliente `bcp` o `ibk` (Interbank Perú) vía `POST /api/v1/clients` / `GET /api/v1/clients`, y un Desarrollador autorizado puede consultar su configuración vía `GET /api/v1/clients/{client_code}` con su paquete base (`pe.com.interbank` o `pe.com.bcp`) y directivas específicas de arquitectura, seguridad y datos.

**Criterios de Aceptación**:
1. **Given** un token válido con rol `ADMIN`, **When** envía `POST /api/v1/clients` con datos válidos (`code`, `name`, `package_prefix`, `java_version`, `quarkus_version`), **Then** se crea el perfil y responde `201 Created`.
2. **Given** un intento de registro con un `code` ya existente o formato inválido (debe ser slug minúscula alfanumérico con guiones), **When** se envía la petición, **Then** responde `409 Conflict` o `422 Unprocessable Entity`.
3. **Given** un Desarrollador autenticado, **When** consulta `GET /api/v1/clients`, **Then** solo recibe los clientes a los que tiene acceso asignado según `auth-access-service`.
4. **Given** un Desarrollador que intenta acceder a un `client_code` no asignado, **When** invoca `GET /api/v1/clients/{client_code}`, **Then** responde `403 Forbidden`.

---

### User Story 2 - Catalogación y Versionado de Directivas Técnicas (Priority: P1)

* **Como**: Administrador de TCS.
* **Quiero**: Definir y versionar directivas técnicas por cliente (categorías: `SECURITY`, `ARCHITECTURE`, `NAMING`, `TESTING`, `OBSERVABILITY`; severidad: `MANDATORY`, `RECOMMENDED`, `OPTIONAL`).
* **Para**: Que la fábrica aplique de forma determinista los estándares específicos del cliente seleccionado durante el diseño y generación de microservicios.
* **Por qué esta prioridad**: Cumple el Principio III de la Constitución: las reglas obligatorias deben identificarse, versionarse y no depender de supuestos de la IA.
* **Prueba Independiente**: Se agrega una directiva obligatoria al cliente `bcp`, y al consultar las directivas activas de ese cliente, la regla aparece con su código, versión y verificación determinista.

**Criterios de Aceptación**:
1. **Given** un token `ADMIN`, **When** invoca `POST /api/v1/clients/{client_code}/directives` con `rule_code`, `category`, `severity`, `description` y `deterministic_rule`, **Then** la regla queda guardada y versionada.
2. **Given** un Desarrollador o el servicio orquestador (`ai-orchestrator-service`), **When** consulta `GET /api/v1/clients/{client_code}/directives`, **Then** recibe la lista de directivas activas para ese cliente.
3. **Given** un intento de crear una regla con `rule_code` duplicado para el mismo cliente, **When** se envía la petición, **Then** responde `409 Conflict`.

---

### User Story 3 - Catalogación y Validación de Contratos OpenAPI (Priority: P1)

* **Como**: Desarrollador o Administrador de TCS.
* **Quiero**: Subir y registrar contratos OpenAPI/Swagger (JSON o YAML) asociados a un cliente, verificando automáticamente su validez sintáctica y semántica.
* **Para**: Proporcionar el contrato formal que guiará la generación precisa del microservicio Quarkus.
* **Por qué esta prioridad**: El contrato OpenAPI es el insumo fundamental para diseñar endpoints, DTOs y pruebas de integración.
* **Prueba Independiente**: Se sube un archivo OpenAPI 3.0/3.1 válido vía `POST /api/v1/clients/{client_code}/contracts`; el servicio valida la estructura OpenAPI, extrae metadatos (título, versión, cantidad de endpoints) y retorna `201 Created`.

**Criterios de Aceptación**:
1. **Given** un Desarrollador asignado al cliente o un Admin, **When** sube un contrato OpenAPI en `POST /api/v1/clients/{client_code}/contracts`, **Then** el sistema valida que sea un OpenAPI 3.x válido, extrae los endpoints y lo almacena con estado `is_valid: true`.
2. **Given** un contrato corrupto o con sintaxis JSON/YAML inválida, **When** se sube, **Then** el sistema responde `422 Unprocessable Entity` detallando los errores de esquema.
3. **Given** un Desarrollador no asignado al cliente, **When** intenta consultar o subir contratos, **Then** responde `403 Forbidden`.

---

### User Story 4 - Contexto de Gobernanza Consolidado para la IA (Priority: P2)

* **Como**: Microservicio orquestador de agentes (`ai-orchestrator-service`).
* **Quiero**: Obtener en una sola llamada el paquete consolidado de gobernanza de un cliente (`GET /api/v1/clients/{client_code}/governance-context?contract_id=...`).
* **Para**: Inyectarlo de forma estructurada en los nodos de diseño y generación de LangGraph sin llamadas HTTP dispersas.
* **Por qué esta prioridad**: Optimiza la latencia de la fábrica y asegura que la IA reciba un contexto coherente e inmutable.
* **Prueba Independiente**: Se invoca el endpoint con `client_code` y `contract_id` válidos, y retorna un JSON con perfil del cliente, directivas obligatorias agrupadas por categoría y el contrato OpenAPI resuelto.

**Criterios de Aceptación**:
1. **Given** un token inter-servicio válido, **When** solicita `GET /api/v1/clients/{client_code}/governance-context`, **Then** retorna `200 OK` con `{ "client": {...}, "directives": [...], "contract": {...} }`.
2. **Given** un `contract_id` inexistente o que pertenece a otro cliente, **When** se solicita el contexto, **Then** responde `404 Not Found` impidiendo mezcla indebida de contratos entre clientes.

---

## 3. Edge Cases & Casos Límite

1. **Aislamiento Hermético entre Cuentas**: Prohibido que un contrato o directiva del cliente A pueda vincularse o transferirse al cliente B.
2. **Cero Datos Precargados (Principio XIV)**: El servicio inicia sin clientes ni reglas precargadas. Para pruebas o demostraciones, se proporciona un script seed independiente o se crean vía API.
3. **Validación Determinista de Contratos**: Detección de OpenAPI versions no soportadas (ej. Swagger 1.x antiguo) con mensaje instructivo.
4. **Fallo de comunicación con Auth Service**: Si `auth-access-service:8001` no responde durante la verificación de token, responder `503 Service Unavailable` de forma resiliente.

---

## 4. Requerimientos Funcionales y No Funcionales

### Requerimientos Funcionales
* **FR-001**: El microservicio DEBE escuchar en el puerto `8002` y exponer Swagger OpenAPI en `/docs`.
* **FR-002**: El servicio DEBE validar la autenticación y permisos invocando `POST http://localhost:8001/api/v1/auth/verify` o validando el JWT emitido con clave compartida.
* **FR-003**: Solo colaboradores con rol `ADMIN` pueden crear, actualizar o desactivar perfiles de clientes y sus directivas.
* **FR-004**: Los Desarrolladores pueden consultar clientes, directivas y contratos únicamente de las cuentas a las que tienen acceso asignado.
* **FR-005**: Los contratos OpenAPI cargados DEBEN validarse como OpenAPI 3.0.x o 3.1.x y parsear el número de rutas (`paths`) y operaciones.
* **FR-006**: Las directivas DEBEN soportar las categorías: `SECURITY`, `ARCHITECTURE`, `NAMING`, `TESTING`, `OBSERVABILITY` y niveles de severidad `MANDATORY`, `RECOMMENDED`, `OPTIONAL`.
* **FR-007**: El microservicio DEBE exponer `GET /api/v1/health` para sondas de disponibilidad.

### Requerimientos No Funcionales
* **NFR-001**: **Rendimiento**: Generación del paquete de gobernanza consolidado en menos de 50 ms.
* **NFR-002**: **Persistencia**: SQLAlchemy 2.0 con SQLite local (`governance_factory_local.db`) / PostgreSQL conmutables vía `DATABASE_URL`.
* **NFR-003**: **Zero Hardcoding**: Ningún cliente (ni BCP ni ningún otro) estará quemado en el código fuente.

---

## 5. Criterios de Éxito Medibles

* **SC-001**: Suite de pruebas automatizadas con 100% de éxito cubriendo clientes, directivas, contratos y control de acceso.
* **SC-002**: 0% de fugas de datos o mezcla de contratos entre clientes distintos.
* **SC-003**: Tiempo de respuesta de endpoints CRUD menor a 100 ms en entorno local.
