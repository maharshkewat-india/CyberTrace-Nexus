"""
authorization.py - Role-Based Access Control (RBAC) permission model.

Design notes:
- Permission names follow a <entity>.<action> convention (e.g. case.create).
- A user's effective permissions are the union of permissions granted by ALL
  roles assigned to them.
- Permission checks happen at the service/database level, NOT at the UI level.
  Hiding UI buttons is purely a convenience; every protected operation calls
  `require_permission(...)` before executing.
- Role names are compared case-insensitively to avoid normalisation bugs.
"""

from __future__ import annotations

from typing import Iterable, Set

# ----------------------------------------------------------------------
# Permission constants (single source of truth)
# ----------------------------------------------------------------------

PERMISSIONS_ALL: tuple[str, ...] = (
    "case.create",
    "case.view",
    "case.update",
    "case.assign",
    "case.close",
    "evidence.create",
    "evidence.view",
    "evidence.update",
    "evidence.hash",
    "evidence.verify",
    "custody.create",
    "custody.view",
    "analysis.create",
    "analysis.view",
    "audit.view",
    "report.generate",
    "user.create",
    "user.view",
    "user.update",
    "user.disable",
    "system.manage",
)

# ----------------------------------------------------------------------
# Default role -> permission map (also seeded into the DB by database.py).
# This dict is the authoritative client-side view used by the UI/services
# when the database has not been queried yet (e.g. lookup for a role name).
# ----------------------------------------------------------------------

DEFAULT_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    "ADMINISTRATOR": frozenset(PERMISSIONS_ALL),
    "CASE INVESTIGATOR": frozenset({
        "case.create", "case.view", "case.update", "case.assign", "case.close",
        "evidence.create", "evidence.view", "evidence.hash", "evidence.verify",
        "custody.create", "custody.view",
        "analysis.create", "analysis.view",
        "report.generate",
    }),
    "FORENSIC ANALYST": frozenset({
        "case.view",
        "evidence.view", "evidence.hash", "evidence.verify",
        "custody.view",
        "analysis.create", "analysis.view",
    }),
    "EVIDENCE CUSTODIAN": frozenset({
        "case.view",
        "evidence.view", "evidence.create",
        "custody.create", "custody.view",
    }),
    "AUDITOR": frozenset({
        "case.view",
        "evidence.view",
        "custody.view",
        "analysis.view",
        "audit.view",
        "report.generate",
    }),
}

DEFAULT_ROLES: tuple[str, ...] = tuple(DEFAULT_ROLE_PERMISSIONS.keys())


# ----------------------------------------------------------------------
# Core permission model
# ----------------------------------------------------------------------

def permissions_for_roles(role_names: Iterable[str]) -> frozenset[str]:
    """Return the union of permissions granted by the given roles."""
    perms: Set[str] = set()
    for name in role_names:
        perms |= DEFAULT_ROLE_PERMISSIONS.get(name.upper(), frozenset())
    return frozenset(perms)


def has_permission(permissions: frozenset[str], permission: str) -> bool:
    """Return True if `permission` is present in the given permission set."""
    return permission in permissions


def require_permission(permissions: frozenset[str], permission: str) -> None:
    """
    Raise a PermissionError if the given permission is not granted.

    Args:
        permissions: The caller's effective permission set.
        permission: The permission being checked.

    Raises:
        PermissionError: If the permission is missing.
    """
    if not permission or permission not in permissions:
        raise PermissionError(f"Permission denied: '{permission}'")


def has_any(permissions: frozenset[str], needed: Iterable[str]) -> bool:
    """Return True if the caller holds at least one of the needed permissions."""
    return bool(permissions & frozenset(needed))


def has_all(permissions: frozenset[str], needed: Iterable[str]) -> bool:
    """Return True if the caller holds ALL of the needed permissions."""
    return frozenset(needed).issubset(permissions)


# ----------------------------------------------------------------------
# Helper: derive a frozenset from a list of role names (DB rows)
# ----------------------------------------------------------------------

def permissions_from_role_names(role_names: Iterable[str]) -> frozenset[str]:
    """Convenience wrapper around permissions_for_roles."""
    return permissions_for_roles(role_names)


# ----------------------------------------------------------------------
# Allowed values for form fields (e.g. status, priority)
# ----------------------------------------------------------------------

CASE_STATUSES: tuple[str, ...] = (
    "Open",
    "Under Investigation",
    "Suspended",
    "Closed",
    "Archived",
)

CASE_PRIORITIES: tuple[str, ...] = ("Low", "Medium", "High", "Critical")

EVIDENCE_TYPES: tuple[str, ...] = (
    "Document", "Image", "Video", "Audio",
    "Binary", "Database", "Other",
)

EVIDENCE_STATUSES: tuple[str, ...] = ("Active", "Seized", "Released", "Destroyed")

CUSTODY_ACTIONS: tuple[str, ...] = (
    "REGISTERED", "TRANSFERRED", "RECEIVED", "EXAMINED",
    "STORED", "RELEASED", "RETURNED", "CORRECTED",
)

AUDIT_ACTIONS: tuple[str, ...] = (
    "LOGIN", "LOGOUT",
    "CASE_CREATED", "CASE_UPDATED", "CASE_ASSIGNED",
    "CASE_CLOSED", "CASE_ARCHIVED",
    "EVIDENCE_REGISTERED", "EVIDENCE_UPDATED",
    "HASH_CALCULATED", "HASH_VERIFIED", "HASH_MISMATCH",
    "CUSTODY_TRANSFER", "CUSTODY_RECEIVED", "CUSTODY_EXAMINED",
    "CUSTODY_STORED", "CUSTODY_RELEASED", "CUSTODY_RETURNED",
    "CUSTODY_CORRECTED",
    "NOTE_CREATED",
    "REPORT_GENERATED",
    "USER_CREATED", "USER_UPDATED", "USER_DISABLED", "USER_ENABLED",
    "PASSWORD_RESET",
    "SYSTEM_SETTING_UPDATED",
)