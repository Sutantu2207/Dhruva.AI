"""FastAPI dependency injection for database sessions, security, and reusable RBAC."""

from typing import List, Callable, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_session
from app.core.security import decode_access_token, UserRole
from app.core.config import settings
from app.domains.identity.models import User
from app.domains.identity.schemas import TokenResponse

security_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    """Provides async database session."""
    async for session in get_db_session():
        yield session


def get_token_from_header_or_cookie(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
) -> str:
    """Extracts access token from Authorization header or fallback."""
    if credentials:
        return credentials.credentials
    # Fallback to Authorization header if bearer wrapper missed it
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication credentials not provided",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user_claims(
    token: str = Depends(get_token_from_header_or_cookie),
) -> dict:
    """Decodes and validates JWT claims."""
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    claims: dict = Depends(get_current_user_claims),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Loads and validates the currently authenticated active user from the database."""
    user_id = claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject missing",
        )

    stmt = select(User).where(User.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated",
        )

    return user


def require_roles(*allowed_roles: UserRole) -> Callable:
    """Centralized RBAC authorization dependency.

    Enforces that the authenticated user possesses one of the allowed roles.
    """
    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


def require_self_or_roles(*privileged_roles: UserRole) -> Callable:
    """Scoping authorization dependency.

    Allows a student/user to access their own target resource,
    OR allows elevated roles (e.g. Teacher, HOD, Admin) access.
    """
    async def scope_checker(
        target_user_id: str,
        current_user: User = Depends(get_current_user),
    ) -> User:
        # User accessing their own resource
        if current_user.id == target_user_id:
            return current_user

        # User is Super Admin
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        # User belongs to one of allowed privileged roles
        if current_user.role in privileged_roles:
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to access another user's resources.",
        )

    return scope_checker


def require_institution_scope() -> Callable:
    """Enforces institution data boundary isolation.

    Ensures that non-super-admins cannot access or modify resources
    outside their assigned institution.
    """
    async def institution_checker(
        target_institution_id: Optional[str],
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user

        if not current_user.institution_id or current_user.institution_id != target_institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access resources outside your assigned institution.",
            )

        return current_user

    return institution_checker
