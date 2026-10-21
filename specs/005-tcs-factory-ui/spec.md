# Feature Specification: Spec 005 — tcs-factory-ui

**Feature Branch**: `005-tcs-factory-ui`  
**Created**: 2026-10-21  
**Status**: Draft  
**Version Alignment**: Constitution `v1.3.0` (Principio X: Experiencia Corporativa TCS Workspace Studio, Principio XI: Observabilidad y Telemetría Transparente, Principio XII: Supervisión Humana HITL Exhaustiva, Principio XIII: Puerto 5173, Principio XIV: Mandato de Generación Sin Errores)

---

## 1. Executive Summary & Purpose

Implementar la aplicación web SPA **`tcs-factory-ui`** (Puerto `5173`) construida con **React + Vite + TypeScript + Tailwind CSS** bajo la identidad visual corporativa de **Tata Consultancy Services (TCS)** ("Workspace Studio"). Esta interfaz unifica y orquesta visualmente los 4 microservicios distribuidos de la plataforma:
- `auth-access-service` (Puerto 8001): Autenticación, RBAC estricto de 2 roles y asignación de clientes.
- `client-governance-service` (Puerto 8002): Perfiles de clientes, directivas técnicas y contratos OpenAPI.
- `ai-orchestrator-service` (Puerto 8003): Bóveda cifrada Fernet, conmutación en caliente de IA, ingesta directa de modelos y pipelines LangGraph con telemetría en tiempo real.
- `sandbox-verifier-service` (Puerto 8004): Compilación y pruebas en Docker / sandbox efímero, manifiesto SHA-256 en segundo plano y descarga `.zip`.

---

## 2. User Scenarios & Prioritized User Stories

### User Story 1 - Autenticación Corporativa y Asistente Zero-State (Priority: P1)
* **Como**: Colaborador de TCS (Administrador o Desarrollador).
* **Quiero**: Iniciar sesión de forma segura y, en caso de arranque limpio sin usuarios, contar con un asistente para inicializar el primer Administrador.
* **Criterios**:
  - Pantalla de login profesional TCS con fondo navy corporativo (`#00142D`, `#0076CE`).
  - Detección de arranque limpio: formulario modal para crear el Administrador inicial vía `POST :8001/api/v1/auth/setup-admin`.
  - Persistencia segura de sesión en `sessionStorage`/`localStorage` y decodificación de rol (`ADMIN` vs `DEVELOPER`).

### User Story 2 - Panel de Gobernanza y Bóveda para Administradores (Priority: P1)
* **Como**: Administrador de TCS.
* **Quiero**: Administrar colaboradores, asignar cuentas de clientes, configurar la bóveda de credenciales cifradas y cambiar proveedores de IA y modelos directamente en caliente.
* **Criterios**:
  - Módulo "Colaboradores": listar usuarios, crear desarrolladores y asignar clientes (`ibk`, `bcp`, etc.).
  - Módulo "Bóveda de IA": guardar y rotar API Keys de Gemini, DeepSeek y Grok cifradas con Fernet con prueba de conectividad inmediata.
  - Módulo "Gateway de IA": selector de proveedor activo e input directo del modelo LLM (`model_name`), eliminando tiers o modos de consumo artificiales.
  - Módulo "Clientes": registro de perfiles, directivas arquitectónicas y contratos OpenAPI.

### User Story 3 - Asistente Interactivo con Doble Entrada: Requerimiento Libre o Blueprint JSON (Priority: P1)
* **Como**: Desarrollador de TCS.
* **Quiero**: Poder redactar libremente mi requerimiento para moldearlo en las fases, o ingestar un Blueprint JSON predefinido para autorellenar y editar todos los pasos antes de la generación:
  - **Doble Entrada**: Alternar entre "Diseñar por Fases" e "Ingestar Blueprint JSON" (con plantillas IBK y BCP o subida de archivo `.json`).
  - **Inputs de Proyecto**: Selector de cliente corporativo (con soporte para `ibk` y `bcp`), nombre del microservicio (`artifactId`), prefijo de paquete base editable (`package_prefix`, ej: `pe.com.interbank`), puerto HTTP y versión de Java (21 / 17).
  - **Inputs de Arquitectura**: Selección de patrón (Hexagonal, Clean Layered, Event-Driven, BFF, gRPC) y caja de texto para directivas arquitectónicas especiales.
  - **Inputs de Seguridad**: Modelo de seguridad (JWT, OIDC, mTLS, Basic, Ninguna), emisor de tokens y roles requeridos.
  - **Inputs de Endpoints Personalizados**: Gestor de endpoints donde el usuario puede agregar, editar y eliminar métodos HTTP (`GET`, `POST`, `PUT`, `DELETE`), rutas de URI y resúmenes de operación.
  - **Inputs de Base de Datos y Entidades**: Motor de persistencia (PostgreSQL, MySQL, MongoDB, Reactive SQL, Redis o None/Stateless), nombre de BD y editor dinámico de entidades con nombres de clases, nombres de tablas y atributos tipados (`String`, `BigDecimal`, `Long`, etc.). Si no se requiere BD, el microservicio es 100% stateless sin librerías forzadas.
  - **Inputs de Extensiones y Propiedades Quarkus**: Catálogo de extensiones recomendadas + campo para escribir extensiones adicionales libres (`custom_extensions`) y propiedades directas en formato `key=value` (`custom_properties`).
  - **Input de Requerimiento de Negocio**: Campo multilínea amplio y destacado para describir la lógica de negocio.
  - **Modos de Vista**: Alternancia entre **Modo Asistente por Pasos** (Stepper 1-7) y **Modo Vista Unificada**.
  - **Exportación de Blueprint**: Botón para exportar y descargar la configuración completa del microservicio como JSON en cualquier momento.
  - **Editor HITL**: Explorador de árbol de archivos y editor de código en línea (CodeViewer) con pestañas para Java, `pom.xml`, application.properties y pruebas con soporte de edición en pantalla (Human-in-the-Loop) vía `PATCH :8003/api/v1/orchestrator/jobs/{id}/files`.

### User Story 4 - Módulo "Consumo & Tokens" en Barra de Navegación Lateral (Priority: P1)
* **Como**: Colaborador de TCS (Desarrollador o Administrador).
* **Quiero**: Una opción accesible en el menú lateral izquierdo denominada **"Consumo & Tokens"** que presente el registro completo de tokens consumidos por proyecto y por proveedor de modelo de IA.
* **Criterios**:
  - Menú lateral izquierdo (`aside`) con acceso directo a Workspace Studio, Consumo & Tokens y Gobernanza Admin.
  - Tarjetas de métricas globales: Total Tokens Consumidos, Tokens de Entrada (Prompt), Tokens de Salida (Completion), Costo Total Acumulado en USD y Total de Trabajos procesados.
  - Desglose consolidado por proveedor de modelo (`Gemini`, `DeepSeek`, `Grok`, `Mock`) con prompt/output tokens, cantidad de jobs y costo en USD.
  - Registro histórico tabular por proyecto/microservicio (Job ID, Cliente, Proveedor/Modelo, Estado, Tokens Entrada/Salida/Total, Costo USD y Fecha), con filtro dinámico por proveedor.

### User Story 5 - Verificación en Docker / Sandbox y Descarga ZIP (Priority: P1)
* **Como**: Desarrollador de TCS.
* **Quiero**: Aprobar el microservicio generado, disparar la compilación real y pruebas en Docker con tecnología nativa Quarkus (`@QuarkusTest`, Surefire, RestAssured) y descargar el `.zip` final con su manifiesto SHA-256 en segundo plano.
* **Criterios**:
  - Botón de aprobación y envío al `sandbox-verifier-service:8004`.
  - Consola estilo terminal con visualización del log del compilador en tiempo real.
  - Cálculo del manifiesto criptográfico `VERIFICATION_MANIFEST.json` con hashes SHA-256 por archivo en segundo plano sin interrumpir al desarrollador.
  - Botón de descarga de archivo `.zip` verificado y empaquetado.

---

## 3. Requerimientos Técnicos y de Diseño

* **RT-001**: Puerto local predeterminado `5173` con Vite.
* **RT-002**: TypeScript estricto con interfaces completas para todos los DTOs de los 4 microservicios.
* **RT-003**: Paleta de colores oficial TCS: Azul marino oscuro (`#00142D`), Azul tecnológico (`#0076CE`), Azul claro de realce (`#00A3E0`), Grises neutros de ingeniería.
* **RT-004**: Iconografía SVG limpia (sin librerías externas pesadas ni fuentes bloatware).
* **RT-005**: Manejo centralizado de peticiones API a través de un cliente HTTP modular tipado.
