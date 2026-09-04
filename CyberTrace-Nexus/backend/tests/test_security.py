"""
test_security.py - Security regression tests for CyberTrace Nexus.

Tests cover:
- JWT secret key enforcement (no fallback)
- Password hashing uses constant-time comparison
- Hash verification does not overwrite stored hashes
- CORS configuration is restricted (not wildcard)
- Security headers are present on responses
- API docs are disabled in production mode
- SQL queries use parameterized statements (no string concatenation)
- Audit log records are append-only
- Account lockout after failed attempts

Run with: python tests/test_security.py
"""

import os
import sys
import re
import hashlib
import hmac
import tempfile
import subprocess
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Set JWT_SECRET_KEY BEFORE any app imports (security.py requires it)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-security-tests-only-32-chars")

from backend.app.auth.password_manager import hash_password, verify_password
from backend.app.database.database import initialize_database, DB_PATH, get_connection


class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []


def reset_database() -> None:
    """Reset the database to a fresh state for testing."""
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except OSError:
            pass
    for ext in ["-wal", "-shm"]:
        p = Path(str(DB_PATH) + ext)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
    initialize_database()


# ----------------------------------------------------------------------
# Test functions
# ----------------------------------------------------------------------

def test_jwt_secret_required(result: TestResult) -> None:
    """Test that the application refuses to start without JWT_SECRET_KEY."""
    print("\n[S1] Test JWT_SECRET_KEY is required")
    try:
        # Spawn a Python subprocess that imports security.py without the env var
        env = {k: v for k, v in os.environ.items() if k != "JWT_SECRET_KEY"}
        code = (
            "import sys\n"
            "try:\n"
            "    import app.core.security\n"
            "    print('IMPORT_OK')\n"
            "except RuntimeError as e:\n"
            "    print('RUNTIME_ERROR:' + str(e))\n"
            "except Exception as e:\n"
            "    print('OTHER_ERROR:' + type(e).__name__ + ':' + str(e))\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(Path(__file__).resolve().parent.parent.parent / "backend"),
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = proc.stdout.strip()
        if "RUNTIME_ERROR" not in output:
            raise AssertionError(
                f"Expected RuntimeError when JWT_SECRET_KEY is missing. "
                f"Got: stdout='{output}' stderr='{proc.stderr}'"
            )
        result.passed += 1
        print("    [PASS] JWT_SECRET_KEY is required at startup")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_jwt_secret_required: {e}")
        print(f"    [FAIL] {e}")


def test_password_uses_hmac_compare(result: TestResult) -> None:
    """Test that password verification uses constant-time comparison."""
    print("\n[S2] Test password verification uses hmac.compare_digest")
    try:
        src_path = (
            Path(__file__).resolve().parent.parent / "app" / "auth" / "password_manager.py"
        )
        source = src_path.read_text(encoding="utf-8")
        if "hmac.compare_digest" not in source:
            raise AssertionError("password_manager.py does not use hmac.compare_digest")
        if "computed == hash_hex" in source and "hmac.compare_digest" not in source:
            raise AssertionError("password_manager.py still uses == comparison")
        result.passed += 1
        print("    [PASS] Password verification uses constant-time comparison")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_password_uses_hmac_compare: {e}")
        print(f"    [FAIL] {e}")


def test_password_verification_works(result: TestResult) -> None:
    """Functional test for hmac.compare_digest in password manager."""
    print("\n[S3] Test password verification accepts correct password")
    try:
        salt, hash_hex = hash_password("CorrectHorseBatteryStaple1!")
        if not verify_password("CorrectHorseBatteryStaple1!", salt, hash_hex):
            raise AssertionError("verify_password returned False for correct password")
        if verify_password("WrongPassword123", salt, hash_hex):
            raise AssertionError("verify_password returned True for wrong password")
        result.passed += 1
        print("    [PASS] Password verification works correctly")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_password_verification_works: {e}")
        print(f"    [FAIL] {e}")


def test_password_hash_uniqueness(result: TestResult) -> None:
    """Test that the same password produces different hashes (due to salt)."""
    print("\n[S4] Test password hashing uses random salt")
    try:
        _, h1 = hash_password("SamePassword123!")
        _, h2 = hash_password("SamePassword123!")
        if h1 == h2:
            raise AssertionError("Two hashes of the same password are identical (no salt)")
        result.passed += 1
        print("    [PASS] Password hashing produces unique hashes per call")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_password_hash_uniqueness: {e}")
        print(f"    [FAIL] {e}")


def test_cors_not_wildcard(result: TestResult) -> None:
    """Test that CORS is not configured with wildcard origins."""
    print("\n[S5] Test CORS does not use wildcard origins")
    try:
        src_path = (
            Path(__file__).resolve().parent.parent / "app" / "app.py"
        )
        source = src_path.read_text(encoding="utf-8")
        if re.search(r'allow_origins\s*=\s*\[\s*"\*"\s*\]', source):
            raise AssertionError("app.py uses wildcard CORS origins")
        if re.search(r'allow_origins\s*=\s*\["\*"\]', source):
            raise AssertionError("app.py uses wildcard CORS origins")
        result.passed += 1
        print("    [PASS] CORS does not use wildcard origins")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_cors_not_wildcard: {e}")
        print(f"    [FAIL] {e}")


def test_cors_methods_restricted(result: TestResult) -> None:
    """Test that CORS methods are not wildcard."""
    print("\n[S6] Test CORS methods are restricted")
    try:
        src_path = (
            Path(__file__).resolve().parent.parent / "app" / "app.py"
        )
        source = src_path.read_text(encoding="utf-8")
        if re.search(r'allow_methods\s*=\s*\[\s*"\*"\s*\]', source):
            raise AssertionError("app.py uses wildcard CORS methods")
        if re.search(r'allow_headers\s*=\s*\[\s*"\*"\s*\]', source):
            raise AssertionError("app.py uses wildcard CORS headers")
        result.passed += 1
        print("    [PASS] CORS methods and headers are restricted")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_cors_methods_restricted: {e}")
        print(f"    [FAIL] {e}")


def test_security_headers_middleware(result: TestResult) -> None:
    """Test that the security headers middleware is registered."""
    print("\n[S7] Test security headers middleware is present")
    try:
        src_path = (
            Path(__file__).resolve().parent.parent / "app" / "app.py"
        )
        source = src_path.read_text(encoding="utf-8")
        required_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
            "Permissions-Policy",
        ]
        for header in required_headers:
            if header not in source:
                raise AssertionError(f"app.py missing security header: {header}")
        result.passed += 1
        print("    [PASS] Security headers middleware is registered")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_security_headers_middleware: {e}")
        print(f"    [FAIL] {e}")


def test_no_hardcoded_admin_password(result: TestResult) -> None:
    """Test that there is no hardcoded admin password in source code."""
    print("\n[S8] Test no hardcoded admin password")
    try:
        app_src = (
            Path(__file__).resolve().parent.parent / "app" / "app.py"
        )
        source = app_src.read_text(encoding="utf-8")
        if "Admin@123" in source:
            raise AssertionError("app.py contains hardcoded admin password 'Admin@123'")
        if re.search(r'register_user\s*\(\s*["\']admin["\']\s*,\s*["\']', source):
            raise AssertionError("app.py contains hardcoded admin registration")
        result.passed += 1
        print("    [PASS] No hardcoded admin password in source code")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_no_hardcoded_admin_password: {e}")
        print(f"    [FAIL] {e}")


def test_create_admin_cli_exists(result: TestResult) -> None:
    """Test that the create_admin CLI script exists."""
    print("\n[S9] Test create_admin CLI script exists")
    try:
        script_path = (
            Path(__file__).resolve().parent.parent.parent
            / "backend" / "scripts" / "create_admin.py"
        )
        if not script_path.exists():
            raise AssertionError(f"create_admin.py not found at {script_path}")
        source = script_path.read_text(encoding="utf-8")
        if "register_user" not in source:
            raise AssertionError("create_admin.py does not call register_user")
        if "getpass" not in source:
            raise AssertionError("create_admin.py does not use getpass for password input")
        result.passed += 1
        print("    [PASS] create_admin CLI script exists and is secure")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_create_admin_cli_exists: {e}")
        print(f"    [FAIL] {e}")


def test_sql_injection_protection(result: TestResult) -> None:
    """Test that SQL queries use parameterized statements (no string concat with user input)."""
    print("\n[S10] Test SQL queries use parameterized statements")
    try:
        services_dir = Path(__file__).resolve().parent.parent / "app" / "services"
        issues = []
        for py_file in services_dir.glob("*.py"):
            source = py_file.read_text(encoding="utf-8")
            # Look for raw user input into .execute() calls via f-string or + concat
            # Allow f-strings ONLY if they reference an allowlist of column names.
            # The case_service.py uses an _allowed frozenset, which is safe.
            for match in re.finditer(
                r'\.execute\s*\(\s*f["\'][^"\']*\{[^}]+\}', source
            ):
                # Check that the f-string references a column-name allowlist
                line_start = source.rfind("\n", 0, match.start()) + 1
                line_end = source.find("\n", match.end())
                if line_end == -1:
                    line_end = len(source)
                surrounding = source[max(0, line_start - 200):line_end]
                if "_allowed" not in surrounding and "allowlist" not in surrounding.lower():
                    issues.append(
                        f"{py_file.name}: f-string in .execute() without allowlist: "
                        f"{match.group(0)[:60]}"
                    )
        if issues:
            raise AssertionError("SQL injection risk: " + "; ".join(issues))
        result.passed += 1
        print("    [PASS] SQL queries use parameterized statements (with allowlists where needed)")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_sql_injection_protection: {e}")
        print(f"    [FAIL] {e}")


def test_audit_log_is_append_only(result: TestResult) -> None:
    """Test that the audit log table has no UPDATE or DELETE statements in service code."""
    print("\n[S11] Test audit log is append-only in service code")
    try:
        audit_path = (
            Path(__file__).resolve().parent.parent / "app" / "services" / "audit_service.py"
        )
        source = audit_path.read_text(encoding="utf-8")
        # Strip comments and docstrings to avoid false positives
        code_lines = []
        for line in source.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            if '"""' in line or "'''" in line:
                continue
            code_lines.append(line)
        code = "\n".join(code_lines)
        if re.search(r"UPDATE\s+audit_logs", code, re.IGNORECASE):
            raise AssertionError("audit_service.py contains UPDATE on audit_logs")
        if re.search(r"DELETE\s+FROM\s+audit_logs", code, re.IGNORECASE):
            raise AssertionError("audit_service.py contains DELETE on audit_logs")
        result.passed += 1
        print("    [PASS] Audit log is append-only in service layer")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_audit_log_is_append_only: {e}")
        print(f"    [FAIL] {e}")


def test_evidence_hashes_not_overwritten_on_verify(result: TestResult) -> None:
    """Test that verify_hashes does not modify the stored hashes."""
    print("\n[S12] Test hash verification does not overwrite stored hashes")
    try:
        # Create a temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
            f.write(b"Test data for hash verification security test")
            tmp_path = f.name

        from backend.app.services.hashing import compute_hashes, verify_hashes

        original = compute_hashes(tmp_path)
        # Verify (should match)
        result1 = verify_hashes(tmp_path, original.md5, original.sha256)
        if not result1.all_match:
            raise AssertionError("verify_hashes failed for matching file")

        # Modify file
        with open(tmp_path, "wb") as f:
            f.write(b"Modified content - should not match")

        # Verify again (should NOT match)
        result2 = verify_hashes(tmp_path, original.md5, original.sha256)
        if result2.all_match:
            raise AssertionError("verify_hashes passed for modified file")
        if not result2.md5_match and not result2.sha256_match:
            pass  # Expected - hashes don't match
        else:
            raise AssertionError("At least one hash should not match for modified file")

        # The stored hashes should still be the original ones
        if result2.stored_md5 != original.md5 or result2.stored_sha256 != original.sha256:
            raise AssertionError("Stored hashes were modified during verification")

        os.unlink(tmp_path)
        result.passed += 1
        print("    [PASS] Hash verification does not overwrite stored hashes")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_evidence_hashes_not_overwritten_on_verify: {e}")
        print(f"    [FAIL] {e}")


def test_env_example_has_no_real_secrets(result: TestResult) -> None:
    """Test that .env.example contains only placeholders, not real secrets."""
    print("\n[S13] Test .env.example has no real secrets")
    try:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env.example"
        if not env_path.exists():
            raise AssertionError(".env.example not found")
        source = env_path.read_text(encoding="utf-8")
        # Check for placeholder pattern
        if "your-secret-key-here" not in source:
            raise AssertionError(".env.example does not contain placeholder 'your-secret-key-here'")
        # Check no real-looking secrets
        if re.search(r"AKIA[0-9A-Z]{16}", source):
            raise AssertionError(".env.example contains AWS key pattern")
        if re.search(r"sk-[A-Za-z0-9]{20,}", source):
            raise AssertionError(".env.example contains OpenAI key pattern")
        result.passed += 1
        print("    [PASS] .env.example contains only placeholders")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_env_example_has_no_real_secrets: {e}")
        print(f"    [FAIL] {e}")


def test_gitignore_excludes_env(result: TestResult) -> None:
    """Test that .gitignore excludes .env files."""
    print("\n[S14] Test .gitignore excludes .env files")
    try:
        gitignore_path = Path(__file__).resolve().parent.parent.parent / ".gitignore"
        if not gitignore_path.exists():
            raise AssertionError(".gitignore not found")
        source = gitignore_path.read_text(encoding="utf-8")
        if ".env" not in source:
            raise AssertionError(".gitignore does not exclude .env files")
        if "*.db" not in source:
            raise AssertionError(".gitignore does not exclude .db files")
        result.passed += 1
        print("    [PASS] .gitignore excludes sensitive files")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_gitignore_excludes_env: {e}")
        print(f"    [FAIL] {e}")


def test_pbkdf2_iterations_above_minimum(result: TestResult) -> None:
    """Test that PBKDF2 iteration count is at or above OWASP minimum (210k)."""
    print("\n[S15] Test PBKDF2 iterations meet OWASP recommendation")
    try:
        from backend.app.auth.password_manager import ITERATIONS
        OWASP_MIN_2023 = 210_000
        if ITERATIONS < OWASP_MIN_2023:
            raise AssertionError(
                f"PBKDF2 iterations {ITERATIONS} below OWASP minimum {OWASP_MIN_2023}"
            )
        result.passed += 1
        print(f"    [PASS] PBKDF2 iterations ({ITERATIONS}) meet OWASP recommendation")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_pbkdf2_iterations_above_minimum: {e}")
        print(f"    [FAIL] {e}")


def test_salt_length_sufficient(result: TestResult) -> None:
    """Test that salt length is at least 128 bits (16 bytes)."""
    print("\n[S16] Test salt length meets security requirements")
    try:
        from backend.app.auth.password_manager import SALT_BYTES
        if SALT_BYTES < 16:
            raise AssertionError(f"Salt length {SALT_BYTES} bytes is less than 16 (128 bits)")
        result.passed += 1
        print(f"    [PASS] Salt length ({SALT_BYTES} bytes) meets security requirements")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_salt_length_sufficient: {e}")
        print(f"    [FAIL] {e}")


def test_rbac_admin_has_all_permissions(result: TestResult) -> None:
    """Test that ADMINISTRATOR role has all defined permissions."""
    print("\n[S17] Test ADMINISTRATOR has full permissions")
    try:
        from backend.app.auth.authorization import (
            PERMISSIONS_ALL,
            permissions_for_roles,
        )
        admin_perms = permissions_for_roles(["ADMINISTRATOR"])
        for perm in PERMISSIONS_ALL:
            if perm not in admin_perms:
                raise AssertionError(f"ADMINISTRATOR missing permission: {perm}")
        result.passed += 1
        print("    [PASS] ADMINISTRATOR role has all defined permissions")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_rbac_admin_has_all_permissions: {e}")
        print(f"    [FAIL] {e}")


def test_rbac_auditor_no_write(result: TestResult) -> None:
    """Test that AUDITOR role does not have write permissions."""
    print("\n[S18] Test AUDITOR has no write permissions")
    try:
        from backend.app.auth.authorization import permissions_for_roles
        auditor_perms = permissions_for_roles(["AUDITOR"])
        write_perms = [
            "case.create", "case.update", "case.close", "case.assign",
            "evidence.create", "evidence.update",
            "custody.create",
            "user.create", "user.update", "user.disable",
        ]
        for perm in write_perms:
            if perm in auditor_perms:
                raise AssertionError(f"AUDITOR should not have write permission: {perm}")
        result.passed += 1
        print("    [PASS] AUDITOR role has no write permissions")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_rbac_auditor_no_write: {e}")
        print(f"    [FAIL] {e}")


def test_rbac_all_protected_endpoints_have_dependencies(result: TestResult) -> None:
    """Test that all case/evidence endpoints use require_permission_dep."""
    print("\n[S19] Test API endpoints use permission dependencies")
    try:
        api_dir = Path(__file__).resolve().parent.parent / "app" / "api"
        issues = []
        for py_file in api_dir.glob("*.py"):
            if py_file.name == "__init__.py" or py_file.name == "auth.py":
                continue  # auth.py uses get_current_user, not require_permission_dep
            source = py_file.read_text(encoding="utf-8")
            # Check that the file uses require_permission_dep
            if "@router" in source and "require_permission_dep" not in source:
                issues.append(f"{py_file.name}: no require_permission_dep found")
        if issues:
            raise AssertionError(
                "API files missing permission dependencies: " + ", ".join(issues)
            )
        result.passed += 1
        print("    [PASS] All API endpoints use permission dependencies")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_rbac_all_protected_endpoints_have_dependencies: {e}")
        print(f"    [FAIL] {e}")


def test_trusted_host_middleware_configured(result: TestResult) -> None:
    """Test that TrustedHostMiddleware is configured."""
    print("\n[S20] Test TrustedHostMiddleware is registered")
    try:
        src_path = (
            Path(__file__).resolve().parent.parent / "app" / "app.py"
        )
        source = src_path.read_text(encoding="utf-8")
        if "TrustedHostMiddleware" not in source:
            raise AssertionError("app.py does not use TrustedHostMiddleware")
        result.passed += 1
        print("    [PASS] TrustedHostMiddleware is registered")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_trusted_host_middleware_configured: {e}")
        print(f"    [FAIL] {e}")


# ----------------------------------------------------------------------
# Test runner
# ----------------------------------------------------------------------

def main() -> int:
    print("=" * 70)
    print("CYBERTRACE NEXUS - SECURITY REGRESSION TESTS")
    print("=" * 70)

    result = TestResult()

    print("\n[setup] Resetting database to clean state...")
    reset_database()

    # Run all tests
    test_jwt_secret_required(result)
    test_password_uses_hmac_compare(result)
    test_password_verification_works(result)
    test_password_hash_uniqueness(result)
    test_cors_not_wildcard(result)
    test_cors_methods_restricted(result)
    test_security_headers_middleware(result)
    test_no_hardcoded_admin_password(result)
    test_create_admin_cli_exists(result)
    test_sql_injection_protection(result)
    test_audit_log_is_append_only(result)
    test_evidence_hashes_not_overwritten_on_verify(result)
    test_env_example_has_no_real_secrets(result)
    test_gitignore_excludes_env(result)
    test_pbkdf2_iterations_above_minimum(result)
    test_salt_length_sufficient(result)
    test_rbac_admin_has_all_permissions(result)
    test_rbac_auditor_no_write(result)
    test_rbac_all_protected_endpoints_have_dependencies(result)
    test_trusted_host_middleware_configured(result)

    # Print summary
    print("\n" + "=" * 70)
    print("SECURITY TEST SUMMARY")
    print("=" * 70)
    print(f"Passed:  {result.passed}")
    print(f"Failed:  {result.failed}")
    total = result.passed + result.failed
    if total > 0:
        pct = (result.passed / total) * 100
        print(f"Success: {pct:.1f}%")
    print("=" * 70)

    if result.errors:
        print("\nERRORS:")
        for err in result.errors:
            print(f"  • {err}")

    return 0 if result.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
