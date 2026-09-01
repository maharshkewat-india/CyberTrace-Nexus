"""
main.py - Entry point for running the CyberTrace Nexus FastAPI backend with uvicorn.

CyberTrace Nexus evolved from the Digital Forensics Evidence Management System foundation.

Usage:
    python -m backend.app.main
    # or
    cd backend && python -m app.main
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.app:app",
        host="0.0.0.0",
        port=8000,
        # Avoid creating a reload supervisor when launched by launcher scripts.
        # On Windows, closing only the parent can leave a child server behind
        # to retain port 8000. Use ``uvicorn app.app:app --reload`` explicitly
        # during development when live reloading is needed.
        reload=False,
        log_level="info",
    )
