"""Test suite for AI Orchestration PII Sanitization Guardrails."""

from app.domains.ai_orchestration.privacy import sanitize_text, sanitize_ai_context


def test_sanitize_text_redacts_email_phone_roll():
    """Confirms emails, phone numbers, and roll numbers are redacted from text strings."""
    raw = "Student John Doe (email: john.doe2026@college.edu, phone: +1-555-123-4567, roll: 2024CS1045) is struggling with trees."
    sanitized = sanitize_text(raw)
    assert "john.doe2026@college.edu" not in sanitized
    assert "[REDACTED_EMAIL]" in sanitized
    assert "+1-555-123-4567" not in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "2024CS1045" not in sanitized
    assert "[REDACTED_STUDENT_ID]" in sanitized


def test_sanitize_ai_context_drops_disallowed_pii_keys():
    """Confirms sensitive student profile keys are excluded from AI payload dictionaries."""
    raw_payload = {
        "student_name": "Alice Smith",
        "email": "alice@university.edu",
        "roll_number": "REG9876543",
        "concept_name": "Binary Search Trees",
        "difficulty": "medium",
        "stats": {
            "attempts": 3,
            "user_email": "alice@university.edu",  # nested email string
        },
    }

    sanitized = sanitize_ai_context(raw_payload)
    assert "student_name" not in sanitized
    assert "email" not in sanitized
    assert "roll_number" not in sanitized
    assert sanitized["concept_name"] == "Binary Search Trees"
    assert sanitized["difficulty"] == "medium"
    assert sanitized["stats"]["attempts"] == 3
    assert "[REDACTED_EMAIL]" in sanitized["stats"]["user_email"]
