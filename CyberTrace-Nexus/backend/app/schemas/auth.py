"""
schemas/auth.py - Authentication request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Username or email")
    password: str = Field(..., min_length=8, description="Plaintext password")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: int
    username: str
    role_names: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    must_change_password: bool = False


class TokenData(BaseModel):
    user_id: int
    username: str
    role_names: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    exp: datetime


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# Update forward refs
UserResponse.model_rebuild()