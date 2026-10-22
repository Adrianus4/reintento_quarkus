import time
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_optional_user, require_admin_or_local
from app.core.database import get_db
from app.core.vault import decrypt_secret, encrypt_secret, mask_secret
from app.models.credential import VaultCredential
from app.schemas.vault import (
    TestConnectionRequest,
    TestConnectionResponse,
    VaultKeyResponse,
    VaultKeySaveRequest,
)

router = APIRouter()


@router.get("/keys", response_model=List[VaultKeyResponse])
def list_vault_keys(
    user: dict = Depends(get_optional_user),
    db: Session = Depends(get_db)
) -> Any:
    """List stored AI provider credentials with masked keys."""
    keys = db.query(VaultCredential).order_by(VaultCredential.provider.asc()).all()
    return keys


@router.get("/status")
def get_vault_status(
    user: dict = Depends(get_optional_user),
    db: Session = Depends(get_db)
) -> Any:
    """Return dictionary of configured AI providers and masked credentials."""
    keys = db.query(VaultCredential).filter(VaultCredential.is_active == True).all()
    providers = {}
    for k in keys:
        providers[k.provider.upper()] = {
            "configured": True,
            "masked_key": k.masked_key,
        }
    return {"providers": providers}


@router.post("/keys", response_model=VaultKeyResponse, status_code=status.HTTP_201_CREATED)
def save_vault_key(
    payload: VaultKeySaveRequest,
    user: dict = Depends(require_admin_or_local),
    db: Session = Depends(get_db)
) -> Any:
    """Store or rotate an AI provider API Key with Fernet encryption at rest."""
    provider_clean = payload.provider.lower().strip()
    encrypted = encrypt_secret(payload.api_key.strip())
    masked = mask_secret(payload.api_key.strip())

    existing = db.query(VaultCredential).filter(VaultCredential.provider == provider_clean).first()
    if existing:
        existing.encrypted_key = encrypted
        existing.masked_key = masked
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return existing

    new_key = VaultCredential(
        provider=provider_clean,
        encrypted_key=encrypted,
        masked_key=masked,
        is_active=True,
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    return new_key


@router.post("/test-connection", response_model=TestConnectionResponse)
def test_vault_connection(
    payload: TestConnectionRequest,
    user: dict = Depends(get_optional_user),
    db: Session = Depends(get_db)
) -> Any:
    """Test connectivity and authentication for a configured AI provider (live or saved key)."""
    provider_clean = payload.provider.lower().strip()
    api_key = payload.api_key.strip() if payload.api_key and payload.api_key.strip() else None

    if not api_key:
        cred = db.query(VaultCredential).filter(
            VaultCredential.provider == provider_clean,
            VaultCredential.is_active == True
        ).first()

        if not cred:
            return TestConnectionResponse(
                provider=provider_clean,
                connected=False,
                latency_ms=0,
                message=f"No active credentials stored for provider '{provider_clean}'."
            )
        api_key = decrypt_secret(cred.encrypted_key)

    t0 = time.time()
    try:
        if provider_clean == "gemini":
            from app.llm.gemini_client import GeminiClient
            client = GeminiClient(api_key=api_key, model_name=payload.model_name)
        elif provider_clean == "anthropic":
            from app.llm.anthropic_client import AnthropicClient
            client = AnthropicClient(api_key=api_key, model_name=payload.model_name)
        else:
            from app.llm.openai_compat import OpenAICompatClient
            client = OpenAICompatClient(provider=provider_clean, api_key=api_key, model_name=payload.model_name, base_url=payload.base_url)

        conn_res = client.test_connection()
        if isinstance(conn_res, tuple):
            is_connected, msg = conn_res
        else:
            is_connected = bool(conn_res)
            msg = "Conexión verificada exitosamente con el proveedor de IA" if is_connected else f"Fallo de autenticación con {provider_clean}: Verifique su API Key o cuota"

        latency = int((time.time() - t0) * 1000)

        return TestConnectionResponse(
            provider=provider_clean,
            connected=is_connected,
            latency_ms=latency,
            message=msg
        )
    except Exception as exc:
        latency = int((time.time() - t0) * 1000)
        return TestConnectionResponse(
            provider=provider_clean,
            connected=False,
            latency_ms=latency,
            message=f"Error al conectar con {provider_clean}: {str(exc)}"
        )


@router.post("/keys/{provider}/test", response_model=TestConnectionResponse)
def test_vault_key_by_path(
    provider: str,
    user: dict = Depends(get_optional_user),
    db: Session = Depends(get_db)
) -> Any:
    """Alternative REST path to test connection for a specific provider."""
    return test_vault_connection(
        payload=TestConnectionRequest(provider=provider),
        user=user,
        db=db
    )
