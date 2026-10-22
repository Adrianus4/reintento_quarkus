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


@router.post("/direct-key")
def setup_direct_key(
    payload: dict,
    user: dict = Depends(get_optional_user),
    db: Session = Depends(get_db)
) -> Any:
    """Setup and activate an API Key directly with zero gateway configuration."""
    api_key = payload.get("api_key", "").strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="Debe ingresar una API Key válida.")

    model_name = payload.get("model_name", "").strip() or None
    provider = payload.get("provider", "").strip().lower()

    # Prioritize user explicit selection (GEMINI, DEEPSEEK, OPENAI, ANTHROPIC, etc.)
    valid_providers = ["deepseek", "gemini", "openai", "anthropic", "grok", "groq", "openrouter", "ollama"]
    if provider in valid_providers:
        if provider == "deepseek" and not model_name:
            model_name = "deepseek-chat"
        elif provider == "gemini" and not model_name:
            model_name = "gemini-1.5-flash"
        elif provider == "openai" and not model_name:
            model_name = "gpt-4o"
        elif provider == "anthropic" and not model_name:
            model_name = "claude-3-5-sonnet-20241022"
        elif provider == "groq" and not model_name:
            model_name = "llama-3.3-70b-versatile"
    else:
        # Auto-detect from key or model name if omitted
        if "deepseek" in (model_name or "").lower():
            provider = "deepseek"
            model_name = model_name or "deepseek-chat"
        elif api_key.startswith("AIzaSy"):
            provider = "gemini"
            model_name = model_name or "gemini-1.5-flash"
        elif api_key.startswith("sk-ant"):
            provider = "anthropic"
            model_name = model_name or "claude-3-5-sonnet-20241022"
        elif api_key.startswith("gsk_"):
            provider = "groq"
            model_name = model_name or "llama-3.3-70b-versatile"
        elif "gemini" in (model_name or "").lower():
            provider = "gemini"
            model_name = model_name or "gemini-1.5-flash"
        elif "claude" in (model_name or "").lower():
            provider = "anthropic"
            model_name = model_name or "claude-3-5-sonnet-20241022"
        else:
            provider = "openai"
            model_name = model_name or "gpt-4o"

    force = bool(payload.get("force", False))

    # Strip accidental quotes or Bearer prefix without touching key payload
    changed = True
    while changed:
        changed = False
        if (api_key.startswith('"') and api_key.endswith('"')) or (api_key.startswith("'") and api_key.endswith("'")):
            api_key = api_key[1:-1].strip()
            changed = True
        if api_key.lower().startswith("bearer "):
            api_key = api_key[7:].strip()
            changed = True

    t0 = time.time()
    try:
        if provider == "gemini":
            from app.llm.gemini_client import GeminiClient
            client = GeminiClient(api_key=api_key, model_name=model_name)
        elif provider == "anthropic":
            from app.llm.anthropic_client import AnthropicClient
            client = AnthropicClient(api_key=api_key, model_name=model_name)
        else:
            from app.llm.openai_compat import OpenAICompatClient
            client = OpenAICompatClient(provider=provider, api_key=api_key, model_name=model_name)

        conn_res = client.test_connection()
        if isinstance(conn_res, tuple):
            is_connected, msg = conn_res
        else:
            is_connected = bool(conn_res)
            msg = "Conexión exitosa" if is_connected else f"Fallo de autenticación con {provider}"

        latency = int((time.time() - t0) * 1000)

        if not is_connected and not force:
            return {
                "success": False,
                "provider": provider.upper(),
                "model_name": model_name,
                "latency_ms": latency,
                "message": msg,
                "can_force": True,
            }

        encrypted = encrypt_secret(api_key)
        masked = mask_secret(api_key)

        existing = db.query(VaultCredential).filter(VaultCredential.provider == provider).first()
        if existing:
            existing.encrypted_key = encrypted
            existing.masked_key = masked
            existing.is_active = True
        else:
            existing = VaultCredential(
                provider=provider,
                encrypted_key=encrypted,
                masked_key=masked,
                is_active=True,
            )
            db.add(existing)

        from app.models.gateway_config import GatewayConfig
        cfg = db.query(GatewayConfig).first()
        if cfg:
            cfg.active_provider = provider
            cfg.model_name = model_name
        else:
            cfg = GatewayConfig(active_provider=provider, model_name=model_name)
            db.add(cfg)

        db.commit()

        return {
            "success": True,
            "provider": provider.upper(),
            "model_name": model_name,
            "masked_key": masked,
            "latency_ms": latency,
            "message": f"API Key verificada y activada exitosamente para {provider.upper()} ({model_name}).",
        }
    except Exception as exc:
        latency = int((time.time() - t0) * 1000)
        return {
            "success": False,
            "provider": provider.upper(),
            "model_name": model_name,
            "latency_ms": latency,
            "message": f"Error conectando con {provider}: {str(exc)}",
        }


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

@router.delete("/keys/{provider}")
def delete_vault_key(
    provider: str,
    user: dict = Depends(get_optional_user),
    db: Session = Depends(get_db)
) -> Any:
    """Delete a stored API Key for a provider."""
    provider_clean = provider.lower().strip()
    cred = db.query(VaultCredential).filter(VaultCredential.provider == provider_clean).first()
    if not cred:
        raise HTTPException(status_code=404, detail=f"No se encontró ninguna credencial para '{provider_clean}'.")

    db.delete(cred)

    # If active provider was this one, reset gateway config
    from app.models.gateway_config import GatewayConfig
    cfg = db.query(GatewayConfig).first()
    if cfg and cfg.active_provider == provider_clean:
        # Check if there is another credential available
        other = db.query(VaultCredential).filter(VaultCredential.provider != provider_clean, VaultCredential.is_active == True).first()
        if other:
            cfg.active_provider = other.provider
        else:
            cfg.active_provider = "gemini"
            cfg.model_name = "gemini-1.5-flash"

    db.commit()
    return {"success": True, "provider": provider_clean.upper(), "message": f"Credencial de {provider.upper()} eliminada exitosamente."}


@router.delete("/keys")
def clear_all_vault_keys(
    user: dict = Depends(get_optional_user),
    db: Session = Depends(get_db)
) -> Any:
    """Clear all stored API keys in the vault."""
    db.query(VaultCredential).delete()
    from app.models.gateway_config import GatewayConfig
    cfg = db.query(GatewayConfig).first()
    if cfg:
        cfg.active_provider = "gemini"
        cfg.model_name = "gemini-1.5-flash"
    db.commit()
    return {"success": True, "message": "Todas las credenciales fueron eliminadas de la bóveda."}
