# CyberTrace Nexus — Security Baseline

**Version:** 1.0
**Date:** 2026-09-03
**Scope:** CyberTrace Nexus backend and frontend security baseline

This document describes the security architecture, configuration, and best
practices for deploying and operating CyberTrace Nexus. It is the canonical
reference for the security baseline established in Phase 1A.

---

## 1. Threat Model

CyberTrace Nexus handles:

- Digital evidence (files of arbitrary size and type)
- Chain of custody records
- Personally identifiable information (PII)
- Cryptographic hashes (MD5, SHA-256) for evidence integrity
- Audit logs covering all sensitive operations

The primary threat actors are:

1. **Insider attackers** — authenticated users attempting to escalate
   privileges or tamper with evidence.
2. **Network attackers** — passive eavesdroppers on the network and active
   man-in-the-middle attackers.
3. **Opportunistic attackers** — automated scanners looking for misconfigured
   services and known vulnerabilities.

---

## 2. Authentication

### 2.1 Password Storage

- **Algorithm:** PBKDF2-HMAC-SHA256
- **Iterations:** 210,000 (NIST SP 800-132 recommended)
- **Salt:** 128 bits, generated per password with `os.urandom`
- **Derived key length:** 256 bits (SHA-256 output)
- **Comparison:** `hmac.compare_digest` (constant-time)

Passwords are **never** stored, logged, or transmitted in plaintext.

### 2.2 Password Policy

- Minimum length: 8 characters
- Maximum length: 128 characters
- Account lockout: 5 failed attempts → 30-minute lockout (see auth policy)

### 2.3 JWT Tokens

- **Algorithm:** HS256
- **Expiry:** 7 days from issuance
- **Secret:** `JWT_SECRET_KEY` environment variable (required, no default)
- **Claims:** `sub` (user_id), `username`, `role_names`, `permissions`, `exp`

The secret key MUST be at least 256 bits of entropy. Generate with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 3. Authorization (RBAC)

Five roles with granular permissions:

| Role | Description |
|------|-------------|
| ADMINISTRATOR | Full system access |
| CASE INVESTIGATOR | Manages cases and evidence |
| FORENSIC ANALYST | Performs analysis, verifies hashes |
| EVIDENCE CUSTODIAN | Handles physical chain of custody |
| AUDITOR | Read-only oversight, audit log access |

All permission checks happen **server-side** via `require_permission_dep(...)`
in route handlers. The frontend hides UI controls based on stored permissions
for convenience, but this is not a security boundary.

---

## 4. Initial Setup

### 4.1 Required Environment Variables

```bash
# REQUIRED — fail-fast if not set
JWT_SECRET_KEY=<256-bit random string>

# OPTIONAL
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
DISABLE_API_DOCS=false
```

### 4.2 Creating the First Administrator

The application does **not** create any user on startup. To create the first
administrator, run the CLI helper:

```bash
python -m backend.scripts.create_admin --username admin
```

The script will interactively prompt for a password. The database must be
empty (no existing users) for this command to succeed.

---

## 5. Deployment Checklist

Before deploying to production, verify:

- [ ] `JWT_SECRET_KEY` is set to a unique, high-entropy value
- [ ] `CORS_ORIGINS` lists only the production frontend domain(s)
- [ ] `DISABLE_API_DOCS=true` to prevent schema leakage
- [ ] Database file is not world-readable (chmod 600 on the file)
- [ ] Evidence files are stored on an encrypted volume or filesystem
- [ ] HTTPS is enforced at the reverse proxy (TLS 1.2+)
- [ ] Security headers are set at the reverse proxy (HSTS, X-Frame-Options)
- [ ] Application is run as a non-root user
- [ ] Firewall rules restrict database and evidence file access

---

## 6. CORS

The backend reads allowed origins from the `CORS_ORIGINS` environment
variable. In production, this should list only the frontend domain(s).
Wildcard origins (`*`) are never used in combination with `allow_credentials`.

Methods and headers are restricted to those the API actually uses:

- Methods: `GET, POST, PUT, DELETE, OPTIONS`
- Headers: `Authorization, Content-Type, Accept`

---

## 7. Audit Logging

All sensitive operations are written to the `audit_logs` table:

- Login / logout
- Case creation, update, assignment, close
- Evidence registration, update, hash verification
- Custody events
- User creation, update, disable, enable
- Password reset
- System settings change

Audit records are **append-only**: there is no API endpoint to modify or
delete audit rows.

---

## 8. Hash Verification

When evidence is registered, the system computes MD5 and SHA-256 of the file
and stores the hashes. The file itself is never modified, copied, or moved.

`POST /evidence/{id}/verify` re-hashes the file and compares to the stored
values. **The stored hashes are never overwritten** during verification —
this preserves forensic integrity.

A verification mismatch triggers an `HASH_MISMATCH` audit event.

---

## 9. Known Limitations

The following items are documented limitations of the current baseline and
should be addressed in future phases:

1. **Tokens in localStorage** — The frontend stores JWT tokens in
   `localStorage`, which is accessible to any JavaScript on the page. A
   migration to `httpOnly` cookies is recommended.
2. **No rate limiting** — Authentication endpoints do not currently enforce
   rate limits. Use a reverse proxy (nginx, Caddy) or `slowapi` to add this.
3. **Synchronous SQLite** — The backend uses sync SQLite. For higher
   throughput, consider migrating to PostgreSQL with async drivers.
4. **No CSP headers** — Content Security Policy is not currently set. The
   reverse proxy or Next.js config should set strict CSP headers.

---

## 10. Reporting Security Issues

If you discover a security vulnerability, please report it to the project
maintainers privately. Do not open a public issue for suspected security
flaws.
