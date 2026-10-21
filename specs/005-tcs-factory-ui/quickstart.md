# Quickstart: Spec 005 — tcs-factory-ui

## 1. Prerequisites
- Node.js 18+ (verified: v24.11.1)
- npm (verified: 11.6.2)
- All 4 microservices running locally:
  - `auth-access-service`: `http://localhost:8001`
  - `client-governance-service`: `http://localhost:8002`
  - `ai-orchestrator-service`: `http://localhost:8003`
  - `sandbox-verifier-service`: `http://localhost:8004`

## 2. Installation & Run
```bash
cd services/tcs-factory-ui
npm.cmd install
npm.cmd run dev
```

The application will be accessible at: `http://localhost:5173`

## 3. Initial Setup Journey (Zero Preloaded Data)
1. Open `http://localhost:5173`.
2. When prompted by the Zero-State Wizard, create the first TCS SuperAdmin:
   - Username: `superadmin`
   - Email: `admin@tcs.com`
   - Password: `AdminPassword123!`
3. Log in as SuperAdmin.
4. In the Admin Panel:
   - Add a test client profile (e.g. `bcp` - Banco de Crédito del Perú).
   - Set active AI Provider (e.g., `MOCK` for offline determinism or `GEMINI`/`DEEPSEEK` with your API Key).
   - Create a developer collaborator (e.g. `dev_tcs` assigned to `bcp`).
5. Log out and log in as `dev_tcs`:
   - Developer will see only assigned client `bcp`.
   - Enter microservice requirements and generate.
   - Inspect files, edit in HITL mode.
   - Verify in Sandbox and download verified `.zip`.

