# Perfil de Referencia Corporativo Interbank (IBK) — TCS Intelligent Microservice Factory

**Cliente:** Interbank Perú (IBK)  
**Código de Cliente:** `ibk`  
**Prefijo de Paquetes:** `pe.com.interbank`  
**Java Version:** `21` (LTS)  
**Quarkus Version:** `3.15.1`  
**Estado:** Activo (Perfil Corporativo Bancario)  

---

## 1. Alcance y Principio de Configuración Abierta de la Fábrica

El perfil **Interbank (IBK)** actúa dentro de la **TCS Intelligent Microservice Factory** como cuenta bancaria corporativa para microservicios Cloud Native de alta disponibilidad, resiliencia y procesamiento financiero en tiempo real.

> [!IMPORTANT]
> **Libertad de Configuración por Pasos (Step-by-Step Configuration):** En lugar de forzar una generación inmediata ciega, la fábrica ofrece un asistente interactivo donde el desarrollador selecciona y afina de forma guiada:
> 1. Patrón arquitectónico (Hexagonal, Clean Layered, Event-Driven, BFF, gRPC).
> 2. Esquema de seguridad bancaria (Quarkus SmallRye JWT, OIDC Keycloak, mTLS o pública).
> 3. Protocolos de comunicación (RESTEasy Reactive REST, gRPC, GraphQL, Reactive Kafka).
> 4. Motor de persistencia y entidades de datos editables (PostgreSQL Panache, MySQL, MongoDB, Reactive SQL, Redis o Stateless).
> 5. Inyección de extensiones Quarkus a demanda (OpenAPI, Health, Metrics Prometheus, Fault Tolerance, OpenTelemetry).

---

## 2. Tecnologías y Directivas Técnicas del Perfil IBK

### Pilar 1: Arquitectura y Desacoplamiento (IBK-ARCH-01)
* **Java:** Versión 21 LTS (`<maven.compiler.release>21</maven.compiler.release>`).
* **Estilo Principal:** Arquitectura Hexagonal (Ports & Adapters) o Clean Architecture, separando rígidamente:
  - `domain`: Modelos inmutables, Value Objects, puertos de entrada y salida (interfaces puras sin dependencias de frameworks).
  - `application`: Casos de uso y orquestación de servicios de dominio.
  - `infrastructure`: Adaptadores REST, repositorios Panache, clientes HTTP e integraciones externas.

### Pilar 2: Seguridad Bancaria y Criptografía (IBK-SEC-01)
* **Quarkus Security:** `quarkus-smallrye-jwt` para validación de tokens Bearer JWT y roles (`ADMIN`, `OPERATOR`, `AUDITOR`) o `quarkus-oidc` para integración con Keycloak corporativo.
* **Secretos:** Cero contraseñas hardcodeadas; configuración a través de variables de entorno y Azure Key Vault / AWS Secrets Manager.

### Pilar 3: APIs y Comunicación REST / Reactiva (IBK-COMM-01 / IBK-EVENT-01)
* **REST Síncrono:** RESTEasy Reactive (`quarkus-resteasy-reactive-jackson`) de alto rendimiento no bloqueante.
* **Documentación:** `quarkus-smallrye-openapi` con UI OpenAPI 3.0 activada.
* **Eventos Asíncronos:** SmallRye Reactive Messaging con Kafka (`quarkus-smallrye-reactive-messaging-kafka`) para transacciones financieras distribuidas y streaming de eventos.

### Pilar 4: Persistencia y Gestión de Datos Transaccionales (IBK-DATA-01)
* **Relacional:** Quarkus Hibernate ORM con Panache (`quarkus-hibernate-orm-panache`) con conector PostgreSQL (`quarkus-jdbc-postgresql`).
* **Entidades Editables:** Modelado en 3FN, transacciones ACID con `@Transactional` y soporte de repositorios Panache (`PanacheRepositoryBase`).

### Pilar 5: Observabilidad y Resiliencia (IBK-OBS-01 / IBK-RESIL-01)
* **Salud:** SmallRye Health (`quarkus-smallrye-health`) con sondas de liveness (`/q/health/live`) y readiness (`/q/health/ready`).
* **Métricas:** Micrometer Prometheus (`quarkus-micrometer-registry-prometheus`) para métricas de latencia y throughput en `/q/metrics`.
* **Tolerancia a Fallos:** SmallRye Fault Tolerance (`quarkus-smallrye-fault-tolerance`) aplicando `@Timeout`, `@Retry` y `@CircuitBreaker`.

### Pilar 6: Calidad Determinista y Pruebas (IBK-TEST-01)
* **Unitarias:** JUnit 5 (`quarkus-junit5`) y Mockito.
* **Integración API:** `@QuarkusTest` y REST-assured para validación determinista de contratos y endpoints antes de la distribución.

