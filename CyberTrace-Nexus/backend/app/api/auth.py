"""
api/auth.py - Authentication API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, timezone

from ..schemas.auth import LoginRequest, LoginResponse, UserResponse, RefreshTokenResponse
from ..core.dependencies import get_current_user, CurrentUser
from ..core.security import create_access_token, verify_access_token
from ..auth.authentication import authenticate_user, logout_user, verify_session
from ..auth.authorization import permissions_for_roles

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.

    Returns access token and user info on success.
    """
    try:
        user_data, session_data = authenticate_user(request.username, request.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    token_data = {
        "user_id": user_data["id"],
        "username": user_data["username"],
        "role_names": user_data["role_names"],
        "permissions": user_data["permissions"],
    }
    access_token = create_access_token(token_data)

    # Parse datetime fields
    created_at = user_data.get("created_at")
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            created_at = datetime.now(timezone.utc)

    last_login = user_data.get("last_login")
    if isinstance(last_login, str):
        try:
            last_login = datetime.fromisoformat(last_login.replace("Z", "+00:00"))
        except ValueError:
            last_login = None

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user_data["id"],
            username=user_data["username"],
            role_names=user_data["role_names"],
            permissions=user_data["permissions"],
            is_active=user_data.get("active", True),
            created_at=created_at,
            last_login=last_login,
            must_change_password=user_data.get("must_change_password", False),
        ),
    )


@router.post("/logout")
async def logout(current_user: CurrentUser = Depends(get_current_user)):
    """
    Logout current user (invalidate session).

    Note: In JWT-based auth, logout is handled client-side by discarding the token.
    This endpoint exists for API consistency and audit logging.
    """
    # Log audit event
    from services.audit_service import log_event
    log_event(
        action="LOGOUT",
        user_id=current_user.id,
        username=current_user.username,
        role_name=", ".join(current_user.role_names),
        description=f"User {current_user.username} logged out via API",
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser = Depends(get_current_user)):
    """
    Get current authenticated user info.
    """
    from database.database import get_connection

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT created_at, last_login, active, must_change_password FROM users WHERE id = ?",
            (current_user.id,)
        ).fetchone()
    finally:
        conn.close()

    created_at = datetime.now(timezone.utc)
    last_login = None
    is_active = True
    must_change_password = False

    if row:
        ca = row["created_at"]
        if isinstance(ca, str):
            try:
                created_at = datetime.fromisoformat(ca.replace("Z", "+00:00"))
            except ValueError:
                pass
        else:
            created_at = ca

        ll = row["last_login"]
        if ll:
            if isinstance(ll, str):
                try:
                    last_login = datetime.fromisoformat(ll.replace("Z", "+00:00"))
                except ValueError:
                    last_login = None
            else:
                last_login = ll

        is_active = bool(row["active"])
        must_change_password = bool(row["must_change_password"])

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        role_names=current_user.role_names,
        permissions=current_user.permissions,
        is_active=is_active,
        created_at=created_at,
        last_login=last_login,
        must_change_password=must_change_password,
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(current_user: CurrentUser = Depends(get_current_user)):
    """
    Refresh the access token.
    """
    token_data = {
        "user_id": current_user.id,
        "username": current_user.username,
        "role_names": current_user.role_names,
        "permissions": current_user.permissions,
    }
    access_token = create_access_token(token_data)
    return RefreshTokenResponse(access_token=access_token, token_type="bearer")
