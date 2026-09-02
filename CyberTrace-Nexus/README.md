# CyberTrace Nexus

AI-Assisted Digital Incident Reconstruction & Evidence Correlation Platform

CyberTrace Nexus evolved from the Digital Forensics Evidence Management System foundation, extending it with AI-powered investigation capabilities.

## Features

- **Case Management** — Create, assign, and track investigation cases
- **Evidence Vault** — Register and manage digital evidence with cryptographic integrity verification
- **Chain of Custody** — Complete audit trail of evidence handling
- **RBAC Security** — Role-based access with 21 granular permissions across 5 roles
- **Audit Logging** — Append-only audit trail of all system operations
- **Report Generation** — Export case data in structured formats

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or pnpm

### Installation

```bash
# Clone the repository
cd CyberTrace-Nexus

# Backend setup
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Start both services
cd ..
./scripts/development/start.sh  # On Windows: scripts\development\start.bat
```

Or use the launcher:

```bash
# On Windows
RUN_ME.bat
```

### Access

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Default Credentials

- Username: `admin`
- Password: `Admin@123`

**Change these immediately in production!**

## Project Structure

```
CyberTrace-Nexus/
├── backend/
│   ├── app/           # FastAPI application
│   │   ├── api/       # API routes
│   │   ├── core/      # Security, dependencies
│   │   ├── database/  # DB connection, schema
│   │   ├── models/    # Data models
│   │   ├── schemas/   # Pydantic schemas
│   │   └── services/  # Business logic
│   ├── tests/         # Backend tests
│   └── scripts/       # Utility scripts
├── frontend/
│   └── src/
│       ├── app/       # Next.js pages
│       ├── components/ # React components
│       ├── hooks/      # Custom hooks
│       └── lib/       # Utilities
├── database/
│   └── schemas/       # SQL schema files
├── scripts/           # Development scripts
└── tests/             # Integration tests
```

## Documentation

- [Project Audit Report](docs/PROJECT_AUDIT.md)
- [Architecture Documentation](docs/architecture/)
- [Development Guide](docs/development/)
- [Security Documentation](docs/security/)

## Technology Stack

### Backend

- **FastAPI** — Modern Python web framework
- **SQLite** — Lightweight database with WAL mode
- **JWT** — Stateless authentication with session tracking
- **PBKDF2** — Secure password hashing (210,000 iterations)

### Frontend

- **Next.js 16** — React framework with App Router
- **React 19** — UI library
- **Tailwind CSS 4** — Utility-first styling
- **shadcn/ui** — Accessible component primitives

## CyberTrace Nexus Roadmap

The project is evolving to add:

- Forensic artifact extraction engine
- Event normalization pipeline
- Timeline construction engine
- Evidence correlation engine
- IOC detection and analysis
- AI investigation assistant
- Incident replay capability

See [BRAIN.md](BRAIN.md) for the full roadmap and architecture vision.

## Security

- PBKDF2-HMAC-SHA256 password hashing
- JWT tokens with 7-day expiry
- 21 granular permissions across 5 roles
- Parameterized SQL queries (SQL injection prevention)
- Foreign key enforcement
- Append-only audit logging

**Important:** Change default admin credentials in production!

## License

See LICENSE file for details.

## Contributing

See the development documentation for contribution guidelines.
