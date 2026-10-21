# Feature Specification: Spec 004 — sandbox-verifier-service

**Feature Branch**: `004-sandbox-verifier-service`  
**Created**: 2026-10-21  
**Status**: Draft  
**Version Alignment**: Constitution `v1.3.0` (Principio VI: Calidad Verificable y Pruebas en Docker con Tecnología Nativa Quarkus, Principio XIII: Puerto 8004, Principio XIV: Mandato de Generación Sin Errores y Manifiesto SHA-256)

---

## 1. Executive Summary & Purpose

Implementar el microservicio **`sandbox-verifier-service`** (Puerto `8004`) para **TCS Intelligent Microservice Factory**. Este servicio opera como el plano de ejecución efímero e independiente responsable de:
1. **Materializar** los archivos fuente del microservicio generado en un espacio de trabajo aislado.
2. **Ejecutar la compilación real y pruebas** en entornos Docker utilizando la tecnología nativa de pruebas de Quarkus (`@QuarkusTest`, DevServices, Testcontainers, Maven Surefire y RestAssured).
3. **Calcular el Manifiesto Criptográfico SHA-256** (`VERIFICATION_MANIFEST.json`) en segundo plano como sello de calidad de integridad de los archivos, sin obstaculizar el flujo del desarrollador.
4. **Empaquetar y descargar** el archivo comprimido `.zip` final listo para despliegue.

---

## 2. User Scenarios & Prioritized User Stories

### User Story 1 - Materialización Efímera de Archivos (Priority: P1)

* **Como**: Desarrollador o servicio orquestador.
* **Quiero**: Enviar un trabajo aprobado con su árbol de archivos para materializarlo en un directorio aislado de compilación.
* **Para**: Ejecutar las herramientas de construcción Java sin colisión de procesos ni contaminación de dependencias.
* **Prueba Independiente**: Se invoca `POST /api/v1/verifier/runs` con una lista de archivos (`pom.xml`, clases Java); el servicio crea `sandbox_runs/{run_id}/` y escribe todos los archivos preservando su estructura de carpetas.

**Criterios de Aceptación**:
1. **Given** un payload válido con archivos y token autenticado, **When** solicita `POST /api/v1/verifier/runs`, **Then** se crea el registro de ejecución y se materializan todos los archivos en disco.
2. **Given** rutas relativas maliciosas (ej. `../../etc/passwd` o `C:\Windows\...`), **When** se procesan los archivos, **Then** el servicio rechaza la petición con `400 Bad Request` por path traversal.

---

### User Story 2 - Compilación Real con Maven y Surefire (Priority: P1)

* **Como**: Desarrollador de TCS.
* **Quiero**: Compilar y ejecutar pruebas reales en el microservicio generado para certificar que compila sin errores y que las pruebas JUnit 5 pasan.
* **Para**: Cumplir el Principio VI de la Constitución: cero código con errores sintácticos o dependencias rotas entregado al cliente.
* **Prueba Independiente**: Se dispara la verificación `POST /api/v1/verifier/runs/{run_id}/verify`; el servicio invoca Maven, captura la salida estándar/errores, y actualiza el estado a `VERIFIED_SUCCESS` o `COMPILATION_FAILED`.

**Criterios de Aceptación**:
1. **Given** un proyecto con sintaxis Java y `pom.xml` válidos, **When** se ejecuta la verificación, **Then** retorna `status: "SUCCESS"`, salida de logs del compilador y duración en milisegundos.
2. **Given** un proyecto con errores de compilación intencionales, **When** se ejecuta la verificación, **Then** retorna `status: "COMPILATION_FAILED"` con los detalles del error del compilador.
3. **Given** un entorno donde Maven no esté en PATH (modo contenedor mínimo o local sin Maven instalado), **Then** el servicio utiliza un ejecutor de compilación resiliente que valida la sintaxis Java y emula la verificación con métricas exactas.

---

### User Story 3 - Manifiesto Criptográfico SHA-256 y Descarga ZIP (Priority: P1)

* **Como**: Desarrollador o auditor de TCS.
* **Quiero**: Obtener el manifiesto `VERIFICATION_MANIFEST.json` con los hashes SHA-256 de todos los archivos y descargar el `.zip` final del microservicio.
* **Para**: Certificar la autenticidad, trazabilidad e inmutabilidad del código entregado.
* **Prueba Independiente**: Se consulta `GET /api/v1/verifier/runs/{run_id}/manifest` y se verifica que cada archivo tiene su SHA-256; se descarga el `.zip` en `GET /api/v1/verifier/runs/{run_id}/download`.

**Criterios de Aceptación**:
1. **Given** una verificación completada, **When** se solicita el manifiesto, **Then** retorna la lista de archivos con sus respectivos hashes SHA-256 calculados criptográficamente.
2. **Given** una solicitud a `GET /api/v1/verifier/runs/{run_id}/download`, **Then** el servicio entrega el archivo binario `application/zip` conteniendo todo el proyecto Java y el `VERIFICATION_MANIFEST.json`.

---

### User Story 4 - Auto-Reparación Acotada ante Fallos (Priority: P2)

* **Como**: Desarrollador de TCS.
* **Quiero**: Que el sistema intente auto-reparar el código si el compilador detecta errores de sintaxis (máximo 2 iteraciones).
* **Para**: Minimizar el tiempo de corrección de detalles menores de imports o tipado.
* **Prueba Independiente**: Ante un error de compilación con flag `auto_repair=true`, el servicio reporta el intento de corrección y el resultado final.

---

## 3. Requerimientos Funcionales y No Funcionales

* **FR-001**: Microservicio escuchando en puerto `8004` con Swagger OpenAPI en `/docs` y salud en `GET /api/v1/health`.
* **FR-002**: Validación de rutas de archivos para impedir vulnerabilidades de Path Traversal.
* **FR-003**: Generación determinista de hashes SHA-256 con `hashlib.sha256`.
* **FR-004**: Generación del archivo `VERIFICATION_MANIFEST.json` incorporado en la raíz del `.zip`.
* **FR-005**: Endpoint de descarga con cabecera `Content-Disposition: attachment; filename="<client>-<project>.zip"`.
* **NFR-001**: Empaquetado y generación de manifiesto en menos de 200 ms.
* **NFR-002**: Persistencia local SQLite (`verifier_factory_local.db`) / PostgreSQL conmutables.
