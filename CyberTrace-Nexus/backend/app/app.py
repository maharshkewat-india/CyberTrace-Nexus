"""
app.py - FastAPI application factory for CyberTrace Nexus.
Evolved from the Digital Forensics Evidence Management System foundation.
"""

import os
from datetime import datetime, timezone

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .database import database
from .api import auth, cases, evidence, custody, audit, users, reports
from .core.dependencies import get_optional_user
from .core.error_handlers import add_error_handlers

# ----------------------------------------------------------------------
# Environment-driven configuration
# ----------------------------------------------------------------------

# CORS origins (comma-separated). Defaults to local development origins.
_default_origins = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"
_cors_origins_raw = os.environ.get("CORS_ORIGINS", _default_origins)
cors_origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

# Disable interactive API docs in production (avoids leaking schema).
_docs_disabled = os.environ.get("DISABLE_API_DOCS", "").lower() in ("1", "true", "yes")
_docs_url = None if _docs_disabled else "/docs"
_redoc_url = None if _docs_disabled else "/redoc"

# Create FastAPI app
app = FastAPI(
    title="CyberTrace Nexus API",
    description="AI-Assisted Digital Incident Reconstruction & Evidence Correlation Platform",
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
)

# Configure CORS (origins from env, restricted methods/headers)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Configure trusted hosts (security: prevent host header attacks)
_allowed_hosts = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1")
_allowed_hosts_list = [h.strip() for h in _allowed_hosts.split(",") if h.strip()]
if _allowed_hosts_list != ["*"]:  # Only enable if not explicitly disabled
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts_list)


# ----------------------------------------------------------------------
# Security headers middleware
# ----------------------------------------------------------------------

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add standard security response headers to every response."""
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), interest-cohort=()"
    )
    response.headers["Cache-Control"] = "no-store"
    return response

# Include routers
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(evidence.router)
app.include_router(custody.router)
app.include_router(audit.router)
app.include_router(users.router)
app.include_router(reports.router)

# Register consistent error handlers
add_error_handlers(app)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup.

    Note: No default user is created automatically. The first administrator
    must be created explicitly via the CLI helper script:
        python -m backend.scripts.create_admin --username <name> --password <pwd>
    See docs/security/SECURITY_BASELINE.md for details.
    """
    database.initialize_database()


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "CyberTrace Nexus API",
        "description": "AI-Assisted Digital Incident Reconstruction & Evidence Correlation Platform",
        "version": "1.0.0",
        "docs": _docs_url,
        "security_headers": True,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/dashboard/stats", response_model=dict)
async def get_dashboard_stats(current_user = Depends(get_optional_user)):
    """Get dashboard statistics (public stats, not user-specific)."""
    from .services import case_service, evidence_service, custody_service, audit_service

    # Get basic stats
    cases = case_service.list_cases(limit=10000)
    evs = evidence_service.list_all_evidence(limit=10000)
    audit_count = audit_service.get_audit_count()
    custody_count = custody_service.count_custody_events()

    open_count = sum(1 for c in cases if c.status == "Open")
    verified_count = evidence_service.count_verified_evidence()

    return {
        "total_cases": len(cases),
        "open_cases": open_count,
        "total_evidence": len(evs),
        "verified_evidence": verified_count,
        "custody_events": custody_count,
        "audit_entries": audit_count,
    }