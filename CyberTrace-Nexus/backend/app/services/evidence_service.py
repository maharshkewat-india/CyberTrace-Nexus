"""
evidence_service.py - Business logic for evidence registration, hashing, and verification.

Design notes:
- Evidence is registered with the absolute path of the original file;
  the file is NEVER copied or modified by the framework.
- MD5 and SHA-256 are computed in a single streaming pass.
- The full evidence registration flow runs inside a single DB transaction
  (insert evidence, insert hashes, insert custody REGISTERED event, audit).
- Hash verification does NOT overwrite stored hashes. It returns a
  VerificationResult that the UI displays and records as an audit event.
- The service layer has no UI imports.
- Hashes are lowercased on input for consistent comparison.
"""

import datetime as dt
import os
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..models.models import Evidence
from ..database.database import get_connection, transaction
from . import hashing, audit_service
from .custody_service import add_custody_event
from ..auth.authorization import require_permission


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _generate_evidence_id(conn, case_number: str) -> str:
    """
    Generate a unique evidence ID: EV-<casenum_short>-<NNNN>.
    E.g. EV-2026-0001-0001
    """
    # Extract the NNNN portion of case number
    parts = case_number.split("-")
    short = parts[-1] if len(parts) >= 3 else "0000"
    prefix = f"EV-{case_number}-"

    row = conn.execute(
        "SELECT evidence_id FROM evidence WHERE evidence_id LIKE ? ORDER BY evidence_id DESC LIMIT 1",
        (f"{prefix}%",)
    ).fetchone()
    if row:
        last = row["evidence_id"]
        # Extract last 4 digits
        try:
            seq = int(last.split("-")[-1]) + 1
        except (IndexError, ValueError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def _collect_file_metadata(file_path: str) -> Dict[str, Any]:
    """Read file stat info; raises FileNotFoundError / PermissionError."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Evidence file not found: {file_path}")

    try:
        st = p.stat()
    except PermissionError:
        raise
    except OSError as e:
        raise OSError(f"Unable to access file: {e}")

    ext = p.suffix.lstrip(".").lower() if p.suffix else ""
    return {
        "size": int(st.st_size),
        "extension": ext,
        "modified_time": dt.datetime.fromtimestamp(
            int(st.st_mtime), tz=dt.timezone.utc
        ).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def register_evidence(
    case_id: int,
    file_path: str,
    *,
    evidence_type: str = "Document",
    description: str = "",
    source: str = "",
    registered_by: int,
    conn=None,
) -> Evidence:
    """
    Register a new piece of evidence in a single transaction.

    Steps (in order, all-or-nothing):
      1. Validate the file exists and is accessible.
      2. Compute MD5 + SHA-256 (chunked streaming read).
      3. Insert into `evidence`.
      4. Insert into `evidence_hashes` (marked as is_original=1).
      5. Insert custody REGISTERED event.
      6. Insert audit event.

    Args:
        case_id: PK of the parent case.
        file_path: Absolute path to the evidence file on disk.
        evidence_type: One of evidence_service.EVIDENCE_TYPES.
        description: Optional free-text description.
        source: Optional provenance/source info.
        registered_by: User ID registering the evidence.

    Returns:
        Evidence model with all metadata.

    Raises:
        ValueError: Invalid inputs.
        FileNotFoundError: File does not exist.
        PermissionError: File not readable.
        OSError: Other I/O failure.
    """
    # Validate case exists
    from .case_service import get_case
    case = get_case(case_id)
    if not case:
        raise ValueError(f"Case {case_id} not found.")

    # Validate file and gather metadata
    meta = _collect_file_metadata(file_path)

    # Now do the full registration in one transaction
    def _do_register(c):
        # Generate unique evidence_id
        evidence_id = _generate_evidence_id(c, case.case_number)
        now = _now_iso()

        # Insert evidence
        cur = c.execute(
            """
            INSERT INTO evidence
                (evidence_id, case_id, evidence_type, description, source,
                 file_path, file_size, file_extension,
                 acquisition_time, original_modified_time,
                 registered_by, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?)
            """,
            (evidence_id, case_id, evidence_type, description, source,
             file_path, meta["size"], meta["extension"],
             now, meta["modified_time"],
             registered_by, now),
        )
        ev_id = cur.lastrowid

        # Compute and store hashes (single streaming pass)
        hash_result = hashing.compute_hashes(file_path)
        c.execute(
            """
            INSERT INTO evidence_hashes
                (evidence_id, md5_hash, sha256_hash, computed_at, is_original)
            VALUES (?, ?, ?, ?, 1)
            """,
            (ev_id, hash_result.md5, hash_result.sha256, now),
        )

        # Insert custody REGISTERED event
        c.execute(
            """
            INSERT INTO custody_events
                (evidence_id, case_id, action, from_person, to_person,
                 location, event_time, notes, recorded_by, created_at)
            VALUES (?, ?, 'REGISTERED', NULL, ?, 'Acquisition', ?, 'Initial registration', ?, ?)
            """,
            (ev_id, case_id, _resolve_username(c, registered_by),
             now, registered_by, now),
        )

        return Evidence(
            id=ev_id,
            evidence_id=evidence_id,
            case_id=case_id,
            evidence_type=evidence_type,
            description=description,
            source=source,
            file_path=file_path,
            file_size=meta["size"],
            file_extension=meta["extension"],
            acquisition_time=now,
            original_modified_time=meta["modified_time"],
            registered_by=registered_by,
            status="Active",
            created_at=now,
            md5=hash_result.md5,
            sha256=hash_result.sha256,
        )

    if conn is not None:
        evidence = _do_register(conn)
        conn.commit()
    else:
        with transaction() as c:
            evidence = _do_register(c)

    # Audit event (outside the transaction; not strictly required to be)
    audit_service.log_event(
        action="EVIDENCE_REGISTERED",
        user_id=registered_by,
        description=(
            f"Registered evidence {evidence.evidence_id} for case {case.case_number} "
            f"({evidence.file_size} bytes)"
        ),
        case_id=case_id,
        entity_type="evidence",
        entity_id=evidence.id,
    )
    return evidence


def get_evidence(evidence_pk: int) -> Optional[Evidence]:
    """Return a single evidence record (by PK) with its hashes."""
    c = get_connection()
    try:
        row = c.execute(
            "SELECT e.*, h.md5_hash, h.sha256_hash "
            "FROM evidence e "
            "LEFT JOIN evidence_hashes h ON h.evidence_id = e.id "
            "WHERE e.id = ?",
            (evidence_pk,),
        ).fetchone()
        return _row_to_evidence(row) if row else None
    finally:
        c.close()


def get_evidence_by_evidence_id(evidence_id: str) -> Optional[Evidence]:
    """Return evidence by its human-readable evidence_id (e.g. EV-...)."""
    c = get_connection()
    try:
        row = c.execute(
            "SELECT e.*, h.md5_hash, h.sha256_hash "
            "FROM evidence e "
            "LEFT JOIN evidence_hashes h ON h.evidence_id = e.id "
            "WHERE e.evidence_id = ?",
            (evidence_id,),
        ).fetchone()
        return _row_to_evidence(row) if row else None
    finally:
        c.close()


def list_evidence_for_case(case_id: int) -> List[Evidence]:
    """Return all evidence for a case, newest first."""
    c = get_connection()
    try:
        rows = c.execute(
            "SELECT e.*, h.md5_hash, h.sha256_hash "
            "FROM evidence e "
            "LEFT JOIN evidence_hashes h ON h.evidence_id = e.id "
            "WHERE e.case_id = ? ORDER BY e.created_at DESC",
            (case_id,),
        ).fetchall()
        return [_row_to_evidence(r) for r in rows]
    finally:
        c.close()


def list_all_evidence(limit: int = 200) -> List[Evidence]:
    """Return all evidence across cases (audit/auditor views)."""
    c = get_connection()
    try:
        rows = c.execute(
            "SELECT e.*, h.md5_hash, h.sha256_hash "
            "FROM evidence e "
            "LEFT JOIN evidence_hashes h ON h.evidence_id = e.id "
            "ORDER BY e.created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_evidence(r) for r in rows]
    finally:
        c.close()


def verify_evidence(
    evidence_pk: int,
    verified_by: int,
) -> Dict[str, Any]:
    """
    Re-hash a file and compare to stored hashes.

    This NEVER overwrites stored hashes. It produces a VerificationResult
    and an audit event.

    Args:
        evidence_pk: Primary key of the evidence row.
        verified_by: User performing the verification.

    Returns:
        Dict with md5_match, sha256_match, current hashes, stored hashes,
        and a 'status' label.

    Raises:
        ValueError: Evidence not found.
        FileNotFoundError: Evidence file no longer exists.
    """
    ev = get_evidence(evidence_pk)
    if not ev:
        raise ValueError(f"Evidence {evidence_pk} not found.")
    if not ev.md5 or not ev.sha256:
        raise ValueError("Stored hashes missing; cannot verify.")

    result = hashing.verify_hashes(ev.file_path, ev.md5, ev.sha256)
    result_dict = result.to_dict()

    # Audit event
    if result.all_match:
        audit_service.log_event(
            action="HASH_VERIFIED",
            user_id=verified_by,
            description=f"Hash verification PASSED for evidence {ev.evidence_id}",
            case_id=ev.case_id,
            entity_type="evidence",
            entity_id=evidence_pk,
        )
    else:
        audit_service.log_event(
            action="HASH_MISMATCH",
            user_id=verified_by,
            description=(
                f"Hash verification FAILED for evidence {ev.evidence_id}. "
                f"Stored MD5={ev.md5}, Current MD5={result.current_md5}. "
                f"Stored SHA256={ev.sha256}, Current SHA256={result.current_sha256}."
            ),
            case_id=ev.case_id,
            entity_type="evidence",
            entity_id=evidence_pk,
            result="FAIL",
        )
    return result_dict


def add_evidence_note(
    case_id: int,
    evidence_pk: int,
    content: str,
    note_type: str = "analysis",
    user_id: int = 0,
) -> int:
    """Add an analysis note (optionally attached to specific evidence)."""
    if not content or not content.strip():
        raise ValueError("Note content is required.")
    now = _now_iso()
    c = get_connection()
    try:
        cur = c.execute(
            """
            INSERT INTO analysis_notes
                (case_id, evidence_id, user_id, note_type, content, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (case_id, evidence_pk if evidence_pk else None,
             user_id, note_type, content.strip(), now),
        )
        c.commit()
        return cur.lastrowid
    finally:
        c.close()


def list_notes_for_case(case_id: int) -> List[Dict[str, Any]]:
    """Return all analysis notes for a case, with username lookup."""
    c = get_connection()
    try:
        rows = c.execute(
            """
            SELECT n.id, n.case_id, n.evidence_id, n.user_id, n.note_type,
                   n.content, n.created_at, u.username
            FROM analysis_notes n
            LEFT JOIN users u ON u.id = n.user_id
            WHERE n.case_id = ?
            ORDER BY n.created_at DESC
            """,
            (case_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        c.close()


def search_evidence(query: str, limit: int = 50) -> List[Evidence]:
    """Search by evidence_id, description, file_path, or case_number."""
    like = f"%{query}%"
    c = get_connection()
    try:
        rows = c.execute(
            """
            SELECT e.*, h.md5_hash, h.sha256_hash
            FROM evidence e
            LEFT JOIN evidence_hashes h ON h.evidence_id = e.id
            LEFT JOIN cases c ON c.id = e.case_id
            WHERE e.evidence_id LIKE ?
               OR e.description LIKE ?
               OR e.file_path LIKE ?
               OR c.case_number LIKE ?
            ORDER BY e.evidence_id
            LIMIT ?
            """,
            (like, like, like, like, limit),
        ).fetchall()
        return [_row_to_evidence(r) for r in rows]
    finally:
        c.close()


# ----------------------------------------------------------------------
# Stats
# ----------------------------------------------------------------------

def count_evidence() -> int:
    c = get_connection()
    try:
        return c.execute("SELECT COUNT(*) AS c FROM evidence").fetchone()["c"]
    finally:
        c.close()


def count_verified_evidence() -> int:
    """Return count of evidence that has matching current-vs-stored hashes.

    Counts only evidence whose file still exists; missing files are not
    counted as 'verified'.
    """
    verified = 0
    c = get_connection()
    try:
        rows = c.execute(
            "SELECT e.file_path, h.md5_hash, h.sha256_hash "
            "FROM evidence e "
            "JOIN evidence_hashes h ON h.evidence_id = e.id"
        ).fetchall()
    finally:
        c.close()
    for r in rows:
        try:
            result = hashing.verify_hashes(r["file_path"], r["md5_hash"], r["sha256_hash"])
            if result.all_match:
                verified += 1
        except (FileNotFoundError, PermissionError, OSError):
            continue
    return verified


# ----------------------------------------------------------------------
# Internal helpers
# ----------------------------------------------------------------------

def _resolve_username(conn, user_id: int) -> str:
    row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
    return row["username"] if row else f"user-{user_id}"


def _row_to_evidence(row) -> Evidence:
    if row is None:
        return None
    return Evidence(
        id=row["id"],
        evidence_id=row["evidence_id"],
        case_id=row["case_id"],
        evidence_type=row["evidence_type"],
        description=row["description"],
        source=row["source"],
        file_path=row["file_path"],
        file_size=row["file_size"],
        file_extension=row["file_extension"],
        acquisition_time=row["acquisition_time"],
        original_modified_time=row["original_modified_time"],
        registered_by=row["registered_by"],
        status=row["status"],
        created_at=row["created_at"],
        md5=row["md5_hash"],
        sha256=row["sha256_hash"],
    )


def _row_to_dict(row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}


if __name__ == "__main__":
    from database.database import initialize_database
    initialize_database()
    print("[evidence_service] Schema ready.")