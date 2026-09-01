"""
api/custody.py - Chain of custody API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime, timezone

from ..core.dependencies import get_current_user, CurrentUser, require_permission_dep
from ..schemas.custody import CustodyEventCreate, CustodyEventResponse, CustodyEventListResponse
from ..services import custody_service

router = APIRouter(prefix="/custody", tags=["Custody"])


def _custody_to_response(event) -> dict:
    """Convert custody event dict to response format."""
    return {
        "id": event["id"],
        "evidence_id": event["evidence_id"],
        "case_id": event["case_id"],
        "action": event["action"],
        "from_person": event["from_person"],
        "to_person": event["to_person"],
        "location": event["location"],
        "event_time": event["event_time"],
        "notes": event["notes"],
        "recorded_by": event["recorded_by"],
        "recorded_by_name": event.get("recorded_by_name"),
        "created_at": event.get("created_at"),
    }


@router.get("/{evidence_id}", response_model=List[dict])
async def list_custody_for_evidence(
    evidence_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("custody.view")),
):
    """Get all custody events for a piece of evidence."""
    events = custody_service.list_custody_for_evidence(evidence_id)
    return [_custody_to_response(e) for e in events]


@router.post("", response_model=dict)
async def add_custody_event(
    request: CustodyEventCreate,
    current_user: CurrentUser = Depends(require_permission_dep("custody.create")),
):
    """Record a new custody event."""
    try:
        # Auto-populate case_id from evidence if not provided
        case_id = request.case_id
        if case_id is None:
            from services.evidence_service import get_evidence
            ev = get_evidence(request.evidence_id)
            if not ev:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence {request.evidence_id} not found")
            case_id = ev.case_id

        event_id = custody_service.add_custody_event(
            evidence_id=request.evidence_id,
            action=request.action,
            from_person=request.from_person,
            to_person=request.to_person,
            location=request.location,
            notes=request.notes,
            case_id=case_id,
            recorded_by=current_user.id,
        )

        from services.audit_service import log_event
        log_event(
            action=f"CUSTODY_{request.action}",
            user_id=current_user.id,
            description=f"Custody event: {request.action} evidence {request.evidence_id}",
            entity_type="custody_event",
            entity_id=event_id,
            case_id=case_id,
        )

        # Return the created event
        event = custody_service.get_custody_event(event_id)
        return _custody_to_response(event)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/case/{case_id}", response_model=List[dict])
async def list_custody_for_case(
    case_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("custody.view")),
):
    """Get all custody events for a case (across all evidence)."""
    events = custody_service.list_custody_for_case(case_id)
    return [_custody_to_response(e) for e in events]