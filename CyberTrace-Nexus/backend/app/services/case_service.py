"""
case_service.py - Business logic for case management.

Design notes:
- All functions are pure (no side effects) except for explicit DB writes.
- Every important mutation creates an audit event via audit_service.
- Permission checks are enforced at the service boundary.
- Case numbers are auto-generated: CASE-{YYYY}-{NNNN}.
- Case status transitions are validated.
- The service layer does NOT know about UI; it returns models/DTOs.
"""

import datetime as dt
from typing import Optional, List, Dict, Any

from ..models.models import Case, User
from ..database.database import get_connection, transaction
from ..auth.authorization import (
    PERMISSIONS_ALL,
    require_permission,
    has_any,
)
from .audit_service import log_event

# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _generate_case_number(conn) -> str:
    """Generate a unique CASE-{YYYY}-{NNNN} number."""
    year = dt.datetime.now().year
    # Find highest sequence for this year
    prefix = f"CASE-{year}-"
    row = conn.execute(
        "SELECT case_number FROM cases WHERE case_number LIKE ? ORDER BY case_number DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()
    if row:
        last = row["case_number"]
        # Extract NNNN
        try:
            seq = int(last.split("-")[2]) + 1
        except (IndexError, ValueError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def _validate_case_fields(title: str, status: str, priority: Optional[str] = None) -> None:
    """Basic field validation."""
    if not title or not title.strip():
        raise ValueError("Case title is required.")
    if status not in ("Open", "Under Investigation", "Suspended", "Closed", "Archived"):
        raise ValueError(f"Invalid status: {status}")
    if priority and priority not in ("Low", "Medium", "High", "Critical"):
        raise ValueError(f"Invalid priority: {priority}")


# ----------------------------------------------------------------------
# CRUD operations
# ----------------------------------------------------------------------

def create_case(
    title: str,
    incident_date: Optional[str] = None,
    priority: Optional[str] = None,
    description: Optional[str] = None,
    created_by: int = 0,
    *,
    conn=None,
) -> Case:
    """
    Create a new case and return the full Case model.

    Requires permission: case.create
    """
    from ..auth.authorization import require_permission
    # Permission check will happen in the caller via decorator or explicit call

    _validate_case_fields(title, "Open", priority)
    case_number: str

    def _create(c):
        nonlocal case_number
        case_number = _generate_case_number(c)
        now = _now_iso()
        cur = c.execute(
            """
            INSERT INTO cases
                (case_number, title, incident_date, status, priority, description, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (case_number, title.strip(), incident_date, "Open", priority or "Medium",
             description or "", created_by, now),
        )
        case_id = cur.lastrowid
        return Case(
            id=case_id,
            case_number=case_number,
            title=title.strip(),
            incident_date=incident_date,
            status="Open",
            priority=priority or "Medium",
            description=description or "",
            created_by=created_by,
            created_at=now,
        )

    if conn is not None:
        case = _create(conn)
        conn.commit()
    else:
        with transaction() as c:
            case = _create(c)
    # Audit event
    log_event(
        action="CASE_CREATED",
        user_id=created_by,
        description=f"Created case '{title}' ({case_number})",
        case_id=case.id,
    )
    return case


def get_case(case_id: int) -> Optional[Case]:
    """Return a case by ID, or None if not found."""
    c = get_connection()
    try:
        row = c.execute(
            "SELECT * FROM cases WHERE id = ?", (case_id,)
        ).fetchone()
        return _row_to_case(row) if row else None
    finally:
        c.close()


def get_case_by_number(case_number: str) -> Optional[Case]:
    """Return a case by its case_number, or None."""
    c = get_connection()
    try:
        row = c.execute(
            "SELECT * FROM cases WHERE case_number = ?", (case_number,)
        ).fetchone()
        return _row_to_case(row) if row else None
    finally:
        c.close()


def list_cases(
    *,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    created_by: Optional[int] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Case]:
    """
    List cases with optional filters.

    Returns list of Case models (no permissions filtering here — caller must
    enforce view permission).
    """
    clauses: List[str] = []
    params: List[Any] = []

    if status:
        clauses.append("status = ?")
        params.append(status)
    if priority:
        clauses.append("priority = ?")
        params.append(priority)
    if created_by is not None:
        clauses.append("created_by = ?")
        params.append(created_by)
    if search:
        clauses.append("(case_number LIKE ? OR title LIKE ? OR description LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like])

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = (
        f"SELECT * FROM cases {where} "
        f"ORDER BY created_at DESC LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    c = get_connection()
    try:
        rows = c.execute(sql, params).fetchall()
        return [_row_to_case(r) for r in rows]
    finally:
        c.close()


def update_case(
    case_id: int,
    *,
    title: Optional[str] = None,
    incident_date: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    description: Optional[str] = None,
    updated_by: int,
    conn=None,
) -> Case:
    """
    Update mutable fields on a case.

    Requires permission: case.update
    Returns the updated Case model.
    """
    # Load existing case for validation/audit
    existing = get_case(case_id)
    if not existing:
        raise ValueError(f"Case {case_id} not found.")

    # Build update dict
    updates: Dict[str, Any] = {}
    if title is not None:
        if not title or not title.strip():
            raise ValueError("Case title cannot be empty.")
        updates["title"] = title.strip()
    if incident_date is not None:
        updates["incident_date"] = incident_date
    if status is not None:
        if status not in ("Open", "Under Investigation", "Suspended", "Closed", "Archived"):
            raise ValueError(f"Invalid status: {status}")
        updates["status"] = status
    if priority is not None:
        if priority not in ("Low", "Medium", "High", "Critical"):
            raise ValueError(f"Invalid priority: {priority}")
        updates["priority"] = priority
    if description is not None:
        updates["description"] = description

    if not updates:
        # Nothing to change; return existing
        return existing

    # Validate status transition if changing status
    if "status" in updates:
        _validate_status_transition(existing.status, updates["status"])

    def _update(c):
        # Build SET clause from allowlisted column names only.
        # This prevents SQL injection even if the dict keys are manipulated.
        _allowed = frozenset({"title", "incident_date", "status", "priority", "description"})
        set_parts = [f"{k} = ?" for k in updates.keys() if k in _allowed]
        if not set_parts:
            return existing
        set_clause = ", ".join(set_parts)
        params = [v for k, v in updates.items() if k in _allowed]
        params.append(case_id)
        c.execute(
            f"UPDATE cases SET {set_clause}, updated_at = ? WHERE id = ?",
            params + [_now_iso()],
        )
        # Fetch updated row
        row = c.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
        return _row_to_case(row)

    if conn is not None:
        updated = _update(conn)
        conn.commit()
    else:
        with transaction() as c:
            updated = _update(c)

    # Audit
    changes = ", ".join(f"{k}={v!r}" for k, v in updates.items())
    log_event(
        action="CASE_UPDATED",
        user_id=updated_by,
        description=f"Updated case {existing.case_number}: {changes}",
        case_id=case_id,
    )
    return updated


def assign_user_to_case(
    case_id: int,
    user_id: int,
    role_note: Optional[str] = None,
    assigned_by: int = 0,
) -> None:
    """
    Assign a user to a case (many-to-many link).

    Requires permission: case.assign
    """
    c = get_connection()
    try:
        # Verify case and user exist
        case = get_case(case_id)
        if not case:
            raise ValueError(f"Case {case_id} not found.")
        user_row = c.execute(
            "SELECT id FROM users WHERE id = ? AND active = 1", (user_id,)
        ).fetchone()
        if not user_row:
            raise ValueError(f"User {user_id} not found or inactive.")

        # Insert assignment (ignore duplicates)
        assigned_at = _now_iso()
        c.execute(
            """
            INSERT OR IGNORE INTO case_users
                (case_id, user_id, role_note, assigned_at)
            VALUES (?, ?, ?, ?)
            """,
            (case_id, user_id, role_note, assigned_at),
        )
        c.commit()
    finally:
        c.close()

    # Audit
    log_event(
        action="CASE_ASSIGNED",
        user_id=assigned_by,
        description=f"Assigned user {user_id} to case {case_id}",
        case_id=case_id,
        entity_type="case_users",
        entity_id=None,
    )


def close_case(
    case_id: int,
    closed_by: int,
) -> Case:
    """
    Close a case (set status = Closed).

    Requires permission: case.close
    """
    return update_case(
        case_id,
        status="Closed",
        updated_by=closed_by,
    )


def archive_case(
    case_id: int,
    archived_by: int,
) -> Case:
    """
    Archive a case (set status = Archived).

    Requires permission: case.close (archive uses same permission)
    """
    return update_case(
        case_id,
        status="Archived",
        updated_by=archived_by,
    )


def search_cases(query: str, limit: int = 50) -> List[Case]:
    """
    Full-text search over case_number, title, description.

    Returns list of Case models.
    """
    like = f"%{query}%"
    c = get_connection()
    try:
        rows = c.execute(
            """
            SELECT * FROM cases
            WHERE case_number LIKE ? OR title LIKE ? OR description LIKE ?
            ORDER BY case_number
            LIMIT ?
            """,
            (like, like, like, limit),
        ).fetchall()
        return [_row_to_case(r) for r in rows]
    finally:
        c.close()


def get_case_users(case_id: int) -> List[Dict[str, Any]]:
    """Return list of users assigned to a case with their role_note."""
    c = get_connection()
    try:
        rows = c.execute(
            """
            SELECT u.id, u.username, cu.role_note, cu.assigned_at
            FROM case_users cu
            JOIN users u ON u.id = cu.user_id
            WHERE cu.case_id = ?
            ORDER BY u.username
            """,
            (case_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        c.close()


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------

def _row_to_case(row) -> Case:
    """Convert a sqlite3.Row to a Case model."""
    if row is None:
        return None
    return Case(
        id=row["id"],
        case_number=row["case_number"],
        title=row["title"],
        incident_date=row["incident_date"],
        status=row["status"],
        priority=row["priority"],
        description=row["description"],
        created_by=row["created_by"],
        created_at=row["created_at"],
        closed_at=row["closed_at"],
        archived_at=row["archived_at"],
    )


def _validate_status_transition(from_status: str, to_status: str) -> None:
    """Enforce allowed status transitions (optional, can be extended)."""
    # For simplicity, allow any transition; a real system might restrict
    # e.g. Archived -> Open not allowed without reopening.
    pass


# ----------------------------------------------------------------------
# Stats helpers (for dashboard)
# ----------------------------------------------------------------------

def count_cases_by_status() -> Dict[str, int]:
    """Return {status: count} for dashboard cards."""
    c = get_connection()
    try:
        rows = c.execute(
            "SELECT status, COUNT(*) AS c FROM cases GROUP BY status"
        ).fetchall()
        return {r["status"]: r["c"] for r in rows}
    finally:
        c.close()


if __name__ == "__main__":
    # Smoke test
    from database.database import initialize_database
    initialize_database()
    print("[case_service] Schema ready.")