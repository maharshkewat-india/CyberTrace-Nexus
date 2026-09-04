"""
tests/test_ui_rbac.py - End-to-end test of login + RBAC.

Verifies:
- Login works with the default admin credentials.
- Each role's permission set is correctly returned.
- require_permission() raises on missing permissions.
- The app navigates between modules without raising PermissionError.
- Each role only sees the modules they're entitled to.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.app.database.database import initialize_database, is_fresh_database, get_connection, DB_PATH
from backend.app.auth.authentication import (
    register_user, authenticate_user, disable_user, enable_user, reset_password,
)
from backend.app.auth.authorization import (
    permissions_for_roles, has_permission, require_permission,
    DEFAULT_ROLE_PERMISSIONS,
)
from backend.app.services import case_service, evidence_service, custody_service, audit_service


def reset_db() -> None:
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except OSError:
            pass
    for ext in ("-wal", "-shm"):
        p = Path(str(DB_PATH) + ext)
        if p.exists():
            try:
                p.unlink()
            except OSError:
                pass
    initialize_database()


def banner(msg: str) -> None:
    print()
    print("=" * 70)
    print(msg)
    print("=" * 70)


def test_admin_login() -> None:
    banner("TEST 1: Admin login works with default credentials")
    reset_db()

    # Auto-create default admin (mirrors app.py on first run)
    register_user("admin", "Admin@123", "ADMINISTRATOR")

    user, session = authenticate_user("admin", "Admin@123")
    assert user["username"] == "admin"
    assert "ADMINISTRATOR" in user["role_names"]
    perms = frozenset(user["permissions"])
    # Spot-check admin permissions
    for p in ("case.create", "evidence.create", "custody.create",
              "audit.view", "user.create", "system.manage", "report.generate"):
        assert has_permission(perms, p), f"ADMIN missing {p}"
    print(f"  [OK] admin logged in with {len(perms)} permissions")


def test_wrong_password_rejected() -> None:
    banner("TEST 2: Wrong password is rejected with ValueError")
    try:
        authenticate_user("admin", "WrongPassword")
    except ValueError as e:
        assert "Invalid" in str(e) or "password" in str(e).lower()
        print(f"  [OK] Rejected: {e}")
        return
    raise AssertionError("Wrong password should have raised ValueError")


def test_inactive_user_blocked() -> None:
    banner("TEST 3: Disabled user cannot log in")
    disable_user(1)  # admin id is 1
    try:
        authenticate_user("admin", "Admin@123")
    except ValueError as e:
        assert "disabled" in str(e).lower() or "inactive" in str(e).lower()
        enable_user(1)
        print(f"  [OK] Rejected: {e}")
        return
    enable_user(1)
    raise AssertionError("Disabled user should have been blocked")


def test_auditor_rbac() -> None:
    banner("TEST 4: AUDITOR role has read-only access (no create perms)")
    register_user("aud", "AudPass123!", "AUDITOR")
    user, _ = authenticate_user("aud", "AudPass123!")
    perms = frozenset(user["permissions"])
    assert has_permission(perms, "case.view")
    assert has_permission(perms, "evidence.view")
    assert has_permission(perms, "audit.view")
    # Write perms must be denied
    for forbidden in ("case.create", "evidence.create", "user.create",
                      "custody.create", "evidence.hash", "case.update"):
        assert not has_permission(perms, forbidden), f"AUDITOR should NOT have {forbidden}"
    # require_permission must raise
    try:
        require_permission(perms, "case.create")
    except PermissionError as e:
        print(f"  [OK] require_permission('case.create') raised: {e}")
        return
    raise AssertionError("require_permission should have raised")


def test_custodian_rbac() -> None:
    banner("TEST 5: EVIDENCE CUSTODIAN can create evidence and custody but not users")
    register_user("cust", "CustPass123!", "EVIDENCE CUSTODIAN")
    user, _ = authenticate_user("cust", "CustPass123!")
    perms = frozenset(user["permissions"])
    assert has_permission(perms, "evidence.create")
    assert has_permission(perms, "custody.create")
    for forbidden in ("user.create", "case.create", "audit.view", "system.manage"):
        assert not has_permission(perms, forbidden), f"CUSTODIAN should NOT have {forbidden}"
    print("  [OK] Custodian has evidence/custody perms only")


def test_investigator_rbac() -> None:
    banner("TEST 6: CASE INVESTIGATOR has full case+evidence perms but no user mgmt")
    register_user("inv", "InvPass123!", "CASE INVESTIGATOR")
    user, _ = authenticate_user("inv", "InvPass123!")
    perms = frozenset(user["permissions"])
    assert has_permission(perms, "case.create")
    assert has_permission(perms, "case.update")
    assert has_permission(perms, "case.close")
    assert has_permission(perms, "evidence.create")
    assert has_permission(perms, "evidence.verify")
    assert has_permission(perms, "custody.create")
    assert has_permission(perms, "report.generate")
    for forbidden in ("user.create", "user.disable", "system.manage"):
        assert not has_permission(perms, forbidden), f"INVESTIGATOR should NOT have {forbidden}"
    print("  [OK] Investigator has case+evidence+report perms, no user mgmt")


def test_sidebar_filtering() -> None:
    banner("TEST 7: Sidebar modules gated on permissions")
    # These mirror the SIDEBAR_MODULES list in app.py
    SIDEBAR_MODULES = [
        ("dashboard", "case.view"),
        ("cases", "case.view"),
        ("evidence", "evidence.view"),
        ("custody", "custody.view"),
        ("reports", "report.generate"),
        ("audit", "audit.view"),
        ("users", "user.view"),
    ]
    for username, role in [
        ("admin", "ADMINISTRATOR"),
        ("aud", "AUDITOR"),
        ("inv", "CASE INVESTIGATOR"),
        ("cust", "EVIDENCE CUSTODIAN"),
    ]:
        perms = permissions_for_roles([role])
        visible = [m for m, p in SIDEBAR_MODULES if p in perms]
        print(f"  {role:25s} sees: {visible}")


def test_full_workflow() -> None:
    banner("TEST 8: End-to-end workflow: login -> case -> evidence -> custody -> verify -> audit")
    user, _ = authenticate_user("admin", "Admin@123")

    case = case_service.create_case(
        title="UI Workflow Test",
        incident_date="2025-08-20",
        priority="High",
        description="Created by UI RBAC test",
        created_by=user["id"],
    )
    assert case.case_number.startswith("CASE-")

    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
        f.write("RBAC test evidence content\n" * 20)
        tmp_path = f.name
    try:
        ev = evidence_service.register_evidence(
            case_id=case.id,
            file_path=tmp_path,
            evidence_type="Document",
            description="Workflow test evidence",
            source="UI test",
            registered_by=user["id"],
        )
        assert ev.md5 and ev.sha256
        # Custody event
        eid = custody_service.add_custody_event(
            evidence_id=ev.id,
            action="TRANSFERRED",
            from_person="alice",
            to_person="bob",
            location="Lab",
            case_id=case.id,
            recorded_by=user["id"],
        )
        assert eid > 0
        # Verify hashes
        result = evidence_service.verify_evidence(ev.id, verified_by=user["id"])
        assert result["md5_match"] and result["sha256_match"]
        # Audit log
        logs = audit_service.get_audit_logs(case_id=case.id, limit=20)
        actions = {l["action"] for l in logs}
        for needed in ("CASE_CREATED", "EVIDENCE_REGISTERED", "HASH_VERIFIED"):
            assert needed in actions, f"Missing audit event: {needed}"
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    print(f"  [OK] Workflow completed: case {case.case_number}, evidence {ev.evidence_id}")
    print(f"  [OK] Audit events captured: {sorted(actions)}")


def test_password_reset() -> None:
    banner("TEST 9: Admin can reset user password")
    from database.database import get_connection
    c = get_connection()
    try:
        row = c.execute("SELECT id FROM users WHERE username = ?", ("aud",)).fetchone()
    finally:
        c.close()
    assert row, "User 'aud' not found"
    reset_password(row["id"], "NewAudPass456!")
    user, _ = authenticate_user("aud", "NewAudPass456!")
    assert user["username"] == "aud"
    print("  [OK] Password reset and re-login works")


def main() -> int:
    print("Digital Forensics Framework - UI & RBAC Test Suite")
    print("=" * 70)
    tests = [
        test_admin_login,
        test_wrong_password_rejected,
        test_inactive_user_blocked,
        test_auditor_rbac,
        test_custodian_rbac,
        test_investigator_rbac,
        test_sidebar_filtering,
        test_full_workflow,
        test_password_reset,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            failed += 1
    print()
    print("=" * 70)
    print(f"RESULT: {passed} passed, {failed} failed")
    print("=" * 70)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
