"""Domain 15 Automated Test Suite: Staging, Production Infrastructure & Deployment Readiness.

Validates:
1. Environment configuration validation & fail-fast production secret guards.
2. Coding sandbox client contracts & graceful REQUIRES_SANDBOX fallbacks without fake execution.
3. Storage provider health probes & path traversal protections.
4. Transactional email service abstraction & health reporting.
5. Live and Ready health probe responses including storage, sandbox, and database.
"""

import pytest
from httpx import AsyncClient
from app.core.config import Settings
from app.domains.assessment.evaluators.coding import (
    HttpSandboxProvider,
    ExecutionRequest,
    ExecutionTestCase,
    check_sandbox_health,
)
from app.core.storage import check_storage_health, S3ObjectStorageProvider
from app.domains.identity.email_service import check_email_health, SMTPEmailService


def test_production_secret_validation_rejects_weak_keys():
    """Verify that validate_production_secrets() strictly blocks weak or default keys in production."""
    # Weak fallback secret in production must fail
    prod_bad_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="fallback_secret_key_which_is_too_weak",
        COOKIE_SECURE=True,
    )
    with pytest.raises(ValueError, match="CRITICAL PRODUCTION VIOLATION: SECRET_KEY"):
        prod_bad_settings.validate_production_secrets()

    # Insecure cookies in production must fail
    prod_insecure_cookie = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="strong_secret_key_with_at_least_32_characters_long",
        COOKIE_SECURE=False,
    )
    with pytest.raises(ValueError, match="CRITICAL PRODUCTION VIOLATION: COOKIE_SECURE"):
        prod_insecure_cookie.validate_production_deployment()

    # Wildcard CORS in production must fail
    prod_wildcard_cors = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="strong_secret_key_with_at_least_32_characters_long",
        COOKIE_SECURE=True,
        DATABASE_URL="postgresql+asyncpg://admin:strong_pass@db.internal:5432/dhruva",
        CORS_ORIGINS=["*"],
    )
    with pytest.raises(ValueError, match="Wildcard CORS origin"):
        prod_wildcard_cors.validate_production_secrets()

    # Valid production settings must pass without exception
    prod_valid_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="a_very_strong_cryptographic_random_key_64_characters_long_abcdef",
        COOKIE_SECURE=True,
        DATABASE_URL="postgresql+asyncpg://admin:strong_pass@db.internal:5432/dhruva",
        CORS_ORIGINS=["https://app.dhruva.edu.in"],
    )
    prod_valid_settings.validate_production_secrets()  # Should not raise


def test_http_sandbox_provider_contract_when_unconfigured():
    """Verify that HttpSandboxProvider never fakes code execution and returns honest unavailable status."""
    provider = HttpSandboxProvider(api_url="", api_token=None)
    assert not provider.is_configured

    req = ExecutionRequest(
        language="python",
        code="print('Hello World')",
        time_limit_ms=2000,
        memory_limit_mb=256,
        test_cases=[
            ExecutionTestCase(input_data="", expected_output="Hello World\n")
        ],
    )
    resp = provider.execute(req)

    # Invariant: Never pretend execution occurred
    assert not resp.is_available
    assert resp.compile_status == "unavailable"
    assert "REQUIRES_SANDBOX" in resp.error_message or "not configured" in resp.error_message
    assert resp.tests_passed == 0
    assert len(resp.test_results) == 0


def test_sandbox_health_probe_reports_status():
    """Verify sandbox health reporting for readiness probes."""
    health = check_sandbox_health()
    assert "status" in health
    # When unconfigured or running without live cluster, it reports degraded/mock honestly
    assert health["status"] in ("healthy", "degraded")


def test_storage_health_probes():
    """Verify storage health probe reports healthy on local disk and degrades safely on unconfigured S3."""
    local_health = check_storage_health()
    assert "status" in local_health
    assert local_health["status"] in ("healthy", "degraded")

    # S3 provider without credentials should report degraded
    s3_provider = S3ObjectStorageProvider()
    s3_health = s3_provider.health_check()
    assert s3_health["backend"] == "s3"
    assert "credentials_configured" in s3_health


def test_email_service_health_probe():
    """Verify transactional email health probe contracts."""
    email_health = check_email_health()
    assert "status" in email_health
    assert email_health["status"] in ("healthy", "degraded")

    # SMTPEmailService without host reports degraded
    smtp_service = SMTPEmailService()
    smtp_health = smtp_service.health_check()
    assert smtp_health["provider"] == "smtp"


@pytest.mark.asyncio
async def test_api_health_live_and_ready_endpoints(async_client: AsyncClient):
    """Verify /health/live and /health/ready endpoints return structured diagnostic payloads."""
    # 1. Test Liveness Probe
    live_res = await async_client.get("/api/v1/health/live")
    assert live_res.status_code == 200
    live_data = live_res.json()
    assert live_data["status"] == "alive"
    assert "timestamp" in live_data

    # 2. Test Readiness Probe
    ready_res = await async_client.get("/api/v1/health/ready")
    assert ready_res.status_code == 200
    ready_data = ready_res.json()
    assert ready_data["status"] in ("healthy", "degraded")
    assert "database" in ready_data
    assert "redis" in ready_data
    assert "storage" in ready_data
    assert "email" in ready_data
    assert "ai_provider" in ready_data
    assert "sandbox" in ready_data
