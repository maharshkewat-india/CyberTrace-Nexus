"""
app.py - FastAPI application factory for CyberTrace Nexus.
Evolved from the Digital Forensics Evidence Management System foundation.
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from .database import database
from .api import auth, cases, evidence, custody, audit, users, reports
from .core.dependencies import get_optional_user

# Create FastAPI app
app = FastAPI(
    title="CyberTrace Nexus API",
    description="AI-Assisted Digital Incident Reconstruction & Evidence Correlation Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for local development
# In production, restrict origins to your domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(evidence.router)
app.include_router(custody.router)
app.include_router(audit.router)
app.include_router(users.router)
app.include_router(reports.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    database.initialize_database()
    if database.is_fresh_database():
        # Create default admin user
        from .auth.authentication import register_user
        try:
            register_user("admin", "Admin@123", "ADMINISTRATOR")
            print("[backend] Default admin created: admin / Admin@123")
        except Exception as e:
            print(f"[backend] [WARN] Could not create default admin: {e}")


@app.get("/")
async def root():
    """Root endpoint - API info."""
    return {
        "name": "CyberTrace Nexus API",
        "description": "AI-Assisted Digital Incident Reconstruction & Evidence Correlation Platform",
        "version": "1.0.0",
        "docs": "/docs",
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