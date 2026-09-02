"""
api/cases.py - Case management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime, timezone

from ..core.dependencies import get_current_user, CurrentUser, require_permission_dep
from ..schemas.case import CaseCreate, CaseUpdate, CaseResponse
from ..services import case_service
from ..services.audit_service import log_event

router = APIRouter(prefix="/cases", tags=["Cases"])


def _parse_datetime(val) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _model_to_response(case) -> dict:
    """Convert Case model to response dict."""
    return {
        "id": case.id,
        "case_number": case.case_number,
        "title": case.title,
        "incident_date": _parse_datetime(case.incident_date),
        "status": case.status,
        "priority": case.priority,
        "description": case.description,
        "created_by": case.created_by,
        "created_at": _parse_datetime(case.created_at) or datetime.now(timezone.utc),
        "closed_at": _parse_datetime(case.closed_at),
        "archived_at": _parse_datetime(case.archived_at),
    }


@router.get("", response_model=List[dict])
async def list_cases(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in case number, title, description"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(require_permission_dep("case.view")),
):
    """List all cases with optional filters."""
    cases = case_service.list_cases(
        status=status,
        priority=priority,
        search=search,
        limit=limit,
        offset=offset,
    )
    return [_model_to_response(c) for c in cases]


@router.post("", response_model=dict)
async def create_case(
    request: CaseCreate,
    current_user: CurrentUser = Depends(require_permission_dep("case.create")),
):
    """Create a new case."""
    try:
        case = case_service.create_case(
            title=request.title,
            incident_date=request.incident_date.isoformat() if request.incident_date else None,
            priority=request.priority,
            description=request.description,
            created_by=current_user.id,
        )
        return _model_to_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{case_id}", response_model=dict)
async def get_case(
    case_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("case.view")),
):
    """Get a single case by ID."""
    case = case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found")
    return _model_to_response(case)


@router.put("/{case_id}", response_model=dict)
async def update_case(
    case_id: int,
    request: CaseUpdate,
    current_user: CurrentUser = Depends(require_permission_dep("case.update")),
):
    """Update an existing case."""
    try:
        # Build kwargs for update
        kwargs = {"updated_by": current_user.id}
        if request.title is not None:
            kwargs["title"] = request.title
        if request.incident_date is not None:
            kwargs["incident_date"] = request.incident_date.isoformat() if request.incident_date else None
        if request.status is not None:
            kwargs["status"] = request.status
        if request.priority is not None:
            kwargs["priority"] = request.priority
        if request.description is not None:
            kwargs["description"] = request.description

        case = case_service.update_case(case_id, **kwargs)
        return _model_to_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{case_id}/close", response_model=dict)
async def close_case(
    case_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("case.close")),
):
    """Close a case."""
    try:
        case = case_service.close_case(case_id, closed_by=current_user.id)
        return _model_to_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{case_id}/archive", response_model=dict)
async def archive_case(
    case_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("case.close")),
):
    """Archive a case."""
    try:
        case = case_service.archive_case(case_id, archived_by=current_user.id)
        return _model_to_response(case)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{case_id}/assign", response_model=dict)
async def assign_user_to_case(
    case_id: int,
    user_id: int = Query(..., description="User ID to assign"),
    role_note: Optional[str] = Query(None, description="Role note"),
    current_user: CurrentUser = Depends(require_permission_dep("case.assign")),
):
    """Assign a user to a case."""
    try:
        case_service.assign_user_to_case(
            case_id=case_id,
            user_id=user_id,
            role_note=role_note,
            assigned_by=current_user.id,
        )
        return {"message": "User assigned successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{case_id}/users", response_model=List[dict])
async def get_case_users(
    case_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("case.view")),
):
    """Get users assigned to a case."""
    users = case_service.get_case_users(case_id)
    return users


@router.get("/{case_id}/evidence", response_model=List[dict])
async def get_case_evidence(
    case_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("evidence.view")),
):
    """Get all evidence for a case."""
    from services import evidence_service
    evidence_list = evidence_service.list_evidence_for_case(case_id)
    return [_evidence_to_dict(ev) for ev in evidence_list]


def _evidence_to_dict(ev) -> dict:
    """Convert Evidence model to dict."""
    return {
        "id": ev.id,
        "evidence_id": ev.evidence_id,
        "case_id": ev.case_id,
        "evidence_type": ev.evidence_type,
        "description": ev.description,
        "source": ev.source,
        "file_path": ev.file_path,
        "file_size": ev.file_size,
        "file_extension": ev.file_extension,
        "acquisition_time": ev.acquisition_time,
        "original_modified_time": ev.original_modified_time,
        "registered_by": ev.registered_by,
        "status": ev.status,
        "created_at": ev.created_at,
        "md5": ev.md5,
        "sha256": ev.sha256,
    }
