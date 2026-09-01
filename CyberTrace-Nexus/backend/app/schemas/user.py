"""
schemas/user.py - User request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    role_names: List[str] = Field(default_factory=list)
    active: bool = True
    must_change_password: bool = False


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)
    role_name: str = Field(default="AUDITOR", description="Initial role")


class UserUpdate(BaseModel):
    role_names: Optional[List[str]] = None
    active: Optional[bool] = None
    must_change_password: Optional[bool] = None


class UserPasswordReset(BaseModel):
    new_password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int