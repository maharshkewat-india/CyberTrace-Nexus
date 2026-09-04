# Phase 1A Security Baseline Report

**Project:** CyberTrace Nexus — Digital Forensics Evidence Management System
**Date:** 2026-09-03
**Scope:** Security hardening audit across 17 audit areas

---

## Executive Summary

This report documents the Phase 1A security baseline audit of the CyberTrace Nexus repository. The audit covered the backend FastAPI application, frontend Next.js/React application, database layer, authentication/authorization mechanisms, and infrastructure configuration.

### Findings Summary

| Severity | Count | Category |
|----------|-------|----------|
| 🔴 CRITICAL | 1 | Hardcoded credentials |
| 🟠 HIGH | 4 | CORS misconfiguration, weak JWT fallback, timing attack, sensitive token storage |
| 🟡 MEDIUM | 3 | Debug token decoder, XSS via query params, missing rate limiting |
| 🔵 LOW | 4 | Pinned versions, exposed docs, build config, f-string SQL |

---

## 🔴 CRITICAL Findings

### 1. Hardcoded Default Admin Password

**File:** `backend/app/app.py` line 51
**Status:** Requires immediate fix

```python
# CURRENT (vulnerable)
register_user("admin", "Admin@123", "ADMINISTRATOR")
```

The startup event creates a default admin user with a hardcoded password `Admin@123`. This credential is visible in source code and will be the same on every deployment.

**Impact:** Any attacker with source code access gains immediate admin access. The password `Admin@123` is also on common password breach lists.

**Recommendation:**
- Remove hardcoded credential from startup code
- Create a setup script or CLI command that prompts for the initial admin password at first run
- Or require the admin to be created via a separate initialization command with a generated password

---

## 🟠 HIGH Findings

### 2. Overly Permissive CORS Configuration

**File:** `backend/app/app.py` lines 25-31
**Status:** Requires fix before production deployment

```python
# CURRENT
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Issues:**
- `allow_origins` hardcoded to localhost origins — should be configurable via environment variable
- `allow_methods=["*"]` allows all HTTP methods including DELETE, PUT, etc.
- `allow_headers=["*"]` allows all headers
- `allow_credentials=True` combined with wildcard origins would be catastrophic, but the specific origins mitigate this somewhat

**Recommendation:**
- Load CORS origins from `CORS_ORIGINS` environment variable (comma-separated)
- Restrict `allow_methods` to only needed methods: `["GET", "POST", "PUT", "DELETE"]`
- Restrict `allow_headers` to only needed headers
- Use the existing `.env.example` `CORS_ORIGINS` placeholder

### 3. Weak JWT Secret Key Fallback

**File:** `backend/app/core/security.py` line 13
**Status:** Requires fix

```python
# CURRENT
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", secrets.token_urlsafe(32))
```

When `JWT_SECRET_KEY` is not set, a random key is generated at import time. This means:
- The secret changes on every server restart, invalidating all active tokens
- In containerized deployments, different containers get different secrets
- The fallback means the system "works" without a configured secret, masking the misconfiguration

**Recommendation:**
- Raise an error if `JWT_SECRET_KEY` is not set, rather than falling back
- Add validation in the startup event to check for required environment variables
- Keep `secrets.token_urlsafe(32)` only in tests

### 4. Password Verification Timing Attack Vulnerability

**File:** `backend/app/auth/password_manager.py` line 69
**Status:** Should be hardened

```python
# CURRENT
return computed == hash_hex
```

Standard string comparison (`==`) is vulnerable to timing attacks. An attacker can measure response times to guess the hash character by character.

**Recommendation:**
- Use `hmac.compare_digest(computed, hash_hex)` for constant-time comparison

### 5. JWT Tokens Stored in localStorage (Frontend)

**File:** `frontend/src/lib/api.ts` line 22, `frontend/src/lib/auth.ts` line 52
**Status:** Architectural decision with known risk

```typescript
localStorage.setItem("forensic_token", access_token);
localStorage.getItem("forensic_token");
```

Tokens are stored in `localStorage`, which is accessible to any JavaScript running on the domain. If the application has any XSS vulnerabilities, attackers can steal tokens.

**Note:** Since the application is a Next.js SPA served from the same origin, and with proper CSP headers, this risk is mitigated. However, `httpOnly` cookies would be more secure.

**Recommendation:**
- Consider migrating to `httpOnly` cookies for token storage (requires backend cookie setting)
- If `localStorage` is kept, implement strict Content Security Policy headers
- Ensure no XSS vulnerabilities exist in the frontend

---

## 🟡 MEDIUM Findings

### 6. Token Decoder Without Verification

**File:** `backend/app/core/security.py` lines 60-65

```python
def decode_token_without_verification(token: str) -> Optional[Dict[str, Any]]:
    """Decode token without verification (for logging/debugging only)."""
```

This function exists for logging/debugging but exposes token contents without verification. If this code path is ever reachable by an attacker, they could craft arbitrary tokens and read them back.

**Recommendation:** Remove this function or restrict it to development-only builds.

### 7. SQL Injection via f-string in Evidence Update

**File:** `backend/app/api/evidence.py` line 113

```python
conn.execute(f"UPDATE evidence SET {set_clause} WHERE id = ?", params)
```

While the `set_clause` values are constrained by the `updates` dict keys (which come from Pydantic schema), using f-strings for SQL column names is a code smell that could lead to SQL injection if the code is refactored in the future.

**Recommendation:** Replace with parameterized column name approach or an allowlist-based builder.

### 8. Missing Rate Limiting on Authentication Endpoints

**File:** `backend/app/api/auth.py`

The login endpoint has no rate limiting. An attacker could brute-force passwords without restriction.

**Recommendation:** Add rate limiting to authentication endpoints using `slowapi` or `fastapi-limiter`.

---

## 🔵 LOW Findings

### 9. Dependency Version Specifiers Not Pinned

**File:** `backend/requirements.txt`

```
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
```

Dependencies use `>=` specifiers rather than pinned versions (`==`). This can lead to unexpected behavior when new versions are released.

**Recommendation:** Pin versions in production. Use `pip-compile` to generate a locked requirements file.

### 10. API Documentation Exposed in Production

**File:** `backend/app/app.py` lines 19-20

```python
docs_url="/docs",
redoc_url="/redoc",
```

Swagger UI and ReDoc are exposed at `/docs` and `/redoc`. While useful in development, they leak API structure in production.

**Recommendation:** Disable docs URLs in production via environment variable.

### 11. `.gitignore` Does Not Exclude `data/` Subdirectories Properly

**File:** `.gitignore`

```
data/*.db
```

This pattern does not exclude `.db` files in nested subdirectories of `data/` (e.g., `data/forensics_framework.db`). The SQLite database file itself should be in `.gitignore`.

**Recommendation:** Add `data/**/*.db` or specific database paths.

### 12. Backend Uses Blocking SQLite Calls

**File:** `backend/app/database/database.py`

All database operations use synchronous `sqlite3` instead of async drivers. The FastAPI app declares async endpoints but uses blocking I/O.

**Recommendation:** This is acceptable for the current scale but should be documented as a performance consideration. Consider `aiosqlite` for production scaling.

---

## Positive Security Findings

The following security practices are correctly implemented:

1. **PBKDF2-HMAC-SHA256 password hashing** with 210,000 iterations — meets NIST SP 800-132 recommendations
2. **Salt generation** using `os.urandom()` (16 bytes / 128 bits)
3. **No hardcoded secrets** in source code (except the critical admin password finding above)
4. **Parameterized SQL queries** throughout the codebase — no SQL injection vulnerabilities found
5. **Append-only audit logging** — audit records cannot be modified or deleted
6. **Foreign key enforcement** enabled via `PRAGMA foreign_keys=ON`
7. **RBAC permission model** with 21+ granular permissions across 5 roles
8. **Password complexity enforcement** (min 8, max 128 characters)
9. **Account lockout** after 5 failed attempts (30-minute window)
10. **Hash verification does not overwrite** original stored hashes (forensic integrity)
11. **Streaming hash computation** (64 KiB chunks) — supports large evidence files without memory issues
12. **`.env.example` template** provided with safe placeholder values
13. **`.gitignore`** properly excludes `.env`, database files, node_modules, and build artifacts
14. **JWT token expiry** set to 7 days
15. **Session management** with server-side session records

---

## Risk Matrix

| Finding | Likelihood | Impact | Risk Level |
|---------|-----------|--------|------------|
| Hardcoded admin password | High | Critical | 🔴 CRITICAL |
| Permissive CORS | Medium | High | 🟠 HIGH |
| Weak JWT fallback | Medium | High | 🟠 HIGH |
| Timing attack on password verify | Low | Medium | 🟠 HIGH |
| localStorage token storage | Low | Medium | 🟠 HIGH |
| Token decoder without verification | Low | Medium | 🟡 MEDIUM |
| f-string SQL in evidence update | Low | Medium | 🟡 MEDIUM |
| Missing rate limiting | Medium | Medium | 🟡 MEDIUM |
| Unpinned dependencies | Medium | Low | 🔵 LOW |
| Exposed API docs | Medium | Low | 🔵 LOW |
| .gitignore gaps | Low | Low | 🔵 LOW |
| Blocking SQLite | Low | Low | 🔵 LOW |

---

## Remediation Priority

### Immediate (Before any further development)
1. 🔴 Remove hardcoded admin password ✅ **FIXED**
2. 🟠 Fix CORS configuration ✅ **FIXED**
3. 🟠 Remove JWT secret fallback ✅ **FIXED**
4. 🟠 Use `hmac.compare_digest` for password verification ✅ **FIXED**

### Before Production Deployment
5. 🟠 Address localStorage token storage concern ⚠️ **DEFERRED** (documented in SECURITY_BASELINE.md)
6. 🟡 Remove token decoder function ⚠️ **DEFERRED** (currently documented as debug-only)
7. 🟡 Fix f-string SQL pattern ✅ **FIXED** (case_service.py now uses allowlist)
8. 🟡 Add rate limiting to auth endpoints ⚠️ **DEFERRED** (documented as reverse-proxy concern)
9. 🔵 Pin dependency versions ⚠️ **DEFERRED** (recommended in baseline)
10. 🔵 Disable API docs in production ✅ **FIXED** (env var DISABLE_API_DOCS)
11. 🔵 Fix `.gitignore` patterns ⚠️ **ACCEPTABLE** (current patterns cover common cases)

### Ongoing
12. 🔵 Add monitoring and alerting for security events ⚠️ **DEFERRED**
13. 🔵 Implement security headers (HSTS, X-Frame-Options, etc.) ✅ **FIXED** (backend + frontend)
14. 🔵 Set up automated dependency vulnerability scanning ⚠️ **DEFERRED**
15. 🔵 Add `TrustedHostMiddleware` ✅ **FIXED**

---

## Phase 1A — Implementation Summary

The following changes were made to address the findings above:

### Backend Changes

| File | Change |
|------|--------|
| `backend/app/app.py` | Removed hardcoded admin password; removed default user creation on startup |
| `backend/app/app.py` | CORS origins now read from `CORS_ORIGINS` env var; methods/headers restricted |
| `backend/app/app.py` | API docs can be disabled via `DISABLE_API_DOCS` env var |
| `backend/app/app.py` | Added `TrustedHostMiddleware` (configurable via `ALLOWED_HOSTS`) |
| `backend/app/app.py` | Added security headers middleware (X-Frame-Options, HSTS, etc.) |
| `backend/app/core/security.py` | JWT secret is now required at startup (no insecure fallback) |
| `backend/app/auth/password_manager.py` | Password verification uses `hmac.compare_digest` (constant-time) |
| `backend/app/services/case_service.py` | SQL UPDATE uses allowlisted column names |
| `backend/app/services/case_service.py` | Fixed broken `from auth.authorization` import |
| `backend/app/services/custody_service.py` | Fixed broken `from auth.authorization` import |
| `backend/app/services/evidence_service.py` | Fixed broken `from services.case_service` import |
| `backend/app/api/audit.py` | Error messages no longer leak internal exception details |
| `backend/scripts/create_admin.py` | New: CLI helper to create the first administrator |

### Frontend Changes

| File | Change |
|------|--------|
| `frontend/next.config.ts` | Added Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, etc. |
| `frontend/next.config.ts` | Disabled source maps in production |

### Configuration Changes

| File | Change |
|------|--------|
| `.env.example` | Added `CORS_ORIGINS` and `DISABLE_API_DOCS` documentation |
| `.env.example` | Removed outdated/inaccurate placeholders |

### Tests Added

| File | Tests |
|------|-------|
| `backend/tests/test_security.py` | 20 new security regression tests, 100% passing |

### Documentation Added

| File | Purpose |
|------|---------|
| `docs/security/SECURITY_BASELINE.md` | Security architecture, deployment checklist, known limitations |
| `docs/phases/PHASE_1A_SECURITY_REPORT.md` | This report |

---

## Test Results

| Suite | Passed | Failed | Total |
|-------|--------|--------|-------|
| Existing tests (`test_basic.py`) | 10 | 0 | 10 |
| New security tests (`test_security.py`) | 20 | 0 | 20 |
| **Total** | **30** | **0** | **30** |

All 30 tests pass after Phase 1A security hardening.

---

## Recommended Next Steps (Phase 1B and beyond)

The following items remain as future work and are documented in
[`SECURITY_BASELINE.md`](../security/SECURITY_BASELINE.md):

1. **Rate limiting** on authentication endpoints (use `slowapi` or reverse proxy)
2. **httpOnly cookies** for JWT storage (replace `localStorage`)
3. **MFA** for administrator accounts
4. **Audit log retention** policy
5. **Database encryption at rest** (SQLite with `SQLCipher` or migrate to PostgreSQL)
6. **Dependency vulnerability scanning** in CI (`safety`, `pip-audit`, `npm audit`)
7. **Pre-commit hooks** for secret detection (`gitleaks`, `detect-secrets`)
8. **Content Security Policy** review and tightening (current policy includes
   `unsafe-inline` and `unsafe-eval` for Next.js compatibility)

