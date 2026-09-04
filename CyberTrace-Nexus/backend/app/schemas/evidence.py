"""
schemas/evidence.py - Evidence request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class EvidenceBase(BaseModel):
    evidence_id: str = Field(..., description="Unique evidence identifier (auto-generated)")
    case_id: int = Field(..., description="Parent case ID")
    evidence_type: str = Field(default="Document", description="Type of evidence")
    description: str = Field(default="", description="Evidence description")
    source: str = Field(default="", description="Evidence source/provenance")
    file_path: str = Field(..., description="Absolute path to the evidence file")
    file_size: int = Field(..., description="File size in bytes")
    file_extension: str = Field(default="", description="File extension")
    acquisition_time: datetime = Field(default_factory=datetime.utcnow)
    original_modified_time: Optional[datetime] = Field(None, description="Original file modification time")
    registered_by: int = Field(..., description="User ID who registered the evidence")
    status: str = Field(default="Active", description="Evidence status")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvidenceCreate(BaseModel):
    """Schema for registering new evidence.

    Note: registered_by is determined from the authenticated user context,
    not from the request body. This prevents a user from registering evidence
    under a different user's identity.
    """
    case_id: int
    file_path: str
    evidence_type: str = "Document"
    description: str = ""
    source: str = ""

    # The following are auto-populated during registration and excluded
    # from the request body. The 'registered_by' field is sourced from the
    # authenticated user (current_user.id) in the API layer.
    evidence_id: Optional[str] = Field(None, exclude=True)
    registered_by: Optional[int] = Field(None, exclude=True)
    file_size: Optional[int] = Field(None, exclude=True)
    file_extension: Optional[str] = Field(None, exclude=True)
    acquisition_time: Optional[datetime] = Field(None, exclude=True)
    original_modified_time: Optional[datetime] = Field(None, exclude=True)


class EvidenceUpdate(BaseModel):
    evidence_type: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None


class EvidenceResponse(EvidenceBase):
    md5: Optional[str] = Field(None, description="MD5 hash")
    sha256: Optional[str] = Field(None, description="SHA-256 hash")


class HashVerifyRequest(BaseModel):
    evidence_id: int  # Primary key of the evidence


class HashVerifyResponse(BaseModel):
    md5_match: bool
    sha256_match: bool
    stored_md5: str
    stored_sha256: str
    current_md5: str
    current_sha256: str
    status: str  # "HASH VERIFIED" or "INTEGRITY WARNING"