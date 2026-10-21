# TCS Intelligent Microservice Factory — UI (tcs-factory-ui)

The corporate frontend SPA for Tata Consultancy Services collaborators, built with **React 18**, **Vite**, **TypeScript**, and **Tailwind CSS** under TCS brand identity ("Workspace Studio").

## Features

- **TCS Brand Identity**: Deep Navy (`#00142D`), Technology Blue (`#0076CE`), Accent Cyan (`#00A3E0`), and clean engineering dark surfaces.
- **Port 5173 Alignment**: Strict conformance to Constitution Principle XIII.
- **Strict 2-Role Support**: Direct RBAC UI adaptation for `ADMIN` and `DEVELOPER`.
- **Zero-State Initial Setup Wizard**: Bootstrap the first SuperAdmin safely via `/setup-admin`.
- **Developer Account Isolation**: Developers can only access clients assigned to their profile.
- **AI Vault & Hot-Switching Gateway**: Real-time LLM provider switching (Gemini, DeepSeek, Grok, Mock) without downtime.
- **LangGraph Multi-Agent Studio**: Live 5-stage pipeline tracking with token and cost telemetry.
- **Interactive Code Viewer & Hot Editing (HITL)**: Full file tree explorer with inline edits persisted via `PATCH`.
- **Sandbox Verifier Console**: Live compiler logs, SHA-256 cryptographic manifest (`VERIFICATION_MANIFEST.json`), and one-click `.zip` bundle download.

## Running Locally

```bash
cd services/tcs-factory-ui
npm.cmd install
npm.cmd run dev
```

Visit: `http://localhost:5173`

