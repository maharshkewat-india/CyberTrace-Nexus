"""
models.py - Lightweight immutable-ish data containers (DTOs) used across layers.

These dataclasses carry row data from the persistence/database layer to the
service and UI layers. They intentionally hold no logic beyond simple lookups.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class Role:
    id: int
    name: str
    description: str = ""


@dataclass(frozen=True)
class Permission:
    id: int
    name: str
    description: str = ""


@dataclass(frozen=True)
class User:
    id: int
    username: str
    password_hash: str
    salt: str
    active: int
    must_change_password: int
    role_names: tuple = ()  # populated via lookup
    last_login: Optional[str] = None
    created_at: Optional[str] = "1970-01-01 00:00:00"

    @property
    def is_active(self) -> bool:
        return bool(self.active)


@dataclass(frozen=True)
class Case:
    id: int
    case_number: str
    title: str = ""
    incident_date: Optional[str] = None
    status: str = "Open"
    priority: str = "Medium"
    description: str = ""
    created_by: int = 0
    created_at: str = "1970-01-01 00:00:00"
    closed_at: Optional[str] = None
    archived_at: Optional[str] = None


@dataclass
class Evidence:
    id: int
    evidence_id: str
    case_id: int
    description: str = ""
    evidence_type: str = ""
    source: str = ""
    file_path: str = ""
    file_size: int = 0
    file_extension: str = ""
    acquisition_time: str = "1970-01-01 00:00:00"
    original_modified_time: Optional[str] = None
    registered_by: int = 0
    status: str = "Active"
    created_at: str = "1970-01-01 00:00:00"

    md5: Optional[str] = None
    sha256: Optional[str] = None

    @property
    def exists(self) -> bool:
        """True when the registered absolute path resolves to a real file."""
        from pathlib import Path
        try:
            return Path(self.file_path).is_file()
        except (OSError, ValueError):
            return False


@dataclass(frozen=True)
class EvidenceHash:
    evidence_id: int
    md5_hash: str
    sha256_hash: str
    algorithm: str = "SHA-256"
    computed_at: str = "1970-01-01 00:00:00"


@dataclass(frozen=True)
class CustodyEvent:
    id: int
    evidence_id: int
    action: str
    event_time: str
    from_person: Optional[str] = None
    to_person: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    case_id: Optional[int] = None
    recorded_by: int = 0
    recorded_by_name: Optional[str] = None
    created_at: Optional[str] = None


@dataclass(frozen=True)
class AnalysisNote:
    id: int
    case_id: int
    content: str
    note_type: str = ""
    evidence_id: Optional[int] = None
    user_id: int = 0
    username: Optional[str] = None
    created_at: str = "1970-01-01 00:00:00"


@dataclass(frozen=True)
class AuditLog:
    id: int
    timestamp: str
    action: str
    username: Optional[str]
    role_name: Optional[str]
    entity_type: Optional[str]
    entity_id: Optional[int]
    case_id: Optional[int]
    description: str
    result: str = "SUCCESS"


@dataclass(frozen=True)
class Session:
    id: int
    user_id: int
    token: str
    created_at: str
    expires_at: Optional[str]
    active: int


@dataclass
class CaseUserAssignment:
    """Join row linking a user to a case for assignment purposes."""
    case_id: int
    user_id: int
    username: str
    role_note: Optional[str] = None
    assigned_at: Optional[str] = None
