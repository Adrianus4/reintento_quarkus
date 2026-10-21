from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "TCS Intelligent Microservice Factory — Sandbox Verifier Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    HOST: str = "0.0.0.0"
    PORT: int = 8004

    # Database
    DATABASE_URL: str = "sqlite:///./verifier_factory_local.db"

    # Ephemeral Sandbox Storage
    SANDBOX_BASE_PATH: str = "./sandbox_runs"

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

