# Digital Forensics Evidence Management System — Phase 0 Technical Audit

> **Repository:** `e:/CyberTrace Nexus/Digital Forensics Evidence Management System/`
> **Auditor:** Claude Code (Phase 0)
> **Date:** 2026-08-31
> **Scope:** Complete codebase audit — backend (FastAPI), frontend (Next.js), database (SQLite), auth/RBAC, tests, and deployment
> **Constraint:** No application source code was modified. Only this document was created.

---

## Table of Contents

1. [Current Architecture](#1-current-architecture)
2. [Frontend Architecture](#2-frontend-architecture)
3. [Backend Architecture](#3-backend-architecture)
4. [Database Architecture](#4-database-architecture)
5. [Authentication Flow](#5-authentication-flow)
6. [RBAC Flow](#6-rbac-flow)
7. [Case Management Flow](#7-case-management-flow)
8. [Evidence Management Flow](#8-evidence-management-flow)
9. [Hashing & Verification Flow](#9-hashing--verification-flow)
10. [Chain of Custody Flow](#10-chain-of-custody-flow)
11. [Audit Logging Flow](#11-audit-logging-flow)
12. [Notes System](#12-notes-system)
13. [Reporting System](#13-reporting-system)
14. [API Inventory](#14-api-inventory)
15. [Database Table Inventory](#15-database-table-inventory)
16. [Frontend Page Inventory](#16-frontend-page-inventory)
17. [Important Components](#17-important-components)
18. [Reusable Services](#18-reusable-services)
19. [Existing Tests](#19-existing-tests)
20. [Dependencies](#20-dependencies)
21. [Security Controls](#21-security-controls)
22. [Technical Debt](#22-technical-debt)
23. [Potential Bugs](#23-potential-bugs)
24. [Missing Validation](#24-missing-validation)
25. [Code Duplication](#25-code-duplication)
26. [Hard-coded Values](#26-hard-coded-values)
27. [Configuration Problems](#27-configuration-problems)
28. [Scalability Concerns](#28-scalability-concerns)
29. [Security Concerns](#29-security-concerns)
30. [V2 Extension Opportunities](#30-v2-extension-opportunities)
31. [Component Classification](#31-component-classification)
32. [CyberTrace Nexus V2 Change Map](#32-cybertrace-nexus-v2-change-map)

---

## 1. Current Architecture

### System Overview

The Digital Forensics Evidence Management System (DFEMS) is a full-stack web application for managing forensic cases, evidence, and chain of custody. It consists of:

- **Backend:** FastAPI 0.104.1+ with uvicorn, Python 3.10+
- **Frontend:** Next.js 16.3.3 with React 19.2.8
- **Database:** SQLite with WAL mode and foreign key enforcement
- **Auth:** PBKDF2-HMAC-SHA256 password hashing + JWT HS256 tokens
- **RBAC:** 5 roles with 21 granular permissions

### Directory Structure

```
Digital Forensics Evidence Management System/
├── backend/                     # FastAPI application
│   ├── main.py                  # Entry point (uvicorn)
│   ├── app.py                   # FastAPI app factory
│   ├── requirements.txt
│   ├── auth/                    # Authentication & RBAC
│   │   ├── authentication.py     # register_user, authenticate_user, session management
│   │   ├── authorization.py      # PERMISSIONS_ALL, has_permission, require_permission
│   │   └── password_manager.py   # PBKDF2 hashing (210k iterations, 16-byte salt)
│   ├── core/
│   │   ├── security.py           # JWT token creation/verification
│   │   └── dependencies.py       # FastAPI dependency injection for auth
│   ├── services/                 # Business logic layer
│   │   ├── case_service.py
│   │   ├── evidence_service.py
│   │   ├── custody_service.py
│   │   ├── audit_service.py
│   │   └── hashing.py            # Streaming MD5+SHA-256 computation
│   ├── api/                     # API route handlers
│   │   ├── auth.py, cases.py, evidence.py
│   │   ├── custody.py, audit.py, users.py, reports.py
│   ├── schemas/                 # Pydantic request/response models
│   │   ├── auth.py, case.py, evidence.py
│   │   ├── custody.py, audit.py, user.py
│   ├── models/
│   │   └── models.py            # Frozen dataclasses (User, Case, Evidence, etc.)
│   ├── database/
│   │   ├── database.py          # Connection management, init, seed
│   │   └── schema.sql           # Full DDL with indexes
│   └── middleware/             # Empty __init__.py only
├── frontend/                    # Next.js application
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   │   ├── layout.tsx       # Root layout with AuthProvider
│   │   │   ├── page.tsx         # Root redirect to /login or /dashboard
│   │   │   ├── login/page.tsx   # Login page
│   │   │   └── (dashboard)/    # Protected dashboard group
│   │   │       ├── layout.tsx   # Auth redirect + Sidebar/Topbar
│   │   │       ├── dashboard/page.tsx
│   │   │       ├── cases/page.tsx
│   │   │       ├── evidence/page.tsx
│   │   │       ├── custody/page.tsx
│   │   │       ├── audit/page.tsx
│   │   │       ├── users/page.tsx
│   │   │       └── reports/page.tsx
│   │   ├── components/
│   │   │   ├── layout/          # Sidebar, Topbar
│   │   │   └── ui/             # shadcn-style primitives (9 components)
│   │   ├── hooks/
│   │   │   └── useAuth.tsx     # AuthContext (React Context)
│   │   ├── lib/
│   │   │   ├── api.ts          # Axios client with JWT interceptors
│   │   │   ├── auth.ts         # Standalone auth helpers
│   │   │   └── utils.ts        # cn(), formatDateTime(), etc.
│   │   └── types/
│   │       └── index.ts        # TypeScript interfaces
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── tests/
│   ├── test_basic.py            # 10 functional unit/integration tests
│   ├── test_integration_rbac.py  # Tkinter-based RBAC integration tests
│   └── test_ui_rbac.py          # UI RBAC tests
├── demo/
│   └── demo_flow.py             # Demo data creation script
├── data/                        # Runtime data directory
│   └── forensics_framework.db   # SQLite database file
├── docs/                        # Documentation
│   └── PROJECT_AUDIT.md         # ← This document
├── RUN_ME.bat                   # Windows launcher (5-step startup)
├── README.md
└── requirements.txt             # Top-level requirements (may be duplicate)
```

### Deployment Model

- **Development:** `RUN_ME.bat` launches both services in separate `cmd.exe` windows
- **Backend:** `python main.py` → uvicorn on `0.0.0.0:8000`
- **Frontend:** `npm run dev` → Next.js on `localhost:3000`
- **Database:** SQLite file at `data/forensics_framework.db` (WAL mode)

**[⬆ Back to TOC](#table-of-contents)**

---

## 2. Frontend Architecture

### Framework & Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 16.3.3 (App Router) |
| UI Library | React 19.2.8 |
| Styling | Tailwind CSS 4 with CSS custom properties |
| Component Library | shadcn/ui-style primitives built on Radix UI |
| HTTP Client | Axios 1.20.0 |
| Forms | react-hook-form |
| Validation | Zod |
| Icons | lucide-react |
| Fonts | Geist + Geist_Mono (next/font/google) |

### Architecture Pattern

The frontend follows a **React Context + Axios** pattern:

- **`AuthContext`** (`useAuth.tsx`): React Context providing `user`, `token`, `isAuthenticated`, `isLoading`, `login()`, `logout()`, `hasPermission()`, `hasAnyPermission()`, `hasRole()`, `refreshUser()`
- **`api.ts`**: Singleton Axios instance with JWT request interceptor and 401 response interceptor
- **Route groups**: `(dashboard)/` group uses `layout.tsx` that enforces auth redirect
- **Permission gating**: Navigation items and UI elements gated by `hasPermission()` / `hasRole()`

### State Management

- **Auth state**: React Context (`AuthContext`) — stored in `localStorage` as `forensic_token` and `forensic_user`
- **Server state**: Per-page `useState` + Axios calls (no TanStack Query / SWR)
- **Form state**: `react-hook-form` per dialog/form

### Theming

Dark theme via CSS custom properties defined in `globals.css`:

```css
:root {
  --background: #0a0a0f;
  --background-secondary: #11111a;
  --background-tertiary: #16161f;
  --foreground: #fafafa;
  --foreground-muted: #a1a1aa;
  --foreground-subtle: #52525b;
  --accent: #6d28d9;
  --accent-hover: #5b21b6;
  --success: #16a34a;
  --warning: #ca8a04;
  --danger: #dc2626;
  --info: #0891b2;
  --border: #27272a;
  --card: #18181b;
}
```

### Routing

| Path | Component | Protection |
|------|-----------|------------|
| `/` | Redirect → `/login` or `/dashboard` | Public |
| `/login` | Login form + branding | Public |
| `/dashboard` | Stats, recent cases, activity feed | Auth required |
| `/cases` | Case table + create dialog | Auth + VIEW_CASES |
| `/evidence` | Evidence table + register dialog | Auth + VIEW_EVIDENCE |
| `/custody` | Custody timeline + record dialog | Auth + VIEW_CUSTODY |
| `/audit` | Audit log with filters | Auth + VIEW_AUDIT |
| `/users` | User management table | Auth + MANAGE_USERS |
| `/reports` | Report generation form | Auth + VIEW_REPORTS |

**[⬆ Back to TOC](#table-of-contents)**

---

## 3. Backend Architecture

### Framework & Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI 0.104.1+ |
| Server | uvicorn |
| Database | SQLite with WAL mode, foreign keys |
| ORM | Raw `sqlite3` (no ORM) |
| Auth | python-jose (JWT), passlib (PBKDF2) |
| Validation | Pydantic v1 |
| Logging | structlog (in requirements) |
| Testing | pytest, httpx |

### Layer Architecture

```
api/           → HTTP handlers (FastAPI routers)
    ↓
services/      → Business logic (case_service, evidence_service, etc.)
    ↓
models/        → Frozen dataclasses (User, Case, Evidence, etc.)
    ↓
database/      → SQLite connection management + schema init
```

### API Router Organization

| Router | Prefix | Routes | Responsibility |
|--------|--------|--------|----------------|
| `auth` | `/auth` | 4 | Login, logout, session refresh, current user |
| `cases` | `/cases` | 9 | Case CRUD + close/archive/assign |
| `evidence` | `/evidence` | 9 | Evidence CRUD + verify/hash/note/custody |
| `custody` | `/custody` | 3 | Custody event listing + creation |
| `audit` | `/audit-logs` | 2 | Audit log listing + count |
| `users` | `/users` | 7 | User CRUD + disable/enable/reset-password |
| `reports` | `/reports` | 1 | Case report generation |

### Startup Behavior

On `app.on_event("startup")`:
1. `database.initialize_database()` — creates schema + seeds roles/permissions if fresh
2. If fresh DB: `register_user("admin", "Admin@123", "ADMINISTRATOR")` — creates default admin

### CORS Configuration

```python
allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

Only 3 specific localhost origins are allowed. Production deployment requires origin update.

**[⬆ Back to TOC](#table-of-contents)**

---

## 4. Database Architecture

### SQLite Configuration

- **Location:** `data/forensics_framework.db`
- **Mode:** WAL (Write-Ahead Logging) enabled via `PRAGMA journal_mode=WAL`
- **Foreign Keys:** Enforced via `PRAGMA foreign_keys=ON`
- **Synchronous:** Default (NORMAL)
- **File locking:** Default SQLite locking

### Schema Summary

13 tables total. Core entities:

```
users ────────────────────────────────────────────
  └─ user_roles ──→ roles ──→ role_permissions ──→ permissions
  └─ sessions
  └─ audit_logs

cases ─────────────────────────────────────────────
  └─ case_users ──→ users
  └─ evidence ──→ evidence_hashes
       └─ custody_events ──→ users
       └─ analysis_notes ──→ users
```

### Key Design Decisions

- **No ORM:** Raw `sqlite3` with parameterized queries throughout — SQL injection prevention is manual
- **No soft deletes:** Records are hard-deleted
- **No migrations:** Schema applied directly via `schema.sql` on startup; no Alembic or Flyway
- **Audit log append-only:** No UPDATE/DELETE on `audit_logs` table
- **WAL mode:** Allows concurrent reads while writing

### Indexes

Defined in `schema.sql`:

| Index | Table | Columns |
|-------|-------|---------|
| `idx_cases_status` | cases | status |
| `idx_cases_priority` | cases | priority |
| `idx_cases_incident_date` | cases | incident_date |
| `idx_evidence_case` | evidence | case_id |
| `idx_evidence_type` | evidence | evidence_type |
| `idx_evidence_status` | evidence | status |
| `idx_custody_evidence` | custody_events | evidence_id |
| `idx_custody_case` | custody_events | case_id |
| `idx_custody_timestamp` | custody_events | timestamp |
| `idx_audit_action` | audit_logs | action |
| `idx_audit_user` | audit_logs | user_id |
| `idx_audit_timestamp` | audit_logs | timestamp |
| `idx_audit_entity` | audit_logs | entity_type, entity_id |
| `idx_evidence_hashes_evidence` | evidence_hashes | evidence_id |
| `idx_analysis_notes_case` | analysis_notes | case_id |
| `idx_sessions_token` | sessions | token |
| `idx_sessions_user` | sessions | user_id |

### Seed Data

On fresh DB initialization, `_seed_roles_permissions()` inserts:

**5 Roles:**
- ADMINISTRATOR
- CASE_INVESTIGATOR
- FORENSIC_ANALYST
- EVIDENCE_CUSTODIAN
- AUDITOR

**21 Permissions** (see Section 6 for full list)

**Default Role Permissions:**
- ADMINISTRATOR → all permissions
- CASE_INVESTIGATOR → case + evidence + custody + notes permissions
- FORENSIC_ANALYST → evidence + custody + notes + hash verification
- EVIDENCE_CUSTODIAN → evidence viewing + custody + notes
- AUDITOR → all viewing permissions (read-only)

**[⬆ Back to TOC](#table-of-contents)**

---

## 5. Authentication Flow

### Login Sequence

```
1. POST /auth/login { username, password }
   │
2. backend/auth/authentication.py → authenticate_user(username, password)
   │
3. Load user by username from SQLite
   │
4. verify_password(password, stored_hash) → PBKDF2-HMAC-SHA256 comparison
   │
5. Check user.is_active flag → reject if disabled
   │
6. create_session_token(user_id) → UUID token + JWT
   │
7. Insert session into sessions table (token, user_id, created_at, expires_at)
   │
8. log_event(LOGIN_SUCCESS) → audit
   │
9. Return { access_token, token_type: "bearer", user }
```

### JWT Token Structure

```python
payload = {
    "sub": str(user_id),        # subject = user ID
    "exp": expire_datetime,      # UTC datetime, default 7 days
    "iat": issued_at,            # issued at
    "jti": uuid_token           # JWT ID (matches session token)
}
encoded = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")
```

### Subsequent Requests

```
1. Axios interceptor reads localStorage.getItem("forensic_token")
2. Attaches: Authorization: Bearer <token>
3. Backend: get_current_user() dependency
   ├── verify_access_token(token) → payload
   ├── Extract user_id from payload["sub"]
   ├── verify_session(token) → check sessions table for valid session
   └── Return CurrentUser object
```

### Logout

```
1. POST /auth/logout
2. Backend deletes session from sessions table
3. Frontend clears localStorage (forensic_token + forensic_user)
4. log_event(LOGOUT)
```

### Session Cleanup

`cleanup_expired_sessions()` is called by `authenticate_user()` on each login attempt — deletes all sessions where `expires_at < now`. No background scheduler.

### 401 Handling (Frontend)

Axios response interceptor: on HTTP 401, clears `localStorage` and redirects to `/login`.

**[⬆ Back to TOC](#table-of-contents)**

---

## 6. RBAC Flow

### Permission Check Pattern

```python
# Service layer
from auth.authorization import require_permission

@router.post("/evidence", dependencies=[Depends(require_permission("REGISTER_EVIDENCE"))])
async def register_evidence(...):
    ...
```

### Permission Resolution

```
has_permission(user_roles, required_permission)
  → permissions_for_roles(user_roles) → frozenset of all permissions
  → check if required_permission in frozenset
```

### 21 Permissions (PERMISSIONS_ALL)

| Permission | Description | Default Role |
|------------|-------------|--------------|
| `VIEW_CASES` | View case list and details | ALL except nobody |
| `CREATE_CASES` | Create new cases | ADMIN, CASE_INVESTIGATOR |
| `EDIT_CASES` | Edit case details | ADMIN, CASE_INVESTIGATOR |
| `CLOSE_CASES` | Close cases | ADMIN, CASE_INVESTIGATOR |
| `ARCHIVE_CASES` | Archive cases | ADMIN |
| `DELETE_CASES` | Delete cases | ADMIN |
| `ASSIGN_CASE_USERS` | Assign users to cases | ADMIN, CASE_INVESTIGATOR |
| `VIEW_EVIDENCE` | View evidence items | ALL |
| `REGISTER_EVIDENCE` | Register new evidence | ADMIN, CASE_INVESTIGATOR, FORENSIC_ANALYST |
| `EDIT_EVIDENCE` | Edit evidence details | ADMIN, CASE_INVESTIGATOR |
| `DELETE_EVIDENCE` | Delete evidence | ADMIN |
| `VERIFY_EVIDENCE` | Verify evidence hashes | ADMIN, CASE_INVESTIGATOR, FORENSIC_ANALYST |
| `VIEW_CUSTODY` | View chain of custody | ALL |
| `CREATE_CUSTODY_EVENTS` | Create custody events | ADMIN, CASE_INVESTIGATOR, FORENSIC_ANALYST, EVIDENCE_CUSTODIAN |
| `VIEW_AUDIT` | View audit logs | ALL |
| `VIEW_REPORTS` | View and generate reports | ALL |
| `MANAGE_USERS` | Manage user accounts | ADMIN |
| `MANAGE_ROLES` | Manage roles and permissions | ADMIN |
| `ADD_NOTES` | Add analysis notes | ADMIN, CASE_INVESTIGATOR, FORENSIC_ANALYST, EVIDENCE_CUSTODIAN |
| `SYSTEM_CONFIG` | Configure system settings | ADMIN |
| `DELETE_AUDIT_LOGS` | Delete audit log entries | ADMIN |

### Frontend Permission Gating

```typescript
// sidebar.tsx
const navItems = [
  { label: "Cases", href: "/cases", icon: Briefcase,
    requiredPermission: "VIEW_CASES" },
  { label: "Evidence", href: "/evidence", icon: FileSearch,
    requiredPermission: "VIEW_EVIDENCE" },
  // ...
];

// Render only if user has permission
{hasPermission(item.requiredPermission) && <NavItem />}
```

### Role Hierarchy

No role hierarchy. Permissions are additive via role assignment. A user can have multiple roles.

**[⬆ Back to TOC](#table-of-contents)**

---

## 7. Case Management Flow

### Case Lifecycle

```
[CREATE] → Open → Under Investigation → [CLOSE] → Closed → [ARCHIVE] → Archived
```

### Create Case

```
POST /cases { title, description, incident_date, priority }
  → validate via CaseCreate Pydantic schema
  → case_service.create_case(current_user, case_data)
  → generate case_number: CASE-YYYY-NNNN
  → INSERT into cases table
  → log_event(CASE_CREATED)
  → return CaseResponse
```

### Assign Users to Case

```
POST /cases/{case_id}/assign { user_id }
  → verify caller has ASSIGN_CASE_USERS
  → verify user_id exists and is active
  → verify case_id exists
  → INSERT into case_users (case_id, user_id)
  → log_event(CASE_ASSIGNED)
```

### Close / Archive

```
POST /cases/{case_id}/close
  → update cases.status = "Closed"
  → log_event(CASE_CLOSED)

POST /cases/{case_id}/archive
  → update cases.status = "Archived"
  → requires ARCHIVE_CASES permission
  → log_event(CASE_ARCHIVED)
```

### Case Number Generation

```python
def _generate_case_number(conn) -> str:
    year = datetime.now().year
    # Count cases with prefix CASE-YYYY-
    count = cursor.execute(
        "SELECT COUNT(*) FROM cases WHERE case_number LIKE ?",
        (f"CASE-{year}-%",)
    ).fetchone()[0]
    return f"CASE-{year}-{str(count + 1).zfill(4)}"
```

### Case Search

`GET /cases?search=query` → `case_service.search_cases()` performs `LIKE` on `title || ' ' || case_number || ' ' || description`.

**[⬆ Back to TOC](#table-of-contents)**

---

## 8. Evidence Management Flow

### Evidence Lifecycle

```
[REGISTER] → Registered → Under Analysis → [VERIFY] → Verified
```

### Register Evidence

```
POST /evidence { case_id, file_path, evidence_type, description, notes }
  → validate via EvidenceCreate Pydantic schema
  → evidence_service.register_evidence(current_user, evidence_data)
  → generate evidence_id: EV-<case_number>-NNNN
  → INSERT into evidence table
  → compute_hashes(file_path) → MD5 + SHA-256 in single 64KB chunk pass
  → INSERT into evidence_hashes (md5_hash, sha256_hash, computed_at, is_original=1)
  → INSERT into custody_events (HANDOFF, from=current_user, to=current_user)
  → log_event(EVIDENCE_REGISTERED)
```

### Evidence Types

`FILE`, `DISK_IMAGE`, `MEMORY_DUMP`, `NETWORK_CAPTURE`, `LOG_FILE`, `REGISTRY_HIVE`, `ARTIFACT`, `OTHER`

### Evidence Statuses

`Registered`, `Under Analysis`, `Verified`, `Corrupted`

### Evidence Verification

```
POST /evidence/{evidence_id}/verify
  → load current stored hashes from evidence_hashes
  → verify_hashes(file_path, stored_md5, stored_sha256)
  → return VerificationResult { md5_match, sha256_match, stored, current }
  → log_event(EVIDENCE_VERIFIED)
  → NOTE: Does NOT update stored hashes (forensic integrity)
```

### Key Design Decision

Hash verification is **non-destructive**: the verification compares current hashes against stored ones but never overwrites the stored values. This ensures the original registration hash is always preserved as evidence.

**[⬆ Back to TOC](#table-of-contents)**

---

## 9. Hashing & Verification Flow

### Streaming Hash Computation

```python
CHUNK_SIZE = 64 * 1024  # 64 KiB

def compute_hashes(file_path: str) -> HashResult:
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            md5.update(chunk)
            sha256.update(chunk)
    return HashResult(md5=md5.hexdigest(), sha256=sha256.hexdigest())
```

### Design Rationale

- **64 KiB chunks:** Good balance between syscall overhead and memory usage
- **Single pass:** Both MD5 and SHA-256 computed simultaneously — no double file I/O
- **Absolute paths:** `Path(file_path).resolve()` ensures no path traversal
- **Frozen dataclasses:** `HashResult` and `VerificationResult` are immutable
- **Never overwrite:** `verify_hashes()` returns comparison only, never updates stored values

### Verification Result

```python
@dataclass(frozen=True)
class VerificationResult:
    md5_match: bool
    sha256_match: bool
    stored_md5: str
    stored_sha256: str
    current_md5: str
    current_sha256: str

    @property
    def all_match(self) -> bool: ...
    @property
    def status_label(self) -> str:  # "HASH VERIFIED" | "INTEGRITY WARNING"
    @property
    def status_color(self) -> str:  # "green" | "red"
```

**[⬆ Back to TOC](#table-of-contents)**

---

## 10. Chain of Custody Flow

### Custody Actions

`HANDOFF`, `SECURE_STORAGE`, `RELEASED`

### Record Custody Event

```
POST /custody { evidence_id, action, from_person, to_person, location, notes }
  → validate via CustodyEventCreate Pydantic schema
  → custody_service.add_custody_event(current_user, custody_data)
  → INSERT into custody_events
  → log_event(CUSTODY_EVENT_CREATED)
```

### Custody Timeline

```
GET /custody/{evidence_id}
  → custody_service.list_custody_for_evidence(evidence_id)
  → SELECT * FROM custody_events WHERE evidence_id=? ORDER BY timestamp ASC
  → return chronological list

GET /custody/case/{case_id}
  → custody_service.list_custody_for_case(case_id)
  → JOIN with evidence table, order by timestamp ASC
```

### Frontend Display

The custody page (`custody/page.tsx`) renders a **vertical timeline** with:
- Action badge (HANDOFF / SECURE_STORAGE / RELEASED)
- From → To person
- Location
- Notes
- Timestamp

**[⬆ Back to TOC](#table-of-contents)**

---

## 11. Audit Logging Flow

### Audit Action Types (17+)

```
LOGIN_SUCCESS, LOGIN_FAILED, LOGOUT,
USER_CREATED, USER_UPDATED, USER_DISABLED, USER_ENABLED, PASSWORD_RESET,
CASE_CREATED, CASE_UPDATED, CASE_CLOSED, CASE_ARCHIVED, CASE_ASSIGNED,
EVIDENCE_REGISTERED, EVIDENCE_UPDATED, EVIDENCE_VERIFIED, EVIDENCE_HASH_COMPUTED,
CUSTODY_EVENT_CREATED,
ANALYSIS_NOTE_ADDED,
SYSTEM_CONFIG_UPDATED,
SESSION_CREATED, SESSION_EXPIRED
```

### Log Event

```python
def log_event(action: str, entity_type: str = None, entity_id: int = None,
              description: str = None, result: str = "SUCCESS",
              ip_address: str = None, user_agent: str = None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO audit_logs (timestamp, user_id, username, action,
                               entity_type, entity_id, description, result,
                               ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (now_iso, user_id, username, action, entity_type, entity_id,
          description, result, ip_address, user_agent))
    conn.commit()
```

### Audit Log Query

```
GET /audit-logs?user_id=&action=&start_date=&end_date=&limit=&offset=
  → audit_service.get_audit_logs(filters)
  → SELECT with WHERE clause
  → return AuditLogListResponse { logs: [...], total: int }
```

### Append-Only Guarantee

No UPDATE or DELETE operations on `audit_logs` table in any API route. The schema has no triggers enforcing this at the DB level — the guarantee is enforced by code convention only.

**[⬆ Back to TOC](#table-of-contents)**

---

## 12. Notes System

### Analysis Notes

```
POST /evidence/{evidence_id}/note { note_text }
  → INSERT into analysis_notes (evidence_id, case_id, note_text, created_by, created_at)
  → log_event(ANALYSIS_NOTE_ADDED)

GET /cases/{case_id}/notes  (via evidence endpoint)
  → SELECT * FROM analysis_notes WHERE case_id=? ORDER BY created_at DESC
```

### Note Data Model

```python
@dataclass(frozen=True)
class AnalysisNote:
    id: int
    evidence_id: int
    case_id: int
    note_text: str
    created_by: int  # user_id
    created_at: str  # ISO timestamp
```

### Access Control

Notes are accessible to any user with `ADD_NOTES` permission on the relevant case. No per-note access control.

**[⬆ Back to TOC](#table-of-contents)**

---

## 13. Reporting System

### Report Types

`summary`, `evidence`, `custody`, `audit`

### Generate Report

```
GET /reports/case/{case_id}?report_type=summary|evidence|custody|audit
  → reports.py assembles data from case_service, evidence_service, etc.
  → returns JSON with report data
  → Frontend provides JSON download
```

### Report Content by Type

| Type | Content |
|------|---------|
| `summary` | Case details + stats (evidence count, custody events, notes count) |
| `evidence` | Full evidence list for case with hashes and status |
| `custody` | Full custody timeline for case |
| `audit` | All audit log entries for case |

### Frontend Report Page

`reports/page.tsx` provides:
- Case selector dropdown
- Report type selector
- Generate button → fetches JSON → triggers browser download

**[⬆ Back to TOC](#table-of-contents)**

---

## 14. API Inventory

### Complete Endpoint List (38 endpoints)

#### Auth Router (`/auth`)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| POST | `/auth/login` | No | — | Login with username/password |
| POST | `/auth/logout` | Yes | — | Logout current session |
| GET | `/auth/me` | Yes | — | Get current user info |
| POST | `/auth/refresh` | Yes | — | Refresh session token |

#### Cases Router (`/cases`)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/cases` | Yes | VIEW_CASES | List cases (search, pagination) |
| POST | `/cases` | Yes | CREATE_CASES | Create new case |
| GET | `/cases/{case_id}` | Yes | VIEW_CASES | Get case details |
| PUT | `/cases/{case_id}` | Yes | EDIT_CASES | Update case |
| POST | `/cases/{case_id}/close` | Yes | CLOSE_CASES | Close case |
| POST | `/cases/{case_id}/archive` | Yes | ARCHIVE_CASES | Archive case |
| POST | `/cases/{case_id}/assign` | Yes | ASSIGN_CASE_USERS | Assign user to case |
| GET | `/cases/{case_id}/users` | Yes | VIEW_CASES | Get case users |
| GET | `/cases/{case_id}/evidence` | Yes | VIEW_CASES | Get case evidence |

#### Evidence Router (`/evidence`)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/evidence` | Yes | VIEW_EVIDENCE | List evidence |
| POST | `/evidence` | Yes | REGISTER_EVIDENCE | Register evidence |
| GET | `/evidence/{evidence_id}` | Yes | VIEW_EVIDENCE | Get evidence details |
| PUT | `/evidence/{evidence_id}` | Yes | EDIT_EVIDENCE | Update evidence |
| POST | `/evidence/{evidence_id}/verify` | Yes | VERIFY_EVIDENCE | Verify hashes |
| POST | `/evidence/{evidence_id}/hash` | Yes | VERIFY_EVIDENCE | Compute/recompute hashes |
| POST | `/evidence/{evidence_id}/note` | Yes | ADD_NOTES | Add analysis note |
| GET | `/evidence/{evidence_id}/custody` | Yes | VIEW_CUSTODY | Get custody timeline |
| GET | `/cases/{case_id}/notes` | Yes | VIEW_EVIDENCE | Get notes for case |

#### Custody Router (`/custody`)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/custody/{evidence_id}` | Yes | VIEW_CUSTODY | Get evidence custody |
| POST | `/custody` | Yes | CREATE_CUSTODY_EVENTS | Create custody event |
| GET | `/custody/case/{case_id}` | Yes | VIEW_CUSTODY | Get case custody |

#### Audit Router (`/audit-logs`)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/audit-logs` | Yes | VIEW_AUDIT | List audit logs (filterable) |
| GET | `/audit-logs/count` | Yes | VIEW_AUDIT | Get total audit log count |

#### Users Router (`/users`)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/users` | Yes | MANAGE_USERS | List users |
| POST | `/users` | Yes | MANAGE_USERS | Create user |
| GET | `/users/{user_id}` | Yes | MANAGE_USERS | Get user details |
| PUT | `/users/{user_id}` | Yes | MANAGE_USERS | Update user |
| POST | `/users/{user_id}/disable` | Yes | MANAGE_USERS | Disable user |
| POST | `/users/{user_id}/enable` | Yes | MANAGE_USERS | Enable user |
| POST | `/users/{user_id}/reset-password` | Yes | MANAGE_USERS | Reset password |

#### Reports Router (`/reports`)

| Method | Path | Auth | Permission | Description |
|--------|------|------|------------|-------------|
| GET | `/reports/case/{case_id}` | Yes | VIEW_REPORTS | Generate case report |

#### Public Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | No | API info |
| GET | `/health` | No | Health check |
| GET | `/dashboard/stats` | Optional | Dashboard statistics (public stats) |

### Future API Groups (V2 Planning)

| Group | Routes | Purpose |
|-------|--------|---------|
| `artifacts` | CRUD for forensic artifacts | Structured artifact management |
| `events` | CRUD for normalized events | Event management |
| `timeline` | Timeline query and construction | Timeline engine |
| `correlation` | Correlation operations | Evidence correlation |
| `graph` | Graph queries | Relationship graph |
| `iocs` | IOC CRUD and search | IOC management |
| `findings` | Findings CRUD | Explainable findings |
| `investigation` | Session management | Investigation sessions |
| `ai-query` | AI investigation queries | AI assistant |
| `replay` | Replay session control | Incident replay |

**[⬆ Back to TOC](#table-of-contents)**

---

## 15. Database Table Inventory

### Existing Tables

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `users` | User accounts | id, username, password_hash, is_active, must_change_password, created_at, last_login |
| `roles` | Role definitions | id, name, description |
| `permissions` | Permission definitions | id, name, description |
| `role_permissions` | Role→Permission mapping | role_id, permission_id |
| `user_roles` | User→Role mapping | user_id, role_id |
| `sessions` | Active sessions | id, token, user_id, created_at, expires_at, ip_address, user_agent |
| `system_settings` | Key-value config | key, value |
| `cases` | Investigative cases | id, case_number, title, description, status, priority, incident_date, created_by, created_at |
| `case_users` | Case→User assignments | case_id, user_id, assigned_at |
| `evidence` | Evidence items | id, evidence_id, case_id, file_path, evidence_type, description, status, notes, created_by, created_at, verified_at, hash_verified |
| `evidence_hashes` | Hash records | id, evidence_id, md5_hash, sha256_hash, computed_at, is_original |
| `custody_events` | Custody records | id, evidence_id, case_id, action, from_person, to_person, location, notes, created_by, timestamp |
| `analysis_notes` | Investigation notes | id, evidence_id, case_id, note_text, created_by, created_at |
| `audit_logs` | Audit trail | id, timestamp, user_id, username, action, entity_type, entity_id, description, result, ip_address, user_agent |

### Future Tables (V2 Planning)

| Table | Description | Key Relationships |
|-------|-------------|-------------------|
| `artifacts` | Structured forensic artifacts extracted from evidence | FK → evidence, FK → cases |
| `events` | Normalized temporal events derived from artifacts | FK → artifacts, FK → entities |
| `timeline_events` | Events ordered temporally within a case | FK → events, temporal index |
| `entities` | Identified actors/objects (users, IPs, files, processes) | Independent |
| `relationships` | Connections between entities | FK → entity (from), FK → entity (to) |
| `iocs` | Indicators of compromise | FK → evidence, FK → events |
| `findings` | Categorized conclusions | FK → cases, FK → evidence |
| `risk_scores` | Quantified risk assessments | FK → events/iocs/findings |
| `attack_techniques` | MITRE ATT&CK mappings | FK → iocs, technique_id |
| `investigation_sessions` | Active investigator inquiry contexts | FK → users, FK → cases |
| `ai_queries` | Logged AI assistant interactions | FK → investigation_session |
| `replay_sessions` | Incident replay states | FK → incident, FK → users |

**[⬆ Back to TOC](#table-of-contents)**

---

## 16. Frontend Page Inventory

| Page | File | Features | Auth Required |
|------|------|----------|----------------|
| **Login** | `login/page.tsx` | Username/password form, branding, feature list, default credentials notice | No |
| **Dashboard** | `dashboard/page.tsx` | 6 stat cards, recent cases list, recent activity feed | Yes |
| **Cases** | `cases/page.tsx` | Searchable case table, status/priority filters, create case dialog | Yes (VIEW_CASES) |
| **Evidence** | `evidence/page.tsx` | Evidence table, inline MD5/SHA-256 display with copy, register dialog | Yes (VIEW_EVIDENCE) |
| **Chain of Custody** | `custody/page.tsx` | Vertical timeline, record custody event dialog, action dropdown | Yes (VIEW_CUSTODY) |
| **Audit Log** | `audit/page.tsx` | Filterable log table (user, action, date range) | Yes (VIEW_AUDIT) |
| **Users** | `users/page.tsx` | User table with role badges, disable/enable buttons, create user dialog | Yes (MANAGE_USERS) |
| **Reports** | `reports/page.tsx` | Case selector, report type selector, JSON download button | Yes (VIEW_REPORTS) |

### UI Components (9 total in `components/ui/`)

| Component | File | Description |
|-----------|------|-------------|
| Button | `button.tsx` | 7 variants (default, destructive, outline, secondary, ghost, link, success), 3 sizes |
| Card | `card.tsx` | Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter |
| Dialog | `dialog.tsx` | Overlay-based modal dialog with Radix UI |
| Table | `table.tsx` | Table, TableHeader, TableBody, TableRow, TableHead, TableCell |
| Badge | `badge.tsx` | Status badge with variants |
| Input | `input.tsx` | Text input with border styling |
| Label | `label.tsx` | Form label |
| Select | `select.tsx` | Dropdown select with Radix UI |
| DropdownMenu | `dropdown-menu.tsx` | Dropdown with Radix UI (14 sub-components) |

### Layout Components (2 in `components/layout/`)

| Component | File | Description |
|-----------|------|-------------|
| Sidebar | `sidebar.tsx` | Navigation with permission gating, logo "DFEMS v1.0.0" |
| Topbar | `topbar.tsx` | Search bar, notification bell, user dropdown with role badges, logout |

**[⬆ Back to TOC](#table-of-contents)**

---

## 17. Important Components

### Backend Services

| Service | Location | Responsibility |
|---------|----------|----------------|
| `case_service` | `services/case_service.py` | Case CRUD, case number generation, user assignment |
| `evidence_service` | `services/evidence_service.py` | Evidence CRUD, evidence ID generation, note management |
| `custody_service` | `services/custody_service.py` | Custody event CRUD, count operations |
| `audit_service` | `services/audit_service.py` | Audit log insertion and querying |
| `hashing` | `services/hashing.py` | Streaming MD5+SHA-256, hash verification |

### Frontend Services

| Service | Location | Responsibility |
|---------|----------|----------------|
| `api` | `lib/api.ts` | Axios singleton with JWT interceptors |
| `auth` | `lib/auth.ts` | Standalone auth helpers (login, logout, permission checks) |
| `utils` | `lib/utils.ts` | `cn()`, date formatting, file size, hash truncation |

### Key Hooks

| Hook | Location | Responsibility |
|------|----------|----------------|
| `useAuth` | `hooks/useAuth.tsx` | React Context providing all auth state and methods |

### Key Utilities

| Utility | Location | Description |
|---------|----------|-------------|
| `formatDateTime()` | `lib/utils.ts` | Format ISO timestamp to readable string |
| `formatDate()` | `lib/utils.ts` | Format date only |
| `formatFileSize()` | `lib/utils.ts` | Format bytes to KB/MB/GB |
| `truncate()` | `lib/utils.ts` | Truncate text to max length |
| `truncateHash()` | `lib/utils.ts` | Truncate hash to first/last N chars |

**[⬆ Back to TOC](#table-of-contents)**

---

## 18. Reusable Services

### Backend Reusable Functions

| Function | Module | Reuse Target |
|---------|--------|--------------|
| `get_connection()` | `database/database.py` | All services |
| `transaction()` | `database/database.py` | All services |
| `verify_password()` | `auth/password_manager.py` | `authenticate_user` |
| `hash_password()` | `auth/password_manager.py` | `register_user`, `reset_password` |
| `create_access_token()` | `core/security.py` | `authenticate_user` |
| `verify_access_token()` | `core/dependencies.py` | `get_current_user` |
| `permissions_for_roles()` | `auth/authorization.py` | `has_permission`, service-layer checks |
| `has_permission()` | `auth/authorization.py` | `require_permission` dependency |
| `compute_hashes()` | `services/hashing.py` | `register_evidence`, `compute_and_store` |
| `verify_hashes()` | `services/hashing.py` | `verify_evidence` |
| `log_event()` | `services/audit_service.py` | All API routes |

### Frontend Reusable Functions

| Function | Location | Reuse Target |
|---------|----------|---------------|
| `login()` | `lib/auth.ts` | `useAuth.login()` |
| `logout()` | `lib/auth.ts` | `useAuth.logout()` |
| `getStoredUser()` | `lib/auth.ts` | `useAuth` init |
| `getStoredToken()` | `lib/auth.ts` | `api.ts` interceptor |
| `hasPermission()` | `lib/auth.ts` | `useAuth.hasPermission()` |
| `hasAnyPermission()` | `lib/auth.ts` | `useAuth.hasAnyPermission()` |
| `hasRole()` | `lib/auth.ts` | `useAuth.hasRole()` |
| `cn()` | `lib/utils.ts` | All UI components (Tailwind class merging) |
| `formatDateTime()` | `lib/utils.ts` | Dashboard, audit, custody pages |
| `getErrorMessage()` | `lib/api.ts` | All API error handling |

**[⬆ Back to TOC](#table-of-contents)**

---

## 19. Existing Tests

### test_basic.py (10 tests)

Custom `TestResult` class with `pass()` / `fail()` methods. No pytest framework used.

| Test | What It Covers |
|------|--------------|
| T1 `test_password_hashing` | Hash and verify same password, wrong password rejection |
| T2 `test_rbac_permissions` | ADMIN has all permissions, AUDITOR has read-only |
| T3 `test_user_registration` | Register, re-register rejection |
| T4 `test_user_authentication` | Correct creds → user object, wrong → None |
| T5 `test_hash_computation` | MD5 + SHA-256 of known test data |
| T6 `test_hash_verification` | Verify matching and mismatching hashes |
| T7 `test_case_creation` | Create case, retrieve by ID, case number format |
| T8 `test_evidence_registration` | Register evidence, verify hashes in DB |
| T9 `test_custody_events` | Add custody event, list by evidence |
| T10 `test_audit_logging` | Log event, retrieve logs, verify fields |

### test_integration_rbac.py

Uses **Tkinter** (GUI framework) to open the legacy `app.py` window and test role-based menu visibility. References `legacy/app.py` which may no longer exist after cleanup. Likely broken.

### test_ui_rbac.py

Frontend UI RBAC tests. Full coverage and functionality not verified.

### demo_flow.py

`run_demo()` function that creates:
1. Admin user
2. Demo case
3. Temporary evidence file
4. Custody events
5. Analysis note
6. Hash verification

Returns a summary dict. Used for manual demonstration.

### Test Coverage Assessment

- **Backend coverage:** Unit-level tests for core services exist but are not pytest-based
- **Frontend coverage:** Minimal UI tests, RBAC integration tests reference legacy code
- **API integration tests:** Not formally structured (test_basic.py has integration elements)
- **Coverage target (80%):** Not currently met — significant gaps in test coverage

**[⬆ Back to TOC](#table-of-contents)**

---

## 20. Dependencies

### Backend (requirements.txt)

```
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6
pydantic>=2.0.0
sqlalchemy>=2.0.0
pytest>=7.4.0
httpx>=0.25.0
structlog>=23.0.0
websockets>=12.0
asyncpg>=0.29.0
```

**Notes:**
- `sqlalchemy` listed but not used (raw `sqlite3` throughout)
- `asyncpg` listed but not used (PostgreSQL async driver, SQLite is sync)
- `websockets` listed but not used in current code
- `pytest` listed but `test_basic.py` uses custom TestResult class, not pytest

### Frontend (package.json)

```json
{
  "dependencies": {
    "next": "16.3.3",
    "react": "19.2.8",
    "react-dom": "19.2.8",
    "axios": "1.20.0",
    "@radix-ui/react-dialog": "^1.1.0",
    "@radix-ui/react-dropdown-menu": "^2.1.0",
    "@radix-ui/react-select": "^2.1.0",
    "@radix-ui/react-slot": "^1.1.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "lucide-react": "^0.400.0",
    "react-hook-form": "^7.51.0",
    "@hookform/resolvers": "^3.3.0",
    "zod": "^3.22.0",
    "tailwind-merge": "^2.3.0"
  }
}
```

**Note:** Next.js 16.3.3 and React 19.2.8 are **future versions** — not released as of August 2026 (current date). These versions do not exist yet. The actual available versions at the time of audit are likely Next.js ~14.x and React ~18.x.

**[⬆ Back to TOC](#table-of-contents)**

---

## 21. Security Controls

### Implemented Controls

| Control | Implementation | Quality |
|---------|---------------|---------|
| Password hashing | PBKDF2-HMAC-SHA256, 210,000 iterations, 16-byte salt | ✅ Strong |
| JWT tokens | HS256, 7-day expiry, per-session token | ✅ Adequate |
| Session tracking | DB-backed sessions with expiry | ✅ Good |
| SQL injection | Parameterized queries throughout | ✅ Good |
| Foreign keys | Enforced via `PRAGMA foreign_keys=ON` | ✅ Good |
| Input validation | Pydantic schemas on all endpoints | ✅ Good |
| RBAC | 21 permissions, 5 roles, service-layer checks | ✅ Good |
| Audit logging | Append-only log of all operations | ✅ Good |
| Auth middleware | FastAPI `Depends()` for all protected routes | ✅ Good |
| 401 handling | Frontend clears token + redirects to login | ✅ Good |

### Missing Controls

| Control | Risk | Priority |
|---------|------|----------|
| Rate limiting | Brute-force login attacks | HIGH |
| CSRF protection | Cross-site request forgery | HIGH |
| XSS sanitization | Stored XSS in notes/description fields | HIGH |
| File upload validation | Path traversal, file type, size limits | HIGH |
| JWT secret from env | Fallback to random secret is insecure | HIGH |
| CORS production config | Hardcoded localhost origins | MEDIUM |
| Session revocation | No explicit logout invalidation across sessions | MEDIUM |
| Password complexity | No policy enforcement | MEDIUM |
| Account lockout | No failed login lockout | MEDIUM |
| Audit log integrity | No cryptographic chaining or tamper detection | MEDIUM |
| HTTPS enforcement | No redirect from HTTP | MEDIUM |
| Secure cookie flags | `httpOnly`, `secure`, `sameSite` | MEDIUM |
| API versioning | No API version prefix for breaking changes | LOW |
| Request size limits | No max request body size | LOW |

**[⬆ Back to TOC](#table-of-contents)**

---

## 22. Technical Debt

### High Priority

1. **Dead code in `hashing.py`**: `compute_and_store()` references `datetime.datetime` imported at bottom of file — `import datetime` on line 171, but line 148 uses `datetime.datetime.now(...)` before the import. This function is also unused (imported only in `demo_flow.py`).

2. **Dead imports in `app.py`**: `WebSocket` imported but never used.

3. **Duplicate code directories**: `auth/`, `services/`, `database/`, `models/` exist both at project root AND inside `backend/`. Top-level copies may be legacy remnants. Their relationship to the backend imports needs clarification.

4. **Non-pytest test file**: `test_basic.py` uses a custom `TestResult` class instead of pytest assertions. The `pytest` dependency is listed but unused.

5. **Legacy Tkinter tests**: `test_integration_rbac.py` references `legacy/app.py` (Tkinter app) which may not exist.

### Medium Priority

6. **Unused dependencies**: `sqlalchemy`, `asyncpg`, `websockets` in requirements.txt but not used in code.

7. **No database migrations**: Schema applied directly on startup with no migration history. Adding columns/tables requires manual schema updates.

8. **No API versioning**: All endpoints at root (`/cases`, `/evidence`, etc.) with no version prefix.

9. **No request ID / correlation ID**: Requests not tagged with IDs for distributed tracing.

10. **No structured logging**: `structlog` in requirements but not used; uses `print()` in startup and `logging` not configured.

11. **Session cleanup on-demand only**: `cleanup_expired_sessions()` only runs during login. Sessions never cleaned up if no one logs in.

### Low Priority

12. **No API pagination metadata**: List endpoints return arrays without `total`, `page`, `limit` metadata in the envelope.

13. **No database connection pooling**: Each request opens/closes a new connection (SQLite limitation, but worth noting).

14. **Evidence file not copied**: Original file is referenced by path, not copied to a managed storage directory. No evidence repository.

15. **No backup strategy**: No DB backup, no evidence backup.

**[⬆ Back to TOC](#table-of-contents)**

---

## 23. Potential Bugs

### Confirmed Issues

1. **`hashing.py` import order bug**: `import datetime` on line 171, but `datetime.datetime.now(...)` used on line 148 inside `compute_and_store()`. This will raise `AttributeError` if `compute_and_store()` is ever called. The function itself is dead code but the bug exists in source.

2. **Default admin password in plaintext**: `Admin@123` appears in `RUN_ME.bat` comments, `backend/app.py` startup, and `README.md`. This credential is easily discoverable and must be changed in production.

3. **`test_integration_rbac.py` references missing file**: Tests import from `legacy.app` which references the Tkinter GUI app. This test file will fail on a clean system.

### Likely Issues

4. **Sidebar permission check race**: `sidebar.tsx` reads `user.permissions` from `localStorage` (via `getStoredUser()`). If the user's permissions change server-side, the sidebar nav won't update until manual refresh/re-login.

5. **Dashboard stats public endpoint bypasses auth check**: `/dashboard/stats` uses `get_optional_user` — no auth required. While the data is aggregate stats (not sensitive), this endpoint still requires no authentication.

6. **No evidence file existence check**: `hashing.py`'s `compute_hashes()` uses `p.is_file()` check, but `evidence_service.register_evidence()` doesn't verify the file exists before inserting the record.

7. **Case search SQL LIKE injection risk**: `case_service.search_cases()` uses f-string SQL: `f"%{search}%"`. This is inside a parameterized query's LIKE clause (`LIKE ?`, parameterized), so it's actually safe — but the pattern is risky and easy to get wrong if modified.

8. **Multiple role assignment without duplicate check**: `assign_user_to_case()` inserts into `case_users` without checking if the assignment already exists. Duplicate entries possible.

9. **`is_fresh_database()` race condition**: `is_fresh_database()` checks if `roles` table is empty. Between the check and the seed, another startup could also seed. The DB is locked by SQLite so this is fine for single-process, but incorrect for multi-process scenarios.

10. **Evidence ID generation not atomic**: `_generate_evidence_id()` counts existing evidence for the case and increments — not atomic. Could produce duplicate IDs under concurrency.

**[⬆ Back to TOC](#table-of-contents)**

---

## 24. Missing Validation

### Input Validation Gaps

| Field | Where | Gap |
|-------|-------|-----|
| `file_path` | `POST /evidence` | No path traversal check, no existence check, no type validation |
| `evidence_type` | `POST /evidence` | Validated as enum but not against allowed types list |
| `case_id` | `POST /evidence` | No explicit check that case exists and is accessible to user |
| `user_id` | `POST /cases/{id}/assign` | No check that user is active before assignment |
| `username` | `POST /users` | No length limit, no character restriction |
| `password` | `POST /users` | No complexity requirements (length, character classes) |
| `description` | `POST /cases` | No length limit, potential stored XSS |
| `notes` | `POST /evidence` | No length limit, potential stored XSS |
| `note_text` | `POST /evidence/{id}/note` | No length limit, potential stored XSS |
| `location` | `POST /custody` | No length/type validation |
| Request body size | All POST endpoints | No max body size limit |

### Business Logic Validation Gaps

- **Cannot close/Archive an already-closed case**: No check (would silently succeed)
- **Cannot archive an open case**: No check
- **Evidence for closed case**: No check that case is still open before registering evidence
- **Delete evidence**: No check for existing custody events
- **Duplicate evidence file_path**: No uniqueness check

**[⬆ Back to TOC](#table-of-contents)**

---

## 25. Code Duplication

### Major Duplications

1. **`auth/` and `backend/auth/`**: Complete duplication of `authentication.py`, `authorization.py`, `password_manager.py`. The `backend/` versions are imported by `backend/app.py`. The top-level versions are standalone. Their relationship is unclear — likely legacy remnants.

2. **`services/` and `backend/services/`**: Same duplication pattern. Top-level `services/` contains copies of all service files.

3. **`database/` and `backend/database/`**: Same pattern. `database/database.py` and `database/schema.sql` exist in both locations.

4. **`models/` and `backend/models/`**: Same pattern. `models/models.py` exists in both locations.

### Minor Duplications

5. **`lib/auth.ts` vs `hooks/useAuth.tsx`**: Both implement `hasPermission()`, `hasAnyPermission()`, `hasRole()`. `lib/auth.ts` is standalone, `useAuth.tsx` wraps it in Context. The standalone version is redundant.

6. **Pydantic schemas vs TypeScript types**: `backend/schemas/*.py` and `frontend/src/types/index.ts` define the same data structures independently. No shared type definition (e.g., no OpenAPI-generated TS types).

7. **`api.ts` error handling vs `getErrorMessage()`**: Error message extraction duplicated across axios interceptors and a helper function.

8. **Role permission definitions**: `authorization.py` has `DEFAULT_ROLE_PERMISSIONS` dict and `PERMISSIONS_ALL` tuple. Frontend `useAuth.tsx` receives these from the API as part of `user.permissions`. These are two separate sources of truth for role permissions.

**[⬆ Back to TOC](#table-of-contents)**

---

## 26. Hard-coded Values

### Security-Critical

| Value | Location | Issue |
|-------|----------|-------|
| `Admin@123` | `backend/app.py:50`, `RUN_ME.bat:77` | Default admin password in plaintext |
| `admin` | `backend/app.py:50` | Default admin username |
| `secrets.token_urlsafe(32)` | `backend/core/security.py:13` | JWT secret fallback uses random value — sessions invalidated on restart |

### Configuration

| Value | Location | Issue |
|-------|----------|-------|
| `http://localhost:3000` | `frontend/src/lib/api.ts:8` | Hardcoded API URL |
| `http://localhost:8000` | `frontend/src/lib/api.ts:8` | Hardcoded API URL |
| `3 localhost origins` | `backend/app.py:26` | Hardcoded CORS origins |
| `8000` | `backend/main.py:10` | Hardcoded port |
| `3000` | `RUN_ME.bat:74` | Hardcoded frontend URL |

### Business Logic

| Value | Location | Issue |
|-------|----------|-------|
| `210_000` | `backend/auth/password_manager.py:12` | PBKDF2 iterations (hardcoded, no config) |
| `16` | `backend/auth/password_manager.py:11` | Salt bytes (hardcoded, no config) |
| `32` | `backend/auth/password_manager.py:13` | DK length (hardcoded, no config) |
| `64 * 1024` | `backend/services/hashing.py:19` | Chunk size for hash computation |
| `60 * 24 * 7` | `backend/core/security.py:15` | 7-day JWT expiry (hardcoded, no config) |
| `10000` | `backend/app.py:78-79` | Dashboard stats limit (magic number) |

### UI

| Value | Location | Issue |
|-------|----------|-------|
| `DFEMS v1.0.0` | `frontend/src/components/layout/sidebar.tsx` | Hardcoded app name + version |
| `CASE-{YYYY}-{NNNN}` | `backend/services/case_service.py` | Case number format hardcoded |
| `EV-<case>-<NNNN>` | `backend/services/evidence_service.py` | Evidence ID format hardcoded |
| `8` | `dashboard/page.tsx:95` | Recent logs limit (magic number) |
| `5` | `dashboard/page.tsx:96` | Recent cases limit (magic number) |

**[⬆ Back to TOC](#table-of-contents)**

---

## 27. Configuration Problems

### Environment Variables

Only one environment variable is read:

```python
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))
```

All other configuration is hardcoded. No `.env` file support, no config module.

### Missing Configuration

| Configuration | Should Be | Currently |
|--------------|-----------|-----------|
| Database path | `DB_PATH` env var | Hardcoded `data/forensics_framework.db` |
| JWT secret | `JWT_SECRET_KEY` env var | Falls back to random (invalidates sessions) |
| CORS origins | `CORS_ORIGINS` env var | Hardcoded 3 localhost origins |
| PBKDF2 iterations | `PASSWORD_HASH_ITERATIONS` env var | Hardcoded 210,000 |
| Session expiry | `SESSION_EXPIRY_DAYS` env var | Hardcoded 7 days |
| Evidence storage | `EVIDENCE_STORAGE_PATH` env var | Not managed — uses raw file paths |
| Log level | `LOG_LEVEL` env var | Not configured |
| API URL | `NEXT_PUBLIC_API_URL` env var | Only used in frontend, with fallback |
| Port | `PORT` env var | Hardcoded in `main.py` |

### Configuration File

No `config.py`, no `settings.py`, no `.env.example`. All configuration is scattered across source files.

**[⬆ Back to TOC](#table-of-contents)**

---

## 28. Scalability Concerns

### Database

- **SQLite single-writer**: WAL mode allows concurrent reads, but only one write at a time. Write-heavy workloads (many concurrent evidence registrations, custody events) will serialize.
- **No connection pooling**: Each request opens a new connection. Under high concurrency, this adds overhead.
- **No read replicas**: All reads hit the primary. No query separation.
- **No caching**: Dashboard stats re-query the DB on every `/dashboard/stats` call.
- **No pagination on large tables**: Audit logs, evidence lists, and case lists load all matching rows into memory (though a `limit` param exists, there's no cursor-based pagination).

### Backend

- **No background workers**: Hash computation is synchronous. Large file hashing blocks the request.
- **No task queue**: Evidence verification, hash computation, and report generation are all synchronous.
- **No caching layer**: No Redis, no in-memory cache. Every request hits SQLite.
- **No API rate limiting**: Endpoints can be hammered.
- **No request queuing**: Spike traffic can overwhelm the single uvicorn worker.

### Frontend

- **No virtualized lists**: Evidence table renders all rows. Large datasets will cause DOM bloat.
- **No optimistic updates**: Form submissions wait for server response.
- **No request deduplication**: Parallel requests for the same data aren't deduplicated.
- **No offline support**: No Service Worker, no offline indicators.

### Evidence Storage

- **Original files not copied**: Evidence is referenced by path. If the original file is moved/deleted, the record becomes orphaned.
- **No evidence repository**: No managed storage directory. Evidence can be anywhere on the filesystem.
- **No file deduplication**: Same file registered twice as different evidence items.

**[⬆ Back to TOC](#table-of-contents)**

---

## 29. Security Concerns

### Critical

1. **Default admin credentials in plaintext**: `admin / Admin@123` appear in source code (`app.py:50`), batch script (`RUN_ME.bat:77`), and documentation. Anyone with repo access can log in.

2. **JWT secret fallback to random**: `secrets.token_urlsafe(32)` generates a new secret on every backend start if `JWT_SECRET_KEY` is not set. All JWTs become invalid on restart, logging everyone out. In multi-instance deployments, each instance has a different secret.

3. **No rate limiting**: `/auth/login` has no brute-force protection. An attacker can try unlimited passwords against any account.

4. **No CSRF protection**: No CSRF tokens. The JWT-based auth is vulnerable to CSRF attacks via `Authorization` header. The frontend doesn't use `sameSite` cookies.

### High

5. **Stored XSS in notes/description**: `note_text`, `description`, `notes` fields accept any string. No HTML sanitization before storage or rendering. Any user with `ADD_NOTES` can inject scripts.

6. **File path validation missing**: `POST /evidence` accepts a `file_path` without validating:
   - Path traversal attacks (`../../etc/passwd`)
   - File existence
   - File accessibility
   - File type/size

7. **No password complexity policy**: Any password accepted during user creation. Empty passwords, single-character passwords, common passwords all accepted.

8. **No account lockout**: Failed login attempts are logged but never trigger lockout. No `failed_login_attempts` counter, no `locked_until` field.

9. **No HTTPS enforcement**: Backend binds to `0.0.0.0` with no TLS. Credentials transmitted in plaintext over HTTP.

### Medium

10. **CORS allows localhost:5173**: Vite's default port in CORS whitelist. Any Vite dev server on that port can make authenticated requests.

11. **JWT stored in `localStorage`**: Vulnerable to XSS attacks. `httpOnly` cookies would be safer. Note: `localStorage` is the current approach throughout the codebase.

12. **No audit log integrity protection**: Audit logs can be deleted by ADMIN (permission `DELETE_AUDIT_LOGS`). No cryptographic chaining, no external log shipping.

13. **No secure cookie flags**: Even if switching to cookies, `httpOnly`, `secure`, and `sameSite` flags are not configured.

14. **No input sanitization for SQL**: While parameterized queries are used (good), the search endpoint uses f-string inside a parameterized query — this is currently safe but the pattern is error-prone for future changes.

15. **Evidence not copied to managed storage**: Original files are referenced directly. No evidence repository means the system can't guarantee file integrity or provide backup.

16. **No request body size limit**: Large POST bodies could cause memory exhaustion.

**[⬆ Back to TOC](#table-of-contents)**

---

## 30. V2 Extension Opportunities

### High-Value Additions

1. **Forensic Artifact Extraction Engine**
   - Parse evidence files (log files, memory dumps, disk images) into structured artifacts
   - Plugin architecture for parser types
   - Artifact-to-evidence traceability

2. **Event Normalization Pipeline**
   - Normalize timestamps across timezones
   - Standardize entity types (IP, username, file, process)
   - Normalized event schema with source attribution

3. **Timeline Engine**
   - Chronological ordering of normalized events
   - Temporal gap detection
   - Interactive timeline visualization (zoom, filter, annotate)

4. **Evidence Correlation Engine**
   - Rule-based correlation (IP → user, file → process)
   - Temporal correlation (events within time windows)
   - Cross-evidence correlation

5. **Evidence Relationship Graph**
   - Graph database or adjacency list in SQLite
   - Entity identification (IP, user, file, process)
   - Interactive graph visualization

### Medium-Value Additions

6. **IOC Detection & Analysis**
   - Pattern-based IOC extraction (IPs, domains, hashes, URLs)
   - IOC categorization and severity rating
   - IOC → evidence linking

7. **Risk Scoring Engine**
   - Multi-factor risk scoring (severity × confidence × asset criticality)
   - Risk score rationale tracking
   - Risk score history

8. **MITRE ATT&CK Mapping**
   - Map detected behaviors to ATT&CK tactics/techniques
   - Technique coverage visualization
   - Evidence citations per technique

9. **Incident Reconstruction Engine**
   - Synthesize correlated events into narrative
   - Step-by-step reconstruction display
   - Reconstruction versioning

10. **Explainable Findings Engine**
    - FACT / INFERENCE / HYPOTHESIS / UNKNOWN categorization
    - Evidence citation per finding
    - Confidence score with methodology

11. **AI Investigation Assistant**
    - Natural language queries against case evidence
    - Evidence-grounded answers with citations
    - Prompt injection resistance

12. **Incident Replay**
    - Visual step-through of timeline events
    - Play/pause/step controls
    - Speed control and timeline scrubbing

### Lower-Value (Foundation-First)

13. **Evidence Repository**
    - Managed storage directory
    - File copying on registration (not referencing original)
    - Deduplication

14. **Professional Report Generation**
    - PDF export with templates
    - Court-ready formatting
    - Finding summaries with evidence citations

15. **Enhanced Audit Log**
    - Cryptographic chaining (hash chain)
    - External log shipping (SIEM integration)
    - Anomaly detection

16. **Investigation Sessions**
    - Named workspaces within a case
    - Session state persistence
    - Multi-investigator collaboration

17. **Evidence Classification & Tagging**
    - Classification levels (public, confidential, secret)
    - Evidence tagging
    - Bulk import

**[⬆ Back to TOC](#table-of-contents)**

---

## 31. Component Classification

### KEEP (Production-Ready, No Changes Needed)

| Component | Location | Reason |
|-----------|----------|--------|
| `password_manager.py` | `backend/auth/` | Solid PBKDF2 implementation, well-documented |
| `authorization.py` | `backend/auth/` | Clean permission system, 21 granular permissions |
| `hashing.py` core functions | `backend/services/` | Excellent streaming design, 64KB chunks, frozen dataclasses |
| `authenticate_user()` | `backend/auth/authentication.py` | Comprehensive login flow with session management |
| `useAuth.tsx` | `frontend/src/hooks/` | Clean React Context implementation |
| `api.ts` | `frontend/src/lib/` | Good axios setup with interceptors |
| `utils.ts` | `frontend/src/lib/` | Useful utilities, clean `cn()` implementation |
| `button.tsx` | `frontend/src/components/ui/` | Well-structured with all variants |
| `card.tsx` | `frontend/src/components/ui/` | Clean card component |
| `RUN_ME.bat` | root | Good 5-step startup flow |
| `schema.sql` | `backend/database/` | Well-structured with proper indexes and FK constraints |

### MODIFY (Needs Changes Before Production)

| Component | Location | Changes Needed |
|-----------|----------|----------------|
| `app.py` | `backend/` | Remove hardcoded admin credentials; use env var |
| `security.py` | `backend/core/` | Fail startup if `JWT_SECRET_KEY` not set (no fallback) |
| `api.ts` | `frontend/src/lib/` | Add `sameSite: 'strict'` if switching to cookies; add request timeout |
| `dashboard/page.tsx` | `frontend/src/app/` | Replace magic numbers (8, 5) with named constants |
| `sidebar.tsx` | `frontend/src/components/layout/` | Replace hardcoded "DFEMS v1.0.0" with config |
| `custody/page.tsx` | `frontend/src/app/` | Add file type/length validation for notes |
| `cases/page.tsx` | `frontend/src/app/` | Add length validation for description |
| `evidence/page.tsx` | `frontend/src/app/` | Add length validation for notes |
| `audit/page.tsx` | `frontend/src/app/` | Add length validation for search inputs |

### EXTEND (Good Base, Add Features)

| Component | Location | Extension Plan |
|-----------|----------|----------------|
| `case_service.py` | `backend/services/` | Add case templates, case tagging, case relationships |
| `evidence_service.py` | `backend/services/` | Add evidence classification, tagging, bulk import |
| `reports.py` | `backend/api/` | Extend to PDF generation, report templates |
| `dashboard/page.tsx` | `frontend/src/app/` | Add intelligence widgets, recent timeline preview |
| `audit/page.tsx` | `frontend/src/app/` | Add timeline visualization, anomaly highlighting |
| `custody/page.tsx` | `frontend/src/app/` | Add visual custody chain diagram |

### REFACTOR LATER (Known Issues)

| Component | Location | Refactoring Needed |
|-----------|----------|--------------------|
| `hashing.py` | `backend/services/` | Move `import datetime` to top; remove `compute_and_store()` or fix it |
| `app.py` | `backend/` | Remove unused `WebSocket` import; remove unused deps from requirements.txt |
| `test_basic.py` | `tests/` | Convert to pytest framework; add fixtures |
| Top-level `auth/` | root | Delete duplicate; migrate any unique code to `backend/auth/` |
| Top-level `services/` | root | Delete duplicates |
| Top-level `database/` | root | Delete duplicates |
| Top-level `models/` | root | Delete duplicates |
| `lib/auth.ts` | `frontend/src/lib/` | Merge redundant permission functions into `useAuth.tsx` |

### DEPRECATE (Remove)

| Component | Location | Reason |
|-----------|----------|--------|
| `compute_and_store()` | `backend/services/hashing.py` | Dead code; has import bug |
| `test_integration_rbac.py` | `tests/` | References missing `legacy/app.py` (Tkinter app) |
| `asyncpg` | `backend/requirements.txt` | Not used; PostgreSQL not the DB |
| `websockets` | `backend/requirements.txt` | Not used |
| `sqlalchemy` | `backend/requirements.txt` | Not used; raw sqlite3 in use |
| Tkinter legacy app | `legacy/` (if exists) | Deprecated; replaced by web app |

### REPLACE (Significant Rework Needed)

| Component | Location | Replacement Strategy |
|-----------|----------|---------------------|
| `test_basic.py` | `tests/` | Replace with pytest-based test suite with fixtures and proper assertions |
| `test_ui_rbac.py` | `tests/` | Replace with Playwright E2E tests for RBAC flows |
| Login page | `frontend/src/app/login/` | Add MFA support, password complexity enforcement, rate limiting feedback |
| Report generation | `backend/api/reports.py` | Replace JSON output with PDF/HTML report generation |
| Evidence registration | `backend/api/evidence.py` | Replace raw file_path with managed file upload + storage |

**[⬆ Back to TOC](#table-of-contents)**

---

## 32. CyberTrace Nexus V2 Change Map

### Architecture Transformation

```
CURRENT (DFEMS v1.0.0)          →  FUTURE (CyberTrace Nexus)
─────────────────────────────────────────────────────────────────
Monolithic FastAPI + Next.js     →  Modular FastAPI + Next.js
SQLite (13 tables)               →  SQLite + New Tables (see below)
Manual RBAC                      →  RBAC + Attribute-Based (future)
JSON reports                     →  PDF reports + Evidence-grounded reports
Single-case evidence             →  Multi-evidence correlation
Manual evidence tracking         →  Artifact → Event → Timeline pipeline
Evidence as files                →  Evidence as evidence (file + extracted data)
Static dashboards                →  Intelligence-augmented dashboards
```

### New Database Tables (V2)

| # | Table | Purpose | Priority |
|---|-------|---------|----------|
| 1 | `artifacts` | Structured forensic artifacts from evidence | P1 |
| 2 | `events` | Normalized temporal events from artifacts | P1 |
| 3 | `timeline_events` | Events ordered within case timeline | P1 |
| 4 | `entities` | Identified actors/objects (user, IP, file, process) | P1 |
| 5 | `relationships` | Entity-to-entity connections | P2 |
| 6 | `iocs` | Indicators of compromise | P2 |
| 7 | `findings` | Categorized conclusions (FACT/INFERENCE/HYPOTHESIS) | P2 |
| 8 | `risk_scores` | Quantified risk assessments | P2 |
| 9 | `attack_techniques` | MITRE ATT&CK technique mappings | P2 |
| 10 | `investigation_sessions` | Investigator workspace sessions | P3 |
| 11 | `ai_queries` | AI assistant interaction log | P3 |
| 12 | `replay_sessions` | Incident replay state | P3 |

### New Backend API Routes (V2)

| # | Route | Purpose | Priority |
|---|-------|---------|----------|
| 1 | `POST /artifacts` | Extract artifact from evidence | P1 |
| 2 | `GET /artifacts/case/{id}` | List artifacts for case | P1 |
| 3 | `POST /events` | Create normalized event | P1 |
| 4 | `GET /events/case/{id}` | List events for case | P1 |
| 5 | `GET /timeline/case/{id}` | Get ordered timeline | P1 |
| 6 | `GET /entities/case/{id}` | List entities for case | P1 |
| 7 | `POST /correlation` | Run correlation on case | P1 |
| 8 | `GET /correlation/{case_id}` | Get correlation results | P1 |
| 9 | `GET /graph/case/{id}` | Get relationship graph | P2 |
| 10 | `POST /iocs/scan` | Scan case for IOCs | P2 |
| 11 | `GET /iocs/case/{id}` | List IOCs for case | P2 |
| 12 | `POST /risk-score/case/{id}` | Calculate risk scores | P2 |
| 13 | `GET /attack-techniques/case/{id}` | Get ATT&CK mappings | P2 |
| 14 | `POST /findings` | Create finding | P2 |
| 15 | `GET /findings/case/{id}` | List findings | P2 |
| 16 | `POST /investigation/sessions` | Create session | P3 |
| 17 | `POST /investigation/{id}/query` | AI query | P3 |
| 18 | `GET /replay/{incident_id}` | Get replay state | P3 |
| 19 | `POST /reports/generate` | Generate PDF report | P3 |

### New Frontend Pages (V2)

| # | Page | Purpose | Priority |
|---|------|---------|----------|
| 1 | `/cases/{id}/artifacts` | Artifact analysis view | P1 |
| 2 | `/cases/{id}/timeline` | Interactive timeline | P1 |
| 3 | `/cases/{id}/graph` | Entity relationship graph | P2 |
| 4 | `/cases/{id}/iocs` | IOC list and details | P2 |
| 5 | `/cases/{id}/findings` | Findings management | P2 |
| 6 | `/cases/{id}/risk` | Risk score dashboard | P2 |
| 7 | `/cases/{id}/attack` | ATT&CK technique mapping | P2 |
| 8 | `/cases/{id}/investigate` | AI investigation assistant | P3 |
| 9 | `/cases/{id}/replay` | Incident replay interface | P3 |
| 10 | `/dashboard` (enhanced) | Intelligence summary widgets | P1 |

### Migration Path

```
Phase 0 (COMPLETE): Repository audit — this document
Phase 1: Stabilize — Fix critical bugs, remove dead code, add tests
Phase 2: Intelligence foundation — Evidence tagging, classification
Phase 3: Artifact extraction — Parse evidence into structured data
Phase 4: Event normalization — Standardize events with timestamps/entities
Phase 5: Timeline engine — Chronological event display
Phase 6: Correlation engine — Link events, entities, evidence
Phase 7: Evidence graph — Relationship visualization
Phase 8: IOC & risk intelligence — Detection and scoring
Phase 9: Incident reconstruction — Narrative synthesis
Phase 10: Explainable findings — FACT/INFERENCE/HYPOTHESIS
Phase 11: AI investigation assistant — Evidence-grounded AI
Phase 12: Incident replay — Visual step-through
Phase 13: Advanced reporting — PDF generation
Phase 14: Security hardening — Rate limiting, MFA, audit integrity
Phase 15: Testing & documentation — 80%+ coverage
```

### Preserved Components (No Changes)

These existing components are **production-ready** and should be preserved without modification through all V2 phases:

- Password hashing (PBKDF2, 210k iterations) — remains the standard
- Authorization engine (21 permissions, 5 roles) — foundation of RBAC
- Session management (JWT + DB sessions) — core auth mechanism
- Chain of custody model — forensic integrity requirement
- Audit logging schema and API — legal compliance requirement
- Case management core — investigative container model
- Evidence registration core — foundation of the evidence vault
- Hash verification (streaming, non-destructive) — forensic integrity requirement
- UI component library — shadcn-style primitives

**[⬆ Back to TOC](#table-of-contents)**

---

*End of Phase 0 Technical Audit — Digital Forensics Evidence Management System*
