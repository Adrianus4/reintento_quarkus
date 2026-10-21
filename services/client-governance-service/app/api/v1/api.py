from fastapi import APIRouter
from app.api.v1.clients import router as clients_router
from app.api.v1.directives import router as directives_router
from app.api.v1.contracts import router as contracts_router
from app.api.v1.governance import router as governance_router

api_router = APIRouter()
api_router.include_router(clients_router, prefix="/clients", tags=["clients"])
api_router.include_router(directives_router, prefix="/clients", tags=["directives"])
api_router.include_router(contracts_router, prefix="/clients", tags=["contracts"])
api_router.include_router(governance_router, prefix="/clients", tags=["governance"])

