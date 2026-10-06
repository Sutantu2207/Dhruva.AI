import asyncio
import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any
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

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Probes email delivery service readiness."""
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

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "provider": "development",
            "external_relay": False,
        }


class SMTPEmailService(EmailServiceInterface):
    """Production SMTP email relay with TLS, retry policies, and fail-safe handling."""

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS
        self.timeout = settings.SMTP_TIMEOUT_SECONDS
        self.from_addr = settings.EMAIL_FROM

    def _send_sync(self, recipient: str, subject: str, html_body: str) -> bool:
        """Synchronous SMTP delivery with TLS."""
        if not self.host:
            logger.warning("SMTP delivery skipped: SMTP_HOST not configured.")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = recipient
        msg.attach(MIMEText(html_body, "html"))

        server = None
        try:
            server = smtplib.SMTP(self.host, self.port, timeout=self.timeout)
            if self.use_tls:
                server.starttls()
            if self.user and self.password:
                server.login(self.user, self.password)
            server.sendmail(self.from_addr, [recipient], msg.as_string())
            logger.info(f"SMTP email successfully relayed to '{recipient}' (subject: '{subject}')")
            return True
        except Exception as exc:
            logger.error(f"SMTP delivery failed to '{recipient}': {exc}")
            return False
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    async def _send_with_retry(self, recipient: str, subject: str, html_body: str, max_retries: int = 2) -> bool:
        """Executes SMTP relay in worker thread with exponential backoff retry."""
        loop = asyncio.get_running_loop()
        for attempt in range(max_retries + 1):
            success = await loop.run_in_executor(None, self._send_sync, recipient, subject, html_body)
            if success:
                return True
            if attempt < max_retries:
                await asyncio.sleep(1.0 * (2 ** attempt))
        return False

    async def send_verification_email(self, recipient_email: str, token: str) -> bool:
        base_url = "https://dhruva.ai" if settings.is_production else "http://localhost:3000"
        link = f"{base_url}/verify-email?token={token}"
        subject = "Dhruva.AI - Verify Your Academic Account"
        html = f"""
        <h2>Verify Your Dhruva.AI Account</h2>
        <p>Welcome to Dhruva.AI. Please verify your institutional email address by clicking the link below:</p>
        <p><a href="{link}" style="display:inline-block;padding:10px 20px;background:#1e40af;color:#fff;text-decoration:none;border-radius:4px;">Verify Account</a></p>
        <p>This verification link will expire in {settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS} hours.</p>
        """
        return await self._send_with_retry(recipient_email, subject, html)

    async def send_password_reset_email(self, recipient_email: str, token: str) -> bool:
        base_url = "https://dhruva.ai" if settings.is_production else "http://localhost:3000"
        link = f"{base_url}/reset-password?token={token}"
        subject = "Dhruva.AI - Password Reset Request"
        html = f"""
        <h2>Reset Your Dhruva.AI Password</h2>
        <p>A password reset request was received for your account. Click the button below to set a new password:</p>
        <p><a href="{link}" style="display:inline-block;padding:10px 20px;background:#b91c1c;color:#fff;text-decoration:none;border-radius:4px;">Reset Password</a></p>
        <p>This link is valid for {settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES} minutes. If you did not request this, please ignore this email.</p>
        """
        return await self._send_with_retry(recipient_email, subject, html)

    def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self.host else "degraded",
            "provider": "smtp",
            "host": self.host,
            "port": self.port,
            "tls_enabled": self.use_tls,
            "configured": bool(self.host),
        }


def get_email_service() -> EmailServiceInterface:
    """Factory selecting the transactional email service based on environment and config."""
    if settings.EMAIL_PROVIDER.lower() in ("smtp", "ses", "production") and settings.SMTP_HOST:
        return SMTPEmailService()
    return DevelopmentEmailService()


email_service: EmailServiceInterface = get_email_service()


def check_email_health() -> Dict[str, Any]:
    """Probes email delivery service readiness."""
    return email_service.health_check()
