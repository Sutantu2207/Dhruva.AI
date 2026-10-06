"""Authentication, Identity, and RBAC API Endpoints.

All endpoints adhere to enterprise security rules:
- Public registration creates ONLY student accounts.
- HttpOnly, SameSite, Secure cookies for refresh tokens.
- Constant-time enumeration defenses.
- Reusable centralized authorization dependencies.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import UserRole
from app.api.deps import (
    get_db,
    get_current_user,
    require_roles,
    require_self_or_roles,
)
from app.domains.identity.models import User
from app.domains.identity.schemas import (
    UserRegisterRequest,
    AdminUserCreateRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    MessageResponse,
    UserSessionResponse,
)
from app.domains.identity.service import identity_service
from app.domains.identity.rate_limiter import auth_rate_limiter

router = APIRouter(prefix="/auth", tags=["Identity & Authentication"])


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    """Sets secure HttpOnly cookie for session refresh token."""
    response.set_cookie(
        key=settings.COOKIE_NAME_REFRESH_TOKEN,
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/api/v1/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    """Clears the refresh token cookie upon logout."""
    response.delete_cookie(
        key=settings.COOKIE_NAME_REFRESH_TOKEN,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/api/v1/auth",
    )


def get_client_ip(request: Request) -> str:
    """Safely resolves client IP address."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new student account",
)
async def register_student(
    request: Request,
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Public self-registration endpoint.

    CRITICAL SECURITY RULE: Creates student accounts ONLY.
    Privileged accounts (teacher, mentor, hod, admin) cannot be created here.
    """
    client_ip = get_client_ip(request)
    auth_rate_limiter.check_or_raise(f"register:{client_ip}", max_requests=10, window_seconds=60, action_name="registration")

    user = await identity_service.register_student(db, data)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and obtain session tokens",
)
async def login(
    request: Request,
    response: Response,
    data: UserLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticates credentials and returns access token + sets HttpOnly refresh cookie."""
    client_ip = get_client_ip(request)
    auth_rate_limiter.check_or_raise(f"login:{client_ip}", max_requests=20, window_seconds=60, action_name="login")

    user_agent = request.headers.get("User-Agent")
    access_token, raw_refresh, user, session = await identity_service.authenticate_user(
        db,
        data,
        user_agent=user_agent,
        ip_address=client_ip,
    )

    set_refresh_cookie(response, raw_refresh)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role,
        refresh_token=raw_refresh,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate refresh token and obtain new access token",
)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Rotates refresh token and issues new access token.

    Accepts refresh token via HttpOnly cookie or Authorization header.
    """
    # Explicit header takes precedence over ambient cookie to allow testing / non-browser clients
    token = request.headers.get("X-Refresh-Token") or request.cookies.get(settings.COOKIE_NAME_REFRESH_TOKEN)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session refresh token not provided.",
        )

    user_agent = request.headers.get("User-Agent")
    access_token, new_refresh, user = await identity_service.refresh_session(
        db,
        raw_refresh_token=token,
        user_agent=user_agent,
    )

    set_refresh_cookie(response, new_refresh)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=user.role,
        refresh_token=new_refresh,
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke current session and clear refresh cookie",
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Revokes the active session and unsets browser authentication cookies."""
    token = request.cookies.get(settings.COOKIE_NAME_REFRESH_TOKEN) or request.headers.get("X-Refresh-Token")
    if token:
        await identity_service.revoke_session_by_token(db, token)

    clear_refresh_cookie(response)
    return MessageResponse(message="Successfully logged out and session revoked.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get currently authenticated user identity",
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Returns profile for currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change user password and revoke other sessions",
)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Changes password for authenticated user and revokes active sessions."""
    await identity_service.change_password(
        db,
        user=current_user,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return MessageResponse(message="Password successfully updated. All other active sessions have been revoked.")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Request password reset link",
)
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Initiates password reset. Constant-time response prevents account enumeration."""
    client_ip = get_client_ip(request)
    auth_rate_limiter.check_or_raise(f"forgot_pwd:{client_ip}", max_requests=5, window_seconds=60, action_name="password reset")

    await identity_service.initiate_password_reset(db, data.email)
    return MessageResponse(
        message="If an account exists with this email address, password reset instructions have been dispatched."
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset password using verified token",
)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Finalizes password reset using a cryptographic token."""
    await identity_service.complete_password_reset(db, data.token, data.new_password)
    return MessageResponse(message="Password successfully reset. You may now log in with your new credentials.")


@router.post(
    "/verify-email",
    response_model=MessageResponse,
    summary="Verify email address with cryptographic token",
)
async def verify_email(
    data: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Verifies account email."""
    await identity_service.verify_email_token(db, data.token)
    return MessageResponse(message="Email address successfully verified.")


@router.post(
    "/admin/create-user",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create staff or admin account (Admin only)",
)
async def admin_create_user(
    data: AdminUserCreateRequest,
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Administrative creation of teacher, mentor, hod, or administrator accounts."""
    if current_user.role == UserRole.INSTITUTION_ADMIN and data.role == UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Institution Administrators cannot create Super Administrator accounts.",
        )

    user = await identity_service.admin_create_user(
        db,
        creator_id=current_user.id,
        creator_role=current_user.role,
        data=data,
    )
    return UserResponse.model_validate(user)


# -------------------------------------------------------------------------
# RBAC Validation Endpoints (used by security testing & verification)
# -------------------------------------------------------------------------

@router.get(
    "/test/student-only",
    response_model=MessageResponse,
    summary="Test endpoint restricted to Students",
)
async def test_student_only(
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
) -> MessageResponse:
    return MessageResponse(message=f"Authorized student access for {current_user.email}")


@router.get(
    "/test/teacher-only",
    response_model=MessageResponse,
    summary="Test endpoint restricted to Teachers",
)
async def test_teacher_only(
    current_user: User = Depends(require_roles(UserRole.TEACHER)),
) -> MessageResponse:
    return MessageResponse(message=f"Authorized teacher access for {current_user.email}")


@router.get(
    "/test/admin-only",
    response_model=MessageResponse,
    summary="Test endpoint restricted to Administrators",
)
async def test_admin_only(
    current_user: User = Depends(require_roles(UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
) -> MessageResponse:
    return MessageResponse(message=f"Authorized admin access for {current_user.email}")


@router.get(
    "/test/user-profile/{target_user_id}",
    response_model=MessageResponse,
    summary="Test endpoint checking self-access or privileged role",
)
async def test_user_profile_scoped(
    target_user_id: str,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    """Enforces that a user can only access their own profile unless they are a Teacher or Admin."""
    checker = require_self_or_roles(UserRole.TEACHER, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)
    await checker(target_user_id=target_user_id, current_user=current_user)
    return MessageResponse(message=f"Access granted to profile of user {target_user_id}")
