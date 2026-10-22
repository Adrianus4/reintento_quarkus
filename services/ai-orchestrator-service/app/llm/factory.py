from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.core.vault import decrypt_secret
from app.llm.base import BaseLLMClient
from app.llm.gemini_client import GeminiClient
from app.llm.anthropic_client import AnthropicClient
from app.llm.mock_client import MockLLMClient
from app.llm.openai_compat import OpenAICompatClient
from app.models.credential import VaultCredential
from app.models.gateway_config import GatewayConfig


class LLMClientFactory:
    @staticmethod
    def get_client(db: Session) -> BaseLLMClient:
        config = db.query(GatewayConfig).first()
        if not config:
            return MockLLMClient(mode="balanced")

        provider = config.active_provider.lower().strip()
        mode = getattr(config, "consumption_mode", "standard") or "standard"
        model_name = getattr(config, "model_name", None)

        if provider == "mock":
            return MockLLMClient(mode=mode)

        # Retrieve and decrypt credential
        cred = db.query(VaultCredential).filter(
            VaultCredential.provider == provider,
            VaultCredential.is_active == True
        ).first()

        if not cred:
            raise HTTPException(
                status_code=400,
                detail=f"No se ha registrado una API Key para el proveedor '{provider.upper()}'. Por favor ingrese su API Key en la configuración de IA."
            )

        api_key = decrypt_secret(cred.encrypted_key)

        if provider == "gemini":
            return GeminiClient(api_key=api_key, mode=mode, model_name=model_name)
        elif provider == "anthropic":
            return AnthropicClient(api_key=api_key, mode=mode, model_name=model_name)
        else:
            # Handles openai, deepseek, grok, openrouter, groq, ollama, etc.
            return OpenAICompatClient(provider=provider, api_key=api_key, mode=mode, model_name=model_name)
