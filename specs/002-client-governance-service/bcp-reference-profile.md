# Perfil de Referencia Piloto BCP — TCS Intelligent Microservice Factory

**Cliente:** Banco de Crédito del Perú (BCP)  
**Código de Cliente:** `bcp`  
**Prefijo de Paquetes:** `pe.com.bcp`  
**Java Version:** `21` (con soporte `17` LTS)  
**Quarkus Version:** `3.15.1`  
**Estado:** Activo (Perfil de Referencia Piloto)  

---

## 1. Alcance y Principio de Neutralidad de la Fábrica

El perfil **BCP** actúa dentro de la **TCS Intelligent Microservice Factory** como la **cuenta piloto de referencia corporativa**, diseñada para demostrar el cumplimiento de lineamientos bancarios estrictos. 

> [!IMPORTANT]
> **Cero Código Hardcodeado (Zero Hardcoding):** El motor central de la fábrica, los agentes LangGraph y las directivas están desacoplados. La plataforma permite registrar perfiles idénticos o con diferentes stacks para futuros clientes de TCS (ej. `santander`, `falabella`, `interbank`) sin alterar una sola línea de código fuente del sistema.

---

## 2. Tecnologías y Prácticas del Perfil Técnico BCP

### Pilar 1: Lenguaje y Framework
* **Java:** Versión 17 o 21 LTS (`<maven.compiler.source>21</maven.compiler.source>`).
* **Quarkus:** Quarkus Core, inyección de dependencias con ArC CDI (`@ApplicationScoped`, `@Inject`) y RESTEasy Reactive (`quarkus-resteasy-reactive`, `quarkus-resteasy-reactive-jackson`).
* **Calidad de Diseño:** SOLID, Clean Code, patrones de diseño GoF y arquitectura hexagonal o en capas desacopladas.

### Pilar 2: APIs e Integración
* **Estándar:** APIs RESTful bajo especificaciones OpenAPI 3.0 / Swagger.
* **Documentación:** `quarkus-smallrye-openapi` preconfigurado para publicación y catálogo en **Azure API Management (APIM)**.
* **Integración:** Comunicación empresarial asíncrona y sincrónica orientada a microservicios.

### Pilar 3: Arquitectura Reactiva y Eventos (Por Demanda)
* **Reactivo:** Mutiny (`Uni<T>`, `Multi<T>`) y SmallRye Reactive Messaging (`quarkus-smallrye-reactive-messaging`).
* **Brokers:** Conectores para Apache Kafka (`quarkus-smallrye-reactive-messaging-kafka`) y Azure Service Bus.
* **Patrones Avanzados:** Saga Orquestada/Coreografiada, Event-Driven Architecture (EDA), CQRS y Transactional Outbox.
* **Criterio de Inclusión:** *Habilitado únicamente cuando el requerimiento justifique explícitamente eventos o alta concurrencia asíncrona*.

### Pilar 4: Seguridad y Cifrado
* **Seguridad Quarkus:** `quarkus-security` y `quarkus-smallrye-jwt` para validación de tokens Bearer JWT y control RBAC.
* **Autenticación/Federación:** OAuth2 / OpenID Connect (OIDC), mTLS y PKI para interconexión inter-servicios.
* **Criptografía:** Cifrado simétrico (AES-GCM-256) y asimétrico (RSA 4096 / ECC).
* **Bóveda de Secretos:** Integración con **Azure Key Vault** o HashiCorp Vault. *Prohibido almacenar secretos o contraseñas en código plano o properties de producción.*

### Pilar 5: Pruebas y Calidad Determinista
* **Framework de Pruebas:** JUnit 5 (`quarkus-junit5`) y Mockito (`quarkus-junit5-mockito`).
* **Pruebas de Integración y API:** `@QuarkusTest` y REST-assured (`rest-assured`).
* **Validación Automatizada:** Ejecución real de suites de pruebas antes de autorizar el artefacto.

### Pilar 6: Persistencia y Gestión de Datos
* **ORM:** Hibernate ORM with Panache (`quarkus-hibernate-orm-panache`).
* **Base de Datos Relacional:** Microsoft SQL Server / Azure SQL (`quarkus-jdbc-mssql`).
* **Lineamientos Relacionales:** Modelamiento en Tercera Forma Normal (3FN), diseño explícito de índices, prevención de problemas N+1 (`JOIN FETCH`) y optimización de transacciones (`@Transactional`).
* **NoSQL (Por Demanda):** `quarkus-mongodb-panache` o Azure Cosmos DB habilitado únicamente para catálogos o trazabilidad desnormalizada justificada.

### Pilar 7: Cloud, Contenedores y DevOps
* **Contenedores:** Dockerfile multi-etapa optimizado (JVM o GraalVM Native Image).
* **Despliegue:** Kubernetes y Azure Container Apps.
* **Almacenamiento de Objetos:** Azure Blob Storage.
* **Automatización CI/CD:** Pipeline exportable `.github/workflows/ci.yml` con etapas deterministas de compilación (`mvn -B clean test-compile`), ejecución de pruebas unitarias (`mvn test`) y empaquetado.

---

## 3. Directivas Técnicas Catalogadas en la Fábrica

| Código | Categoría | Severidad | Descripción | Deterministic Check |
|---|---|:---:|---|---|
| `BCP-LANG-01` | ARCHITECTURE | **MANDATORY** | Java 17 o 21 LTS con Quarkus Core, ArC y RESTEasy Reactive. | `pom.xml:java.version in [17,21]` |
| `BCP-LANG-02` | ARCHITECTURE | **RECOMMENDED** | Principios SOLID, Clean Code y separación en capas desacopladas. | `package_structure_clean` |
| `BCP-API-01` | ARCHITECTURE | **MANDATORY** | Pequeña especificación SmallRye OpenAPI alineada a Azure APIM. | `io.quarkus:quarkus-smallrye-openapi` |
| `BCP-EVENT-01` | ARCHITECTURE | **OPTIONAL** | Mutiny y Reactive Messaging (Kafka/Service Bus) solo por demanda justificada. | `quarkus-smallrye-reactive-messaging` |
| `BCP-SEC-01` | SECURITY | **MANDATORY** | Quarkus Security + JWT. Cero credenciales hardcodeadas (Azure Key Vault). | `quarkus-smallrye-jwt` |
| `BCP-TEST-01` | TESTING | **MANDATORY** | JUnit 5, @QuarkusTest, Mockito y REST-assured obligatorios. | `quarkus-junit5 & rest-assured` |
| `BCP-DATA-01` | ARCHITECTURE | **MANDATORY** | Hibernate ORM Panache + SQL Server / Azure SQL con prevención N+1. | `quarkus-jdbc-mssql` |
| `BCP-DATA-NOSQL-02` | ARCHITECTURE | **OPTIONAL** | Soporte MongoDB / Cosmos DB solo bajo justificación explícita de negocio. | `quarkus-mongodb-panache` |
| `BCP-CLOUD-01` | OBSERVABILITY | **MANDATORY** | Dockerfile y pipeline `.github/workflows/ci.yml` con validación `mvn test`. | `ci_workflow_present` |

---

## 4. Reglas de Comportamiento del Motor Multi-Agente (LangGraph)

1. **Aislamiento de Cuentas:** Los desarrolladores asignados a `bcp` solo pueden generar microservicios dentro del contexto y políticas de BCP.
2. **Arquitectura Adaptativa (No One-Size-Fits-All):** El agente de arquitectura (`BLUEPRINT_DESIGN_NODE`) evalúa los requerimientos funcionales y selecciona únicamente los componentes indispensables. Si el requerimiento es un CRUD síncrono transaccional, no inyecta Kafka ni NoSQL.
3. **Validación Determinista:** En el `sandbox-verifier-service` (:8004), cada microservicio generado se compila contra el JDK 21/17 y se emite el manifiesto criptográfico `VERIFICATION_MANIFEST.json` con los hashes SHA-256 de cada archivo fuente.

