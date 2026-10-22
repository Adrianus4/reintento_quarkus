import os
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
        """Instantiate the active LLM client directly from the configured API Key."""
        # 1. Fetch current active model_name and active_provider if set
        config = db.query(GatewayConfig).first()
        active_prov = config.active_provider.lower().strip() if config and config.active_provider else None
        model_name = getattr(config, "model_name", None) if config else None

        # Explicit offline selection must never inspect credentials or paid-provider keys.
        if active_prov == "mock":
            return MockLLMClient(mode="balanced")

        # 2. Check for matching active credential
        cred = None
        if active_prov and active_prov != "mock":
            cred = db.query(VaultCredential).filter(
                VaultCredential.provider == active_prov,
                VaultCredential.is_active == True
            ).first()

        # If not found by active_provider, take the most recent active credential
        if not cred:
            cred = db.query(VaultCredential).filter(VaultCredential.is_active == True).order_by(VaultCredential.updated_at.desc()).first()

        if cred:
            api_key = decrypt_secret(cred.encrypted_key)
            provider = cred.provider.lower().strip() if cred.provider else "openai"
            return LLMClientFactory._build_client(provider, api_key, model_name)

        # 3. Check environment variables as fallback
        for env_key, prov in [
            ("GEMINI_API_KEY", "gemini"),
            ("OPENAI_API_KEY", "openai"),
            ("ANTHROPIC_API_KEY", "anthropic"),
            ("DEEPSEEK_API_KEY", "deepseek"),
        ]:
            val = os.getenv(env_key)
            if val:
                return LLMClientFactory._build_client(prov, val.strip(), model_name)

        # 4. If no credentials are found in DB (e.g. isolated unit test suite), fallback to mock client
        return MockLLMClient(mode="balanced")

    @staticmethod
    def _build_client(provider: str, api_key: str, model_name: str = None) -> BaseLLMClient:
        """Instantiate the appropriate LLM client with auto-detection from key prefix."""
        prov = provider.lower().strip() if provider else ""

        # Auto-detect from API Key format
        if api_key.startswith("AIzaSy"):
            prov = "gemini"
        elif api_key.startswith("sk-ant"):
            prov = "anthropic"
        elif api_key.startswith("gsk_"):
            prov = "groq"
        elif api_key.startswith("sk-") and prov not in ["deepseek", "openrouter"]:
            prov = "openai"

        # Sanitize model name if it was set to placeholder
        if model_name in ("mock-fast", "default", None, ""):
            model_name = None

        if prov == "gemini":
            return GeminiClient(api_key=api_key, model_name=model_name or "gemini-1.5-flash")
        elif prov == "anthropic":
            return AnthropicClient(api_key=api_key, model_name=model_name or "claude-3-5-sonnet-20241022")
        else:
            return OpenAICompatClient(provider=prov or "openai", api_key=api_key, model_name=model_name)
