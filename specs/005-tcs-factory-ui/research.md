# Phase 0 Research: Spec 005 — tcs-factory-ui

## 1. Technical Decisions & Trade-Offs

### 1.1 Language & Framework
- **Decision**: **React 18+** with **Vite** and **TypeScript** running on port `5173`.
- **Styling**: **Tailwind CSS** with TCS corporate branding colors:
  - Deep Navy background: `#00142D`
  - Technology Blue primary: `#0076CE`
  - Accent Cyan: `#00A3E0`
  - Crisp Slate & Neutral dark surfaces: `#0A192F`, `#1E293B`, `#334155`
- **Rationale**: Vite provides instant HMR (< 50ms), lightning-fast builds, and zero-overhead TypeScript compilation.

### 1.2 Microservices Distributed Connection Pattern
- The SPA connects to the 4 backend microservices:
  - `AUTH_API`: `http://localhost:8001/api/v1`
  - `GOVERNANCE_API`: `http://localhost:8002/api/v1`
  - `ORCHESTRATOR_API`: `http://localhost:8003/api/v1`
  - `VERIFIER_API`: `http://localhost:8004/api/v1`
- Centralized API Client (`src/services/api.ts`) injects Bearer token in all outbound requests and handles 401 token expiration.

### 1.3 State Management & RBAC Routing
- Single `AuthContext` provides `user`, `token`, `role` (`ADMIN` or `DEVELOPER`), and `assigned_clients`.
- Views adapt seamlessly based on role:
  - Admin sees user governance, vault credentials, AI gateway settings, and client profiles.
  - Developer sees only their assigned clients and generation studio.

---

## 2. Directory Layout Decision

```text
services/tcs-factory-ui/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── context/
│   │   └── AuthContext.tsx       # Auth provider, login, logout, setup-admin
│   ├── services/
│   │   └── api.ts                # HTTP clients for ports 8001, 8002, 8003, 8004
│   ├── components/
│   │   ├── Navbar.tsx            # TCS branding, user badge, role tag, logout
│   │   ├── LoginModal.tsx        # Login and initial admin bootstrap wizard
│   │   ├── AdminPanel.tsx        # Users, AI Vault, Gateway hot-switch, Client governance
│   │   ├── StudioPanel.tsx       # Requirements prompt, OpenAPI selector, LangGraph telemetry
│   │   ├── CodeViewer.tsx        # Tree explorer, file editor (HITL), syntax styling
│   │   └── VerifierModal.tsx     # Compilation console, SHA-256 manifest, ZIP download
│   └── types/
│       └── index.ts              # Full TypeScript interfaces for all 4 microservices
```

