# CyberTrace Nexus — API Inventory

**Generated:** 2026-09-04
**Phase:** 1B — API Stabilization
**Backend:** FastAPI + SQLite

---

## Overview

The CyberTrace Nexus API exposes endpoints for forensic case management,
evidence handling, chain of custody, audit logging, user administration, and
report generation. All endpoints (except `/`, `/health`, and `/auth/login`)
require a valid JWT bearer token.

### Conventions

- **Base URL:** `http://localhost:8000`
- **Content-Type:** `application/json`
- **Authentication:** `Authorization: Bearer <jwt>` (except login + health)
- **Date format:** ISO 8601 (UTC, `Z` suffix)
- **Pagination:** `limit` (1–500) and `offset` (≥0) query params

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Successful read or update |
| 201 | Resource successfully created |
| 204 | Successful operation, no response body |
| 400 | Malformed or invalid request body |
| 401 | Missing or invalid authentication |
| 403 | Authenticated but not authorized |
| 404 | Resource not found |
| 409 | Conflict (duplicate, etc.) |
| 422 | Pydantic / request validation failure |
| 500 | Unexpected server error |

---

## Router: `/auth` — Authentication

| Method | Path | Auth | Permission | Request | Response | Status |
|--------|------|------|-----------|---------|----------|--------|
| POST | `/auth/login` | None | — | `LoginRequest` | `LoginResponse` | 200, 401, 422 |
| POST | `/auth/logout` | Bearer | authenticated | — | `{message}` | 200, 401 |
| GET | `/auth/me` | Bearer | authenticated | — | `UserResponse` | 200, 401 |
| POST | `/auth/refresh` | Bearer | authenticated | — | `RefreshTokenResponse` | 200, 401 |

### Schemas

- `LoginRequest`: `{username: str, password: str}` (password min 8)
- `LoginResponse`: `{access_token, token_type, user: UserResponse}`
- `UserResponse`: `{id, username, role_names[], permissions[], is_active, created_at, last_login, must_change_password}`
- `RefreshTokenResponse`: `{access_token, token_type}`

---

## Router: `/cases` — Case Management

| Method | Path | Auth | Permission | Request | Response | Status |
|--------|------|------|-----------|---------|----------|--------|
| GET | `/cases` | Bearer | `case.view` | query: `status, priority, search, limit, offset` | `Case[]` | 200, 401, 403 |
| POST | `/cases` | Bearer | `case.create` | `CaseCreate` | `Case` | 201, 400, 401, 403 |
| GET | `/cases/{case_id}` | Bearer | `case.view` | path: `case_id` | `Case` | 200, 401, 403, 404 |
| PUT | `/cases/{case_id}` | Bearer | `case.update` | `CaseUpdate` | `Case` | 200, 400, 401, 403, 404 |
| POST | `/cases/{case_id}/close` | Bearer | `case.close` | — | `Case` | 200, 400, 401, 403, 404 |
| POST | `/cases/{case_id}/archive` | Bearer | `case.close` | — | `Case` | 200, 400, 401, 403, 404 |
| POST | `/cases/{case_id}/assign` | Bearer | `case.assign` | query: `user_id, role_note` | `{message}` | 200, 400, 401, 403, 404 |
| GET | `/cases/{case_id}/users` | Bearer | `case.view` | path: `case_id` | `{id, username, role_note, assigned_at}[]` | 200, 401, 403 |
| GET | `/cases/{case_id}/evidence` | Bearer | `evidence.view` | path: `case_id` | `Evidence[]` | 200, 401, 403, 404 |

### Schemas

- `CaseCreate`: `{title, incident_date?, priority?, description?}` (title min 1)
- `CaseUpdate`: partial `{title?, incident_date?, status?, priority?, description?}`
- `Case`: `{id, case_number, title, incident_date, status, priority, description, created_by, created_at, closed_at?, archived_at?}`

### Status values

`Open` | `Under Investigation` | `Suspended` | `Closed` | `Archived`

### Priority values

`Low` | `Medium` | `High` | `Critical`

---

## Router: `/evidence` — Evidence Management

| Method | Path | Auth | Permission | Request | Response | Status |
|--------|------|------|-----------|---------|----------|--------|
| GET | `/evidence` | Bearer | `evidence.view` | query: `limit` | `Evidence[]` | 200, 401, 403 |
| POST | `/evidence` | Bearer | `evidence.create` | `EvidenceCreate` | `Evidence` | 201, 400, 401, 403, 404, 500 |
| GET | `/evidence/{evidence_id}` | Bearer | `evidence.view` | path: `evidence_id` | `Evidence` | 200, 401, 403, 404 |
| PUT | `/evidence/{evidence_id}` | Bearer | `evidence.update` | `EvidenceUpdate` | `Evidence` | 200, 400, 401, 403, 404 |
| POST | `/evidence/{evidence_id}/verify` | Bearer | `evidence.verify` | path: `evidence_id` | `HashVerifyResult` | 200, 400, 401, 403, 404, 500 |
| POST | `/evidence/{evidence_id}/hash` | Bearer | `evidence.hash` | path: `evidence_id` | `{md5, sha256, status}` | 200, 401, 403, 404, 500 |
| POST | `/evidence/{evidence_id}/note` | Bearer | `analysis.create` | query: `content, note_type` | `{id, message}` | 200, 400, 401, 403, 404 |
| GET | `/evidence/{evidence_id}/notes` | Bearer | `analysis.view` | path: `evidence_id` | `Note[]` | 200, 401, 403, 404 |
| GET | `/evidence/{evidence_id}/custody` | Bearer | `custody.view` | path: `evidence_id` | `CustodyEvent[]` | 200, 401, 403, 404 |

### Schemas

- `EvidenceCreate`: `{case_id, file_path, evidence_type?, description?, source?}`
- `EvidenceUpdate`: partial `{evidence_type?, description?, source?, status?}`
- `Evidence`: `{id, evidence_id, case_id, evidence_type, description, source, file_path, file_size, file_extension, acquisition_time, original_modified_time, registered_by, status, created_at, md5?, sha256?}`
- `HashVerifyResult`: `{md5_match, sha256_match, stored_md5, stored_sha256, current_md5, current_sha256, status}`

### Evidence type values

`Document` | `Image` | `Video` | `Audio` | `Binary` | `Database` | `Other`

### Evidence status values

`Active` | `Seized` | `Released` | `Destroyed`

---

## Router: `/custody` — Chain of Custody

| Method | Path | Auth | Permission | Request | Response | Status |
|--------|------|------|-----------|---------|----------|--------|
| GET | `/custody/{evidence_id}` | Bearer | `custody.view` | path: `evidence_id` | `CustodyEvent[]` | 200, 401, 403 |
| POST | `/custody` | Bearer | `custody.create` | `CustodyEventCreate` | `CustodyEvent` | 201, 400, 401, 403, 404 |
| GET | `/custody/case/{case_id}` | Bearer | `custody.view` | path: `case_id` | `CustodyEvent[]` | 200, 401, 403 |

### Schemas

- `CustodyEventCreate`: `{evidence_id, action, from_person?, to_person?, location?, notes?, case_id?}`
- `CustodyEvent`: `{id, evidence_id, case_id, action, from_person?, to_person?, location?, event_time, notes?, recorded_by, recorded_by_name?, created_at?}`

### Action values

`REGISTERED` | `TRANSFERRED` | `RECEIVED` | `EXAMINED` | `STORED` | `RELEASED` | `RETURNED` | `CORRECTED`

---

## Router: `/audit-logs` — Audit Trail

| Method | Path | Auth | Permission | Request | Response | Status |
|--------|------|------|-----------|---------|----------|--------|
| GET | `/audit-logs` | Bearer | `audit.view` | query: `limit, user, action, entity_type, result, date_from, date_to, case_id` | `AuditLog[]` | 200, 401, 403, 500 |
| GET | `/audit-logs/count` | Bearer | `audit.view` | — | `{total}` | 200, 401, 403 |

### Schemas

- `AuditLog`: `{id, timestamp, action, username?, role_name?, entity_type?, entity_id?, case_id?, description?, result}`

---

## Router: `/users` — User Administration

| Method | Path | Auth | Permission | Request | Response | Status |
|--------|------|------|-----------|---------|----------|--------|
| GET | `/users` | Bearer | `user.view` | query: `limit` | `User[]` | 200, 401, 403 |
| POST | `/users` | Bearer | `user.create` | `UserCreate` | `{message, user_id}` | 201, 400, 401, 403, 500 |
| GET | `/users/{user_id}` | Bearer | `user.view` | path: `user_id` | `User` | 200, 401, 403, 404 |
| PUT | `/users/{user_id}` | Bearer | `user.update` | `UserUpdate` | `{message}` | 200, 401, 403, 404, 500 |
| POST | `/users/{user_id}/disable` | Bearer | `user.disable` | path: `user_id` | `{message}` | 200, 400, 401, 403, 500 |
| POST | `/users/{user_id}/enable` | Bearer | `user.disable` | path: `user_id` | `{message}` | 200, 401, 403, 500 |
| POST | `/users/{user_id}/reset-password` | Bearer | `user.update` | `UserPasswordReset` | `{message}` | 200, 400, 401, 403, 500 |

### Schemas

- `UserCreate`: `{username, password, role_name, active?, must_change_password?}` (password min 8, max 128)
- `UserUpdate`: partial `{role_names?, active?, must_change_password?}`
- `UserPasswordReset`: `{new_password}` (min 8, max 128)
- `User`: `{id, username, role_names[], active, must_change_password, created_at, last_login?}`

### Role values

`ADMINISTRATOR` | `CASE INVESTIGATOR` | `FORENSIC ANALYST` | `EVIDENCE CUSTODIAN` | `AUDITOR`

---

## Router: `/reports` — Report Generation

| Method | Path | Auth | Permission | Request | Response | Status |
|--------|------|------|-----------|---------|----------|--------|
| GET | `/reports/case/{case_id}` | Bearer | `report.generate` | path: `case_id`, query: `report_type` | `Report` | 200, 400, 401, 403, 404 |

### Report type values

`summary` | `evidence` | `custody` | `audit`

### Report schema (varies by `report_type`)

- `summary`: `{type, case{}, generated_at, generated_by}`
- `evidence`: `{type, case{}, evidence[], evidence_count, generated_at, generated_by}`
- `custody`: `{type, case{}, custody_events[], event_count, generated_at, generated_by}`
- `audit`: `{type, case{}, audit_logs[], log_count, generated_at, generated_by}`

---

## System Endpoints (no auth)

| Method | Path | Purpose | Response |
|--------|------|---------|----------|
| GET | `/` | API info | `{name, description, version, docs}` |
| GET | `/health` | Health check | `{status, timestamp}` |
| GET | `/dashboard/stats` | Optional auth, public stats | `{total_cases, open_cases, total_evidence, verified_evidence, custody_events, audit_entries}` |

---

## Case-Level Access Control (Object Authorization)

The existing RBAC is **role-based**, not object-based. A user with `case.view`
permission can view ALL cases in the system, not just cases they are
explicitly assigned to via `case_users` table. This is a known architectural
gap; object-level authorization is deferred to a later phase (see
[Known Limitations](PHASE_1B_API_STABILIZATION.md#known-limitations)).

The `case_users` table exists and `assign_user_to_case` writes to it, but it
is not currently used to filter read access.

---

## Pagination

List endpoints accept:

- `limit` (default 100, max 500–2000 depending on endpoint)
- `offset` (default 0, must be ≥0)

Responses return a list (not an envelope) and do not include `total` count.
A list endpoint with `count` is provided for audit logs at `GET /audit-logs/count`.

---

## Error Responses

Errors return `{"detail": "..."}` with the appropriate HTTP status code. The
`detail` field contains a human-readable message that is safe to expose (no
internal exception traces, SQL, or stack traces).

Validation errors (HTTP 422) from Pydantic return:

```json
{
  "detail": [
    {"loc": ["body", "field_name"], "msg": "error message", "type": "value_error"}
  ]
}
```

---

## Database Interactions

| Service | Tables Touched |
|---------|---------------|
| `case_service` | `cases`, `case_users` |
| `evidence_service` | `evidence`, `evidence_hashes`, `custody_events` (initial), `cases` (lookup) |
| `custody_service` | `custody_events`, `evidence` (lookup) |
| `audit_service` | `audit_logs` (append-only) |
| `authentication` | `users`, `sessions`, `user_roles`, `roles`, `role_permissions`, `permissions` |

All queries use parameterized statements. There are NO `f"SELECT ... {user_input}"`
patterns in production service code. The single `f"UPDATE cases SET ..."` in
`case_service.update_case` is safe because column names are filtered through
a hardcoded allowlist (`_allowed = frozenset({...})`).

---

## Summary

| Router | Endpoints | All require auth? | All require permission? |
|--------|-----------|-------------------|------------------------|
| `/auth` | 4 | mixed (login is public) | n/a |
| `/cases` | 9 | yes | yes |
| `/evidence` | 9 | yes | yes |
| `/custody` | 3 | yes | yes |
| `/audit-logs` | 2 | yes | yes |
| `/users` | 7 | yes | yes |
| `/reports` | 1 | yes | yes |
| System | 3 | mixed (health/root public) | n/a |
| **Total** | **38** | — | — |
