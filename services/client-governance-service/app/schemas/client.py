from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ClientBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    package_prefix: str = Field("com.tcs.generated", min_length=3, max_length=255)
    java_version: str = Field("17", pattern="^(17|21)$")
    quarkus_version: str = Field("3.15.1", min_length=3, max_length=20)


class ClientCreate(ClientBase):
    code: str = Field(
        ...,
        min_length=2,
        max_length=64,
        pattern="^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="Unique URL-friendly client slug (e.g. 'bcp', 'retail-corp')"
    )


class ClientUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    package_prefix: Optional[str] = Field(None, min_length=3, max_length=255)
    java_version: Optional[str] = Field(None, pattern="^(17|21)$")
    quarkus_version: Optional[str] = Field(None, min_length=3, max_length=20)
    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    id: str
    code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

