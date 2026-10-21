# Feature Specification: Spec 005 — tcs-factory-ui

**Feature Branch**: `005-tcs-factory-ui`  
**Created**: 2026-10-21  
**Status**: Draft  
**Version Alignment**: Constitution `v1.2.0` (Principio X: Experiencia Corporativa TCS Workspace Studio, Principio XIII: Puerto 5173, Principio XIV: Zero Preloaded Data)

---

## 1. Executive Summary & Purpose

Implementar la aplicación web SPA **`tcs-factory-ui`** (Puerto `5173`) construida con **React + Vite + TypeScript + Tailwind CSS** bajo la identidad visual corporativa de **Tata Consultancy Services (TCS)** ("Workspace Studio"). Esta interfaz unifica y orquesta visualmente los 4 microservicios distribuidos de la plataforma:
- `auth-access-service` (Puerto 8001): Autenticación, RBAC estricto de 2 roles y asignación de clientes.
- `client-governance-service` (Puerto 8002): Perfiles de clientes, directivas técnicas y contratos OpenAPI.
- `ai-orchestrator-service` (Puerto 8003): Bóveda de credenciales, conmutación en caliente de IA y pipelines LangGraph.
- `sandbox-verifier-service` (Puerto 8004): Compilación en sandbox efímero, manifiesto SHA-256 y descarga `.zip`.

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
* **Quiero**: Administrar colaboradores, asignar cuentas de clientes, configurar la bóveda de credenciales cifradas y cambiar proveedores de IA en caliente.
* **Criterios**:
  - Módulo "Colaboradores": listar usuarios, crear desarrolladores y asignar clientes (`bcp`, `retail-corp`, etc.).
  - Módulo "Bóveda de IA": guardar y rotar API Keys de Gemini, DeepSeek y Grok con prueba de conectividad inmediata.
  - Módulo "Gateway de IA": selector de proveedor activo y modo de consumo (`economic`, `balanced`, `advanced`).
  - Módulo "Clientes": registro de perfiles, directivas arquitectónicas y contratos OpenAPI.

### User Story 3 - Workspace Studio de Microservicios para Desarrolladores (Priority: P1)
* **Como**: Desarrollador de TCS.
* **Quiero**: Seleccionar uno de mis clientes asignados, ingresar requerimientos, generar el microservicio con LangGraph y revisar el código interactivo.
* **Criterios**:
  - Selector de cliente restringido estrictamente a las cuentas asignadas al desarrollador.
  - Asistente de generación con entrada de requerimientos y selección de contrato OpenAPI.
  - Barra de progreso de etapas LangGraph en tiempo real con telemetría (tokens consumidos, duración y costo en USD).
  - Explorador de árbol de archivos y editor de código en línea con pestañas para Java, `pom.xml`, propiedades y pruebas.
  - Soporte de edición en caliente (Human-in-the-Loop) vía `PATCH :8003/api/v1/orchestrator/jobs/{id}/files`.

### User Story 4 - Consola de Verificación en Sandbox y Descarga del .ZIP (Priority: P1)
* **Como**: Desarrollador de TCS.
* **Quiero**: Aprobar el microservicio generado, disparar la compilación real en el sandbox efímero y descargar el `.zip` con su manifiesto SHA-256.
* **Criterios**:
  - Botón de aprobación y envío al `sandbox-verifier-service:8004`.
  - Consola estilo terminal con streaming o visualización del log del compilador.
  - Tabla visual del manifiesto criptográfico `VERIFICATION_MANIFEST.json` con hashes SHA-256 por archivo.
  - Botón de descarga de archivo `.zip` verificado y empaquetado.

---

## 3. Requerimientos Técnicos y de Diseño

* **RT-001**: Puerto local predeterminado `5173` con Vite.
* **RT-002**: TypeScript estricto con interfaces completas para todos los DTOs de los 4 microservicios.
* **RT-003**: Paleta de colores oficial TCS: Azul marino oscuro (`#00142D`), Azul tecnológico (`#0076CE`), Azul claro de realce (`#00A3E0`), Grises neutros de ingeniería.
* **RT-004**: Iconografía SVG limpia (sin librerías externas pesadas ni fuentes bloatware).
* **RT-005**: Manejo centralizado de peticiones API a través de un cliente HTTP modular tipado.
