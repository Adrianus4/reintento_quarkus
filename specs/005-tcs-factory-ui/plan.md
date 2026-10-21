# Implementation Plan: Spec 005 — tcs-factory-ui

**Branch**: `005-tcs-factory-ui` | **Date**: 2026-10-21 | **Spec**: [specs/005-tcs-factory-ui/spec.md](specs/005-tcs-factory-ui/spec.md)

**Input**: Feature specification from `specs/005-tcs-factory-ui/spec.md`

## Summary

Implement the enterprise web application **`tcs-factory-ui`** running on port `5173` using **React 18 + Vite + TypeScript + Tailwind CSS** with official Tata Consultancy Services branding. It orchestrates the 4 backend microservices (`auth-access-service` :8001, `client-governance-service` :8002, `ai-orchestrator-service` :8003, `sandbox-verifier-service` :8004). It provides a complete Zero-State initial admin wizard, role-based access control (`ADMIN` vs `DEVELOPER`), dynamic client isolation, AI vault & provider hot-switching, LangGraph telemetry studio, interactive code explorer with HITL editing, and sandbox verification with SHA-256 manifest and `.zip` download.

## Technical Context

**Language/Version**: TypeScript 5.4+, React 18.3+
**Primary Dependencies**: Vite, Tailwind CSS, Lucide icons (SVG based), Axios / native Fetch
**Storage**: Client-side auth tokens in `sessionStorage` / `localStorage`
**Testing**: Typecheck (`tsc --noEmit`), Vite build validation (`vite build`)
**Target Platform**: Web Browsers (Chrome, Firefox, Edge) / Localhost Port 5173
**Project Type**: Single Page Application (SPA)
**Performance Goals**: First contentful paint < 500ms, HMR < 50ms
**Constraints**: TCS corporate design system (`#00142D`, `#0076CE`, `#00A3E0`), strict 2-role UI enforcement, zero mock data hardcoded.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked post-design.*

| Principle | Compliance Assessment | Status |
|---|---|---|
| **X. Experiencia Corporativa TCS** | UI profesional con identidad visual TCS ("Workspace Studio"), sin bloatware ni estilos infantiles. | PASS |
| **XIII. Arquitectura Fábrica** | Puerto formal 5173, estructura en `services/tcs-factory-ui/`. | PASS |
| **XIV. Zero Preloaded Data** | Asistente de arranque limpio para inicializar el SuperAdmin vía `/setup-admin`. | PASS |
| **XV. Dos Roles Únicos** | Separación estricta de vistas y acciones entre `ADMIN` y `DEVELOPER`. | PASS |

## Project Structure

### Source Code Layout

```text
services/tcs-factory-ui/
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── context/
│   │   └── AuthContext.tsx
│   ├── services/
│   │   └── api.ts
│   ├── components/
│   │   ├── Navbar.tsx
│   │   ├── LoginModal.tsx
│   │   ├── AdminPanel.tsx
│   │   ├── StudioPanel.tsx
│   │   ├── CodeViewer.tsx
│   │   └── VerifierModal.tsx
│   └── types/
│       └── index.ts
└── README.md
```

## Complexity Tracking

> **No Constitution violations detected.** Full distributed microservices alignment, isolated client views, zero hardcoded tenant data.
