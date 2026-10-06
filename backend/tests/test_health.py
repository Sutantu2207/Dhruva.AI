"""Test system health and architecture endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Verifies that the /api/v1/health endpoint responds with expected status structure."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "database" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_system_architecture_endpoint(async_client: AsyncClient):
    """Verifies that system architecture exposes all deterministic engines and RBAC roles."""
    response = await async_client.get("/api/v1/system/architecture")
    assert response.status_code == 200
    data = response.json()
    assert data["product"] == "Dhruva.AI"
    assert data["architecture_model"] == "Deterministic-First Hybrid Architecture"
    assert len(data["deterministic_engines"]) >= 5
    assert len(data["supported_roles"]) == 7
    assert "student" in data["supported_roles"]
    assert "institution_admin" in data["supported_roles"]
    assert data["ai_orchestration"]["pii_leak_prevention"] == "active"
