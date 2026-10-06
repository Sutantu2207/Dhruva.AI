"""Privacy and PII Sanitization Guardrails for AI Context Construction.

MANDATORY RULE: Never expose student identity information (name, email, roll number,
registration ID, phone, etc.) to the Large Language Model.
"""

import re
from typing import Dict, Any

# Regular expressions for detecting standard PII patterns
EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_PATTERN = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
STUDENT_ID_PATTERN = re.compile(r"\b(20\d{2}[A-Z]{2,4}\d{3,5}|REG\d{6,10}|ROLL[0-9]{4,10})\b", re.IGNORECASE)

# Disallowed student identity keys
DISALLOWED_KEYS = {
    "student_name",
    "name",
    "full_name",
    "first_name",
    "last_name",
    "email",
    "phone",
    "phone_number",
    "roll_number",
    "registration_number",
    "usn",
    "ip_address",
    "address",
    "ssn",
    "national_id",
}


def sanitize_text(text: str) -> str:
    """Scrubs PII patterns from free-form text strings."""
    if not text:
        return ""
    sanitized = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    sanitized = PHONE_PATTERN.sub("[REDACTED_PHONE]", sanitized)
    sanitized = STUDENT_ID_PATTERN.sub("[REDACTED_STUDENT_ID]", sanitized)
    return sanitized


def sanitize_ai_context(raw_context: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively removes student PII from dictionary structures before AI prompt construction."""
    sanitized: Dict[str, Any] = {}

    for key, val in raw_context.items():
        lower_key = key.lower()
        if lower_key in DISALLOWED_KEYS:
            continue

        if isinstance(val, dict):
            sanitized[key] = sanitize_ai_context(val)
        elif isinstance(val, list):
            sanitized[key] = [
                sanitize_ai_context(item) if isinstance(item, dict)
                else (sanitize_text(item) if isinstance(item, str) else item)
                for item in val
            ]
        elif isinstance(val, str):
            sanitized[key] = sanitize_text(val)
        else:
            sanitized[key] = val

    return sanitized
