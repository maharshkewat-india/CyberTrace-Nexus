# Phase 1B — API Stabilization Report

**Project:** CyberTrace Nexus — Digital Forensics Evidence Management System
**Date:** 2026-09-04
**Scope:** Backend API stabilization, contract enforcement, and end-to-end
contract testing

---

## Executive Summary

Phase 1B is a **stability-only** phase. It preserves all existing forensic
functionality, the FastAPI+SQLite stack, the RBAC model, and the database
schema. The work covers:

- A complete API inventory
- Consistent HTTP status codes
- A centralized, sanitized error envelope
- Verified service / API separation
- Verified authentication and authorization on every endpoint
- DB access patterns and transaction safety
- Standardized pagination
- Allowlist-based filter and update builders
- Forensic integrity preservation
- Frontend compatibility
- 50 automated tests (basic + security + API contract)

No new features are added and no existing data model is changed.

---

## Deliverables

| File | Purpose |
|------|---------|
| `docs/api/API_INVENTORY.md` | Full enumeration of every HTTP endpoint |
| `backend/app/core/error_handlers.py` | Centralized error envelope with sanitization |
| `backend/app/app.py` | Wires error handlers into the FastAPI app |
| `backend/conftest.py` | Pytest fixture shared by all test modules |
| `backend/tests/test_api_contract.py` | 20 contract tests covering status codes, auth, validation |
| `docs/phases/PHASE_1B_API_STABILIZATION.md` | This report |

---

## API Inventory

All 38 endpoints are catalogued in
[`docs/api/API_INVENTORY.md`](../api/API_INVENTORY.md). For each endpoint:

- HTTP method and path
- Router and tag
- Auth requirement (none / Bearer)
- Permission name (e.g. `case.create`)
- Request and response schema
- Possible status codes
- Service function and tables touched

This is the authoritative reference for any client (frontend, CLI, scripts)
that needs to talk to the API.

---

## HTTP Status Code Audit

### Findings & Fixes

| Issue | Endpoint(s) | Before | After |
|-------|-------------|--------|-------|
| `POST /cases` returned 200 instead of 201 | `POST /cases` | 200 | **201** |
| `POST /evidence` returned 200 instead of 201 | `POST /evidence` | 200 | **201** |
| `POST /custody` returned 200 instead of 201 | `POST /custody` | 200 | **201** |
| `POST /users` returned 200 instead of 201 | `POST /users` | 200 | **201** |
| Duplicate username returned 400 instead of 409 | `POST /users` | 400 | **409** |
| `/cases/{id}/users` did not 404 when case missing | `GET /cases/{id}/users` | 200 `[]` | **404** |
| `/cases/{id}/evidence` did not 404 when case missing | `GET /cases/{id}/evidence` | 200 `[]` | **404** |
| Generic `Exception` handler returned raw `str(e)` | many | leak | sanitized |

### Status Code Conventions

| Code | Used for |
|------|----------|
| 200 | Successful read or update |
| 201 | Resource created (POST that creates) |
| 400 | Validation / business-logic error |
| 401 | Missing or invalid token |
| 403 | Authenticated but missing permission |
| 404 | Resource not found |
| 409 | Conflict (duplicate, etc.) |
| 422 | Pydantic validation failure |
| 500 | Unexpected server error (sanitized) |

---

## Error Response Format

All errors are normalized to the following envelope (see
`backend/app/core/error_handlers.py`):

```json
{
  "error_code": "NOT_FOUND",
  "detail": "Case 9999 not found",
  "timestamp": "2026-09-04T12:34:56Z"
}
```

Properties:

- `error_code` is a stable machine-readable identifier
  (`NOT_FOUND`, `UNAUTHORIZED`, `FORBIDDEN`, `CONFLICT`, `VALIDATION_ERROR`,
  `SERVER_ERROR`, `VALUE_ERROR`, `PERMISSION_ERROR`, `FILE_NOT_FOUND`,
  `DUPLICATE_ERROR`, `ERROR`).
- `detail` is sanitized — it never contains raw exception messages,
  SQL fragments, file paths, stack traces, or Pydantic internal types.
- `timestamp` is ISO 8601 UTC.

Pydantic 422 errors still include the `detail` array for field-level
errors, but the global handler is the safety net for everything else.

---

## Authentication & Authorization

### Verified

- Every non-system endpoint requires `Bearer <jwt>`.
- Every protected endpoint declares a specific permission through
  `require_permission_dep(...)`.
- The 21-permission RBAC table is unchanged.
- Five roles (`ADMINISTRATOR`, `CASE INVESTIGATOR`, `FORENSIC ANALYST`,
  `EVIDENCE CUSTODIAN`, `AUDITOR`) and their permission sets are unchanged.

### Known Limitation — Case-Level Object Authorization

RBAC is **role-based**, not object-based. A user with `case.view` can read
ALL cases, not just those they are assigned to. The `case_users` table
exists and `assign_user_to_case` writes to it, but it is not used to filter
read access. This is documented as a known limitation in
[`API_INVENTORY.md`](../api/API_INVENTORY.md#case-level-access-control-object-authorization)
and is deferred to a later phase that will not destabilize the API.

---

## Service / API Separation

- All business logic lives in `backend/app/services/`.
- Routers in `backend/app/api/` are thin: they validate input, call one
  service function, and translate exceptions to HTTP errors.
- The only DB calls inside routers are read-only lookups that the service
  cannot perform atomically (e.g. verifying a related row exists); in every
  case the lookups are simple `SELECT ... WHERE id = ?` parameterized
  queries.
- All writes go through services.

---

## Database Access Patterns

- Every production query uses parameterized statements.
- The single `f"UPDATE cases SET ..."` pattern (in `case_service.update_case`)
  is safe because column names are filtered through a hardcoded allowlist
  (`_allowed = frozenset({...})`).
- All write transactions go through `with transaction() as c:` or an
  explicit `c.commit()` after write.
- `case_service.update_case` and `evidence_service.register_evidence` keep
  audit events in the same logical write as the row that triggered them.

---

## Pagination

- All list endpoints accept `limit` (1–500 or 1–2000) and `offset` (≥0).
- Defaults are documented per-endpoint in the API inventory.
- Responses return a list (not an envelope). The single `count` endpoint
  (`GET /audit-logs/count`) is preserved for backward compatibility.
- Out-of-range values are rejected with HTTP 422 by Pydantic / Query
  validators (covered by `test_pagination_limit_validation` and
  `test_pagination_offset_validation`).

---

## Filtering & Sorting

- All filter values are validated against hardcoded allowlists inside the
  service layer (e.g. `case_service.list_cases` only accepts status values
  that exist in the schema, and is filtered by Query choices).
- `case_service.update_case` filters UPDATE column names through the
  `_allowed` frozenset before composing the SET clause.
- No user-supplied column name or operator flows into SQL.

---

## Forensic Integrity Preservation

- Evidence registration always writes the original hash row
  (`is_original = 1`) and never overwrites it during verification.
- Hash verification re-computes hashes from the file and compares them to
  the stored values, producing a `HashVerifyResult` with `md5_match` and
  `sha256_match` flags.
- Custody chain of custody is append-only; the only place the framework
  writes to `custody_events` is through `add_custody_event` and
  `register_evidence` (initial `REGISTERED` event).
- Audit log is append-only: there is no `PUT`/`DELETE` on `/audit-logs`.
- The `evidence.file_path` is the absolute path to the original file; the
  framework never copies or modifies the source.

---

## Frontend Compatibility

- The 201 / 200 / 404 / 409 / 422 contract is strictly **additive** for
  successful reads. Every previously-working request still returns the
  same JSON body shape.
- The error envelope is **additive**: clients that read `detail` from a
  `{"detail": "..."}` payload still work. The new fields (`error_code`,
  `timestamp`) are added alongside, not replacing `detail`.
- The `POST` body schemas and `PUT` body schemas are unchanged.
- Pagination query parameters are unchanged.

No frontend code changes are required for this phase.

---

## Logging Review

- Logger is used in the error handler for server-side context
  (path, method, exception type).
- `detail` exposed to the client is sanitized; full exception text goes
  only to server logs.
- No raw passwords, tokens, or PII are logged.
- Audit log writes include actor, action, target, and description; the
  password reset audit does not log the new password.

---

## Health Check

- `GET /health` is public, returns `{status: "healthy", timestamp: ...}`.
- It is unaffected by the global error handler.
- Suitable for liveness/readiness probes.

---

## Performance Sanity Check

- All list endpoints cap `limit` (max 500–2000).
- The dashboard `GET /dashboard/stats` reads counts via service helpers
  with explicit limits.
- `evidence_service.count_verified_evidence` iterates only when necessary
  and tolerates missing files. Acceptable at current scale.
- No N+1 patterns were introduced in this phase.

---

## Test Results

| Suite | Passed | Failed | Total |
|-------|--------|--------|-------|
| `test_basic.py` | 10 | 0 | 10 |
| `test_security.py` | 20 | 0 | 20 |
| `test_api_contract.py` | 20 | 0 | 20 |
| `test_ui_rbac.py` | 9 | 0 | 9 |
| **Total** | **59** | **0** | **59** |

Coverage of API contract:

- 201 CREATED on POST /cases, /evidence, /custody, /users
- 401 UNAUTHORIZED on every protected endpoint without a token
- 403 FORBIDDEN when a permission is missing
- 404 NOT_FOUND on missing case, missing evidence, missing case for
  `/cases/{id}/users` and `/cases/{id}/evidence`
- 409 CONFLICT on duplicate username
- 422 VALIDATION on bad pagination
- Standard error envelope (error_code, detail, timestamp)
- `/health` and `/` do not require auth
- `/auth/logout` works under bearer auth
- `/reports/case/{id}` returns a summary
- `/audit-logs` returns entries

---

## Open Items / Future Phases

These are intentionally **out of scope** for Phase 1B and are deferred:

- Case-level object authorization (filter reads by `case_users`).
- Rate limiting on `/auth/login`.
- `httpOnly` cookies for token storage.
- Database migration to async driver (`aiosqlite`) or PostgreSQL.
- `mf` decorator / multi-factor auth for administrators.
- Dependency vulnerability scanning in CI.
- Pinning of `requirements.txt` versions.
- The full intelligence stack: Artifact Intelligence Engine, Event
  Normalization, Timeline Engine, Correlation Engine, Evidence Graph, IOC
  Intelligence, Risk Engine, Incident Reconstruction, AI Investigator,
  Incident Replay.

---

## How to Run the Tests

```bash
cd backend
JWT_SECRET_KEY="test-secret-32-chars-for-unit-tests" python tests/test_basic.py
JWT_SECRET_KEY="test-secret-32-chars-for-unit-tests" python tests/test_security.py
JWT_SECRET_KEY="test-secret-32-chars-for-unit-tests" python tests/test_api_contract.py
JWT_SECRET_KEY="test-secret-32-chars-for-unit-tests" python tests/test_ui_rbac.py
```

All four scripts end with a summary block. The expected outcome is
`Passed: <N>  Failed: 0  Success: 100.0%`.
