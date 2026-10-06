"""PII minimization and context scrubber for external model calls."""

import re
from typing import Dict, Any

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"(\+?[0-9]{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}")
TOKEN_PATTERN = re.compile(r"(Bearer\s+[a-zA-Z0-9\-_.]+|ghp_[a-zA-Z0-9]{36}|AIza[0-9A-Za-z-_]{35})")


class PIIScrubber:
    """Deterministic PII and sensitive secret redactor."""

    @staticmethod
    def redact_text(text: str) -> str:
        """Redacts emails, phone numbers, and bearer credentials."""
        if not text:
            return text

        scrubbed = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
        scrubbed = PHONE_PATTERN.sub("[REDACTED_PHONE]", scrubbed)
        scrubbed = TOKEN_PATTERN.sub("[REDACTED_SECRET]", scrubbed)
        return scrubbed

    @staticmethod
    def sanitize_context_payload(data: Dict[str, Any]) -> Dict[str, Any]:
        """Deeply sanitizes dictionary context payloads, dropping sensitive internal attributes."""
        sanitized = {}
        disallowed_keys = {
            "hashed_password",
            "password",
            "access_token",
            "refresh_token",
            "session_token",
            "phone",
            "phone_number",
            "token",
            "api_key",
            "secret",
        }

        for k, v in data.items():
            if k.lower() in disallowed_keys:
                continue

            if isinstance(v, str):
                sanitized[k] = PIIScrubber.redact_text(v)
            elif isinstance(v, dict):
                sanitized[k] = PIIScrubber.sanitize_context_payload(v)
            elif isinstance(v, list):
                sanitized[k] = [
                    PIIScrubber.sanitize_context_payload(i) if isinstance(i, dict)
                    else PIIScrubber.redact_text(i) if isinstance(i, str)
                    else i
                    for i in v
                ]
            else:
                sanitized[k] = v

        return sanitized
