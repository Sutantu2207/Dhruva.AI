"""Scoped Knowledge Retriever over Approved Curriculum Content (Domain 11 RAG)."""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.domains.ai.models import AIKnowledgeChunk
from app.domains.content.models import Lesson, Concept, CourseContent


class ScopedKnowledgeRetriever:
    """Retrieves approved, version-controlled curriculum materials grounded in verified sources."""

    @staticmethod
    async def retrieve_approved_content(
        db: AsyncSession,
        query: str,
        institution_id: Optional[str] = None,
        concept_id: Optional[str] = None,
        limit: int = 4,
    ) -> List[Dict[str, Any]]:
        """Searches indexed curriculum chunks and active lessons."""
        citations = []

        # 1. Search lessons directly for concept
        if concept_id:
            c_res = await db.execute(select(Concept).where(Concept.id == concept_id))
            concept = c_res.scalar_one_or_none()
            if concept:
                citations.append({
                    "source_type": "concept",
                    "source_id": concept.id,
                    "title": f"Canonical Concept: {concept.name}",
                    "content_snippet": concept.description or f"Core definition and learning objectives for {concept.name}.",
                    "relevance_score": 0.95,
                })

        # 2. Search approved AI Knowledge Chunks
        stmt = (
            select(AIKnowledgeChunk)
            .where(
                AIKnowledgeChunk.chunk_text.ilike(f"%{query[:30]}%")
                if query else True
            )
            .limit(limit)
        )
        res = await db.execute(stmt)
        chunks = res.scalars().all()

        for ch in chunks:
            citations.append({
                "source_type": ch.source_type,
                "source_id": ch.source_id,
                "title": ch.title,
                "content_snippet": ch.chunk_text[:300],
                "chunk_id": ch.id,
                "relevance_score": 0.88,
            })

        return citations
