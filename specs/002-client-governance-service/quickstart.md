# Quickstart: Spec 002 — client-governance-service

## 1. Prerequisites
- Python 3.11+
- Running `auth-access-service` on port `8001` (optional for local mock mode, required for full integration).

## 2. Environment Configuration
Create a `.env` in `services/client-governance-service/`:

```env
PORT=8002
HOST=0.0.0.0
DATABASE_URL=sqlite:///./governance_factory_local.db
AUTH_SERVICE_VERIFY_URL=http://localhost:8001/api/v1/auth/verify
JWT_SECRET_KEY=tcs-factory-dev-secret-change-in-prod-0987654321
JWT_ALGORITHM=HS256
```

## 3. Installation & Run
```bash
cd services/client-governance-service
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Unix:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

## 4. Verification

### Step 1: Health Check
```bash
curl http://localhost:8002/api/v1/health
```

### Step 2: Create Client Profile (Admin Token from Port 8001)
```bash
curl -X POST http://localhost:8002/api/v1/clients \
  -H "Authorization: Bearer <ADMIN_JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "bcp",
    "name": "Banco de Credito del Peru",
    "description": "Banking client with strict resilience and security standards",
    "package_prefix": "com.bcp.enterprise",
    "java_version": "17",
    "quarkus_version": "3.15.1"
  }'
```

### Step 3: Add Technical Directive
```bash
curl -X POST http://localhost:8002/api/v1/clients/bcp/directives \
  -H "Authorization: Bearer <ADMIN_JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_code": "SEC_JWT_MANDATORY",
    "category": "SECURITY",
    "severity": "MANDATORY",
    "description": "All public endpoints must validate JWT tokens via SmallRye JWT.",
    "deterministic_check": "check_smallrye_jwt_dependency"
  }'
```

### Step 4: Upload OpenAPI Contract
```bash
curl -X POST http://localhost:8002/api/v1/clients/bcp/contracts \
  -H "Authorization: Bearer <ADMIN_OR_DEV_JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Cards Payment API",
    "version": "1.0.0",
    "format": "json",
    "raw_content": "{\"openapi\": \"3.0.1\", \"info\": {\"title\": \"Cards Payment API\", \"version\": \"1.0.0\"}, \"paths\": {\"/cards/pay\": {\"post\": {\"summary\": \"Execute payment\"}}}}"
  }'
```

