"""
api/audit.py - Audit log API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional

from ..core.dependencies import get_current_user, CurrentUser, require_permission_dep
from ..schemas.audit import AuditLogResponse, AuditLogListResponse
from ..services.audit_service import get_audit_logs, get_audit_count

router = APIRouter(prefix="/audit-logs", tags=["Audit"])


@router.get("", response_model=List[dict])
async def list_audit_logs(
    limit: int = Query(500, ge=1, le=2000),
    user: Optional[str] = Query(None, description="Filter by username"),
    action: Optional[str] = Query(None, description="Filter by action"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    result: Optional[str] = Query(None, description="Filter by result (SUCCESS/FAIL)"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO 8601)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO 8601)"),
    case_id: Optional[int] = Query(None, description="Filter by case ID"),
    current_user: CurrentUser = Depends(require_permission_dep("audit.view")),
):
    """List audit log entries with optional filters."""
    try:
        logs = get_audit_logs(
            limit=limit,
            user=user,
            action=action,
            entity_type=entity_type,
            result=result,
            date_from=date_from,
            date_to=date_to,
            case_id=case_id,
        )
        return logs
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load audit logs"
        )


@router.get("/count", response_model=dict)
async def get_audit_count_endpoint(
    current_user: CurrentUser = Depends(require_permission_dep("audit.view")),
):
    """Get total count of audit log entries."""
    count = get_audit_count()
    return {"total": count}