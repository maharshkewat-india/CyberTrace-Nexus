-- Digital Forensics Framework - SQLite Schema
-- Run: python -m src.database.schema or import this module in app init

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ----------------------------------------------------------------------
-- Users & Auth
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    salt TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    must_change_password INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    last_login TEXT
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS permissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------
-- System Settings
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- ----------------------------------------------------------------------
-- Cases
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_number TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    incident_date TEXT,
    status TEXT NOT NULL DEFAULT 'Open',
    priority TEXT,
    description TEXT,
    created_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    closed_at TEXT,
    archived_at TEXT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS case_users (
    case_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role_note TEXT,
    assigned_at TEXT NOT NULL,
    PRIMARY KEY (case_id, user_id),
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------
-- Evidence
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id TEXT NOT NULL UNIQUE,
    case_id INTEGER NOT NULL,
    evidence_type TEXT,
    description TEXT,
    source TEXT,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    file_extension TEXT,
    acquisition_time TEXT NOT NULL,
    original_modified_time TEXT,
    registered_by INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active',
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE RESTRICT,
    FOREIGN KEY (registered_by) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS evidence_hashes (
    evidence_id INTEGER PRIMARY KEY,
    md5_hash TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    algorithm TEXT NOT NULL DEFAULT 'SHA-256',
    computed_at TEXT NOT NULL,
    is_original INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------
-- Chain of Custody
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS custody_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evidence_id INTEGER NOT NULL,
    case_id INTEGER,
    action TEXT NOT NULL,
    from_person TEXT,
    to_person TEXT,
    location TEXT,
    event_time TEXT NOT NULL,
    notes TEXT,
    recorded_by INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
    FOREIGN KEY (recorded_by) REFERENCES users(id) ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------
-- Analysis Notes
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analysis_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    evidence_id INTEGER,
    user_id INTEGER NOT NULL,
    note_type TEXT,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id) ON DELETE CASCADE,
    FOREIGN KEY (evidence_id) REFERENCES evidence(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ----------------------------------------------------------------------
-- Audit Log
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    user_id INTEGER,
    username TEXT,
    role_name TEXT,
    action TEXT NOT NULL,
    entity_type TEXT,
    entity_id INTEGER,
    case_id INTEGER,
    description TEXT,
    result TEXT NOT NULL DEFAULT 'SUCCESS',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

-- ----------------------------------------------------------------------
-- Indexes for common queries
-- ----------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_cases_case_number ON cases(case_number);
CREATE INDEX IF NOT EXISTS idx_evidence_evidence_id ON evidence(evidence_id);
CREATE INDEX IF NOT EXISTS idx_evidence_case_id ON evidence(case_id);
CREATE INDEX IF NOT EXISTS idx_custody_evidence_id ON custody_events(evidence_id);
CREATE INDEX IF NOT EXISTS idx_custody_case_id ON custody_events(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_cases_status ON cases(status);
CREATE INDEX IF NOT EXISTS idx_case_users_user ON case_users(user_id);
CREATE INDEX IF NOT EXISTS idx_evidence_hashes ON evidence_hashes(evidence_id);