from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

CategoryLiteral = Literal["SECURITY", "ARCHITECTURE", "NAMING", "TESTING", "OBSERVABILITY"]
SeverityLiteral = Literal["MANDATORY", "RECOMMENDED", "OPTIONAL"]


class DirectiveBase(BaseModel):
    rule_code: str = Field(..., min_length=2, max_length=100)
    category: CategoryLiteral
    severity: SeverityLiteral = "MANDATORY"
    description: str = Field(..., min_length=5)
    deterministic_check: Optional[str] = None


class DirectiveCreate(DirectiveBase):
    pass


class DirectiveUpdate(BaseModel):
    category: Optional[CategoryLiteral] = None
    severity: Optional[SeverityLiteral] = None
    description: Optional[str] = Field(None, min_length=5)
    deterministic_check: Optional[str] = None
    is_enabled: Optional[bool] = None


class DirectiveResponse(DirectiveBase):
    id: str
    client_code: str
    version: int
    is_enabled: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

