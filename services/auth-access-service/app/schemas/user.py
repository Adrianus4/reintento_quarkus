from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    role: Literal["ADMIN", "DEVELOPER"] = "DEVELOPER"


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[Literal["ADMIN", "DEVELOPER"]] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    assigned_clients: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class ClientAssignmentUpdate(BaseModel):
    client_codes: List[str] = Field(
        ...,
        description="List of authorized client codes (e.g. ['bcp', 'retail-corp'])"
    )

