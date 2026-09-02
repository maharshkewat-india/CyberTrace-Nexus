"""
database.py - SQLite connection helpers and one-time schema/seed bootstrap.
"""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

# Resolve paths relative to project root (one level up from this package).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "forensics_framework.db"
SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


# ----------------------------------------------------------------------
# Connection helpers
# ----------------------------------------------------------------------

def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with foreign keys enabled and Row factory."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def transaction():
    """Context manager for an explicit SQLite transaction with rollback on error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ----------------------------------------------------------------------
# Schema + seed bootstrap
# ----------------------------------------------------------------------

def _load_schema() -> str:
    return SCHEMA_PATH.read_text(encoding="utf-8")


def _seed_roles_permissions(conn: sqlite3.Connection) -> None:
    """Insert default roles/permissions if missing. Safe to call repeatedly."""
    permissions = [
        ("case.create", "Create new cases"),
        ("case.view", "View cases"),
        ("case.update", "Edit cases"),
        ("case.assign", "Assign personnel to cases"),
        ("case.close", "Close/Archive cases"),
        ("evidence.create", "Register new evidence"),
        ("evidence.view", "View evidence"),
        ("evidence.update", "Edit evidence metadata"),
        ("evidence.hash", "Calculate hashes"),
        ("evidence.verify", "Verify hashes"),
        ("custody.create", "Record custody events"),
        ("custody.view", "View custody history"),
        ("analysis.create", "Add analysis notes"),
        ("analysis.view", "View analysis notes"),
        ("audit.view", "View audit log"),
        ("report.generate", "Generate reports"),
        ("user.create", "Create users"),
        ("user.view", "View users"),
        ("user.update", "Edit users"),
        ("user.disable", "Enable/Disable users"),
        ("system.manage", "System settings"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO permissions (name, description) VALUES (?, ?)",
        permissions,
    )

    # Role -> permission map
    role_perms: dict[str, list[str]] = {
        "ADMINISTRATOR": [p for p, _ in permissions],
        "CASE INVESTIGATOR": [
            "case.create", "case.view", "case.update", "case.assign", "case.close",
            "evidence.create", "evidence.view", "evidence.hash", "evidence.verify",
            "custody.create", "custody.view",
            "analysis.create", "analysis.view",
            "report.generate",
        ],
        "FORENSIC ANALYST": [
            "case.view",
            "evidence.view", "evidence.hash", "evidence.verify",
            "custody.view",
            "analysis.create", "analysis.view",
        ],
        "EVIDENCE CUSTODIAN": [
            "case.view",
            "evidence.view", "evidence.create",
            "custody.create", "custody.view",
        ],
        "AUDITOR": [
            "case.view",
            "evidence.view",
            "custody.view",
            "analysis.view",
            "audit.view",
            "report.generate",
        ],
    }

    role_descriptions = {
        "ADMINISTRATOR": "Full administrative access",
        "CASE INVESTIGATOR": "Manages cases and evidence",
        "FORENSIC ANALYST": "Performs analysis and verifies evidence",
        "EVIDENCE CUSTODIAN": "Handles physical chain of custody",
        "AUDITOR": "Read-only oversight",
    }

    for role_name, perms in role_perms.items():
        conn.execute(
            "INSERT OR IGNORE INTO roles (name, description) VALUES (?, ?)",
            (role_name, role_descriptions[role_name]),
        )
        role_row = conn.execute(
            "SELECT id FROM roles WHERE name = ?", (role_name,)
        ).fetchone()
        if role_row is None:
            continue
        role_id = role_row["id"]
        for perm in perms:
            perm_row = conn.execute(
                "SELECT id FROM permissions WHERE name = ?", (perm,)
            ).fetchone()
            if perm_row is None:
                continue
            conn.execute(
                "INSERT OR IGNORE INTO role_permissions (role_id, permission_id) VALUES (?, ?)",
                (role_id, perm_row["id"]),
            )


def initialize_database() -> None:
    """Create tables and seed default roles/permissions. Idempotent."""
    conn = get_connection()
    try:
        conn.executescript(_load_schema())
        _seed_roles_permissions(conn)
        conn.commit()
    finally:
        conn.close()


def is_fresh_database() -> bool:
    """Return True when the database has not been initialized (no users)."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
        return (row["c"] or 0) == 0
    finally:
        conn.close()


def database_info() -> dict:
    """Return a small dict with DB location/size for the launcher."""
    exists = DB_PATH.exists()
    size = DB_PATH.stat().st_size if exists else 0
    return {
        "path": str(DB_PATH),
        "exists": exists,
        "size_bytes": size,
    }


if __name__ == "__main__":
    initialize_database()
    print(f"[init] Database created at: {DB_PATH}")
