from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator


class CustomEndpoint(BaseModel):
    method: str = "GET"
    path: str = "/api/v1/items"
    summary: str = "Endpoint operation"


class JobCreateRequest(BaseModel):
    client_code: str = Field(..., min_length=2, max_length=64)
    requirements: Optional[str] = Field(None, description="Natural language microservice specifications")
    raw_requirement: Optional[str] = None
    contract_id: Optional[str] = None
    architecture_style: Optional[str] = "Hexagonal"
    custom_architecture_notes: Optional[str] = None
    security_option: Optional[str] = "JWT"
    jwt_issuer: Optional[str] = None
    security_roles: Optional[List[str]] = Field(default_factory=list)
    communication_protocol: Optional[str] = "REST"
    custom_endpoints: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    database_option: Optional[str] = "POSTGRESQL_PANACHE"
    database_name: Optional[str] = None
    package_prefix: Optional[str] = None
    artifact_id: Optional[str] = "generated-microservice"
    http_port: Optional[int] = 8080
    java_version: Optional[str] = "21"
    quarkus_version: Optional[str] = "3.15.1"
    build_tool: Optional[str] = "maven"
    design_patterns: Optional[List[str]] = Field(default_factory=list)
    naming_conventions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    event_broker: Optional[str] = "none"
    channels: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    extensions: Optional[List[str]] = Field(default_factory=list)
    custom_extensions: Optional[List[str]] = Field(default_factory=list)
    custom_properties: Optional[Union[Dict[str, str], str]] = None
    entities: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def reconcile_requirements(cls, data: Any) -> Any:
        if isinstance(data, dict):
            req = data.get("requirements") or data.get("raw_requirement")
            if req:
                data["requirements"] = str(req).strip()
            elif not data.get("requirements"):
                data["requirements"] = "Microservicio empresarial Quarkus con gobernanza corporativa"
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
