"""
test_basic.py - Basic tests for CyberTrace Nexus.

Tests cover:
- Password hashing
- Authentication
- RBAC permission checks
- Case creation
- Evidence registration
- MD5/SHA-256 calculation
- Hash verification (success and mismatch)
- Custody event creation
- Audit logging
- Unauthorized access

CyberTrace Nexus evolved from the Digital Forensics Evidence Management System foundation.

Design notes:
- Each test resets the database to a known state (fresh database)
- Tests use the standard library only (pytest is not required)
- Run with: python tests/test_basic.py
"""

import os
import sys
import tempfile
import hashlib
import shutil
import datetime as dt
from pathlib import Path

# Add project root to path for imports (project root = 2 levels up from backend/tests/)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.database.database import initialize_database, get_connection, DB_PATH
from backend.app.auth.password_manager import hash_password, verify_password
from backend.app.auth.authorization import (
    DEFAULT_ROLE_PERMISSIONS,
    permissions_for_roles,
    has_permission,
    require_permission,
)
from backend.app.auth.authentication import (
    register_user,
    authenticate_user,
)
from backend.app.services.hashing import compute_hashes, verify_hashes, HashResult, VerificationResult
from backend.app.services.case_service import create_case, get_case, list_cases
from backend.app.services.evidence_service import register_evidence, verify_evidence, get_evidence
from backend.app.services.custody_service import add_custody_event, list_custody_for_evidence
from backend.app.services.audit_service import log_event, get_audit_logs


# ----------------------------------------------------------------------
# Test harness
# ----------------------------------------------------------------------

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []


def assert_eq(actual, expected, msg="") -> bool:
    if actual == expected:
        return True
    return False


def assert_true(value, msg="") -> bool:
    if value:
        return True
    return False


# ----------------------------------------------------------------------
# Test data setup
# ----------------------------------------------------------------------

def reset_database() -> None:
    """Reset the database to a fresh state for testing."""
    # Remove existing DB
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except OSError:
            pass

    # Also remove WAL/SHM if they exist
    for ext in ["-wal", "-shm"]:
        p = Path(str(DB_PATH) + ext)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass

    initialize_database()


def create_temp_test_file(content: bytes = None) -> str:
    """Create a temporary test file and return its absolute path."""
    if content is None:
        content = b"Sample test file content for forensic evidence testing.\n" * 50
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as f:
        f.write(content)
        return f.name


def cleanup_temp_file(path: str) -> None:
    """Remove a temporary file if it still exists."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


# ----------------------------------------------------------------------
# Test functions
# ----------------------------------------------------------------------

def test_password_hashing(result: TestResult) -> None:
    """Test that password hashing and verification work correctly."""
    print("\n[T1] Test password hashing")
    try:
        salt, hash_hex = hash_password("TestPassword123!")
        if not salt or not hash_hex:
            raise AssertionError("hash_password returned empty values")

        # Verify the password matches
        if not verify_password("TestPassword123!", salt, hash_hex):
            raise AssertionError("Password verification failed for correct password")

        # Verify wrong password doesn't match
        if verify_password("WrongPassword", salt, hash_hex):
            raise AssertionError("Wrong password was incorrectly verified")

        result.passed += 1
        print("    [PASS] Password hashing and verification works correctly")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_password_hashing: {e}")
        print(f"    [FAIL] {e}")


def test_rbac_permissions(result: TestResult) -> None:
    """Test role-based access control permissions."""
    print("\n[T2] Test RBAC permissions")
    try:
        # Test ADMINISTRATOR has all permissions
        admin_perms = permissions_for_roles(["ADMINISTRATOR"])
        if not has_permission(admin_perms, "case.create"):
            raise AssertionError("ADMINISTRATOR missing case.create")
        if not has_permission(admin_perms, "user.create"):
            raise AssertionError("ADMINISTRATOR missing user.create")
        if not has_permission(admin_perms, "system.manage"):
            raise AssertionError("ADMINISTRATOR missing system.manage")

        # Test AUDITOR has only read permissions
        auditor_perms = permissions_for_roles(["AUDITOR"])
        if not has_permission(auditor_perms, "case.view"):
            raise AssertionError("AUDITOR missing case.view")
        if has_permission(auditor_perms, "case.create"):
            raise AssertionError("AUDITOR should not have case.create")
        if has_permission(auditor_perms, "user.create"):
            raise AssertionError("AUDITOR should not have user.create")

        # Test CASE INVESTIGATOR permissions
        investigator_perms = permissions_for_roles(["CASE INVESTIGATOR"])
        if not has_permission(investigator_perms, "case.create"):
            raise AssertionError("CASE INVESTIGATOR missing case.create")
        if has_permission(investigator_perms, "system.manage"):
            raise AssertionError("CASE INVESTIGATOR should not have system.manage")

        # Test require_permission raises on missing permission
        try:
            require_permission(auditor_perms, "case.create")
            raise AssertionError("require_permission should have raised on missing perm")
        except PermissionError:
            pass  # Expected

        result.passed += 1
        print("    [PASS] RBAC permission checks work correctly")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_rbac_permissions: {e}")
        print(f"    [FAIL] {e}")


def test_user_registration_and_auth(result: TestResult) -> None:
    """Test user registration and authentication."""
    print("\n[T3] Test user registration and authentication")
    try:
        # Create a test user
        user = register_user("test_user", "TestPass123!", "CASE INVESTIGATOR")
        if user["username"] != "test_user":
            raise AssertionError("Username mismatch")
        if user["role_name"] != "CASE INVESTIGATOR":
            raise AssertionError("Role mismatch")

        # Authenticate with correct password
        user_data, session_data = authenticate_user("test_user", "TestPass123!")
        if user_data["username"] != "test_user":
            raise AssertionError("Auth returned wrong username")
        if "CASE INVESTIGATOR" not in user_data["role_names"]:
            raise AssertionError("Auth returned wrong roles")

        # Authenticate with wrong password
        try:
            authenticate_user("test_user", "WrongPassword")
            raise AssertionError("Wrong password should fail")
        except ValueError:
            pass  # Expected

        # Authenticate non-existent user
        try:
            authenticate_user("nonexistent_user", "anything")
            raise AssertionError("Non-existent user should fail")
        except ValueError:
            pass  # Expected

        result.passed += 1
        print("    [PASS] User registration and authentication work correctly")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_user_registration_and_auth: {e}")
        print(f"    [FAIL] {e}")


def test_hashing(result: TestResult) -> None:
    """Test MD5 and SHA-256 hash calculation."""
    print("\n[T4] Test hashing")
    tmp_file = None
    try:
        # Create test file
        content = b"Test data for hashing"
        tmp_file = create_temp_test_file(content)

        # Compute hashes via our service
        result_hash = compute_hashes(tmp_file)

        # Compare with hashlib directly
        with open(tmp_file, "rb") as f:
            data = f.read()
        expected_md5 = hashlib.md5(data).hexdigest()
        expected_sha256 = hashlib.sha256(data).hexdigest()

        if result_hash.md5 != expected_md5:
            raise AssertionError(f"MD5 mismatch: {result_hash.md5} != {expected_md5}")
        if result_hash.sha256 != expected_sha256:
            raise AssertionError(f"SHA-256 mismatch: {result_hash.sha256} != {expected_sha256}")

        result.passed += 1
        print(f"    [PASS] MD5 and SHA-256 calculated correctly")
        print(f"      MD5: {result_hash.md5}")
        print(f"      SHA-256: {result_hash.sha256}")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_hashing: {e}")
        print(f"    [FAIL] {e}")
    finally:
        if tmp_file:
            cleanup_temp_file(tmp_file)


def test_hash_verification(result: TestResult) -> None:
    """Test hash verification (success and mismatch)."""
    print("\n[T5] Test hash verification")
    tmp_file = None
    try:
        tmp_file = create_temp_test_file(b"Original content for hash verification test")
        hashes = compute_hashes(tmp_file)

        # Verify with correct hashes (should match)
        v1 = verify_hashes(tmp_file, hashes.md5, hashes.sha256)
        if not v1.all_match:
            raise AssertionError("Hash verification failed for matching file")

        # Now modify the file and re-verify (should mismatch)
        with open(tmp_file, "wb") as f:
            f.write(b"Modified content - hash should mismatch now")
        v2 = verify_hashes(tmp_file, hashes.md5, hashes.sha256)
        if v2.all_match:
            raise AssertionError("Hash verification passed for modified file")
        if v2.md5_match:
            raise AssertionError("MD5 incorrectly matched for modified file")
        if v2.sha256_match:
            raise AssertionError("SHA-256 incorrectly matched for modified file")

        result.passed += 1
        print("    [PASS] Hash verification correctly detects matches and mismatches")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_hash_verification: {e}")
        print(f"    [FAIL] {e}")
    finally:
        if tmp_file:
            cleanup_temp_file(tmp_file)


def test_case_creation(result: TestResult) -> None:
    """Test case creation and listing."""
    print("\n[T6] Test case creation")
    try:
        # Create admin user
        register_user("admin_user", "AdminPass123!", "ADMINISTRATOR")
        user_data, _ = authenticate_user("admin_user", "AdminPass123!")

        # Create a case
        case = create_case(
            title="Test Case - Phishing Investigation",
            incident_date="2025-08-15",
            priority="High",
            description="Test case for unit testing.",
            created_by=user_data["id"],
        )
        if not case.case_number:
            raise AssertionError("Case number not generated")
        if case.status != "Open":
            raise AssertionError(f"New case should be Open, got {case.status}")

        # Get case by ID
        retrieved = get_case(case.id)
        if retrieved.id != case.id:
            raise AssertionError("Case retrieval failed")
        if retrieved.title != case.title:
            raise AssertionError("Case title mismatch")

        # List cases
        all_cases = list_cases()
        if len(all_cases) < 1:
            raise AssertionError("Case not in list")

        result.passed += 1
        print(f"    [PASS] Case creation works correctly: {case.case_number}")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_case_creation: {e}")
        print(f"    [FAIL] {e}")


def test_evidence_registration(result: TestResult) -> None:
    """Test evidence registration with file hashing."""
    print("\n[T7] Test evidence registration")
    tmp_file = None
    try:
        # Create user and case
        register_user("test_inv", "InvPass123!", "CASE INVESTIGATOR")
        user_data, _ = authenticate_user("test_inv", "InvPass123!")

        case = create_case(
            title="Evidence Test Case",
            incident_date="2025-08-15",
            priority="Medium",
            description="Test case for evidence.",
            created_by=user_data["id"],
        )

        # Create test file
        tmp_file = create_temp_test_file(b"Sample evidence content")

        # Register evidence
        evidence = register_evidence(
            case_id=case.id,
            file_path=tmp_file,
            evidence_type="Document",
            description="Test evidence for unit test",
            source="Test",
            registered_by=user_data["id"],
        )
        if not evidence.evidence_id:
            raise AssertionError("Evidence ID not generated")
        if not evidence.md5 or not evidence.sha256:
            raise AssertionError("Hashes not calculated")

        # Retrieve evidence
        retrieved = get_evidence(evidence.id)
        if retrieved.id != evidence.id:
            raise AssertionError("Evidence retrieval failed")
        if retrieved.evidence_id != evidence.evidence_id:
            raise AssertionError("Evidence ID mismatch")

        result.passed += 1
        print(f"    [PASS] Evidence registration works: {evidence.evidence_id}")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_evidence_registration: {e}")
        print(f"    [FAIL] {e}")
    finally:
        if tmp_file:
            cleanup_temp_file(tmp_file)


def test_custody_events(result: TestResult) -> None:
    """Test chain of custody event creation."""
    print("\n[T8] Test custody events")
    tmp_file = None
    try:
        register_user("cust_user", "CustPass123!", "EVIDENCE CUSTODIAN")
        user_data, _ = authenticate_user("cust_user", "CustPass123!")

        case = create_case(
            title="Custody Test",
            incident_date="2025-08-15",
            priority="Low",
            description="Test case for custody events.",
            created_by=user_data["id"],
        )

        tmp_file = create_temp_test_file(b"Test data for custody")
        evidence = register_evidence(
            case_id=case.id,
            file_path=tmp_file,
            registered_by=user_data["id"],
        )

        # Add a TRANSFERRED event
        event_id = add_custody_event(
            evidence_id=evidence.id,
            action="TRANSFERRED",
            from_person="Alice",
            to_person="Bob",
            location="Lab 1",
            notes="Test transfer",
            case_id=case.id,
            recorded_by=user_data["id"],
        )
        if not event_id:
            raise AssertionError("Custody event not created")

        # List custody events
        events = list_custody_for_evidence(evidence.id)
        if len(events) < 2:  # REGISTERED + TRANSFERRED
            raise AssertionError(f"Expected at least 2 custody events, got {len(events)}")

        result.passed += 1
        print(f"    [PASS] Custody events created correctly ({len(events)} events)")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_custody_events: {e}")
        print(f"    [FAIL] {e}")
    finally:
        if tmp_file:
            cleanup_temp_file(tmp_file)


def test_audit_logging(result: TestResult) -> None:
    """Test audit log functionality."""
    print("\n[T9] Test audit logging")
    try:
        register_user("audit_user", "AuditPass123!", "AUDITOR")
        user_data, _ = authenticate_user("audit_user", "AuditPass123!")

        # Log a custom event
        log_event(
            action="TEST_ACTION",
            user_id=user_data["id"],
            description="Test audit log entry",
        )

        # Verify it's in the log
        logs = get_audit_logs(limit=10)
        test_logs = [l for l in logs if l["action"] == "TEST_ACTION"]
        if not test_logs:
            raise AssertionError("Test audit log entry not found")

        result.passed += 1
        print("    [PASS] Audit logging works correctly")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_audit_logging: {e}")
        print(f"    [FAIL] {e}")


def test_unauthorized_access(result: TestResult) -> None:
    """Test that unauthorized operations are rejected."""
    print("\n[T10] Test unauthorized access")
    try:
        # Reset to clean state
        reset_database()
        register_user("low_user", "LowPass123!", "AUDITOR")
        user_data, _ = authenticate_user("low_user", "LowPass123!")

        # AUDITOR should not be able to create cases
        auditor_perms = permissions_for_roles(["AUDITOR"])
        if has_permission(auditor_perms, "case.create"):
            raise AssertionError("AUDITOR should not have case.create")

        # require_permission should raise
        try:
            require_permission(auditor_perms, "case.create")
            raise AssertionError("require_permission should raise for AUDITOR")
        except PermissionError:
            pass  # Expected

        # AUDITOR should not be able to create users
        if has_permission(auditor_perms, "user.create"):
            raise AssertionError("AUDITOR should not have user.create")

        result.passed += 1
        print("    [PASS] Unauthorized access correctly rejected")
    except Exception as e:
        result.failed += 1
        result.errors.append(f"test_unauthorized_access: {e}")
        print(f"    [FAIL] {e}")


# ----------------------------------------------------------------------
# Test runner
# ----------------------------------------------------------------------

def main() -> int:
    print("="*70)
    print("DIGITAL FORENSICS FRAMEWORK - TEST SUITE")
    print("="*70)

    result = TestResult()

    # Reset database once before all tests
    print("\n[setup] Resetting database to clean state...")
    reset_database()

    # Run all tests
    test_password_hashing(result)
    test_rbac_permissions(result)
    test_user_registration_and_auth(result)
    test_hashing(result)
    test_hash_verification(result)
    test_case_creation(result)
    test_evidence_registration(result)
    test_custody_events(result)
    test_audit_logging(result)
    test_unauthorized_access(result)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
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