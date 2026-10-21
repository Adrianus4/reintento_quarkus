# Quickstart: Spec 004 — sandbox-verifier-service

## 1. Prerequisites
- Python 3.11+
- Optional: Apache Maven (`mvn`) on PATH for native compilation runs.

## 2. Environment Configuration
Create a `.env` in `services/sandbox-verifier-service/`:

```env
PORT=8004
HOST=0.0.0.0
DATABASE_URL=sqlite:///./verifier_factory_local.db
SANDBOX_BASE_PATH=./sandbox_runs
JWT_SECRET_KEY=tcs-factory-dev-secret-change-in-prod-0987654321
JWT_ALGORITHM=HS256
```

## 3. Installation & Run
```bash
cd services/sandbox-verifier-service
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Unix:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

## 4. Verification

### Step 1: Health Check
```bash
curl http://localhost:8004/api/v1/health
```

### Step 2: Trigger Verification Run
```bash
curl -X POST http://localhost:8004/api/v1/verifier/runs \
  -H "Authorization: Bearer <DEVELOPER_JWT>" \
  -H "Content-Type: application/json" \
  -d '{
    "client_code": "bcp",
    "files": {
      "pom.xml": "<project>...</project>",
      "src/main/resources/application.properties": "quarkus.http.port=8080\n",
      "src/main/java/com/bcp/Hello.java": "package com.bcp;\npublic class Hello {}"
    }
  }'
```

### Step 3: Download Generated ZIP
```bash
curl -O -J -H "Authorization: Bearer <DEVELOPER_JWT>" http://localhost:8004/api/v1/verifier/runs/<RUN_ID>/download
```

