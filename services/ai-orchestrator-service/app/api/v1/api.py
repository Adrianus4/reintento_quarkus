from fastapi import APIRouter
from app.api.v1.vault import router as vault_router
from app.api.v1.gateway import router as gateway_router
from app.api.v1.orchestrator import router as orchestrator_router

api_router = APIRouter()
api_router.include_router(vault_router, prefix="/vault", tags=["vault"])
api_router.include_router(gateway_router, prefix="/ai-gateway", tags=["gateway"])
api_router.include_router(orchestrator_router, prefix="/orchestrator", tags=["orchestrator"])

