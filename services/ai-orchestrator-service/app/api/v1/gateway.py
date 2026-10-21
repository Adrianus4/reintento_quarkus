from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_verified_user, require_admin
from app.core.database import get_db
from app.models.gateway_config import GatewayConfig
from app.schemas.gateway import GatewayConfigResponse, GatewayConfigUpdate

router = APIRouter()


def _get_or_create_config(db: Session) -> GatewayConfig:
    config = db.query(GatewayConfig).first()
    if not config:
        config = GatewayConfig(
            active_provider="mock",
            consumption_mode="balanced",
            temperature=0.2,
            max_tokens=8192,
        )
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


@router.get("/config", response_model=GatewayConfigResponse)
def get_gateway_config(
    user: dict = Depends(get_verified_user),
    db: Session = Depends(get_db)
) -> Any:
    """Retrieve active AI gateway provider and consumption mode."""
    return _get_or_create_config(db)


@router.put("/config", response_model=GatewayConfigResponse)
def update_gateway_config(
    payload: GatewayConfigUpdate,
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Any:
    """Update active provider, consumption mode, or temperature in hot-switch. Requires ADMIN role."""
    config = _get_or_create_config(db)

    if payload.active_provider is not None:
        config.active_provider = payload.active_provider.lower().strip()
    if payload.model_name is not None:
        config.model_name = payload.model_name.strip()
    if payload.consumption_mode is not None:
        config.consumption_mode = payload.consumption_mode.lower().strip()
    if payload.temperature is not None:
        config.temperature = payload.temperature
    if payload.max_tokens is not None:
        config.max_tokens = payload.max_tokens

    db.commit()
    db.refresh(config)
    return config

