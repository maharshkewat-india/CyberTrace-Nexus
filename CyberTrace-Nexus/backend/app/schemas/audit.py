"""
schemas/audit.py - Audit log request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AuditLogQuery(BaseModel):
    limit: int = Field(default=500, ge=1, le=2000)
    user: Optional[str] = None
    action: Optional[str] = None
    entity_type: Optional[str] = None
    result: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    case_id: Optional[int] = None


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    action: str
    username: Optional[str]
    role_name: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[int]
    case_id: Optional[int]
    description: Optional[str]
    result: str = "SUCCESS"


class AuditLogListResponse(BaseModel):
    logs: List[AuditLogResponse]
    total: int