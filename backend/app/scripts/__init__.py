"""DHRUVA.AI - Domain 13 Seed & Data Ingestion Pipeline.

Provides versioned, idempotent, transaction-safe seed commands for:
- National Academic Catalog (Disciplines, Degree Types, Programs, Specializations, Skills, Careers)
- Canonical Course Catalog, Curriculums, Modules, Lessons, Concepts, and Resources
- Multi-Type Question Banks, Rubrics, Test Cases, and Assessment Blueprints
- Project Template Library and Evaluation Criteria
- Isolated Synthetic Pilot Institution ("Dhruva Demo University")
- High-Fidelity Synthetic Faculty & 50+ Student Learner Histories
- RAG Curriculum Knowledge Chunk Ingestion
"""

import os
from app.core.config import settings

DHRUVA_SEED_VERSION = "1.0.0"


def ensure_seed_safety(allow_synthetic: bool = True) -> None:
    """Safeguard preventing accidental synthetic pilot execution in production.
    
    Raises:
        RuntimeError: If attempting to seed synthetic demo data in production without explicit flag.
    """
    is_prod = str(getattr(settings, "APPLICATION_ENV", getattr(settings, "ENVIRONMENT", "development"))).lower() == "production"
    explicit_synthetic_allowed = os.getenv("ENABLE_SYNTHETIC_PILOT_DATA", "false").lower() in ("true", "1", "yes")

    if is_prod and allow_synthetic and not explicit_synthetic_allowed:
        raise RuntimeError(
            "CRITICAL DATA SAFETY VIOLATION: Execution of synthetic pilot seeding is strictly "
            "blocked in PRODUCTION environment unless ENABLE_SYNTHETIC_PILOT_DATA=true is explicitly set."
        )
