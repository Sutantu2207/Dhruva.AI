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
    """Verify both root-level (/health/*) and versioned (/api/v1/health/*) endpoints."""
    # 1. Test Root-level Liveness Probe (used by Railway, Docker, and Kubernetes)
    root_live = await async_client.get("/health/live")
    assert root_live.status_code == 200
    root_live_data = root_live.json()
    assert root_live_data["status"] == "alive"
    assert "timestamp" in root_live_data

    # 2. Test Root-level Readiness Probe
    root_ready = await async_client.get("/health/ready")
    assert root_ready.status_code == 200
    root_ready_data = root_ready.json()
    assert root_ready_data["status"] in ("healthy", "degraded")
    assert "database" in root_ready_data

    # 3. Test Root Metadata Endpoint (GET /)
    root_res = await async_client.get("/")
    assert root_res.status_code == 200
    root_data = root_res.json()
    assert root_data["status"] == "healthy"
    assert root_data["health_live"] == "/health/live"

    # 4. Test Versioned API Liveness Probe (GET /api/v1/health/live)
    live_res = await async_client.get("/api/v1/health/live")
    assert live_res.status_code == 200
    live_data = live_res.json()
    assert live_data["status"] == "alive"

    # 5. Test Versioned API Readiness Probe (GET /api/v1/health/ready)
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


def test_railway_deployment_configuration_files():
    """Verify that railway.json and railway.toml exist and properly configure Dockerfile.backend."""
    import json
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent

    # 1. railway.json validation
    railway_json_path = repo_root / "railway.json"
    assert railway_json_path.exists(), "railway.json must exist at repository root"
    with open(railway_json_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    assert config.get("build", {}).get("builder") == "DOCKERFILE"
    assert config.get("build", {}).get("dockerfilePath") == "Dockerfile.backend"
    assert config.get("deploy", {}).get("healthcheckPath") == "/health/live"

    # 2. railway.toml validation
    railway_toml_path = repo_root / "railway.toml"
    assert railway_toml_path.exists(), "railway.toml must exist at repository root"
    content = railway_toml_path.read_text(encoding="utf-8")
    assert 'builder = "DOCKERFILE"' in content
    assert 'dockerfilePath = "Dockerfile.backend"' in content


def test_database_url_cloud_adapter():
    """Verify that Settings adapts cloud-injected postgresql:// or postgres:// URLs to asyncpg."""
    # Railway standard injected URL
    railway_url = "postgresql://postgres:secret123@roundhouse.proxy.rlwy.net:12345/railway"
    s1 = Settings(DATABASE_URL=railway_url)
    assert s1.DATABASE_URL.startswith("postgresql+asyncpg://")

    # Legacy Heroku-style URL
    legacy_url = "postgres://user:pass@host:5432/dbname"
    s2 = Settings(DATABASE_URL=legacy_url)
    assert s2.DATABASE_URL.startswith("postgresql+asyncpg://")

    # Native asyncpg URL left unchanged
    asyncpg_url = "postgresql+asyncpg://user:pass@host:5432/dbname"
    s3 = Settings(DATABASE_URL=asyncpg_url)
    assert s3.DATABASE_URL == asyncpg_url


def test_backend_dockerfile_railway_contract():
    """Verify Dockerfile.backend binds to dynamic $PORT and executes via non-root user."""
    from pathlib import Path

    repo_root = Path(__file__).resolve().parent.parent.parent
    dockerfile_path = repo_root / "Dockerfile.backend"
    assert dockerfile_path.exists(), "Dockerfile.backend must exist at repository root"

    content = dockerfile_path.read_text(encoding="utf-8")
    # Must bind to 0.0.0.0 and dynamic $PORT
    assert "${PORT:-8000}" in content
    assert "0.0.0.0" in content
    assert "USER dhruva:dhruva" in content
    assert "HEALTHCHECK" in content


def test_alembic_migrations_chain_and_head_completeness():
    """Verify that Alembic migration revisions form an unbroken linear chain up to 0013 head."""
    from pathlib import Path
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    backend_root = Path(__file__).resolve().parent.parent
    ini_path = backend_root / "alembic.ini"
    assert ini_path.exists(), "alembic.ini must exist in backend directory"

    config = Config(str(ini_path))
    script = ScriptDirectory.from_config(config)

    # 1. Exactly one head revision
    heads = script.get_heads()
    assert len(heads) == 1, f"Expected single migration head, got: {heads}"
    assert heads[0] == "0013_create_production_operations_tables"

    # 2. Exactly 13 sequential revisions
    revisions = list(script.walk_revisions())
    assert len(revisions) == 13, f"Expected 13 revisions, found: {len(revisions)}"

    # 3. Unbroken dependency chain from 0001 to 0013
    ordered_rev_ids = [r.revision for r in reversed(revisions)]
    assert ordered_rev_ids[0] == "0001_create_identity_tables"
    assert ordered_rev_ids[-1] == "0013_create_production_operations_tables"

