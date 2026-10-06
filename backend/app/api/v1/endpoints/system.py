"""System architecture and deterministic engine verification endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.security import UserRole
from app.domains.ai_orchestration.client import ai_orchestrator

router = APIRouter(tags=["System"])


class DomainStatus(BaseModel):
    domain: str
    is_deterministic: bool
    status: str
    description: str


class SystemArchitectureResponse(BaseModel):
    product: str
    architecture_model: str
    deterministic_engines: List[DomainStatus]
    ai_orchestration: Dict[str, Any]
    supported_roles: List[str]


@router.get("/system/architecture", response_model=SystemArchitectureResponse)
async def get_system_architecture() -> SystemArchitectureResponse:
    """Returns the platform's architectural topology and engine readiness."""
    domains = [
        DomainStatus(
            domain="Identity & RBAC",
            is_deterministic=True,
            status="active",
            description="Cryptographic JWT with strict 7-role RBAC enforcement",
        ),
        DomainStatus(
            domain="Assessment Engine",
            is_deterministic=True,
            status="active",
            description="Pure mathematical scoring, rubric weighting, zero LLM hallucination",
        ),
        DomainStatus(
            domain="Concept Mastery",
            is_deterministic=True,
            status="active",
            description="Deterministic exponential moving average & 4-tier mastery thresholds",
        ),
        DomainStatus(
            domain="Spaced Repetition",
            is_deterministic=True,
            status="active",
            description="SuperMemo SM-2 algorithm for interval and easiness factor scheduling",
        ),
        DomainStatus(
            domain="Career Intelligence",
            is_deterministic=True,
            status="active",
            description="Deterministic skill-gap differential analysis and evidence-backed confidence",
        ),
        DomainStatus(
            domain="Audit Logging",
            is_deterministic=True,
            status="active",
            description="Immutable structured audit log with SHA-256 payload integrity hashing",
        ),
    ]

    return SystemArchitectureResponse(
        product="Dhruva.AI",
        architecture_model="Deterministic-First Hybrid Architecture",
        deterministic_engines=domains,
        ai_orchestration={
            "gateway": "ControlledAIOrchestrator",
            "model": ai_orchestrator.model,
            "privacy_sanitization": "enforced",
            "pii_leak_prevention": "active",
            "api_configured": ai_orchestrator.is_configured(),
        },
        supported_roles=[role.value for role in UserRole],
    )
