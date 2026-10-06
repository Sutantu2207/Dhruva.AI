"""REST Endpoints for Domain 6: Knowledge State, Concept Mastery & Spaced Repetition."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import StudentAcademicProfile
from app.domains.content.models import Concept
from app.domains.mastery.models import (
    StudentConceptKnowledgeState,
    ConceptReviewState,
)
from app.domains.mastery.service import knowledge_state_service
from app.domains.mastery.schemas import (
    ConceptKnowledgeStateResponse,
    ConceptReviewStateResponse,
    ConceptReviewCompletionPayload,
    ConceptReviewHistoryResponse,
    LearningPriorityResponse,
    DailyMissionResponse,
    DailyMissionTaskResponse,
    ConceptDetailResponse,
    StudentKnowledgeSummaryResponse,
)

router = APIRouter()


async def _resolve_student_profile(db: AsyncSession, user_id: str) -> StudentAcademicProfile:
    """Helper to resolve the student academic profile for the authenticated user."""
    stmt = select(StudentAcademicProfile).where(StudentAcademicProfile.user_id == user_id)
    res = await db.execute(stmt)
    prof = res.scalar_one_or_none()
    if not prof:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student academic profile not provisioned.",
        )
    return prof


# =========================================================================
# 1. Student Knowledge State & Overview
# =========================================================================

@router.get("/knowledge/me", response_model=StudentKnowledgeSummaryResponse)
async def get_my_knowledge_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns student aggregate knowledge summary (mastered count, developing, due reviews, averages)."""
    prof = await _resolve_student_profile(db, current_user.id)
    summary = await knowledge_state_service.get_student_knowledge_summary(db, prof.id)
    return summary


@router.get("/knowledge/me/concepts", response_model=List[ConceptKnowledgeStateResponse])
async def list_my_concept_states(
    state_filter: Optional[str] = Query(None, alias="state"),
    q: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns paginated, searchable concept knowledge states for the authenticated student."""
    prof = await _resolve_student_profile(db, current_user.id)

    stmt = (
        select(StudentConceptKnowledgeState)
        .join(Concept, StudentConceptKnowledgeState.concept_id == Concept.id)
        .where(StudentConceptKnowledgeState.student_profile_id == prof.id)
    )

    if state_filter:
        stmt = stmt.where(StudentConceptKnowledgeState.state == state_filter)

    if q:
        stmt = stmt.where(
            or_(
                Concept.name.ilike(f"%{q}%"),
                Concept.description.ilike(f"%{q}%"),
            )
        )

    stmt = stmt.order_by(StudentConceptKnowledgeState.updated_at.desc()).limit(limit).offset(offset)
    records = (await db.execute(stmt)).scalars().all()

    # Load concept names
    concept_ids = [r.concept_id for r in records]
    concepts_map = {}
    if concept_ids:
        c_stmt = select(Concept).where(Concept.id.in_(concept_ids))
        concepts_map = {c.id: c for c in (await db.execute(c_stmt)).scalars().all()}

    results = []
    for r in records:
        c = concepts_map.get(r.concept_id)
        results.append(
            ConceptKnowledgeStateResponse(
                id=r.id,
                concept_id=r.concept_id,
                concept_name=c.name if c else None,
                concept_slug=c.slug if c else None,
                current_mastery=float(r.current_mastery) if r.current_mastery is not None else None,
                confidence=float(r.confidence),
                retention_estimate=float(r.retention_estimate),
                state=r.state,
                trend=r.trend,
                evidence_count=r.evidence_count,
                first_evidence_at=r.first_evidence_at,
                last_evidence_at=r.last_evidence_at,
                last_successful_evidence_at=r.last_successful_evidence_at,
                last_failed_evidence_at=r.last_failed_evidence_at,
                prerequisite_readiness=float(r.prerequisite_readiness) if r.prerequisite_readiness is not None else None,
                prerequisite_health=r.prerequisite_health,
                algorithm_version=r.algorithm_version,
                updated_at=r.updated_at,
            )
        )
    return results


@router.get("/knowledge/me/concepts/{concept_id}", response_model=ConceptDetailResponse)
async def get_my_concept_detail(
    concept_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns detailed concept knowledge state, prerequisites, evidence history, and review state."""
    prof = await _resolve_student_profile(db, current_user.id)
    detail = await knowledge_state_service.get_concept_detail(db, prof.id, concept_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Concept not found.",
        )
    return detail


@router.get("/knowledge/me/weak-concepts", response_model=List[ConceptKnowledgeStateResponse])
async def get_my_weak_concepts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns concepts currently classified as developing or at-risk."""
    prof = await _resolve_student_profile(db, current_user.id)
    stmt = (
        select(StudentConceptKnowledgeState)
        .join(Concept, StudentConceptKnowledgeState.concept_id == Concept.id)
        .where(
            and_(
                StudentConceptKnowledgeState.student_profile_id == prof.id,
                or_(
                    StudentConceptKnowledgeState.state.in_(["developing", "at_risk"]),
                    StudentConceptKnowledgeState.current_mastery < 0.60,
                ),
            )
        )
        .order_by(StudentConceptKnowledgeState.current_mastery.asc().nullslast())
        .limit(20)
    )
    records = (await db.execute(stmt)).scalars().all()

    concept_ids = [r.concept_id for r in records]
    concepts_map = {}
    if concept_ids:
        c_stmt = select(Concept).where(Concept.id.in_(concept_ids))
        concepts_map = {c.id: c for c in (await db.execute(c_stmt)).scalars().all()}

    return [
        ConceptKnowledgeStateResponse(
            id=r.id,
            concept_id=r.concept_id,
            concept_name=concepts_map[r.concept_id].name if r.concept_id in concepts_map else None,
            concept_slug=concepts_map[r.concept_id].slug if r.concept_id in concepts_map else None,
            current_mastery=float(r.current_mastery) if r.current_mastery is not None else None,
            confidence=float(r.confidence),
            retention_estimate=float(r.retention_estimate),
            state=r.state,
            trend=r.trend,
            evidence_count=r.evidence_count,
            first_evidence_at=r.first_evidence_at,
            last_evidence_at=r.last_evidence_at,
            last_successful_evidence_at=r.last_successful_evidence_at,
            last_failed_evidence_at=r.last_failed_evidence_at,
            prerequisite_readiness=float(r.prerequisite_readiness) if r.prerequisite_readiness is not None else None,
            prerequisite_health=r.prerequisite_health,
            algorithm_version=r.algorithm_version,
            updated_at=r.updated_at,
        )
        for r in records
    ]


@router.get("/knowledge/me/at-risk", response_model=List[ConceptKnowledgeStateResponse])
async def get_my_at_risk_concepts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns concepts at immediate risk of forgetting or mastery collapse."""
    prof = await _resolve_student_profile(db, current_user.id)
    stmt = (
        select(StudentConceptKnowledgeState)
        .join(Concept, StudentConceptKnowledgeState.concept_id == Concept.id)
        .where(
            and_(
                StudentConceptKnowledgeState.student_profile_id == prof.id,
                StudentConceptKnowledgeState.state == "at_risk",
            )
        )
        .order_by(StudentConceptKnowledgeState.updated_at.desc())
    )
    records = (await db.execute(stmt)).scalars().all()

    concept_ids = [r.concept_id for r in records]
    concepts_map = {}
    if concept_ids:
        c_stmt = select(Concept).where(Concept.id.in_(concept_ids))
        concepts_map = {c.id: c for c in (await db.execute(c_stmt)).scalars().all()}

    return [
        ConceptKnowledgeStateResponse(
            id=r.id,
            concept_id=r.concept_id,
            concept_name=concepts_map[r.concept_id].name if r.concept_id in concepts_map else None,
            concept_slug=concepts_map[r.concept_id].slug if r.concept_id in concepts_map else None,
            current_mastery=float(r.current_mastery) if r.current_mastery is not None else None,
            confidence=float(r.confidence),
            retention_estimate=float(r.retention_estimate),
            state=r.state,
            trend=r.trend,
            evidence_count=r.evidence_count,
            first_evidence_at=r.first_evidence_at,
            last_evidence_at=r.last_evidence_at,
            last_successful_evidence_at=r.last_successful_evidence_at,
            last_failed_evidence_at=r.last_failed_evidence_at,
            prerequisite_readiness=float(r.prerequisite_readiness) if r.prerequisite_readiness is not None else None,
            prerequisite_health=r.prerequisite_health,
            algorithm_version=r.algorithm_version,
            updated_at=r.updated_at,
        )
        for r in records
    ]


@router.post("/knowledge/rebuild", response_model=Dict[str, Any])
async def trigger_student_knowledge_rebuild(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Triggers a safe full deterministic rebuild of knowledge states from Domain 5 evidence."""
    prof = await _resolve_student_profile(db, current_user.id)
    rebuilt_count = await knowledge_state_service.rebuild_student_knowledge_state(db, prof.id)
    return {
        "status": "success",
        "student_profile_id": prof.id,
        "rebuilt_concept_states": rebuilt_count,
        "timestamp": datetime.now().isoformat(),
    }


# =========================================================================
# 2. Spaced Repetition (SM-2) Reviews
# =========================================================================

@router.get("/reviews/me/due", response_model=List[ConceptReviewStateResponse])
async def list_due_reviews(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns concepts whose review date is due or overdue based on server clock."""
    prof = await _resolve_student_profile(db, current_user.id)
    reviews = await knowledge_state_service.get_due_reviews(db, prof.id)
    return [
        ConceptReviewStateResponse(
            id=r.id,
            concept_id=r.concept_id,
            concept_name=r.concept.name if r.concept else None,
            repetition=r.repetition,
            ease_factor=float(r.ease_factor),
            interval_days=r.interval_days,
            last_reviewed_at=r.last_reviewed_at,
            next_review_at=r.next_review_at,
            last_quality=r.last_quality,
            review_status=r.review_status,
            algorithm_version=r.algorithm_version,
        )
        for r in reviews
    ]


@router.get("/reviews/me/upcoming", response_model=List[ConceptReviewStateResponse])
async def list_upcoming_reviews(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns future scheduled reviews."""
    prof = await _resolve_student_profile(db, current_user.id)
    reviews = await knowledge_state_service.get_upcoming_reviews(db, prof.id, limit=limit)
    return [
        ConceptReviewStateResponse(
            id=r.id,
            concept_id=r.concept_id,
            concept_name=r.concept.name if r.concept else None,
            repetition=r.repetition,
            ease_factor=float(r.ease_factor),
            interval_days=r.interval_days,
            last_reviewed_at=r.last_reviewed_at,
            next_review_at=r.next_review_at,
            last_quality=r.last_quality,
            review_status=r.review_status,
            algorithm_version=r.algorithm_version,
        )
        for r in reviews
    ]


@router.post("/reviews/{concept_id}/complete", response_model=ConceptReviewStateResponse)
async def complete_review(
    concept_id: str,
    payload: ConceptReviewCompletionPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Completes a spaced repetition review trial (quality 0-5) and advances SM-2 schedule."""
    prof = await _resolve_student_profile(db, current_user.id)
    r_state, _ = await knowledge_state_service.complete_concept_review(
        db=db,
        student_profile_id=prof.id,
        concept_id=concept_id,
        quality=payload.quality,
        duration_seconds=payload.duration_seconds,
        trigger=payload.trigger or "recall_session",
    )

    c_stmt = select(Concept).where(Concept.id == concept_id)
    concept = (await db.execute(c_stmt)).scalar_one_or_none()

    return ConceptReviewStateResponse(
        id=r_state.id,
        concept_id=r_state.concept_id,
        concept_name=concept.name if concept else None,
        repetition=r_state.repetition,
        ease_factor=float(r_state.ease_factor),
        interval_days=r_state.interval_days,
        last_reviewed_at=r_state.last_reviewed_at,
        next_review_at=r_state.next_review_at,
        last_quality=r_state.last_quality,
        review_status=r_state.review_status,
        algorithm_version=r_state.algorithm_version,
    )


# =========================================================================
# 3. Learning Priority & Daily Mission
# =========================================================================

@router.get("/learning-priority/me", response_model=List[LearningPriorityResponse])
async def get_my_learning_priorities(
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns deterministic student learning priorities ranked by urgency, mastery gap, and risk."""
    prof = await _resolve_student_profile(db, current_user.id)
    priorities = await knowledge_state_service.get_student_learning_priorities(db, prof.id, limit=limit)
    return [
        LearningPriorityResponse(
            concept_id=p.concept_id,
            concept_name=p.concept_name,
            priority_score=float(p.priority_score),
            reason_codes=p.reason_codes,
            mastery_gap=float(p.mastery_gap),
            retention_risk=float(p.retention_risk),
            prerequisite_readiness=float(p.prerequisite_readiness),
            recommended_task_type=p.recommended_task_type,
            reference_lesson_id=p.reference_lesson_id,
            reference_assessment_id=p.reference_assessment_id,
        )
        for p in priorities
    ]


@router.get("/learning-priority/me/daily", response_model=DailyMissionResponse)
async def get_my_daily_mission(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Generates a structured, deduplicated daily mission for student study."""
    prof = await _resolve_student_profile(db, current_user.id)
    tasks = await knowledge_state_service.get_daily_mission(db, prof.id, max_tasks=5)
    total_mins = sum(t.estimated_minutes for t in tasks)

    return DailyMissionResponse(
        date=datetime.now().strftime("%Y-%m-%d"),
        tasks=[
            DailyMissionTaskResponse(
                task_id=t.task_id,
                task_type=t.task_type,
                title=t.title,
                concept_id=t.concept_id,
                concept_name=t.concept_name,
                priority_score=t.priority_score,
                reason_codes=t.reason_codes,
                reference_id=t.reference_id,
                estimated_minutes=t.estimated_minutes,
            )
            for t in tasks
        ],
        total_estimated_minutes=total_mins,
    )


# =========================================================================
# 4. Scoped Faculty & Institutional Views
# =========================================================================

@router.get("/students/{student_id}/knowledge", response_model=StudentKnowledgeSummaryResponse)
async def get_student_knowledge_by_id(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)
    ),
):
    """Faculty/Admin endpoint to view a specific student's aggregate knowledge state within authorized scope."""
    stmt = select(StudentAcademicProfile).where(
        or_(
            StudentAcademicProfile.id == student_id,
            StudentAcademicProfile.user_id == student_id,
        )
    )
    prof = (await db.execute(stmt)).scalar_one_or_none()
    if not prof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student academic profile not found.",
        )

    # Scoping check
    if current_user.role != UserRole.SUPER_ADMIN:
        if prof.institution_id != current_user.institution_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied across institutional boundary.",
            )

    summary = await knowledge_state_service.get_student_knowledge_summary(db, prof.id)
    return summary
