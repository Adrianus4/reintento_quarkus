from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class VaultKeySaveRequest(BaseModel):
    provider: str
    api_key: str = Field(..., min_length=5, description="Raw provider API Key to be encrypted with Fernet")
    model_name: Optional[str] = None
    base_url: Optional[str] = None

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, v: str) -> str:
        return v.lower().strip() if isinstance(v, str) else v


class VaultKeyResponse(BaseModel):
    id: str
    provider: str
    masked_key: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestConnectionRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, v: str) -> str:
        return v.lower().strip() if isinstance(v, str) else v


class TestConnectionResponse(BaseModel):
    provider: str
    connected: bool
    latency_ms: int
    message: str
