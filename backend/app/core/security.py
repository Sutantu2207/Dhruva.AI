"""Security, cryptography, role-based access control (RBAC), and JWT handling."""

from datetime import datetime, timezone, timedelta
from enum import Enum
import hashlib
import re
import secrets
from typing import Optional, Dict, Any
import argon2
from argon2.exceptions import VerifyMismatchError, VerificationError
import jwt
from app.core.config import settings

# Argon2id password hasher (RFC 9106 recommended parameters)
_argon2_hasher = argon2.PasswordHasher(
    time_cost=2,
    memory_cost=65536,  # 64 MiB
    parallelism=1,
    hash_len=32,
    type=argon2.Type.ID,
)


class UserRole(str, Enum):
    """The 7 official platform roles defined in Dhruva.AI system specifications."""
    STUDENT = "student"
    TEACHER = "teacher"
    MENTOR = "mentor"
    HOD = "hod"
    PLACEMENT_OFFICER = "placement_officer"
    INSTITUTION_ADMIN = "institution_admin"
    SUPER_ADMIN = "super_admin"


def validate_password_strength(password: str) -> None:
    """Validates that a password satisfies enterprise complexity rules.

    Rules:
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special symbol (!@#$%^&*...)
    """
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_+=\[\]]", password):
        raise ValueError("Password must contain at least one special character")


def get_password_hash(password: str) -> str:
    """Generates an Argon2id cryptographic hash of the plaintext password."""
    return _argon2_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against an Argon2id hash.

    Returns False safely on any mismatch without leaking exception details.
    """
    try:
        return _argon2_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False
    except Exception:
        return False


def verify_dummy_password() -> None:
    """Runs a constant-time dummy verification to protect against timing attacks

    when a user account does not exist.
    """
    dummy_hash = "$argon2id$v=19$m=65536,t=2,p=1$c29tZXNhbHQ$RdescudvJCsgqlfreplfluhKsnnIqGEUbAc0ly0DGFY"
    try:
        _argon2_hasher.verify(dummy_hash, "DummyPassword123!")
    except Exception:
        pass


def hash_token_secret(token_secret: str) -> str:
    """Produces SHA-256 hex digest of a token secret for safe database lookup."""
    return hashlib.sha256(token_secret.encode("utf-8")).hexdigest()


def generate_secure_token(nbytes: int = 48) -> str:
    """Generates a high-entropy URL-safe cryptographic token."""
    return secrets.token_urlsafe(nbytes)


def create_access_token(
    subject: str,
    role: UserRole,
    session_id: Optional[str] = None,
    institution_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed, scoped JWT access token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role.value,
        "sid": session_id,
        "inst": institution_id,
        "exp": expire,
        "iat": now,
        "type": "access",
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates the signature and claims of an access token."""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"require": ["exp", "sub", "role"]},
    )
    return payload
