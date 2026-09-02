"""
audit_service.py - Append-only audit log service.

Design notes:
- Audit records are append-only from the normal UI: there is no
  'updateAudit' exposed; administrators cannot edit history.
- Each entry captures: timestamp, user, role, action, entity type/id,
  case-id, free-text description, and outcome.
- Write-through uses a parameterized INSERT for safety.
- Audit reads use the shared database connection with foreign keys ON.
"""

import datetime as dt
from typing import Optional, Dict, Any, List

from ..database.database import get_connection, transaction


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def log_event(
    action: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    role_name: Optional[str] = None,
    *,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    case_id: Optional[int] = None,
    description: Optional[str] = None,
    result: str = "SUCCESS",
    conn=None,
) -> int:
    """
    Insert an audit-log row.

    Args:
        action: One of the AUDIT_ACTIONS constants.
        user_id: Authenticated user performing the action (may be None for
                 system-initiated events like LOGIN failures).
        username: Denormalized username (for readability without a JOIN).
        role_name: Denormalized role string.
        entity_type / entity_id: What object was affected (e.g. 'case', 42).
        case_id: Optional linked case for scope.
        description: Free-text context.
        result: 'SUCCESS' or an error label (default SUCCESS).
        conn: Optional open transaction connection; if omitted a new connection
              is used for a one-shot write.

    Returns:
        The new audit log row id.
    """
    now = _now_iso()

    def _insert(c):
        cur = c.execute(
            """
            INSERT INTO audit_logs
                (timestamp, user_id, username, role_name, action,
                 entity_type, entity_id, case_id, description, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (now, user_id, username, role_name, action,
             entity_type, entity_id, case_id, description, result),
        )
        return cur.lastrowid

    if conn is not None:
        rowid = _insert(conn)
        conn.commit()
    else:
        c = get_connection()
        try:
            rowid = _insert(c)
            c.commit()
        finally:
            c.close()
    return rowid


def get_audit_logs(
    limit: int = 500,
    *,
    user: Optional[str] = None,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    result: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    case_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Query audit logs with optional filters. Returns list of dict rows.

    Filters are AND-combined. Date strings are ISO-8601 and compared
    lexicographically (works because we store UTC 'Z' timestamps).
    """
    clauses: List[str] = []
    params: List[Any] = []

    if user:
        clauses.append("username = ?")
        params.append(user)
    if action:
        clauses.append("action = ?")
        params.append(action)
    if entity_type:
        clauses.append("entity_type = ?")
        params.append(entity_type)
    if result:
        clauses.append("result = ?")
        params.append(result)
    if case_id is not None:
        clauses.append("case_id = ?")
        params.append(case_id)
    if date_from:
        clauses.append("timestamp >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("timestamp <= ?")
        params.append(date_to)

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = (
        f"SELECT id, timestamp, username, role_name, action, entity_type, "
        f"entity_id, case_id, description, result "
        f"FROM audit_logs {where} ORDER BY timestamp DESC LIMIT ?"
    )
    params.append(limit)

    c = get_connection()
    try:
        rows = c.execute(sql, params).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        c.close()


def get_audit_count() -> int:
    """Total number of audit rows (used on dashboard)."""
    c = get_connection()
    try:
        return c.execute("SELECT COUNT(*) AS c FROM audit_logs").fetchone()["c"]
    finally:
        c.close()


# Backward-compatibility alias used by the demo flow.
count_audit_logs = get_audit_count


def _row_to_dict(row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def init_audit_tables_if_needed(conn) -> None:
    """Ensure audit_logs table exists (no-op; schema.sql handles this)."""
    pass
