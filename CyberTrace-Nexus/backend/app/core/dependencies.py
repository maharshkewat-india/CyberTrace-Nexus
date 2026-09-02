"""
core/dependencies.py - FastAPI dependency injection for auth and RBAC.
"""

from typing import Optional, List, Dict
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .security import verify_access_token
from ..auth.authorization import permissions_for_roles, require_permission, PERMISSIONS_ALL
from ..auth.authorization import has_permission

# HTTP Bearer scheme for JWT tokens
bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser:
    """Container for the current authenticated user."""
    def __init__(self, user_id: int, username: str, role_names: List[str], permissions: List[str]):
        self.id = user_id
        self.username = username
        self.role_names = role_names
        self.permissions = permissions

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions

    def has_any_permission(self, permissions: List[str]) -> bool:
        return bool(set(permissions) & set(self.permissions))


def get_token_data(credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)) -> Optional[Dict]:
    """
    Extract and verify JWT token from request.

    Returns the decoded payload or None if no token provided.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    payload = verify_access_token(token)
    return payload


async def get_current_user(token_data: Optional[Dict] = Depends(get_token_data)) -> CurrentUser:
    """
    FastAPI dependency to get the current authenticated user.

    Raises HTTPException if no valid token is provided.
    """
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = token_data.get("user_id")
    username = token_data.get("username", "")
    role_names = token_data.get("role_names", [])
    permissions = token_data.get("permissions", [])

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return CurrentUser(
        user_id=user_id,
        username=username,
        role_names=role_names,
        permissions=permissions,
    )


async def get_optional_user(token_data: Optional[Dict] = Depends(get_token_data)) -> Optional[CurrentUser]:
    """Optional user - returns None if not authenticated instead of raising exception."""
    if token_data is None:
        return None

    user_id = token_data.get("user_id")
    if user_id is None:
        return None

    return CurrentUser(
        user_id=user_id,
        username=token_data.get("username", ""),
        role_names=token_data.get("role_names", []),
        permissions=token_data.get("permissions", []),
    )


class RequirePermission:
    """FastAPI dependency that checks for a specific permission."""

    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(self, current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if self.permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{self.permission}'",
            )
        return current_user


def require_permission_dep(permission: str):
    """Factory for permission check dependencies."""
    return RequirePermission(permission)
