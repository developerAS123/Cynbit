from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered intern or administrator email")
    password: str = Field(..., min_length=8, max_length=128, description="Account password")

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="User email for account recovery")

class GenericStatusResponse(BaseModel):
    success: bool
    message: str

class TokenResponse(BaseModel):
    success: bool
    token_type: str = "Bearer"
    user: "UserSummary"

class UserSummary(BaseModel):
    id: str
    email: EmailStr
    full_name: Optional[str]
    role: str

