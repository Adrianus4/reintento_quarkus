from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models.gateway_config import GatewayConfig


from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.database import Base, SessionLocal, engine
from app.models.gateway_config import GatewayConfig


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(gateway_configurations);"))
            cols = [row[1] for row in res.fetchall()]
            if cols and "model_name" not in cols:
                conn.execute(text("ALTER TABLE gateway_configurations ADD COLUMN model_name VARCHAR(100) DEFAULT 'mock-fast';"))
                conn.commit()
        except Exception:
            pass

    # Ensure default gateway config exists
    db = SessionLocal()
    try:
        config = db.query(GatewayConfig).first()
        if not config:
            config = GatewayConfig(
                active_provider="gemini",
                model_name="gemini-1.5-flash",
                consumption_mode="balanced",
                temperature=0.2,
                max_tokens=8192,
            )
            db.add(config)
            db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="TCS Intelligent Microservice Factory — AI Credential Vault, Multi-Provider Gateway & LangGraph Orchestrator",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get(f"{settings.API_V1_STR}/health", tags=["health"])
def health_check():
    """Health check endpoint for container orchestrators and load balancers."""
    return {
        "status": "ok",
        "service": "ai-orchestrator-service",
        "port": settings.PORT,
        "version": settings.VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)

