"""
schemas/case.py - Case request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CaseBase(BaseModel):
    case_number: str = Field(..., description="Unique case identifier (auto-generated)")
    title: str = Field(..., min_length=1, description="Case title")
    incident_date: Optional[datetime] = Field(None, description="Date of incident")
    status: str = Field(default="Open", description="Case status")
    priority: str = Field(default="Medium", description="Case priority")
    description: str = Field(default="", description="Case description")
    created_by: int = Field(..., description="User ID who created the case")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = Field(None, description="Date case was closed")
    archived_at: Optional[datetime] = Field(None, description="Date case was archived")


class CaseCreate(CaseBase):
    # case_number is auto-generated
    case_number: Optional[str] = Field(None, exclude=True)


class CaseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    incident_date: Optional[datetime] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    description: Optional[str] = None
    closed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None


class CaseResponse(CaseBase):
    # Additional computed fields if needed
    pass