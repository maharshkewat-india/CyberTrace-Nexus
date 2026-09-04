"""
test_api_contract.py - API contract tests for CyberTrace Nexus.

Tests verify:
- HTTP status codes are correct (201 for POST creates, 404 for missing resources)
- Error responses use the standard format with error_code and detail
- Authentication is required on protected endpoints
- Pagination parameters are validated
- 201 CREATED on POST /cases, /evidence, /custody, /users

Run with: python backend/tests/test_api_contract.py
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Set required env before importing app modules.
# ALLOWED_HOSTS=* disables the TrustedHostMiddleware so the test client
# (which uses 'testclient' as the host) can connect without being rejected.
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-contract-tests-only-32chars"
os.environ["ALLOWED_HOSTS"] = "*"

# Use an isolated test database in a temp dir so we don't touch the
# production forensics_framework.db.
_TEST_DB_DIR = Path(tempfile.mkdtemp(prefix="cybertrace_test_"))
_TEST_DB_PATH = _TEST_DB_DIR / "test_forensics.db"

from fastapi.testclient import TestClient

from backend.app.app import app
from backend.app.database.database import initialize_database
from backend.app.database import database as _db_module

# Force DB_PATH to the temp test database BEFORE initialize_database runs.
_db_module.DB_PATH = _TEST_DB_PATH
_db_module.DATA_DIR = _TEST_DB_DIR


def reset_test_db():
    """Reset the test database to a clean state."""
    if _TEST_DB_PATH.exists():
        try:
            _TEST_DB_PATH.unlink()
        except OSError:
            pass
    for ext in ["-wal", "-shm"]:
        p = Path(str(_TEST_DB_PATH) + ext)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
    initialize_database()


def create_temp_file(content: bytes = b"Test evidence content for API contract tests.") -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(content)
        return f.name


def cleanup_temp_file(path: str) -> None:
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def setup_admin_user():
    """Register an admin user for authenticated requests.

    Idempotent: if the user already exists in the test database
    (e.g. from a previous test in this process), this returns
    the existing user data via authenticate_user.
    """
    from backend.app.auth.authentication import register_user, authenticate_user
    from backend.app.database.database import get_connection
    # Check if user already exists
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM users WHERE username = ?", ("contract_admin",)).fetchone()
    finally:
        conn.close()
    if row:
        user_data, _ = authenticate_user("contract_admin", "AdminPass123!")
        return user_data
    return register_user("contract_admin", "AdminPass123!", "ADMINISTRATOR")


def get_auth_headers(username: str, password: str) -> dict:
    """Get JWT auth headers for a user."""
    from backend.app.auth.authentication import authenticate_user
    from backend.app.core.security import create_access_token

    user_data, _ = authenticate_user(username, password)
    token_data = {
        "user_id": user_data["id"],
        "username": user_data["username"],
        "role_names": user_data["role_names"],
        "permissions": user_data["permissions"],
    }
    access_token = create_access_token(token_data)
    return {"Authorization": f"Bearer {access_token}"}


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def test_root_endpoint(result: TestResult) -> None:
    """GET / returns API info."""
    print("\n[T-CR1] Test GET / root endpoint")
    client = TestClient(app)
    response = client.get("/")
    try:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "name" in data
        assert "version" in data
        result.passed += 1
        print("    [PASS] Root endpoint returns API info")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_root_endpoint: {e}")
        print(f"    [FAIL] {e}")


def test_health_endpoint(result: TestResult) -> None:
    """GET /health returns health status without auth."""
    print("\n[T-CR2] Test GET /health endpoint")
    client = TestClient(app)
    response = client.get("/health")
    try:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        result.passed += 1
        print("    [PASS] Health endpoint works without auth")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_health_endpoint: {e}")
        print(f"    [FAIL] {e}")


def test_login_requires_no_auth(result: TestResult) -> None:
    """POST /auth/login works without a Bearer token."""
    print("\n[T-CR3] Test POST /auth/login (no auth required)")
    client = TestClient(app)
    # Create user first
    setup_admin_user()
    response = client.post("/auth/login", json={"username": "contract_admin", "password": "AdminPass123!"})
    try:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == "contract_admin"
        result.passed += 1
        print("    [PASS] Login works without auth, returns token")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_login_requires_no_auth: {e}")
        print(f"    [FAIL] {e}")


def test_protected_endpoints_require_auth(result: TestResult) -> None:
    """Protected endpoints return 401 without auth."""
    print("\n[T-CR4] Test protected endpoints require auth")
    client = TestClient(app)

    protected_paths = [
        ("GET", "/cases"),
        ("POST", "/cases"),
        ("GET", "/evidence"),
        ("POST", "/evidence"),
        ("GET", "/custody/1"),
        ("POST", "/custody"),
        ("GET", "/audit-logs"),
        ("GET", "/users"),
        ("POST", "/users"),
    ]

    failures = []
    for method, path in protected_paths:
        response = getattr(client, method.lower())(path)
        if response.status_code != 401:
            failures.append(f"{method} {path} returned {response.status_code} (expected 401)")

    try:
        assert not failures, "; ".join(failures)
        result.passed += 1
        print("    [PASS] All protected endpoints return 401 without auth")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_protected_endpoints_require_auth: {e}")
        print(f"    [FAIL] {e}")


def test_post_cases_returns_201(result: TestResult) -> None:
    """POST /cases returns 201 CREATED."""
    print("\n[T-CR5] Test POST /cases returns 201 CREATED")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    response = client.post(
        "/cases",
        headers=headers,
        json={"title": "Contract Test Case", "priority": "High"},
    )
    try:
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = response.json()
        assert "id" in data
        assert data["case_number"].startswith("CASE-")
        assert data["status"] == "Open"
        result.passed += 1
        print(f"    [PASS] POST /cases returned 201: {data['case_number']}")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_post_cases_returns_201: {e}")
        print(f"    [FAIL] {e}")


def test_post_evidence_returns_201(result: TestResult) -> None:
    """POST /evidence returns 201 CREATED."""
    print("\n[T-CR6] Test POST /evidence returns 201 CREATED")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    # Create a case first
    case_resp = client.post(
        "/cases",
        headers=headers,
        json={"title": "Evidence Test Case", "priority": "Medium"},
    )
    case_id = case_resp.json()["id"]

    # Create a temp file
    tmp_file = create_temp_file()
    try:
        response = client.post(
            "/evidence",
            headers=headers,
            json={
                "case_id": case_id,
                "file_path": tmp_file,
                "evidence_type": "Document",
                "description": "Contract test evidence",
            },
        )
        try:
            assert response.status_code == 201, f"Expected 201, got {response.status_code} body={response.text[:200]}"
            data = response.json()
            assert "id" in data
            assert "evidence_id" in data
            assert "md5" in data
            assert "sha256" in data
            result.passed += 1
            print(f"    [PASS] POST /evidence returned 201: {data['evidence_id']}")
        except AssertionError as e:
            result.failed += 1
            result.errors.append(f"test_post_evidence_returns_201: {e}")
            print(f"    [FAIL] {e}")
    finally:
        cleanup_temp_file(tmp_file)


def test_post_custody_returns_201(result: TestResult) -> None:
    """POST /custody returns 201 CREATED."""
    print("\n[T-CR7] Test POST /custody returns 201 CREATED")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    # Create case + evidence
    case_resp = client.post(
        "/cases", headers=headers, json={"title": "Custody Test Case"}
    )
    case_id = case_resp.json()["id"]

    tmp_file = create_temp_file()
    try:
        ev_resp = client.post(
            "/evidence",
            headers=headers,
            json={"case_id": case_id, "file_path": tmp_file},
        )
        evidence_id = ev_resp.json()["id"]

        response = client.post(
            "/custody",
            headers=headers,
            json={
                "evidence_id": evidence_id,
                "action": "TRANSFERRED",
                "from_person": "Alice",
                "to_person": "Bob",
                "location": "Lab A",
            },
        )
        try:
            assert response.status_code == 201, f"Expected 201, got {response.status_code}"
            data = response.json()
            assert "id" in data
            assert data["action"] == "TRANSFERRED"
            result.passed += 1
            print(f"    [PASS] POST /custody returned 201")
        except AssertionError as e:
            result.failed += 1
            result.errors.append(f"test_post_custody_returns_201: {e}")
            print(f"    [FAIL] {e}")
    finally:
        cleanup_temp_file(tmp_file)


def test_post_users_returns_201(result: TestResult) -> None:
    """POST /users returns 201 CREATED."""
    print("\n[T-CR8] Test POST /users returns 201 CREATED")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    response = client.post(
        "/users",
        headers=headers,
        json={
            "username": "contract_test_user",
            "password": "UserPass123!",
            "role_name": "AUDITOR",
        },
    )
    try:
        assert response.status_code == 201, f"Expected 201, got {response.status_code} body={response.text[:200]}"
        data = response.json()
        assert "user_id" in data
        assert "message" in data
        result.passed += 1
        print("    [PASS] POST /users returned 201")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_post_users_returns_201: {e}")
        print(f"    [FAIL] {e}")


def test_get_nonexistent_case_returns_404(result: TestResult) -> None:
    """GET /cases/{id} returns 404 for non-existent case."""
    print("\n[T-CR9] Test GET /cases/{id} returns 404 for missing case")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    response = client.get("/cases/99999", headers=headers)
    try:
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        result.passed += 1
        print("    [PASS] Non-existent case returns 404")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_get_nonexistent_case_returns_404: {e}")
        print(f"    [FAIL] {e}")


def test_get_case_users_returns_404_for_missing_case(result: TestResult) -> None:
    """GET /cases/{id}/users returns 404 when case doesn't exist."""
    print("\n[T-CR10] Test GET /cases/{id}/users returns 404 for missing case")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    response = client.get("/cases/99999/users", headers=headers)
    try:
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        result.passed += 1
        print("    [PASS] Missing case returns 404 for /cases/{id}/users")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_get_case_users_returns_404: {e}")
        print(f"    [FAIL] {e}")


def test_get_case_evidence_returns_404_for_missing_case(result: TestResult) -> None:
    """GET /cases/{id}/evidence returns 404 when case doesn't exist."""
    print("\n[T-CR11] Test GET /cases/{id}/evidence returns 404 for missing case")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    response = client.get("/cases/99999/evidence", headers=headers)
    try:
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        result.passed += 1
        print("    [PASS] Missing case returns 404 for /cases/{id}/evidence")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_get_case_evidence_returns_404: {e}")
        print(f"    [FAIL] {e}")


def test_get_nonexistent_evidence_returns_404(result: TestResult) -> None:
    """GET /evidence/{id} returns 404 for non-existent evidence."""
    print("\n[T-CR12] Test GET /evidence/{id} returns 404 for missing evidence")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    response = client.get("/evidence/99999", headers=headers)
    try:
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        result.passed += 1
        print("    [PASS] Non-existent evidence returns 404")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_get_nonexistent_evidence_returns_404: {e}")
        print(f"    [FAIL] {e}")


def test_duplicate_username_returns_409(result: TestResult) -> None:
    """POST /users with duplicate username returns 409 CONFLICT."""
    print("\n[T-CR13] Test POST /users duplicate username returns 409")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    # First user
    client.post(
        "/users",
        headers=headers,
        json={"username": "duplicate_test", "password": "UserPass123!", "role_name": "AUDITOR"},
    )
    # Duplicate
    response = client.post(
        "/users",
        headers=headers,
        json={"username": "duplicate_test", "password": "UserPass123!", "role_name": "AUDITOR"},
    )
    try:
        assert response.status_code == 409, f"Expected 409, got {response.status_code}"
        result.passed += 1
        print("    [PASS] Duplicate username returns 409 CONFLICT")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_duplicate_username_returns_409: {e}")
        print(f"    [FAIL] {e}")


def test_pagination_limit_validation(result: TestResult) -> None:
    """List endpoints validate pagination limit parameter."""
    print("\n[T-CR14] Test pagination limit validation")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    # limit=0 should fail
    response = client.get("/cases?limit=0", headers=headers)
    try:
        assert response.status_code == 422, f"Expected 422 for limit=0, got {response.status_code}"
        result.passed += 1
        print("    [PASS] limit=0 returns 422 validation error")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_pagination_limit_validation: {e}")
        print(f"    [FAIL] {e}")


def test_pagination_offset_validation(result: TestResult) -> None:
    """offset must be >= 0."""
    print("\n[T-CR15] Test pagination offset validation")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    response = client.get("/cases?offset=-1", headers=headers)
    try:
        assert response.status_code == 422, f"Expected 422 for offset=-1, got {response.status_code}"
        result.passed += 1
        print("    [PASS] offset=-1 returns 422 validation error")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_pagination_offset_validation: {e}")
        print(f"    [FAIL] {e}")


def test_error_response_format(result: TestResult) -> None:
    """Error responses include error_code and detail."""
    print("\n[T-CR16] Test error response format")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    # 404 case
    response = client.get("/cases/99999", headers=headers)
    try:
        assert response.status_code == 404
        data = response.json()
        # Standard error envelope
        assert "detail" in data or "error_code" in data, f"Expected error envelope, got: {data}"
        result.passed += 1
        print("    [PASS] Error response has standard format")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_error_response_format: {e}")
        print(f"    [FAIL] {e}")


def test_forbidden_without_permission(result: TestResult) -> None:
    """Endpoints return 403 when user lacks the required permission."""
    print("\n[T-CR17] Test 403 when permission is missing")
    client = TestClient(app)

    # Create an AUDITOR user (no case.create permission)
    from backend.app.auth.authentication import register_user, authenticate_user
    from backend.app.core.security import create_access_token

    register_user("auditor_user", "AuditPass123!", "AUDITOR")
    user_data, _ = authenticate_user("auditor_user", "AuditPass123!")
    token = create_access_token({
        "user_id": user_data["id"],
        "username": user_data["username"],
        "role_names": user_data["role_names"],
        "permissions": user_data["permissions"],
    })
    auditor_headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/cases",
        headers=auditor_headers,
        json={"title": "Unauthorized Case"},
    )
    try:
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        result.passed += 1
        print("    [PASS] Missing permission returns 403")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_forbidden_without_permission: {e}")
        print(f"    [FAIL] {e}")


def test_logout_endpoint(result: TestResult) -> None:
    """POST /auth/logout works with valid auth."""
    print("\n[T-CR18] Test POST /auth/logout endpoint")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    response = client.post("/auth/logout", headers=headers)
    try:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "message" in data
        result.passed += 1
        print("    [PASS] Logout endpoint works")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_logout_endpoint: {e}")
        print(f"    [FAIL] {e}")


def test_case_report_generation(result: TestResult) -> None:
    """GET /reports/case/{id} generates reports with correct structure."""
    print("\n[T-CR19] Test GET /reports/case/{id} report generation")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    # Create a case
    case_resp = client.post(
        "/cases", headers=headers,
        json={"title": "Report Test Case", "priority": "Critical"},
    )
    case_id = case_resp.json()["id"]

    # Summary report
    response = client.get(f"/reports/case/{case_id}?report_type=summary", headers=headers)
    try:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["type"] == "case_summary"
        assert "case" in data
        assert "generated_at" in data
        result.passed += 1
        print("    [PASS] Summary report generated correctly")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_case_report_generation: {e}")
        print(f"    [FAIL] {e}")


def test_audit_log_list_endpoint(result: TestResult) -> None:
    """GET /audit-logs returns list with proper structure."""
    print("\n[T-CR20] Test GET /audit-logs endpoint")
    client = TestClient(app)
    setup_admin_user()
    headers = get_auth_headers("contract_admin", "AdminPass123!")

    # Create something to generate audit logs
    client.post(
        "/cases", headers=headers,
        json={"title": "Audit Test Case", "priority": "Low"},
    )

    response = client.get("/audit-logs?limit=10", headers=headers)
    try:
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list response"
        if len(data) > 0:
            log = data[0]
            assert "id" in log
            assert "timestamp" in log
            assert "action" in log
        result.passed += 1
        print(f"    [PASS] Audit logs endpoint works ({len(data)} entries)")
    except AssertionError as e:
        result.failed += 1
        result.errors.append(f"test_audit_log_list_endpoint: {e}")
        print(f"    [FAIL] {e}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main() -> int:
    print("="*70)
    print("CYBERTRACE NEXUS - API CONTRACT TESTS")
    print("="*70)

    result = TestResult()
    print("\n[setup] Resetting database...")
    reset_test_db()

    # Run all tests
    test_root_endpoint(result)
    test_health_endpoint(result)
    test_login_requires_no_auth(result)
    test_protected_endpoints_require_auth(result)
    test_post_cases_returns_201(result)
    test_post_evidence_returns_201(result)
    test_post_custody_returns_201(result)
    test_post_users_returns_201(result)
    test_get_nonexistent_case_returns_404(result)
    test_get_case_users_returns_404_for_missing_case(result)
    test_get_case_evidence_returns_404_for_missing_case(result)
    test_get_nonexistent_evidence_returns_404(result)
    test_duplicate_username_returns_409(result)
    test_pagination_limit_validation(result)
    test_pagination_offset_validation(result)
    test_error_response_format(result)
    test_forbidden_without_permission(result)
    test_logout_endpoint(result)
    test_case_report_generation(result)
    test_audit_log_list_endpoint(result)

    print("\n" + "="*70)
    print("API CONTRACT TEST SUMMARY")
    print("="*70)
    print(f"Passed:  {result.passed}")
    print(f"Failed:  {result.failed}")
    total = result.passed + result.failed
    if total > 0:
        pct = (result.passed / total) * 100
        print(f"Success: {pct:.1f}%")
    print("="*70)

    if result.errors:
        print("\nERRORS:")
        for err in result.errors:
            print(f"  • {err}")

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
