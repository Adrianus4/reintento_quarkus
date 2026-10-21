from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class JobCreateRequest(BaseModel):
    client_code: str = Field(..., min_length=2, max_length=64)
    requirements: Optional[str] = Field(None, min_length=5, description="Natural language microservice specifications")
    raw_requirement: Optional[str] = None
    contract_id: Optional[str] = None
    architecture_style: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_requirements(cls, data: Any) -> Any:
        if isinstance(data, dict):
            req = data.get("requirements") or data.get("raw_requirement")
            if req:
                data["requirements"] = str(req).strip()
        return data


class FileEditRequest(BaseModel):
    files: Dict[str, str] = Field(
        ...,
        description="Mapping of relative file path (e.g. 'src/main/java/...') to updated content"
    )


class JobResponse(BaseModel):
    id: str
    user_id: str
    client_code: str
    contract_id: Optional[str] = None
    requirements: str
    architecture_style: Optional[str] = None
    status: str
    blueprint: Optional[Dict[str, Any]] = None
    files: Dict[str, str] = {}
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    duration_ms: int
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

