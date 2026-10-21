---
description: "Task list for Spec 005 — tcs-factory-ui implementation"
---

# Tasks: Spec 005 — tcs-factory-ui

**Input**: Design documents from `/specs/005-tcs-factory-ui/` (`spec.md`, `plan.md`, `research.md`, `data-model.md`, `quickstart.md`)
**Version Alignment**: Constitution `v1.2.0` (Principles X, XIII, XIV, XV)

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Associated User Story (`[US1]`, `[US2]`, `[US3]`, `[US4]`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Frontend SPA directory structure, npm configuration, Vite, TypeScript, and Tailwind CSS with TCS theme tokens.

- [x] T001 Initialize React 18 + Vite + TypeScript application layout in `services/tcs-factory-ui/` (`package.json`, `tsconfig.json`, `tsconfig.node.json`, `vite.config.ts`, `index.html`).
- [x] T002 [P] Configure Tailwind CSS with TCS corporate branding colors (`#00142D`, `#0076CE`, `#00A3E0`, `#0A192F`, slate neutrals) in `services/tcs-factory-ui/tailwind.config.js`, `postcss.config.js`, and `src/index.css`.
- [x] T003 [P] Define comprehensive TypeScript types and interfaces in `services/tcs-factory-ui/src/types/index.ts` covering all 4 microservices DTOs.
- [x] T004 [P] Implement centralized API client in `services/tcs-factory-ui/src/services/api.ts` connecting to ports 8001, 8002, 8003, and 8004 with Bearer authorization and error handling.

---

## Phase 2: Foundational Components & State Management

**Purpose**: Core application provider, authentication context, layout navigation bar, and main entrypoint.

- [x] T005 Implement `AuthContext.tsx` in `services/tcs-factory-ui/src/context/AuthContext.tsx` managing login, token persistence, role state (`ADMIN` vs `DEVELOPER`), assigned clients, and logout.
- [x] T006 [P] Implement `Navbar.tsx` in `services/tcs-factory-ui/src/components/Navbar.tsx` featuring official TCS branding ("TCS Intelligent Microservice Factory"), active user badge, role tag, and logout action.
- [x] T007 Implement main SPA controller in `services/tcs-factory-ui/src/App.tsx` coordinating views based on auth state and role.

---

## Phase 3: User Story 1 - Autenticación Corporativa y Asistente Zero-State (Priority: P1)

**Goal**: Provide secure TCS branded login and a Zero-State initial admin bootstrap wizard (`/setup-admin`) when no users exist.

- [x] T008 [US1] Implement `LoginModal.tsx` in `services/tcs-factory-ui/src/components/LoginModal.tsx` with standard login form and seamless toggle to the Initial SuperAdmin Bootstrap Wizard (`POST :8001/api/v1/auth/setup-admin`).
- [x] T009 [US1] Add automated zero-state detection in `AuthContext.tsx` that checks backend status and prompts the setup wizard automatically when appropriate.

---

## Phase 4: User Story 2 - Panel de Gobernanza y Bóveda para Administradores (Priority: P1)

**Goal**: Allow Administrators to manage collaborators, client tenant assignments, AI credential vault, AI provider hot-switching, and client technical profiles.

- [x] T010 [US2] Implement `AdminPanel.tsx` in `services/tcs-factory-ui/src/components/AdminPanel.tsx` with tabbed or modular layout:
  - Tab 1: **Colaboradores** (list users, register new developer, assign clients).
  - Tab 2: **Bóveda de IA & Gateway** (save/rotate Gemini/DeepSeek/Grok API keys, hot-switch active provider between Gemini, DeepSeek, Grok, Mock, select tier).
  - Tab 3: **Gobernanza de Clientes** (register client profiles, add technical directives, view OpenAPI catalog).

---

## Phase 5: User Story 3 - Workspace Studio de Microservicios para Desarrolladores (Priority: P1)

**Goal**: Allow Developers to select assigned clients, enter requirements, trigger LangGraph generation with live telemetry, and review/edit code in HITL mode.

- [x] T011 [US3] Implement `StudioPanel.tsx` in `services/tcs-factory-ui/src/components/StudioPanel.tsx` with:
  - Client selector (strictly filtered to `user.assigned_clients`).
  - OpenAPI specification selector.
  - Microservice requirements prompt input area.
  - LangGraph stage execution visualizer (Ingestion -> Architecture -> Generation -> Compilation & Test -> Completed).
  - Live telemetry display (total tokens, duration in seconds, estimated USD cost).
- [x] T012 [US3] Implement `CodeViewer.tsx` in `services/tcs-factory-ui/src/components/CodeViewer.tsx` featuring:
  - Interactive file tree explorer grouped by directory (`src/main/java/...`, `src/test/java/...`, `pom.xml`, `application.properties`).
  - Code editor panel with syntax highlighting appearance and line numbering.
  - Human-in-the-Loop hot edit capability saving file modifications via `PATCH :8003/api/v1/orchestrator/jobs/{id}/files`.

---

## Phase 6: User Story 4 - Consola de Verificación en Sandbox y Descarga del .ZIP (Priority: P1)

**Goal**: Allow Developers to approve generated microservices, trigger sandbox verification on port 8004, inspect compiler logs, view cryptographic SHA-256 manifest, and download the `.zip`.

- [x] T013 [US4] Implement `VerifierModal.tsx` in `services/tcs-factory-ui/src/components/VerifierModal.tsx` featuring:
  - Approval action triggering `POST :8004/api/v1/verifier/runs`.
  - Terminal-style compilation log viewer displaying Maven / syntax validation output.
  - Visual table of `VERIFICATION_MANIFEST.json` showing file paths, SHA-256 hashes, and file sizes.
  - Direct download button for the generated microservice `.zip` package (`GET :8004/api/v1/verifier/runs/{run_id}/download`).

---

## Phase 7: Polish & End-to-End Orchestration

**Purpose**: Build validation, dependency installation, and end-to-end multi-service runner.

- [x] T014 Install frontend dependencies and verify TypeScript compilation with `npm.cmd run build` without errors.
- [x] T015 Create unified startup orchestrator script `scripts/start_factory.ps1` to launch all 4 microservices (ports 8001, 8002, 8003, 8004) and the UI (port 5173).
- [x] T016 Document complete user manual and system guide in `services/tcs-factory-ui/README.md`.

