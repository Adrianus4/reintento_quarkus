from sqlalchemy.orm import Session
from app.core.vault import decrypt_secret
from app.llm.base import BaseLLMClient
from app.llm.gemini_client import GeminiClient
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

        provider = config.active_provider.lower()
        mode = config.consumption_mode

        if provider == "mock":
            return MockLLMClient(mode=mode)

        # Retrieve and decrypt credential
        cred = db.query(VaultCredential).filter(
            VaultCredential.provider == provider,
            VaultCredential.is_active == True
        ).first()

        if not cred:
            # Fallback to mock if API key is missing
            return MockLLMClient(mode=mode)

        api_key = decrypt_secret(cred.encrypted_key)

        if provider == "gemini":
            return GeminiClient(api_key=api_key, mode=mode)
        elif provider in ["deepseek", "grok"]:
            return OpenAICompatClient(provider=provider, api_key=api_key, mode=mode)

        return MockLLMClient(mode=mode)

