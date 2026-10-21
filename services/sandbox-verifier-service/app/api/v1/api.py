from fastapi import APIRouter
from app.api.v1.verifier import router as verifier_router

api_router = APIRouter()
api_router.include_router(verifier_router, prefix="/verifier", tags=["verifier"])

