"""
api/users.py - User management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime, timezone

from ..core.dependencies import get_current_user, CurrentUser, require_permission_dep
from ..schemas.user import UserCreate, UserUpdate, UserPasswordReset, UserResponse, UserListResponse
from ..auth.authentication import register_user, reset_password, disable_user, enable_user, authenticate_user
from ..auth.authorization import permissions_for_roles
from ..services.audit_service import log_event

router = APIRouter(prefix="/users", tags=["Users"])


def _model_to_response(user) -> dict:
    """Convert user model to response dict."""
    return {
        "id": user.id,
        "username": user.username,
        "role_names": user.role_names,
        "permissions": user.permissions,
        "is_active": bool(user.active),
        "created_at": user.created_at,
        "last_login": user.last_login,
        "must_change_password": bool(user.must_change_password),
    }


@router.get("", response_model=List[dict])
async def list_users(
    limit: int = Query(100, ge=1, le=500),
    current_user: CurrentUser = Depends(require_permission_dep("user.view")),
):
    """List all users (admin only)."""
    from database.database import get_connection

    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT u.id, u.username, u.active, u.created_at, u.last_login,
                   GROUP_CONCAT(r.name, ', ') AS role_names,
                   GROUP_CONCAT(p.name, ', ') AS permissions
            FROM users u
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            LEFT JOIN role_permissions rp ON rp.role_id = r.id
            LEFT JOIN permissions p ON p.id = rp.permission_id
            GROUP BY u.id
            ORDER BY u.username
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

        users = []
        for row in rows:
            users.append(_model_to_response({
                "id": row["id"],
                "username": row["username"],
                "role_names": row["role_names"].split(", ") if row["role_names"] else [],
                "permissions": row["permissions"].split(", ") if row["permissions"] else [],
                "active": row["active"],
                "created_at": row["created_at"],
                "last_login": row["last_login"],
                "must_change_password": 0,  # Not stored in query result, default to false
            }))

        return users
    finally:
        conn.close()


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreate,
    current_user: CurrentUser = Depends(require_permission_dep("user.create")),
):
    """Create a new user account."""
    try:
        # First check if user already exists
        from database.database import get_connection
        conn = get_connection()
        try:
            row = conn.execute("SELECT id FROM users WHERE username = ?", (request.username,)).fetchone()
            if row:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User '{request.username}' already exists",
                )
        finally:
            conn.close()

        # Register the user
        user_data = register_user(
            username=request.username,
            password=request.password,
            role_name=request.role_name,
        )

        # Log the user creation
        log_event(
            action="USER_CREATED",
            user_id=current_user.id,
            username=current_user.username,
            role_name=", ".join(current_user.role_names),
            description=f"Created user '{request.username}' with role '{request.role_name}'",
            entity_type="user",
            entity_id=user_data["id"],
        )

        return {"message": f"User '{request.username}' created successfully", "user_id": user_data["id"]}
    except HTTPException:
        # Re-raise HTTPException (e.g. 409 conflict) as-is
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        import sqlite3 as _sqlite3
        if isinstance(e, _sqlite3.IntegrityError):
            msg = str(e).lower()
            if "unique" in msg and "username" in msg:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User '{request.username}' already exists",
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Database integrity error",
            )
        # Re-raise so the global error handler returns a clean 500
        # without leaking internal details. The pre-check above should
        # prevent IntegrityError in normal operation.
        raise


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("user.view")),
):
    """Get user details by ID."""
    from database.database import get_connection

    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT u.id, u.username, u.active, u.created_at, u.last_login,
                   GROUP_CONCAT(r.name, ', ') AS role_names,
                   GROUP_CONCAT(p.name, ', ') AS permissions
            FROM users u
            LEFT JOIN user_roles ur ON ur.user_id = u.id
            LEFT JOIN roles r ON r.id = ur.role_id
            LEFT JOIN role_permissions rp ON rp.role_id = r.id
            LEFT JOIN permissions p ON p.id = rp.permission_id
            WHERE u.id = ?
            GROUP BY u.id
            """,
            (user_id,)
        ).fetchone()

        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")

        return _model_to_response({
            "id": row["id"],
            "username": row["username"],
            "role_names": row["role_names"].split(", ") if row["role_names"] else [],
            "permissions": row["permissions"].split(", ") if row["permissions"] else [],
            "active": row["active"],
            "created_at": row["created_at"],
            "last_login": row["last_login"],
            "must_change_password": 0,
        })
    finally:
        conn.close()


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    request: UserUpdate,
    current_user: CurrentUser = Depends(require_permission_dep("user.update")),
):
    """Update user details (role assignment, status)."""
    from database.database import get_connection

    conn = get_connection()
    try:
        # Verify user exists
        user_row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found")

        # Update role if specified
        if request.role_names is not None:
            # Delete existing roles
            conn.execute("DELETE FROM user_roles WHERE user_id = ?", (user_id,))

            # Add new roles (assuming role_names already validated)
            from ..auth.authorization import DEFAULT_ROLE_PERMISSIONS
            valid_roles = [r for r in request.role_names if r in DEFAULT_ROLE_PERMISSIONS]

            for role_name in valid_roles:
                role_row = conn.execute("SELECT id FROM roles WHERE name = ?", (role_name,)).fetchone()
                if role_row:
                    conn.execute("INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)", (user_id, role_row["id"]))

        # Update active status if specified
        if request.active is not None:
            conn.execute("UPDATE users SET active = ? WHERE id = ?", (1 if request.active else 0, user_id))

        # Update must_change_password if specified
        if request.must_change_password is not None:
            conn.execute("UPDATE users SET must_change_password = ? WHERE id = ?", (1 if request.must_change_password else 0, user_id))

        conn.commit()

        # Log the update
        log_event(
            action="USER_UPDATED",
            user_id=current_user.id,
            username=current_user.username,
            role_name=", ".join(current_user.role_names),
            description=f"Updated user {user_id}",
            entity_type="user",
            entity_id=user_id,
        )

        return {"message": f"User {user_id} updated successfully"}
    finally:
        conn.close()


@router.post("/{user_id}/disable", response_model=dict)
async def disable_user_endpoint(
    user_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("user.disable")),
):
    """Disable a user account."""
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot disable yourself")

    disable_user(user_id)

    # Get username for logging
    from database.database import get_connection
    conn = get_connection()
    try:
        row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        username = row["username"] if row else f"user-{user_id}"
    finally:
        conn.close()

    # Log the action
    log_event(
        action="USER_DISABLED",
        user_id=current_user.id,
        username=current_user.username,
        role_name=", ".join(current_user.role_names),
        description=f"Disabled user {username} (ID: {user_id})",
        entity_type="user",
        entity_id=user_id,
    )

    return {"message": f"User {user_id} disabled successfully"}


@router.post("/{user_id}/enable", response_model=dict)
async def enable_user_endpoint(
    user_id: int,
    current_user: CurrentUser = Depends(require_permission_dep("user.disable")),
):
    """Re-enable a user account."""
    enable_user(user_id)

    # Get username for logging
    from database.database import get_connection
    conn = get_connection()
    try:
        row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        username = row["username"] if row else f"user-{user_id}"
    finally:
        conn.close()

    # Log the action
    log_event(
        action="USER_ENABLED",
        user_id=current_user.id,
        username=current_user.username,
        role_name=", ".join(current_user.role_names),
        description=f"Enabled user {username} (ID: {user_id})",
        entity_type="user",
        entity_id=user_id,
    )

    return {"message": f"User {user_id} enabled successfully"}


@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: int,
    request: UserPasswordReset,
    current_user: CurrentUser = Depends(require_permission_dep("user.update")),
):
    """Reset user password (admin only)."""
    # Get username for logging
    from database.database import get_connection
    conn = get_connection()
    try:
        row = conn.execute("SELECT username FROM users WHERE id = ?", (user_id,)).fetchone()
        username = row["username"] if row else f"user-{user_id}"
    finally:
        conn.close()

    # Reset the password (may raise ValueError for invalid password)
    reset_password(user_id, request.new_password)

    # Log the action
    log_event(
        action="PASSWORD_RESET",
        user_id=current_user.id,
        username=current_user.username,
        role_name=", ".join(current_user.role_names),
        description=f"Password reset for user {username} (ID: {user_id})",
        entity_type="user",
        entity_id=user_id,
    )

    return {"message": f"Password reset for user {username} (ID: {user_id})"}