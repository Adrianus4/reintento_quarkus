from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

ProviderChoice = Literal["gemini", "deepseek", "grok", "mock"]


class GatewayConfigUpdate(BaseModel):
    active_provider: Optional[ProviderChoice] = None
    model_name: Optional[str] = None
    consumption_mode: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(None, ge=1024, le=16384)

    @field_validator("active_provider", mode="before")
    @classmethod
    def normalize_active_provider(cls, v: Optional[str]) -> Optional[str]:
        return v.lower().strip() if isinstance(v, str) else v


class GatewayConfigResponse(BaseModel):
    id: str
    active_provider: str
    model_name: Optional[str] = "default"
    consumption_mode: Optional[str] = "standard"
    temperature: float
    max_tokens: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
