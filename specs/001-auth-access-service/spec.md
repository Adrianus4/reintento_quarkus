# Feature Specification: Spec 001 — auth-access-service

**Feature Branch**: `001-auth-access-service`  
**Created**: 2026-10-21  
**Status**: Draft  
**Version Alignment**: Constitution `v1.3.0` (Principio IV: Control de Accesos RBAC de Dos Roles Estrictos, Principio XIII: Puerto 8001, Principio XIV: Zero Preloaded Data)

---

## 1. Executive Summary & Purpose

Implementar el microservicio **`auth-access-service`** (Puerto `8001`) para **TCS Intelligent Microservice Factory**. Este servicio gestiona el ciclo de vida de los colaboradores y administradores de TCS, la autenticación mediante tokens JWT seguros, el control de acceso basado estrictamente en **dos roles corporativos (`ADMIN` y `DEVELOPER`)** y la asignación hermética de desarrolladores a las cuentas de clientes autorizadas:
- **Administrador (`ADMIN`)**: Gestiona colaboradores, asigna accesos a cuentas de clientes, gestiona credenciales cifradas y configura la Bóveda de IA y directivas de gobierno.
- **Desarrollador (`DEVELOPER`)**: Diseña proyectos, ingresa requerimientos, edita código en pantalla y genera microservicios exclusivamente en las cuentas de clientes que tiene asignadas.
Garantiza que ningún desarrollador pueda visualizar ni generar microservicios para clientes no asignados.

---

## 2. User Scenarios & Prioritized User Stories

### User Story 1 - Autenticación Segura y Emisión de JWT (Priority: P1)

* **Como**: Colaborador de TCS (Administrador o Desarrollador).
* **Quiero**: Iniciar sesión en la plataforma ingresando mi correo corporativo y contraseña.
* **Para**: Obtener un token de acceso JWT firmado con mi rol y poder operar en la plataforma según mis permisos.
* **Por qué esta prioridad**: Es la puerta de entrada indispensable del sistema; sin autenticación no es posible identificar quién opera ni aislar las cuentas de los clientes.
* **Prueba Independiente**: Puede probarse enviando credenciales a `POST /api/v1/auth/login` y verificando la obtención de un JWT válido decodificable con su rol (`ADMIN` o `DEVELOPER`).

**Criterios de Aceptación**:
1. **Given** un usuario registrado con estado activo y credenciales válidas, **When** solicita `POST /api/v1/auth/login`, **Then** el sistema retorna `200 OK`, el token JWT firmado (con tiempo de expiración configurable) y los datos básicos del perfil (nombre, correo, rol).
2. **Given** credenciales inválidas o una cuenta inactiva, **When** solicita `POST /api/v1/auth/login`, **Then** el sistema rechaza la petición con `401 Unauthorized` y un mensaje de error seguro sin revelar si el correo existe.
3. **Given** una plataforma en estado limpio inicial (sin usuarios), **When** se invoca el proceso de inicialización del primer Administrador (`POST /api/v1/auth/setup-admin`), **Then** se crea el Administrador inicial y se bloquea el endpoint para llamadas posteriores.

---

### User Story 2 - Gestión de Colaboradores y Asignación de los 2 Roles (Priority: P1)

* **Como**: Administrador de TCS.
* **Quiero**: Registrar colaboradores, listar el padrón de usuarios, actualizar sus estados (activo/inactivo) y asignarles su rol (`ADMIN` o `DEVELOPER`).
* **Para**: Controlar quién tiene acceso a la fábrica y qué nivel de privilegio posee.
* **Por qué esta prioridad**: Permite la administración interna de colaboradores requerida por la gobernanza de TCS.
* **Prueba Independiente**: El Administrador crea un nuevo usuario con rol `DEVELOPER`, y dicho usuario puede iniciar sesión inmediatamente.

**Criterios de Aceptación**:
1. **Given** un token con rol `ADMIN`, **When** invoca `POST /api/v1/users` con correo corporativo, nombre completo y rol (`ADMIN` o `DEVELOPER`), **Then** el sistema registra al usuario con contraseña cifrada (Argon2id o BCrypt) y retorna `201 Created`.
2. **Given** un intento de registro con un correo ya existente o un rol ajeno a `ADMIN`/`DEVELOPER`, **When** se envía la petición, **Then** el sistema responde `422 Unprocessable Entity` con el error de validación.
3. **Given** un usuario con rol `DEVELOPER`, **When** intenta invocar endpoints administrativos de usuarios (`GET /api/v1/users` o `POST /api/v1/users`), **Then** el sistema responde `403 Forbidden`.

---

### User Story 3 - Asignación y Aislamiento de Cuentas de Clientes por Desarrollador (Priority: P2)

* **Como**: Administrador de TCS.
* **Quiero**: Asignar a cada Desarrollador una lista de códigos/identificadores de cuentas de clientes autorizadas (ej. `bcp`, `retail-corp`, `telecom-x`).
* **Para**: Garantizar que el Desarrollador únicamente pueda ver y generar proyectos para los clientes que tiene formalmente asignados.
* **Por qué esta prioridad**: Implementa el aislamiento estricto multi-cliente exigido en el Principio IV y V de la Constitución.
* **Prueba Independiente**: Se asigna al desarrollador "dev1" únicamente el cliente "bcp"; al consultar `GET /api/v1/auth/me/clients`, la respuesta contiene únicamente "bcp".

**Criterios de Aceptación**:
1. **Given** un Administrador autenticado, **When** envía `PUT /api/v1/users/{user_id}/assigned-clients` con un listado de `client_codes` válidos, **Then** el sistema guarda las asignaciones y responde `200 OK`.
2. **Given** un Desarrollador autenticado, **When** invoca `GET /api/v1/auth/me/clients`, **Then** el sistema retorna exclusivamente los clientes a los que tiene acceso asignado.
3. **Given** un Administrador autenticado, **When** consulta `GET /api/v1/auth/me/clients`, **Then** el sistema retorna acceso universal a todos los clientes por su rol `ADMIN`.

---

### User Story 4 - Verificación y Validación de Tokens para los Demás Microservicios (Priority: P2)

* **Como**: Microservicio consumidor de la suite (`client-governance-service`, `ai-orchestrator-service` o `sandbox-verifier-service`).
* **Quiero**: Validar la autenticidad del JWT y los permisos del colaborador que invoca una operación inter-servicio.
* **Para**: Aplicar las compuertas de seguridad y verificar si el desarrollador tiene permiso sobre el cliente del proyecto.
* **Por qué esta prioridad**: Habilita la seguridad distribuida y la comunicación segura en la arquitectura de microservicios de la fábrica.
* **Prueba Independiente**: Se envía un JWT al endpoint `POST /api/v1/auth/verify` y se recibe la respuesta con el estado del token, `user_id`, `role` y lista de `assigned_clients`.

**Criterios de Aceptación**:
1. **Given** un token JWT válido y no expirado, **When** se invoca `POST /api/v1/auth/verify`, **Then** retorna `200 OK` con `{ "valid": true, "user_id": "...", "role": "DEVELOPER", "assigned_clients": ["bcp"] }`.
2. **Given** un token manipulado, con firma inválida o expirado, **When** se invoca `POST /api/v1/auth/verify`, **Then** retorna `200 OK` con `{ "valid": false, "reason": "TOKEN_EXPIRED" }`.

---

## 3. Edge Cases & Casos Límite

1. **Intento de autodesactivación del Administrador**: Un usuario con rol `ADMIN` no puede desactivarse a sí mismo ni revocar su propio rol si es el único Administrador activo del sistema.
2. **Eliminación o cambio de asignación de cliente en curso**: Si un Administrador retira el acceso a un cliente a un Desarrollador, las solicitudes subsiguientes de ese Desarrollador hacia dicho cliente serán rechazadas con `403 Forbidden`.
3. **Tokens con expiración vencida**: Las peticiones con tokens expirados deben retornar `401 Unauthorized` con el código `TOKEN_EXPIRED`, permitiendo refresco si está habilitado o solicitando login.
4. **Cero Datos Precargados (Zero Preloaded Data - Principio XIV)**: La base de datos inicia sin usuarios ni contraseñas quemadas; el primer arranque expone un mecanismo seguro de inicialización (`setup-admin`).

---

## 4. Requerimientos Funcionales y No Funcionales

### Requerimientos Funcionales
* **FR-001**: El microservicio DEBE escuchar en el puerto `8001` y exponer documentación Swagger OpenAPI en `/docs`.
* **FR-002**: El sistema DEBE soportar exactamente dos roles de usuario: `ADMIN` y `DEVELOPER`.
* **FR-003**: Las contraseñas DEBEN cifrarse mediante funciones hash robustas unidireccionales (Argon2id o BCrypt con factor de costo adecuado); NUNCA en texto plano.
* **FR-004**: Los tokens de acceso DEBEN ser JWT estándar firmados con algoritmo criptográfico seguro (HS256 con clave secreta en bóveda o RS256) e incluir claims: `sub` (user_id), `email`, `role`, `exp`, `iat`.
* **FR-005**: El Administrador DEBE poder crear usuarios, listar usuarios con filtros, actualizar roles y cambiar su estado (`ACTIVE` / `INACTIVE`).
* **FR-006**: El sistema DEBE registrar la relación muchos a muchos entre usuarios y clientes asignados (`UserClientAssignment`).
* **FR-007**: El endpoint `GET /api/v1/auth/me` DEBE devolver el perfil del usuario autenticado actual con sus clientes autorizados.
* **FR-008**: El endpoint `POST /api/v1/auth/verify` DEBE verificar el token y retornar los permisos y clientes autorizados para consumo de los demás microservicios de la suite.
* **FR-009**: Las acciones de inicio de sesión exitoso y fallido DEBEN registrarse en un log de auditoría con fecha, hora e IP (sin guardar contraseñas).
* **FR-010**: El microservicio DEBE exponer un endpoint de verificación de salud en `GET /api/v1/health`.

### Requerimientos No Funcionales
* **NFR-001**: **Rendimiento**: La validación de credenciales y generación de JWT debe completarse en menos de 250 ms.
* **NFR-002**: **Persistencia Limpia**: Uso de SQLAlchemy con SQLite local para desarrollo ágil / PostgreSQL para producción empresarial, con migraciones versionadas.
* **NFR-003**: **Zero Hardcoding**: Ningún usuario ni cliente está quemado en el código fuente.

---

## 5. Entidades de Dominio Clave

```text
┌───────────────────────────┐         ┌───────────────────────────┐
│           User            │ 1     * │   UserClientAssignment    │
├───────────────────────────┤---------├───────────────────────────┤
│ id: UUID (PK)             │         │ id: UUID (PK)             │
│ email: String (Unique)    │         │ user_id: UUID (FK)        │
│ hashed_password: String   │         │ client_code: String       │
│ full_name: String         │         │ assigned_at: Timestamp    │
│ role: Enum(ADMIN,DEV)     │         │ assigned_by_user_id: UUID │
│ is_active: Boolean        │         └───────────────────────────┘
│ created_at: Timestamp     │
│ updated_at: Timestamp     │
└─────────────┬─────────────┘
              │ 1
              │ *
┌─────────────┴─────────────┐
│      AuditLoginLog        │
├───────────────────────────┤
│ id: UUID (PK)             │
│ user_id: UUID (Nullable)  │
│ email_attempted: String   │
│ success: Boolean          │
│ ip_address: String        │
│ attempted_at: Timestamp   │
└───────────────────────────┘
```

---

## 6. Criterios de Éxito Medibles

* **SC-001**: La suite de pruebas automatizadas del microservicio cubre el 100% de los flujos de autenticación, autorización por rol (`ADMIN` vs `DEVELOPER`) y asignación de clientes.
* **SC-002**: Un usuario con rol `DEVELOPER` no puede acceder a ningún endpoint administrativo de usuarios ni a clientes no asignados (0% de fugas de autorización).
* **SC-003**: El tiempo de respuesta de `POST /api/v1/auth/verify` es menor a 20 ms en local, permitiendo validación inter-servicio sin degradar la experiencia de usuario.
* **SC-004**: Cero secretos o contraseñas expuestas en respuestas HTTP, logs o artefactos.

---

## 7. Supuestos y Dependencias

* **A001**: En el entorno local MVP, la persistencia se gestiona con SQLite (`auth_factory_local.db`) con soporte para PostgreSQL mediante variable de entorno `DATABASE_URL`.
* **A002**: Las contraseñas iniciales de los colaboradores las define el Administrador en la creación; el desarrollador puede cambiarla posteriormente.
* **A003**: Los microservicios downstream (`client-governance-service`, `ai-orchestrator-service`) confiarán en el token JWT emitido o validarán contra `POST /api/v1/auth/verify`.
