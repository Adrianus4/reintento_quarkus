import base64
import os
from typing import List
from cryptography.fernet import Fernet
from pydantic_settings import BaseSettings, SettingsConfigDict


def _generate_default_vault_key() -> str:
    # Deterministic default key for local MVP dev
    raw = b"tcs-factory-master-vault-key-32b"  # exactly 32 bytes
    return base64.urlsafe_b64encode(raw).decode("utf-8")


class Settings(BaseSettings):
    PROJECT_NAME: str = "TCS Intelligent Microservice Factory — AI Orchestrator Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    HOST: str = "0.0.0.0"
    PORT: int = 8003

    # Database
    DATABASE_URL: str = "sqlite:///./orchestrator_factory_local.db"

    # Vault master key (Fernet urlsafe base64-encoded 32-byte key)
    VAULT_MASTER_KEY: str = _generate_default_vault_key()

    # Inter-service URLs
    GOVERNANCE_SERVICE_URL: str = "http://localhost:8002/api/v1"
    SANDBOX_SERVICE_URL: str = "http://localhost:8004/api/v1/verifier"

    # JWT Authentication
    JWT_SECRET_KEY: str = "tcs-factory-dev-secret-change-in-prod-0987654321"
    JWT_ALGORITHM: str = "HS256"

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003",
        "http://localhost:8004",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
