"""Identity and Authentication business logic service.

All authentication operations, session lifecycles, and security verifications
are implemented deterministically here.
"""

from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, List
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import (
    UserRole,
    get_password_hash,
    verify_password,
    verify_dummy_password,
    generate_secure_token,
    hash_token_secret,
    create_access_token,
)
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
)
from app.domains.identity.email_service import email_service
from app.domains.audit.service import record_audit_event


class IdentityService:
    """Service orchestrating account lifecycle, password management, and sessions."""

    async def register_student(
        self,
        db: AsyncSession,
        data: UserRegisterRequest,
    ) -> User:
        """Registers a new student account.

        CRITICAL SECURITY ENFORCEMENT:
        Public self-registration CANNOT create privileged accounts.
        The role is strictly hardcoded to UserRole.STUDENT.
        """
        normalized_email = data.email.strip().lower()

        # Check for existing account
        stmt = select(User).where(User.normalized_email == normalized_email)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

        hashed_pwd = get_password_hash(data.password)
        display_name = f"{data.first_name.strip()} {data.last_name.strip()}".strip()

        new_user = User(
            email=data.email.strip(),
            normalized_email=normalized_email,
            hashed_password=hashed_pwd,
            role=UserRole.STUDENT,  # Hardcoded strictly to student
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            display_name=display_name,
            institution_id=data.institution_id,
            is_active=True,
            is_verified=False,
        )
        db.add(new_user)
        await db.flush()

        # Generate email verification token
        raw_verify_token = generate_secure_token(32)
        verify_token_hash = hash_token_secret(raw_verify_token)
        verification_record = EmailVerificationToken(
            user_id=new_user.id,
            token_hash=verify_token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS),
        )
        db.add(verification_record)

        # Audit event
        record_audit_event(
            actor_id=new_user.id,
            actor_role=new_user.role,
            event_type="registration",
            resource_type="user",
            resource_id=new_user.id,
            payload={"email": normalized_email, "role": new_user.role.value},
        )

        await db.commit()
        await db.refresh(new_user)

        # Trigger verification delivery abstraction
        await email_service.send_verification_email(new_user.email, raw_verify_token)

        return new_user

    async def admin_create_user(
        self,
        db: AsyncSession,
        creator_id: str,
        creator_role: UserRole,
        data: AdminUserCreateRequest,
    ) -> User:
        """Controlled administrative endpoint for creating staff/faculty/admin accounts."""
        normalized_email = data.email.strip().lower()

        stmt = select(User).where(User.normalized_email == normalized_email)
        res = await db.execute(stmt)
        if res.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email address already exists.",
            )

        hashed_pwd = get_password_hash(data.password)
        display_name = f"{data.first_name.strip()} {data.last_name.strip()}".strip()

        new_user = User(
            email=data.email.strip(),
            normalized_email=normalized_email,
            hashed_password=hashed_pwd,
            role=data.role,
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            display_name=display_name,
            institution_id=data.institution_id,
            is_active=True,
            is_verified=True,  # Admin-provisioned accounts default to verified
        )
        db.add(new_user)
        await db.flush()

        record_audit_event(
            actor_id=creator_id,
            actor_role=creator_role,
            event_type="admin_user_create",
            resource_type="user",
            resource_id=new_user.id,
            payload={"created_user_role": data.role.value, "created_user_email": normalized_email},
        )

        await db.commit()
        await db.refresh(new_user)
        return new_user

    async def authenticate_user(
        self,
        db: AsyncSession,
        data: UserLoginRequest,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Tuple[str, str, User, UserSession]:
        """Authenticates user credentials, enforces lockout, creates a session,

        and returns (access_token, raw_refresh_token, user, session).
        """
        normalized_email = data.email.strip().lower()
        now = datetime.now(timezone.utc)

        stmt = select(User).where(User.normalized_email == normalized_email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            # Timing side-channel mitigation
            verify_dummy_password()
            record_audit_event(
                actor_id="anonymous",
                actor_role=UserRole.STUDENT,
                event_type="login_failure",
                resource_type="auth",
                resource_id=normalized_email,
                payload={"reason": "nonexistent_account"},
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Check account lockout
        if user.locked_until:
            locked_dt = user.locked_until
            if locked_dt.tzinfo is None:
                locked_dt = locked_dt.replace(tzinfo=timezone.utc)
            if locked_dt > now:
                minutes_left = max(1, int((locked_dt - now).total_seconds() / 60))
                record_audit_event(
                    actor_id=user.id,
                actor_role=user.role,
                event_type="login_blocked_lockout",
                resource_type="user",
                resource_id=user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is temporarily locked. Please try again in {minutes_left} minutes.",
            )

        # Check active status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated. Please contact an administrator.",
            )

        # Verify password
        if not verify_password(data.password, user.hashed_password):
            user.failed_login_count += 1
            if user.failed_login_count >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
                record_audit_event(
                    actor_id=user.id,
                    actor_role=user.role,
                    event_type="account_lock",
                    resource_type="user",
                    resource_id=user.id,
                    payload={"attempts": user.failed_login_count},
                )
            record_audit_event(
                actor_id=user.id,
                actor_role=user.role,
                event_type="login_failure",
                resource_type="auth",
                resource_id=user.id,
            )
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        # Successful login: reset lockouts and update last_login
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = now

        # Create session and refresh token
        raw_refresh_token = generate_secure_token(48)
        refresh_hash = hash_token_secret(raw_refresh_token)
        session = UserSession(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            created_at=now,
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            last_seen_at=now,
            user_agent=user_agent[:255] if user_agent else None,
            ip_address=ip_address[:45] if ip_address else None,
        )
        db.add(session)
        await db.flush()

        access_token = create_access_token(
            subject=user.id,
            role=user.role,
            session_id=session.id,
            institution_id=user.institution_id,
        )

        record_audit_event(
            actor_id=user.id,
            actor_role=user.role,
            event_type="login_success",
            resource_type="session",
            resource_id=session.id,
        )

        await db.commit()
        return access_token, raw_refresh_token, user, session

    async def refresh_session(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
        user_agent: Optional[str] = None,
    ) -> Tuple[str, str, User]:
        """Rotates an existing refresh token and returns a new access token."""
        now = datetime.now(timezone.utc)
        token_hash = hash_token_secret(raw_refresh_token)

        stmt = select(UserSession).where(
            UserSession.refresh_token_hash == token_hash,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()

        if not session:
            record_audit_event(
                actor_id="anonymous",
                actor_role=UserRole.STUDENT,
                event_type="session_refresh_failure",
                resource_type="session",
                resource_id="invalid_token",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session. Please log in again.",
            )

        stmt_user = select(User).where(User.id == session.user_id)
        res_user = await db.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        if not user or not user.is_active:
            session.revoked_at = now
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive or no longer exists.",
            )

        # Rotate refresh token
        new_raw_refresh_token = generate_secure_token(48)
        session.refresh_token_hash = hash_token_secret(new_raw_refresh_token)
        session.last_seen_at = now
        session.expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        if user_agent:
            session.user_agent = user_agent[:255]

        access_token = create_access_token(
            subject=user.id,
            role=user.role,
            session_id=session.id,
            institution_id=user.institution_id,
        )

        record_audit_event(
            actor_id=user.id,
            actor_role=user.role,
            event_type="session_refresh",
            resource_type="session",
            resource_id=session.id,
        )

        await db.commit()
        return access_token, new_raw_refresh_token, user

    async def revoke_session_by_token(
        self,
        db: AsyncSession,
        raw_refresh_token: str,
    ) -> None:
        """Revokes a session by its refresh token on logout."""
        now = datetime.now(timezone.utc)
        token_hash = hash_token_secret(raw_refresh_token)

        stmt = select(UserSession).where(UserSession.refresh_token_hash == token_hash)
        res = await db.execute(stmt)
        session = res.scalar_one_or_none()

        if session and session.revoked_at is None:
            session.revoked_at = now
            record_audit_event(
                actor_id=session.user_id,
                actor_role=UserRole.STUDENT,
                event_type="logout",
                resource_type="session",
                resource_id=session.id,
            )
            await db.commit()

    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """Changes user password and invalidates all existing sessions."""
        if not verify_password(current_password, user.hashed_password):
            record_audit_event(
                actor_id=user.id,
                actor_role=user.role,
                event_type="password_change_failure",
                resource_type="user",
                resource_id=user.id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect current password.",
            )

        now = datetime.now(timezone.utc)
        user.hashed_password = get_password_hash(new_password)
        user.password_changed_at = now

        # Invalidate all active sessions for this user to prevent session hijacking
        stmt_sessions = select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        res = await db.execute(stmt_sessions)
        for s in res.scalars():
            s.revoked_at = now

        record_audit_event(
            actor_id=user.id,
            actor_role=user.role,
            event_type="password_change",
            resource_type="user",
            resource_id=user.id,
        )

        await db.commit()

    async def initiate_password_reset(
        self,
        db: AsyncSession,
        email: str,
    ) -> None:
        """Initiates password reset workflow without leaking whether account exists."""
        normalized_email = email.strip().lower()
        now = datetime.now(timezone.utc)

        stmt = select(User).where(User.normalized_email == normalized_email)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()

        if not user:
            # Constant-time mitigation
            verify_dummy_password()
            return

        raw_reset_token = generate_secure_token(32)
        token_hash = hash_token_secret(raw_reset_token)

        reset_record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=now + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
        )
        db.add(reset_record)

        record_audit_event(
            actor_id=user.id,
            actor_role=user.role,
            event_type="password_reset_request",
            resource_type="user",
            resource_id=user.id,
        )

        await db.commit()
        await email_service.send_password_reset_email(user.email, raw_reset_token)

    async def complete_password_reset(
        self,
        db: AsyncSession,
        raw_token: str,
        new_password: str,
    ) -> None:
        """Finalizes password reset using a valid, unused token."""
        now = datetime.now(timezone.utc)
        token_hash = hash_token_secret(raw_token)

        stmt = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
        res = await db.execute(stmt)
        token_record = res.scalar_one_or_none()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset link.",
            )

        stmt_user = select(User).where(User.id == token_record.user_id)
        res_user = await db.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account associated with this token could not be found.",
            )

        user.hashed_password = get_password_hash(new_password)
        user.password_changed_at = now
        user.failed_login_count = 0
        user.locked_until = None
        token_record.used_at = now

        # Invalidate all user sessions
        stmt_sessions = select(UserSession).where(
            UserSession.user_id == user.id,
            UserSession.revoked_at.is_(None),
        )
        res_sessions = await db.execute(stmt_sessions)
        for s in res_sessions.scalars():
            s.revoked_at = now

        record_audit_event(
            actor_id=user.id,
            actor_role=user.role,
            event_type="password_reset_complete",
            resource_type="user",
            resource_id=user.id,
        )

        await db.commit()

    async def verify_email_token(
        self,
        db: AsyncSession,
        raw_token: str,
    ) -> None:
        """Verifies account email address using a valid verification token."""
        now = datetime.now(timezone.utc)
        token_hash = hash_token_secret(raw_token)

        stmt = select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == token_hash,
            EmailVerificationToken.used_at.is_(None),
            EmailVerificationToken.expires_at > now,
        )
        res = await db.execute(stmt)
        token_record = res.scalar_one_or_none()

        if not token_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification link.",
            )

        stmt_user = select(User).where(User.id == token_record.user_id)
        res_user = await db.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account associated with this token could not be found.",
            )

        user.is_verified = True
        token_record.used_at = now

        record_audit_event(
            actor_id=user.id,
            actor_role=user.role,
            event_type="email_verification",
            resource_type="user",
            resource_id=user.id,
        )

        await db.commit()


identity_service = IdentityService()
