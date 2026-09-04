"""
api/evidence.py - Evidence management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime, timezone

from ..core.dependencies import get_current_user, CurrentUser, require_permission_dep
from ..schemas.evidence import EvidenceCreate, EvidenceUpdate, EvidenceResponse, HashVerifyResponse
from ..services import evidence_service

router = APIRouter(prefix="/evidence", tags=["Evidence"])


def _evidence_to_response(ev) -> dict:
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


@router.get("", response_model=List[dict])
async def list_all_evidence(
    limit: int = Query(200, ge=1, le=500),
    current_user: CurrentUser = Depends(require_permission_dep("evidence.view")),
):
    """List all evidence across all cases."""
    evidence_list = evidence_service.list_all_evidence(limit=limit)
    return [_evidence_to_response(ev) for ev in evidence_list]


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_evidence(
    request: EvidenceCreate,
    current_user: CurrentUser = Depends(require_permission_dep("evidence.create")),
):
    """Register new evidence (computes MD5 + SHA-256 automatically)."""
    try:
        ev = evidence_service.register_evidence(
            case_id=request.case_id,
            file_path=request.file_path,
            evidence_type=request.evidence_type,
            description=request.description,
            source=request.source,
            registered_by=current_user.id,
        )
        return _evidence_to_response(ev)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file not found.",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to read the evidence file.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{evidence_id}", response_model=dict)
async def get_evidence(
    evidence_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("evidence.view")),
):
    """Get a single evidence item by primary key."""
    ev = evidence_service.get_evidence(evidence_id)
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence {evidence_id} not found")
    return _evidence_to_response(ev)


@router.put("/{evidence_id}", response_model=dict)
async def update_evidence(
    evidence_id: int,
    request: EvidenceUpdate,
    current_user: CurrentUser = Depends(require_permission_dep("evidence.update")),
):
    """Update evidence metadata (does NOT change hashes)."""
    ev = evidence_service.get_evidence(evidence_id)
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence {evidence_id} not found")

    from database.database import get_connection
    conn = get_connection()
    try:
        # Build update dict, filtering by allowlisted column names to prevent
        # any future schema/code drift from introducing SQL-injection-prone
        # dynamic SET clauses.
        _allowed = frozenset({"evidence_type", "description", "source", "status"})
        updates = {}
        if request.evidence_type is not None:
            updates["evidence_type"] = request.evidence_type
        if request.description is not None:
            updates["description"] = request.description
        if request.source is not None:
            updates["source"] = request.source
        if request.status is not None:
            updates["status"] = request.status

        safe_updates = {k: v for k, v in updates.items() if k in _allowed}
        if safe_updates:
            set_clause = ", ".join(f"{k} = ?" for k in safe_updates.keys())
            params = list(safe_updates.values())
            params.append(evidence_id)
            conn.execute(f"UPDATE evidence SET {set_clause} WHERE id = ?", params)
            conn.commit()

            from ..services.audit_service import log_event
            log_event(
                action="EVIDENCE_UPDATED",
                user_id=current_user.id,
                description=f"Updated evidence {evidence_id}: {', '.join(safe_updates.keys())}",
                entity_type="evidence",
                entity_id=evidence_id,
            )

        ev = evidence_service.get_evidence(evidence_id)
        return _evidence_to_response(ev)
    finally:
        conn.close()


@router.post("/{evidence_id}/verify", response_model=dict)
async def verify_evidence(
    evidence_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("evidence.verify")),
):
    """
    Re-compute MD5 and SHA-256 for the evidence file and compare to stored values.

    This NEVER overwrites the original stored hashes.
    Returns verification result with status.
    """
    try:
        result = evidence_service.verify_evidence(
            evidence_pk=evidence_id,
            verified_by=current_user.id,
        )
        return result
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file is missing on disk; cannot verify integrity.",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{evidence_id}/hash", response_model=dict)
async def compute_hash(
    evidence_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("evidence.hash")),
):
    """Compute hash for evidence file (returns current hashes without verification)."""
    ev = evidence_service.get_evidence(evidence_id)
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence {evidence_id} not found")

    try:
        from ..services.hashing import compute_hashes
        result = compute_hashes(ev.file_path)
        return {
            "md5": result.md5,
            "sha256": result.sha256,
            "status": "computed",
        }
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence file is missing on disk.",
        )


@router.post("/{evidence_id}/note", response_model=dict)
async def add_evidence_note(
    evidence_id: int,
    content: str = Query(..., description="Note content"),
    note_type: str = Query("analysis", description="Note type"),
    current_user: CurrentUser = Depends(require_permission_dep("analysis.create")),
):
    """Add an analysis note to evidence."""
    ev = evidence_service.get_evidence(evidence_id)
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence {evidence_id} not found")

    try:
        note_id = evidence_service.add_evidence_note(
            case_id=ev.case_id,
            evidence_pk=evidence_id,
            content=content,
            note_type=note_type,
            user_id=current_user.id,
        )
        return {"id": note_id, "message": "Note added successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{evidence_id}/notes", response_model=List[dict])
async def get_evidence_notes(
    evidence_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("analysis.view")),
):
    """Get all analysis notes for evidence."""
    ev = evidence_service.get_evidence(evidence_id)
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Evidence {evidence_id} not found")

    notes = evidence_service.list_notes_for_case(ev.case_id)
    # Filter to only notes for this evidence
    filtered = [n for n in notes if n.get("evidence_id") == evidence_id]
    return filtered


@router.get("/{evidence_id}/custody", response_model=List[dict])
async def get_custody(
    evidence_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("custody.view")),
):
    """Get chain of custody for evidence."""
    from ..services import custody_service
    events = custody_service.list_custody_for_evidence(evidence_id)
    return events
