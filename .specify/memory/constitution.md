<!--
Sync Impact Report:
- Version change: 1.2.0 -> 1.3.0 (MINOR: Ratificación de Mandatos Fundamentales: Arquitectura de Fábrica de Agentes Basada en Microservicios, Generación sin Errores en Quarkus según Pedido, Cero Librerías Innecesarias y 100% Stateless sin BD, Dos Roles Corporativos RBAC Estrictos, Verificación y Pruebas en Docker con Tecnología Nativa Quarkus, Bóveda Fernet e IA Desacoplada sin Intermediarios, HITL Exhaustivo y Telemetría en Tiempo Real de Tokens y Costos por Proyecto y Proveedor).
- Principles established:
  - I. Estilos Arquitectónicos Adaptativos (Hexagonal, En Capas, Event-Driven, BFF Stateless, gRPC según el caso)
  - II. Capacidades Estrictamente Bajo Demanda (Prohibido agregar librerías innecesarias; si no necesita BD, será 100% stateless)
  - III. Cumplimiento Normativo y Verificación Determinista
  - IV. Control de Accesos (RBAC): Dos roles estrictos (Administrador: credenciales cifradas y políticas; Desarrollador: proyectos en clientes asignados)
  - V. Plataforma 100% Agnóstica a Clientes (Cero código hardcodeado; BCP e IBK como cuentas y perfiles dinámicos)
  - VI. Calidad Verificable y Pruebas en Docker con Tecnología Nativa Quarkus (@QuarkusTest, DevServices, Testcontainers, Surefire)
  - VII. Automatización CI/CD (GitHub Actions .github/workflows/ci.yml)
  - VIII. Orquestación Controlada y Resiliente (LangGraph con presupuesto y estado finito)
  - IX. Bóveda Cifrada e IA Desacoplada (Llaves cifradas con Fernet; conmutación en caliente entre Gemini, DeepSeek, Grok y Mock sin intermediarios)
  - X. Experiencia Corporativa TCS Workspace Studio (React + Vite + TypeScript + Tailwind CSS)
  - XI. Observabilidad y Telemetría Transparente (Registro en tiempo real de tokens y costos por proyecto y proveedor de modelo)
  - XII. Supervisión Humana Innegociable (Human-in-the-Loop - HITL: el usuario pide lo que quiere, la IA propone, el desarrollador inspecciona, configura, visualiza, edita el código en pantalla y aprueba antes de descargar el ZIP)
  - XIII. Arquitectura de la Fábrica de Agentes (Suite de Microservicios Distribuidos: auth-access-service :8001, client-governance-service :8002, ai-orchestrator-service :8003, sandbox-verifier-service :8004, tcs-factory-ui :5173)
  - XIV. Mandato de Generación Sin Errores en Quarkus según el Pedido (Cero errores sintácticos, dependencias exactas y Manifiesto SHA-256)
-->

# TCS Intelligent Microservice Factory Constitution

Plataforma corporativa de agentes de inteligencia artificial para colaboradores de Tata Consultancy Services (TCS), implementada mediante una suite distribuida de microservicios, diseñada para acelerar y estandarizar la generación de microservicios con Java y Quarkus **sin errores según el pedido del usuario**, a partir de requerimientos de negocio en lenguaje natural, contratos OpenAPI/Swagger o blueprints estructurados, garantizando código limpio, modular, calidad verificable en Docker, control de accesos RBAC y gobernanza multi-cliente sin código quemado (*zero hardcoding*).

---

## Core Principles

### I. Estilos Arquitectónicos Adaptativos (No One-Size-Fits-All)
- **Selección Justificada por Microservicio**: Los microservicios generados NO están obligados a seguir un único patrón rígido. La arquitectura de cada microservicio se determina según su necesidad técnica real y las directivas de su cliente:
  - *Arquitectura Hexagonal (Puertos y Adaptadores)*: Para microservicios de dominio complejo o alta transaccionalidad bancaria/empresarial.
  - *Arquitectura en Capas (Layered Architecture)*: Para servicios CRUD directos o aplicaciones estándar.
  - *Worker / Procesador Asíncrono (Event-Driven)*: Para consumidores o productores de mensajería (Kafka/AMQP) sin capas web innecesarias.
  - *API Gateway / BFF / Orquestador Stateless*: Para servicios de integración o agregación de datos sin base de datos ni persistencia.
  - *Microservicio de Alta Velocidad gRPC*: Para comunicación binaria interna de baja latencia.
- **Calidad de Código**: Todo microservicio generado, independientemente de su estilo, DEBE aplicar principios SOLID, Clean Code, inmutabilidad donde aplique, separación estricta de responsabilidades y bajo acoplamiento.

### II. Capacidades Estrictamente Bajo Demanda (Zero Over-Engineering & 100% Stateless)
- **Prohibido Agregar Librerías Innecesarias**: Está terminantemente prohibido forzar extensiones, dependencias o configuraciones que el microservicio no requiera:
  - *Microservicios 100% Stateless*: Si el microservicio no necesita base de datos, será estrictamente **100% stateless** (cero dependencias de Hibernate ORM, cero Panache, cero JDBC DataSources, cero Flyway/Liquibase y cero drivers de base de datos en el `pom.xml`).
  - *Seguridad Bajo Demanda*: Solo se configura JWT, OIDC, mTLS o API Key si el requerimiento o la directiva del cliente lo exige explícitamente. No se inyectan filtros de seguridad ni llaves criptográficas dummy a microservicios públicos, internos o que no los requieran.
  - *Resiliencia e Idempotencia Justificada*: Patrones como `X-Idempotency-Key`, Circuit Breakers o Retry solo se añaden cuando el microservicio realice operaciones transaccionales o consuma servicios externos que lo ameriten.
- **Ecosistema Oficial Java y Quarkus**: Uso exclusivo de Java 17 o 21 LTS y Quarkus 3.x con el BOM oficial `io.quarkus.platform`. Prohibido el uso de librerías o anotaciones ajenas a Quarkus (como dependencias de Spring Boot).

### III. Cumplimiento Normativo y Verificación Determinista
- **Directivas de Cliente Versionadas**: Las reglas técnicas obligatorias de cada cliente (IBK, BCP, etc.) se identifican, configuran y versionan formalmente como políticas de su perfil en la gobernanza.
- **Comprobación Determinista**: Las reglas obligatorias DEBEN validarse mediante herramientas estáticas de análisis de código y pruebas automáticas, no confiar únicamente en las instrucciones en lenguaje natural dadas al modelo de IA.
- **Cero Normas Inventadas**: Prohibido inventar directivas de clientes o de TCS. Se aplican exclusivamente las directivas autorizadas del cliente seleccionado para ese microservicio.

### IV. Control de Accesos (RBAC): Dos Roles Estrictos
- **Modelo de 2 Roles Corporativos Estrictos**: La plataforma gestiona el acceso mediante exactamente dos roles bien delimitados:
  1. *Administrador*:
     - Gestiona colaboradores y asigna a qué cuentas de clientes tiene acceso cada uno.
     - Gestiona las credenciales cifradas y configura la Bóveda de IA.
     - Define y versiona los estándares, políticas y directivas técnicas de las cuentas de clientes.
     - Acceso global a auditoría, trazabilidad y telemetría de costos y tokens.
  2. *Desarrollador*:
     - Diseña proyectos, ingresa requerimientos y carga contratos OpenAPI exclusivamente en las cuentas de clientes que tiene asignadas.
     - Diseña, ejecuta la generación de código con IA, edita y revisa artefactos en el Workspace Studio.
     - Dispara la verificación y pruebas en Docker / Sandbox y descarga los microservicios finales.
- **Aislamiento por Colaborador**: Ningún Desarrollador puede visualizar ni generar proyectos para clientes a los que no ha sido asignado por un Administrador.
- **Bóveda Cifrada**: Las API Keys y credenciales corporativas se configuran en la UI, se cifran en reposo y NUNCA se exponen en texto plano, logs ni repositorios.

### V. Plataforma 100% Agnóstica a Clientes (Zero Hardcoding)
- **Cero Código Quemado**: El núcleo de la fábrica de agentes es completamente genérico y neutral. No contendrá ningún nombre de cliente, regla bancaria o condición fija quemada en el código fuente de los agentes.
- **Clientes como Perfiles Dinámicos**: Clientes como BCP o Interbank (IBK) son cuentas y perfiles de gobernanza dinámicos y desacoplados. No son normas fijas para otros clientes ni para todos los microservicios.
- **Aislamiento Hermético de Información**: La documentación, contratos y reglas de un cliente NUNCA se utilizarán para generar soluciones de otro cliente. Cada perfil tiene su propio espacio de memoria y catálogo de contratos.

### VI. Calidad Verificable y Pruebas en Docker con Tecnología Nativa Quarkus
- **Pruebas en Contenedores Docker**: Las pruebas del microservicio generado en Quarkus deben ejecutarse en entornos de contenedores Docker utilizando la tecnología nativa de pruebas de Quarkus (`@QuarkusTest`, DevServices, Testcontainers, Maven Surefire y RestAssured).
- **Compilación Real sin Mocks**: Todo microservicio generado debe verificarse en un entorno efímero ejecutando la compilación real (`mvn -B clean compile test-compile`).
- **Pruebas Automatizadas Coherentes**: El microservicio debe incluir pruebas automáticas pertinentes para su arquitectura (pruebas unitarias con JUnit 5 y pruebas de integración reactivas de endpoints con `@QuarkusTest`).
- **Auto-Reparación Acotada**: Ante fallos de compilación o pruebas, el agente de reparación intentará solucionar los errores guiado por la evidencia real del compilador (máximo 2 iteraciones).

### VII. Automatización CI/CD
- **Workflows Exportables**: Cada microservicio generado incluye su workflow de GitHub Actions (`.github/workflows/ci.yml`) adaptado a las herramientas y pruebas que ese microservicio en particular utiliza.

### VIII. Orquestación Controlada y Resiliente (LangGraph)
- **Flujos con Estado y Dependencias**: La generación se orquesta mediante grafos LangGraph con dependencias claras, control de estados y límites de reintentos.
- **Contexto Acumulativo**: Cada nodo del grafo recibe los contratos y clases ya generadas en nodos previos para evitar métodos, imports o rutas inventadas.
- **Límites de Presupuesto**: Control estricto de tokens, tiempo y costo máximo en USD por corrida. Si se alcanza un límite, se detiene de forma limpia en estado `PARTIAL`.

### IX. Bóveda Cifrada e Inteligencia Artificial Desacoplada
- **Bóveda Cifrada con Fernet**: Las llaves de API de los proveedores de IA se almacenan cifradas en reposo mediante Fernet de alta seguridad.
- **Conmutación en Caliente sin Intermediarios**: Conmutación dinámica e inmediata entre **Google Gemini**, **DeepSeek**, **Grok** y **Mock** sin intermediarios, sin capas de tiers ni dependencias artificiales de consumo. Se ingesta directamente el proveedor y el modelo LLM seleccionado.
- **Parser Resiliente**: Auto-cierre de JSON truncados y asignación de tokens de salida suficientes (`maxOutputTokens >= 8192`).

### X. Experiencia Corporativa TCS Workspace Studio
- **Interfaz Profesional de Ingeniería**: Interfaz web (`tcs-factory-ui` con React + Vite + TypeScript + Tailwind CSS) orientada a productividad, con soporte para gestión de clientes, configuración de IA, roles RBAC y supervisión de agentes.
- **Navegación Unificada**: Menú lateral izquierdo con acceso instantáneo a Workspace Studio, Consumo & Tokens y Gobernanza Admin.
- **Visualización Adaptada**: Muestra diagramas interactivos (Mermaid) acordes a la naturaleza del servicio (Arquitectura, ERD solo si tiene persistencia relacional, OpenAPI si expone APIs, o Topología de Eventos si es asíncrono).

### XI. Observabilidad y Telemetría Transparente
- **Registro en Tiempo Real de Tokens y Costos**: Visualización y auditoría transparente del registro de tokens consumidos (Tokens de Prompt vs. Tokens de Output generados) y costos acumulados en USD, organizados tanto por proyecto/job individual como desglosados por proveedor de modelo (Gemini, DeepSeek, Grok, Mock).

### XII. Supervisión Humana Innegociable (Human-in-the-Loop - HITL)
- **El Usuario Pide lo que Quiere**: El usuario tiene la libertad total de redactar su requerimiento en lenguaje natural o ingestar un Blueprint JSON completo.
- **La IA Propone, el Humano Dispone**: La IA propone la arquitectura y el código, pero el desarrollador humano inspecciona, selecciona, configura y visualiza las propuestas y selecciones.
- **Edición en Pantalla y Aprobación Previa**: El desarrollador tiene la facultad de editar el código fuente generado directamente en la pantalla (editor HITL) y aprobarlo explícitamente antes de empaquetar y descargar el archivo `.zip` final.
- **Cero Despliegues Autónomos**: Ningún agente puede desplegar en producción ni aprobar excepciones de seguridad sin autorización humana explícita.

### XIII. Arquitectura de la Fábrica de Agentes (Suite de Microservicios Distribuidos)
- **Suite de 4 Microservicios Distribuidos + UI**:
  1. `auth-access-service` (Puerto 8001): Microservicio dedicado a la autenticación, gestión de usuarios (2 roles estrictos: Administrador y Desarrollador), asignación de cuentas de clientes y emisión de tokens JWT.
  2. `client-governance-service` (Puerto 8002): Microservicio para la gestión de perfiles de clientes, versionado de directivas corporativas y catalogación de contratos OpenAPI/Swagger.
  3. `ai-orchestrator-service` (Puerto 8003): Microservicio de orquestación de IA con LangGraph, bóveda cifrada Fernet multi-proveedor (Gemini, DeepSeek, Grok, Mock) e ingesta directa de modelos.
  4. `sandbox-verifier-service` (Puerto 8004): Microservicio del plano de ejecución efímero e independiente; materializa el código Java, ejecuta compilación real (`mvn clean compile test-compile`), pruebas en Docker con tecnología nativa Quarkus y empaqueta el `.zip` final con manifiesto SHA-256.
  5. `tcs-factory-ui` (Puerto 5173): Frontend SPA corporativo en React + Vite + TypeScript + Tailwind CSS bajo la identidad visual de TCS ("Workspace Studio").
- **Orquestación y Despliegue**: Coordinación local mediante `docker-compose.yml` y scripts de inicio rápido, con cada microservicio desacoplado y preparado para escalar independientemente en Azure Container Apps, Azure Key Vault y Azure Blob Storage.

### XIV. Mandato de Generación Sin Errores en Quarkus según el Pedido
- **Generación Sin Errores**: La IA debe generar microservicios en Quarkus libres de errores sintácticos, de dependencias y de compilación, ajustándose con exactitud al pedido y a los inputs suministrados por el usuario.
- **Veracidad y Estado Limpio (Zero Preloaded Data)**: La plataforma inicia sin proyectos inventados ni métricas simuladas.
- **Manifiesto Criptográfico**: Todo paquete `.zip` entregado incluye `VERIFICATION_MANIFEST.json` con hashes SHA-256 de los archivos fuente generados y el resultado real de la verificación.

---

## Proceso de Desarrollo Spec-Kit

1. **Especificación Previa (`spec.md`)**: Ninguna funcionalidad de la plataforma se implementa sin especificación técnica aprobada.
2. **Plan y Tareas (`plan.md` y `tasks.md`)**: Fases delimitadas, verificables y con dependencias claras.
3. **Criterio de Entrega**: Funcionalidad completa y validada de extremo a extremo con pruebas automatizadas reales.

## Gobernanza

- Esta Constitución es la ley suprema de **TCS Intelligent Microservice Factory** y rige todo el ciclo de vida del proyecto.
- Cualquier enmienda a estos principios requerirá registro formal bajo control semántico de versiones (`MAJOR.MINOR.PATCH`).

**Version**: 1.3.0 | **Ratified**: 2026-10-21 | **Last Amended**: 2026-10-21
