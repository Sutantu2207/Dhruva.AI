"""Identity and Authentication domain package."""

from app.domains.identity.models import (
    User,
    UserSession,
    PasswordResetToken,
    EmailVerificationToken,
)
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
    UserSessionResponse,
    MessageResponse,
)
from app.domains.identity.service import IdentityService, identity_service
from app.domains.identity.email_service import email_service
from app.domains.identity.rate_limiter import auth_rate_limiter

__all__ = [
    "User",
    "UserSession",
    "PasswordResetToken",
    "EmailVerificationToken",
    "UserRegisterRequest",
    "AdminUserCreateRequest",
    "UserLoginRequest",
    "TokenResponse",
    "UserResponse",
    "ChangePasswordRequest",
    "ForgotPasswordRequest",
    "ResetPasswordRequest",
    "VerifyEmailRequest",
    "UserSessionResponse",
    "MessageResponse",
    "IdentityService",
    "identity_service",
    "email_service",
    "auth_rate_limiter",
]
