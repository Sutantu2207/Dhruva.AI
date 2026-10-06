"""Pydantic schemas for Identity and Authentication domain.

ENFORCEMENT: Public self-registration cannot select privileged roles.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from app.core.security import UserRole, validate_password_strength


class UserRegisterRequest(BaseModel):
    """Public student self-registration request.

    CRITICAL SECURITY RULE: No role field is exposed here.
    Public registration is strictly restricted to creating student accounts.
    """
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    institution_id: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class AdminUserCreateRequest(BaseModel):
    """Controlled administrative endpoint for creating staff/faculty/admin accounts."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    institution_id: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class UserLoginRequest(BaseModel):
    """Credentials required to authenticate."""
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Returned upon successful authentication or token refresh."""
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    role: UserRole
    # refresh_token is provided in response body for API clients,
    # as well as set in an HttpOnly cookie for browser sessions
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    """Public profile representation of the authenticated user identity."""
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    display_name: str
    role: UserRole
    institution_id: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ChangePasswordRequest(BaseModel):
    """Request to change password for an authenticated session."""
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class ForgotPasswordRequest(BaseModel):
    """Request to initiate password reset workflow."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request to finalize password reset using a cryptographically verified token."""
    token: str = Field(min_length=16)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        validate_password_strength(v)
        return v


class VerifyEmailRequest(BaseModel):
    """Request to verify student/user email address."""
    token: str = Field(min_length=16)


class UserSessionResponse(BaseModel):
    """Metadata for an active user session."""
    id: str
    created_at: datetime
    expires_at: datetime
    last_seen_at: datetime
    user_agent: Optional[str] = None
    is_current: bool = False

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """Generic status response message."""
    message: str
