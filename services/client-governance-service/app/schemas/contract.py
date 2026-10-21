from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class ContractUploadRequest(BaseModel):
    title: Optional[str] = None
    version: Optional[str] = None
    format: Literal["json", "yaml"] = "json"
    raw_content: str = Field(..., min_length=10, description="Raw OpenAPI 3.x contract definition in JSON or YAML")


class ContractResponse(BaseModel):
    id: str
    client_code: str
    title: str
    version: str
    format: str
    endpoints_count: int
    is_valid: bool
    created_at: datetime
    raw_content: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

