"""
schemas/custody.py - Chain of custody request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CustodyEventCreate(BaseModel):
    evidence_id: int
    action: str = Field(..., description="Custody action (REGISTERED, TRANSFERRED, RECEIVED, etc.)")
    from_person: Optional[str] = Field(None, description="Previous custodian")
    to_person: Optional[str] = Field(None, description="New custodian")
    location: Optional[str] = Field(None, description="Location of custody transfer")
    notes: Optional[str] = Field(None, description="Additional notes")
    case_id: Optional[int] = Field(None, description="Case ID (auto-populated from evidence)")


class CustodyEventResponse(BaseModel):
    id: int
    evidence_id: int
    case_id: Optional[int]
    action: str
    from_person: Optional[str]
    to_person: Optional[str]
    location: Optional[str]
    event_time: datetime
    notes: Optional[str]
    recorded_by: int
    recorded_by_name: Optional[str] = None
    created_at: Optional[datetime] = None


class CustodyEventListResponse(BaseModel):
    events: list[CustodyEventResponse]
    total: int