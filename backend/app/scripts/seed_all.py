"""DHRUVA.AI - Master Seed Orchestrator (Domain 13).

Runs complete, idempotent data seeding across all sub-modules:
1. National Academic Catalog (Disciplines, Degrees, Programs, Skills, Careers)
2. Canonical Courses, Concepts, and Prerequisite DAG
3. Question Banks, Multi-Type Questions, Rubrics, and Assessments
4. Synthetic Pilot Institution (Dhruva Demo University) & 50+ Student Histories
5. RAG Curriculum Knowledge Ingestion

Usage:
  python -m app.scripts.seed_all
"""

import asyncio
import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker, async_engine, Base
from app.core.config import settings
from app.scripts import DHRUVA_SEED_VERSION, ensure_seed_safety
from app.scripts.seed_catalog import seed_academic_catalog
from app.scripts.seed_courses import seed_courses_and_concepts
from app.scripts.seed_questions import seed_question_banks_and_assessments
from app.scripts.seed_demo_institution import seed_demo_institution_and_cohort
from app.scripts.seed_rag import seed_rag_knowledge_chunks

logger = logging.getLogger("dhruva.seed_all")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def run_master_seed() -> None:
    """Executes the complete Domain 13 seed and ingestion pipeline."""
    start_time = time.perf_counter()
    logger.info("================================================================")
    logger.info("DHRUVA.AI — DOMAIN 13 MASTER SEED PIPELINE (Version %s)", DHRUVA_SEED_VERSION)
    logger.info("================================================================")

    # 1. Environment Safety Check
    ensure_seed_safety(allow_synthetic=True)
    logger.info("Safety Check: PASS. Safe to proceed with pilot data provisioning.")

    # In development or test, ensure schemas exist
    if str(getattr(settings, "APPLICATION_ENV", getattr(settings, "ENVIRONMENT", "development"))).lower() != "production":
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schemas verified.")

    async with async_session_maker() as db:
        # Phase 1: National Academic Catalog
        logger.info("\n--- Phase 1: Seeding National Academic Catalog ---")
        cat_stats = await seed_academic_catalog(db)

        # Phase 2: Canonical Courses & Concept DAG
        logger.info("\n--- Phase 2: Seeding Canonical Courses & Concepts ---")
        course_stats = await seed_courses_and_concepts(db)

        # Phase 3: Question Banks & Assessments
        logger.info("\n--- Phase 3: Seeding Question Banks & Assessments ---")
        q_stats = await seed_question_banks_and_assessments(db)

        # Phase 4: Pilot University & 50+ Student Cohort
        logger.info("\n--- Phase 4: Seeding Pilot Institution & Student Histories ---")
        pilot_stats = await seed_demo_institution_and_cohort(db)

        # Phase 5: RAG Curriculum Indexing
        logger.info("\n--- Phase 5: Indexing RAG Curriculum Knowledge ---")
        rag_stats = await seed_rag_knowledge_chunks(db)

    elapsed = time.perf_counter() - start_time
    logger.info("================================================================")
    logger.info("MASTER SEED COMPLETED SUCCESSFULLY in %.2f seconds", elapsed)
    logger.info("Catalog Records:     %s", sum(cat_stats.values()))
    logger.info("Course & Concepts:   %s", sum(course_stats.values()))
    logger.info("Assessment Records:  %s", sum(q_stats.values()))
    logger.info("Pilot Inst Records:  %s", sum(pilot_stats.values()))
    logger.info("RAG Knowledge Chunks: %s", sum(rag_stats.values()))
    logger.info("================================================================")


def main():
    asyncio.run(run_master_seed())


if __name__ == "__main__":
    main()
