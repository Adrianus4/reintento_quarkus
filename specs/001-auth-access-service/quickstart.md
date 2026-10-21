# Quickstart: Spec 001 — auth-access-service

## 1. Prerequisites
- Python 3.11+
- Virtual environment (`venv` or `conda`)

## 2. Environment Configuration
Create a `.env` file in `services/auth-access-service/`:

```env
PORT=8001
HOST=0.0.0.0
DATABASE_URL=sqlite:///./auth_factory_local.db
JWT_SECRET_KEY=tcs-factory-dev-secret-change-in-prod-0987654321
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
```

## 3. Installation & Run
```bash
cd services/auth-access-service
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Unix:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 4. Verification & Initial Bootstrap

### Step 1: Health Check
```bash
curl http://localhost:8001/api/v1/health
```

### Step 2: Bootstrap First Administrator (Zero Preloaded State)
```bash
curl -X POST http://localhost:8001/api/v1/auth/setup-admin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@tcs.com",
    "password": "Password123!",
    "full_name": "TCS Lead Administrator"
  }'
```

### Step 3: Login to Obtain JWT
```bash
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@tcs.com",
    "password": "Password123!"
  }'
```

### Step 4: Inter-Service Token Verification
```bash
curl -X POST http://localhost:8001/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{
    "token": "<JWT_FROM_STEP_3>"
  }'
```

## 5. Automated Tests
```bash
cd services/auth-access-service
pytest -v
```

