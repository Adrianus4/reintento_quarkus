from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.user import UserResponse


class SetupAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4, description="Initial administrator password")
    full_name: str = Field(..., min_length=2, max_length=255)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=4, description="User password")
    full_name: str = Field(..., min_length=2, max_length=255)
    role: Optional[str] = "ADMIN"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenVerifyRequest(BaseModel):
    token: str


class TokenVerifyResponse(BaseModel):
    valid: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    assigned_clients: List[str] = []
    reason: Optional[str] = None
