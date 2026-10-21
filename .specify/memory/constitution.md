<!--
Sync Impact Report:
- Version change: 1.1.1 -> 1.2.0 (MINOR: Consolidación de los Pilares Ratificados: Suite de 4 Microservicios Distribuidos + UI, 2 Roles Corporativos RBAC, Capacidades y Arquitecturas On-Demand sin generalización bancaria y Cero Hardcoding con BCP como cuenta piloto).
- Principles established:
  - I. Estilos Arquitectónicos Adaptativos (Hexagonal, En Capas, Event-Driven, BFF Stateless, gRPC según el caso)
  - II. Capacidades Estrictamente Bajo Demanda (Sin librerías, persistencia ni seguridad forzada si no se solicitan)
  - III. Cumplimiento Normativo y Verificación Determinista
  - IV. Control de Accesos (RBAC): Modelo de 2 roles corporativos (Administrador y Desarrollador)
  - V. Plataforma 100% Agnóstica a Clientes (Cero código hardcodeado; BCP como cuenta piloto de prueba)
  - VI. Calidad Verificable en Sandbox Aislado (Compilación y pruebas reales con Surefire)
  - VII. Automatización CI/CD (GitHub Actions .github/workflows/ci.yml)
  - VIII. Orquestación Controlada y Resiliente (LangGraph con presupuesto y estado finito)
  - IX. Capa Flexible de Inteligencia Artificial (Conmutación en caliente entre Gemini, DeepSeek y Grok)
  - X. Experiencia Corporativa TCS Workspace Studio (React + Vite + TypeScript + Tailwind CSS)
  - XI. Observabilidad, Telemetría y Eficiencia
  - XII. Supervisión Humana (Human-in-the-Loop innegociable)
  - XIII. Arquitectura de la Fábrica (Suite de Microservicios Distribuidos: auth-access-service :8001, client-governance-service :8002, ai-orchestrator-service :8003, sandbox-verifier-service :8004, tcs-factory-ui :5173)
  - XIV. Veracidad y Estado Limpio (Zero Preloaded Data y Manifiesto SHA-256)
-->

# TCS Intelligent Microservice Factory Constitution

Plataforma corporativa de agentes de inteligencia artificial para colaboradores de Tata Consultancy Services (TCS), diseñada para acelerar y estandarizar la generación de microservicios con Java y Quarkus a partir de requerimientos de negocio, contratos OpenAPI/Swagger y documentación técnica autorizada, garantizando código limpio, modular, calidad verificable, control de accesos RBAC y gobernanza multi-cliente sin código quemado (*zero hardcoding*).

---

## Core Principles

### I. Estilos Arquitectónicos Adaptativos (No One-Size-Fits-All)
- **Selección Justificada por Microservicio**: Los microservicios generados NO están obligados a seguir un único patrón rígido. La arquitectura de cada microservicio se determina según su necesidad técnica real y las directivas de su cliente:
  - *Arquitectura Hexagonal (Puertos y Adaptadores)*: Para microservicios de dominio complejo o alta transaccionalidad.
  - *Arquitectura en Capas (Layered Architecture)*: Para servicios CRUD directos o aplicaciones empresariales estándar.
  - *Worker / Procesador Asíncrono (Event-Driven)*: Para consumidores o productores de mensajería (Kafka/AMQP) sin capas web innecesarias.
  - *API Gateway / BFF / Orquestador Stateless*: Para servicios de integración o agregación de datos sin base de datos ni persistencia.
  - *Microservicio de Alta Velocidad gRPC*: Para comunicación binaria interna de baja latencia.
- **Calidad de Código**: Todo microservicio generado, independientemente de su estilo, DEBE aplicar SOLID, Clean Code, separación de responsabilidades y bajo acoplamiento.

### II. Capacidades Estrictamente Bajo Demanda (Zero Over-Engineering)
- **Inclusión Exclusiva de lo Necesario**: Está terminantemente prohibido forzar extensiones, dependencias o configuraciones que el microservicio no requiera:
  - *Persistencia*: Si el microservicio no gestiona datos propios, será 100% *stateless* (sin Hibernate, sin Panache, sin JDBC, sin Flyway).
  - *Seguridad*: Solo se configura JWT, OIDC, mTLS o API Key si el requerimiento o la directiva del cliente lo exige explícitamente. No se inyectan filtros de seguridad ni llaves criptográficas dummy a microservicios públicos, internos o que no los requieran.
  - *Resiliencia e Idempotencia*: Patrones como `X-Idempotency-Key`, Circuit Breaker o Retry solo se añaden cuando el microservicio realice operaciones transaccionales o consuma servicios externos que lo justifiquen.
- **Java y Quarkus Oficial**: Uso de Java 17 o 21 LTS y Quarkus 3.x con el BOM oficial `io.quarkus.platform`. Prohibido el uso de librerías o anotaciones ajenas a Quarkus (como dependencias de Spring Boot).

### III. Cumplimiento Normativo y Verificación Determinista
- **Directivas del Cliente Versionadas**: Las reglas obligatorias del cliente correspondiente se identifican, configuran y versionan formalmente como políticas de su perfil.
- **Comprobación Determinista**: Cuando sea técnicamente posible, las reglas obligatorias DEBEN validarse mediante herramientas estáticas de análisis de código y pruebas automáticas, no confiar únicamente en las instrucciones en lenguaje natural dadas al modelo de IA.
- **Sin Suposiciones ni Normas Inventadas**: Prohibido inventar directivas de clientes o de TCS. Se aplican exclusivamente las directivas autorizadas del cliente seleccionado para ese microservicio.

### IV. Control de Accesos (RBAC), Identidad y Bóveda de Secretos
- **Modelo de 2 Roles Corporativos**: La plataforma gestiona el acceso mediante exactamente dos roles bien delimitados:
  1. *Administrador*:
     - Gestiona colaboradores y asigna a qué cuentas de clientes tiene acceso cada uno.
     - Configura los proveedores de IA globales y la bóveda de credenciales cifradas.
     - Define y versiona los estándares, políticas y directivas técnicas de las cuentas de clientes.
     - Acceso global de auditoría, trazabilidad y telemetría de costos.
  2. *Desarrollador / Colaborador*:
     - Crea proyectos, ingresa requerimientos y carga contratos OpenAPI exclusivamente en las cuentas de clientes que tiene asignadas.
     - Diseña, ejecuta la generación de código con IA, edita y revisa artefactos en la plataforma.
     - Dispara la verificación real en sandbox efímero y descarga los microservicios finales.
- **Aislamiento por Colaborador**: Ningún Desarrollador puede visualizar ni generar proyectos para clientes a los que no ha sido asignado por un Administrador.
- **Bóveda de Credenciales**: Las API Keys y credenciales corporativas se configuran en la UI, se cifran en reposo y NUNCA se exponen en texto plano, logs ni repositorios.

### V. Plataforma 100% Agnóstica a Clientes (Zero Hardcoding)
- **Cero Código Quemado**: El núcleo de la fábrica de agentes es completamente genérico y neutral. No contendrá ningún nombre de cliente, regla bancaria o condición fija quemada en el código fuente de los agentes.
- **BCP fue solo un Ejemplo Puntual**: El caso de BCP fue un ejemplo de requerimientos bancarios exigentes mencionado como referencia. No es la norma general ni la plantilla para otros clientes ni para todos los microservicios.
- **Aislamiento Hermético de Información**: La documentación, contratos y reglas de un cliente NUNCA se utilizarán para generar soluciones de otro cliente. Cada perfil tiene su propio espacio de memoria y artefactos.

### VI. Calidad Verificable en Sandbox Aislado
- **Compilación Real sin Mocks**: Todo microservicio generado debe verificarse en un entorno de sandbox aislado y efímero ejecutando la compilación real (`mvn -B clean compile test-compile`).
- **Pruebas Automatizadas Coherentes**: El microservicio debe incluir pruebas automáticas pertinentes para su arquitectura (pruebas unitarias con JUnit 5 y, si expone endpoints o servicios, pruebas con `@QuarkusTest` y RestAssured).
- **Auto-Reparación Acotada**: Ante fallos de compilación o pruebas, el agente de reparación intentará solucionar los errores guiado por la evidencia real del compilador (máximo 2 iteraciones).

### VII. Automatización CI/CD
- **Workflows Exportables**: Cada microservicio generado incluye su workflow de GitHub Actions (`.github/workflows/ci.yml`) adaptado a las herramientas y pruebas que ese microservicio en particular utiliza.

### VIII. Orquestación Controlada y Resiliente (LangGraph)
- **Flujos con Estado y Dependencias**: La generación se orquesta mediante grafos LangGraph con dependencias claras, control de estados y límites de reintentos.
- **Contexto Acumulativo**: Cada agente recibe los contratos y clases ya generadas en nodos previos para evitar métodos o rutas inventadas.
- **Límites de Presupuesto**: Control estricto de tokens, tiempo y costo máximo en USD por corrida. Si se alcanza un límite, se detiene de forma limpia en estado `PARTIAL`.

### IX. Capa Flexible de Inteligencia Artificial
- **Intercambiabilidad de Modelos**: Compatibilidad desacoplada con Google Gemini, DeepSeek y Grok, configurable dinámicamente en caliente.
- **Modos de Consumo Operativo**:
  - *Económico*: Para clarificación ágil y microservicios pequeños.
  - *Equilibrado (Recomendado)*: Para diseño y generación estándar.
  - *Avanzado*: Para microservicios con alta densidad de lógica de negocio.
- **Parser Resiliente**: Auto-cierre de JSON truncados y asignación de tokens de salida suficientes (`maxOutputTokens >= 8192`).

### X. Experiencia Corporativa TCS Workspace Studio
- **Interfaz Profesional de Ingeniería**: Interfaz web (`tcs-factory-ui` con React + Vite + TypeScript + Tailwind CSS) orientada a productividad ("Workspace Studio"), con soporte para gestión de clientes, configuración de IA, roles RBAC y supervisión de agentes.
- **Visualización Adaptada al Microservicio**: Muestra diagramas interactivos (Mermaid) acordes a la naturaleza del servicio (Arquitectura, ERD solo si tiene persistencia relacional, OpenAPI si expone APIs, o Topología de Eventos si es asíncrono).

### XI. Observabilidad, Telemetría y Eficiencia
- **Auditoría Transparente**: Visualización de tokens consumidos, costos estimados vs. confirmados y duración de compilación, protegiendo siempre los datos sensibles de los clientes.

### XII. Supervisión Humana (Human-in-the-Loop)
- **El Desarrollador Decide**: La IA es un copiloto acelerador. El desarrollador de TCS puede inspeccionar, editar el código generado en la plataforma y aprobar el resultado antes de empaquetarlo.
- **Cero Despliegues Autónomos**: Ningún agente puede desplegar en producción ni aprobar excepciones de seguridad sin autorización humana explícita.

### XIII. Arquitectura de la Fábrica de Agentes (Suite de Microservicios Distribuidos)
- **Suite de Microservicios Distribuidos de la Plataforma**:
  1. `auth-access-service` (Puerto 8001): Microservicio dedicado a la autenticación, gestión de usuarios/administradores (2 roles: Administrador y Desarrollador), asignación de cuentas de clientes y emisión de tokens JWT.
  2. `client-governance-service` (Puerto 8002): Microservicio para la gestión de perfiles de clientes, versionado de directivas corporativas y catalogación de contratos OpenAPI/Swagger.
  3. `ai-orchestrator-service` (Puerto 8003): Microservicio de orquestación de IA con LangGraph, bóveda de credenciales multi-proveedor (Gemini, DeepSeek, Grok) y pipelines de diseño y generación acumulativa.
  4. `sandbox-verifier-service` (Puerto 8004): Microservicio del plano de ejecución efímero e independiente; materializa el código Java, ejecuta compilación real (`mvn clean compile test-compile`), pruebas Surefire y empaqueta el `.zip` final con manifiesto SHA-256.
  5. `tcs-factory-ui` (Puerto 5173): Frontend SPA corporativo en React + Vite + TypeScript + Tailwind CSS bajo la identidad visual de TCS ("Workspace Studio").
- **Orquestación Local y Proyección Azure**: Ejecución local coordinada mediante `docker-compose.yml` (y scripts de inicio rápido), con cada microservicio desacoplado y preparado para escalar independientemente en Azure Container Apps, Azure Key Vault y Azure Blob Storage.

### XIV. Veracidad y Estado Limpio (Zero Preloaded Data)
- **Cero Datos Falsos**: La plataforma inicia sin proyectos inventados ni métricas simuladas.
- **Manifiesto Criptográfico**: Todo paquete `.zip` entregado incluye `VERIFICATION_MANIFEST.json` con hashes SHA-256 de los archivos fuente generados y el resultado real de la verificación.

---

## Proceso de Desarrollo Spec-Kit

1. **Especificación Previa (`spec.md`)**: Ninguna funcionalidad de la plataforma se implementa sin especificación técnica aprobada.
2. **Plan y Tareas (`plan.md` y `tasks.md`)**: Fases delimitadas, verificables y con dependencias claras.
3. **Criterio de Entrega**: Funcionalidad completa y validada de extremo a extremo con pruebas automatizadas reales.

## Gobernanza

- Esta Constitución es la ley suprema de **TCS Intelligent Microservice Factory** y rige todo el ciclo de vida del proyecto.
- Cualquier enmienda a estos principios requerirá registro formal bajo control semántico de versiones (`MAJOR.MINOR.PATCH`).

**Version**: 1.2.0 | **Ratified**: 2026-10-21 | **Last Amended**: 2026-10-21
