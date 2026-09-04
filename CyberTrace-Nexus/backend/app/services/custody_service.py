"""
custody_service.py - Business logic for chain-of-custody event recording.

Design notes:
- Every custody event is append-only; history cannot be edited silently.
- Corrections require a new event with action='CORRECTED' and notes explaining why.
- The service does NOT validate the plausibility of transitions (e.g.
  TRANSFERRED -> RECEIVED) – policy enforcement happens at the UI or SOP level.
- Each event writes an audit log entry.
"""

import datetime as dt
from typing import Optional, List, Dict, Any

from ..database.database import get_connection, transaction
from .audit_service import log_event
from ..auth.authorization import require_permission


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _resolve_username(conn, user_id: int) -> str:
    row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    return row["username"] if row else f"user-{user_id}"


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def add_custody_event(
    evidence_id: int,
    *,
    action: str,
    from_person: Optional[str] = None,
    to_person: Optional[str] = None,
    location: Optional[str] = None,
    notes: Optional[str] = None,
    case_id: Optional[int] = None,
    recorded_by: int,
    conn=None,
) -> int:
    """
    Record a custody event and return the new event id.

    Required permission: custody.create
    """
    # Validate action
    from ..auth.authorization import CUSTODY_ACTIONS
    if action not in CUSTODY_ACTIONS:
        raise ValueError(f"Invalid custody action: {action}")

    # If case_id not provided, look it up from evidence
    if case_id is None:
        conn_local = get_connection()
        try:
            row = conn_local.execute(
                "SELECT case_id FROM evidence WHERE id = ?", (evidence_id,)
            ).fetchone()
            case_id = row["case_id"] if row else None
        finally:
            conn_local.close()
        if case_id is None:
            raise ValueError(f"Evidence {evidence_id} not found or has no case.")

    def _do_insert(c):
        now = _now_iso()
        cur = c.execute(
            """
            INSERT INTO custody_events
                (evidence_id, case_id, action, from_person, to_person,
                 location, event_time, notes, recorded_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evidence_id,
                case_id,
                action,
                from_person,
                to_person,
                location,
                now,
                notes,
                recorded_by,
                now,
            ),
        )
        return cur.lastrowid

    if conn is not None:
        event_id = _do_insert(conn)
        conn.commit()
    else:
        with transaction() as c:
            event_id = _do_insert(c)

    # Audit event
    from_desc = from_person or "system"
    to_desc = to_person or "system"
    loc = location or "unspecified"
    note_text = notes or "(no notes)"
    log_event(
        action="CUSTODY_TRANSFER" if action in ("TRANSFERRED", "RECEIVED") else f"CUSTODY_{action}",
        user_id=recorded_by,
        description=(
            f"Custody event: {action} evidence {evidence_id} "
            f"from {from_desc} to {to_desc} at {loc}. Notes: {note_text}"
        ),
        case_id=case_id,
        entity_type="custody_event",
        entity_id=event_id,
    )
    return event_id


def list_custody_for_evidence(evidence_id: int) -> List[Dict[str, Any]]:
    """Return all custody events for a piece of evidence, oldest first."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT ce.*, u.username AS recorded_by_name
            FROM custody_events ce
            LEFT JOIN users u ON u.id = ce.recorded_by
            WHERE ce.evidence_id = ?
            ORDER BY ce.event_time ASC
            """,
            (evidence_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def list_custody_for_case(case_id: int) -> List[Dict[str, Any]]:
    """Return all custody events for a case (across its evidence)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT ce.*, u.username AS recorded_by_name, e.evidence_id
            FROM custody_events ce
            JOIN evidence e ON e.id = ce.evidence_id
            LEFT JOIN users u ON u.id = ce.recorded_by
            WHERE ce.case_id = ?
            ORDER BY ce.event_time ASC
            """,
            (case_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_custody_event(event_id: int) -> Optional[Dict[str, Any]]:
    """Return a single custody event by PK."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT ce.*, u.username AS recorded_by_name
            FROM custody_events ce
            LEFT JOIN users u ON u.id = ce.recorded_by
            WHERE ce.id = ?
            """,
            (event_id,),
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def count_custody_events() -> int:
    """Total custody events (for dashboard)."""
    conn = get_connection()
    try:
        return conn.execute("SELECT COUNT(*) AS c FROM custody_events").fetchone()["c"]
    finally:
        conn.close()


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------

def _row_to_dict(row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


if __name__ == "__main__":
    from database.database import initialize_database
    initialize_database()
    print("[custody_service] Schema ready.")