# Quickstart: Spec 003 — ai-orchestrator-service

## 1. Prerequisites
- Python 3.11+
- Running `auth-access-service` (:8001) and `client-governance-service` (:8002).

## 2. Environment Configuration
Create a `.env` in `services/ai-orchestrator-service/`:

```env
PORT=8003
HOST=0.0.0.0
DATABASE_URL=sqlite:///./orchestrator_factory_local.db
VAULT_MASTER_KEY=ZTM0NzY5YmM3OGE4OWQwZTFhMmIzYzRkNTVmNmU3YTg=
JWT_SECRET_KEY=tcs-factory-dev-secret-change-in-prod-0987654321
JWT_ALGORITHM=HS256
GOVERNANCE_SERVICE_URL=http://localhost:8002/api/v1
```

## 3. Installation & Run
```bash
cd services/ai-orchestrator-service
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Unix:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

## 4. Verification

### Step 1: Health Check
```bash
curl http://localhost:8003/api/v1/health
```

### Step 2: Store an API Key in Encrypted Vault
```bash
curl -X POST http://localhost:8003/api/v1/vault/keys \
  -H "Authorization: Bearer <ADMIN_JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "gemini",
    "api_key": "AIzaSyFakeDevTestKeyForVaultTesting123456"
  }'
```

### Step 3: Configure AI Gateway in Hot-Switch
```bash
curl -X PUT http://localhost:8003/api/v1/ai-gateway/config \
  -H "Authorization: Bearer <ADMIN_JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "active_provider": "mock",
    "consumption_mode": "balanced",
    "temperature": 0.2
  }'
```

### Step 4: Run Microservice Generation Job
```bash
curl -X POST http://localhost:8003/api/v1/orchestrator/jobs \
  -H "Authorization: Bearer <DEVELOPER_JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_code": "bcp",
    "requirements": "Microservicio REST con Java 17 y Quarkus para consulta de saldo de cuentas corrientes con Panache y validaciones Bean."
  }'
```

