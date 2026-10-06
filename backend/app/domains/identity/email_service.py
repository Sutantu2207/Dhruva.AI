"""Email delivery service abstraction for verification and password reset workflows.

SAFETY RULE: Never pretend an email was sent via an external provider when it was not.
In development mode without an external SMTP/provider configured, tokens are logged
to the structured development server log for testing.
"""

from abc import ABC, abstractmethod
from typing import Optional
from app.core.config import settings
from app.core.logging import logger


class EmailServiceInterface(ABC):
    """Abstract interface for transactional email delivery."""

    @abstractmethod
    async def send_verification_email(self, recipient_email: str, token: str) -> bool:
        """Sends an account email verification link."""
        pass

    @abstractmethod
    async def send_password_reset_email(self, recipient_email: str, token: str) -> bool:
        """Sends a secure password reset link."""
        pass


class DevelopmentEmailService(EmailServiceInterface):
    """Development and testing email handler.

    Explicitly logs verification and password reset links to console
    without pretending an external SMTP relay occurred.
    """

    async def send_verification_email(self, recipient_email: str, token: str) -> bool:
        verification_link = f"http://localhost:3000/verify-email?token={token}"
        logger.info(
            f"[DEV EMAIL SERVICE] Email verification initiated for '{recipient_email}'. "
            f"Verification Link: {verification_link} (External SMTP not configured in dev)"
        )
        return True

    async def send_password_reset_email(self, recipient_email: str, token: str) -> bool:
        reset_link = f"http://localhost:3000/reset-password?token={token}"
        logger.info(
            f"[DEV EMAIL SERVICE] Password reset initiated for '{recipient_email}'. "
            f"Reset Link: {reset_link} (External SMTP not configured in dev)"
        )
        return True


# Default instance based on environment
email_service: EmailServiceInterface = DevelopmentEmailService()
