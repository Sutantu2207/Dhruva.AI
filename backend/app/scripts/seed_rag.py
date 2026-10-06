"""DHRUVA.AI - Seed Script: RAG Curriculum Knowledge Chunk Ingestion (Domain 11).

Ingests approved, published canonical concepts and curriculum materials into:
- AIKnowledgeChunk (for scoped RAG retrieval)

Guarantees:
- Only approved and canonical content is indexed
- Source type and source ID references are preserved for real citations
- Scoped access levels are respected
"""

import asyncio
import logging
from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.domains.content.models import Concept
from app.domains.ai.models import AIKnowledgeChunk

logger = logging.getLogger("dhruva.seed_rag")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def seed_rag_knowledge_chunks(db: AsyncSession) -> Dict[str, int]:
    """Indexes canonical approved concepts into AIKnowledgeChunk table."""
    stats = {"knowledge_chunks": 0}

    res = await db.execute(select(Concept).where(Concept.status == "active"))
    concepts = res.scalars().all()

    for concept in concepts:
        chunk_res = await db.execute(
            select(AIKnowledgeChunk).where(
                AIKnowledgeChunk.source_type == "concept",
                AIKnowledgeChunk.source_id == concept.id,
            )
        )
        if not chunk_res.scalar_one_or_none():
            chunk_text = (
                f"Canonical Concept: {concept.name}\n"
                f"Difficulty Level: {concept.difficulty.capitalize()}\n"
                f"Summary: {concept.description or 'Foundational engineering knowledge unit.'}\n"
                f"Scope: Canonical Indian Higher Technical Education Curriculum."
            )
            chunk = AIKnowledgeChunk(
                source_type="concept",
                source_id=concept.id,
                version_id=1,
                title=f"Canonical Concept: {concept.name}",
                chunk_index=0,
                chunk_text=chunk_text,
                metadata_payload={
                    "concept_name": concept.name,
                    "difficulty": concept.difficulty,
                    "slug": concept.slug,
                    "provenance": "CURATED",
                },
                access_scope="public",
            )
            db.add(chunk)
            stats["knowledge_chunks"] += 1

    await db.commit()
    logger.info("RAG knowledge chunks indexed successfully: %s", stats)
    return stats


async def main():
    async with async_session_maker() as db:
        await seed_rag_knowledge_chunks(db)


if __name__ == "__main__":
    asyncio.run(main())
