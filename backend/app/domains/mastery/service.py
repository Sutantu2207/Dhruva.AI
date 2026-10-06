"""Transactional Service Layer for Domain 6: Knowledge State, Mastery & Spaced Repetition."""

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.domains.academic.models import StudentAcademicProfile
from app.domains.content.models import Concept, ConceptPrerequisite, LessonConcept, Lesson
from app.domains.assessment.models import ConceptEvidence, QuestionVersion, Assessment
from app.domains.mastery.models import (
    StudentConceptKnowledgeState,
    KnowledgeStateHistory,
    ConceptEvidenceProcessing,
    ConceptReviewState,
    ConceptReviewHistory,
    LearningPrioritySnapshot,
    MasteryAdjustment,
)
from app.domains.mastery.clock import Clock, SystemClock
from app.domains.mastery.config import KnowledgeStateConfig, DEFAULT_KNOWLEDGE_CONFIG
from app.domains.mastery.mastery_engine import ConceptMasteryEngine, EvidenceItemDTO, MasteryEvaluationOutput
from app.domains.mastery.retention_engine import RetentionEngine
from app.domains.mastery.sm2_scheduler import SM2Scheduler
from app.domains.mastery.prerequisite_engine import PrerequisiteReadinessEngine
from app.domains.mastery.priority_engine import (
    LearningPriorityEngine,
    ConceptStateContext,
    PriorityEvaluationResult,
    DailyMissionTask,
)


def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class KnowledgeStateService:
    """Enterprise service managing student knowledge states, mastery calculations, and SM-2."""

    def __init__(
        self,
        clock: Clock = SystemClock(),
        config: KnowledgeStateConfig = DEFAULT_KNOWLEDGE_CONFIG,
    ):
        self.clock = clock
        self.config = config

    # =========================================================================
    # 1. Evidence Ingestion & Deterministic Recalculation
    # =========================================================================

    async def ingest_concept_evidence(
        self,
        db: AsyncSession,
        evidence_id: str,
        trigger: str = "assessment_evidence",
    ) -> Optional[StudentConceptKnowledgeState]:
        """Idempotently processes a Domain 5 ConceptEvidence record into the student's knowledge state."""
        # 1. Idempotency Check: Was this evidence already processed?
        proc_stmt = select(ConceptEvidenceProcessing).where(
            ConceptEvidenceProcessing.evidence_id == evidence_id
        )
        existing_proc = (await db.execute(proc_stmt)).scalar_one_or_none()
        if existing_proc:
            # Already processed; retrieve existing state without double-counting
            state_stmt = select(StudentConceptKnowledgeState).where(
                and_(
                    StudentConceptKnowledgeState.student_profile_id == existing_proc.student_profile_id,
                    StudentConceptKnowledgeState.concept_id == existing_proc.concept_id,
                )
            )
            return (await db.execute(state_stmt)).scalar_one_or_none()

        # 2. Fetch Evidence Record
        ev_stmt = select(ConceptEvidence).where(ConceptEvidence.id == evidence_id)
        evidence = (await db.execute(ev_stmt)).scalar_one_or_none()
        if not evidence:
            return None

        student_profile_id = evidence.student_profile_id
        concept_id = evidence.concept_id
        now = self.clock.now()

        # 3. Fetch all historical evidence for this (student, concept)
        all_ev_stmt = (
            select(ConceptEvidence)
            .where(
                and_(
                    ConceptEvidence.student_profile_id == student_profile_id,
                    ConceptEvidence.concept_id == concept_id,
                )
            )
            .order_by(ConceptEvidence.timestamp.asc())
        )
        all_ev_records = (await db.execute(all_ev_stmt)).scalars().all()

        qv_ids = [ev.question_version_id for ev in all_ev_records if ev.question_version_id]
        qv_map: Dict[str, QuestionVersion] = {}
        if qv_ids:
            qv_stmt = select(QuestionVersion).where(QuestionVersion.id.in_(qv_ids))
            qv_map = {qv.id: qv for qv in (await db.execute(qv_stmt)).scalars().all()}

        evidence_dtos: List[EvidenceItemDTO] = []
        for ev in all_ev_records:
            diff = "medium"
            qv = qv_map.get(ev.question_version_id)
            if qv and hasattr(qv, "difficulty"):
                diff = qv.difficulty or "medium"

            evidence_dtos.append(
                EvidenceItemDTO(
                    id=ev.id,
                    concept_id=ev.concept_id,
                    score=ev.score,
                    max_score=ev.max_score,
                    evidence_type=ev.evidence_type,
                    difficulty=diff,
                    timestamp=ev.timestamp,
                )
            )

        # 4. Fetch existing knowledge state (if any)
        state_stmt = select(StudentConceptKnowledgeState).where(
            and_(
                StudentConceptKnowledgeState.student_profile_id == student_profile_id,
                StudentConceptKnowledgeState.concept_id == concept_id,
            )
        )
        k_state = (await db.execute(state_stmt)).scalar_one_or_none()
        previous_state_str = k_state.state if k_state else None
        previous_mastery_val = k_state.current_mastery if k_state else None

        # 5. Evaluate Mastery Deterministically
        eval_result = ConceptMasteryEngine.evaluate(
            concept_id=concept_id,
            evidence_items=evidence_dtos,
            previous_state=previous_state_str,
            config=self.config,
            now=now,
        )

        # 6. Fetch or initialize SM-2 Review State to calculate retention
        review_stmt = select(ConceptReviewState).where(
            and_(
                ConceptReviewState.student_profile_id == student_profile_id,
                ConceptReviewState.concept_id == concept_id,
            )
        )
        r_state = (await db.execute(review_stmt)).scalar_one_or_none()
        if not r_state:
            initial_sm2 = SM2Scheduler.initialize_schedule(now=now, config=self.config.sm2)
            r_state = ConceptReviewState(
                id=str(uuid.uuid4()),
                student_profile_id=student_profile_id,
                concept_id=concept_id,
                repetition=initial_sm2.repetition,
                ease_factor=initial_sm2.ease_factor,
                interval_days=initial_sm2.interval_days,
                last_reviewed_at=eval_result.last_evidence_at,
                next_review_at=initial_sm2.next_review_at,
                review_status=initial_sm2.review_status,
                algorithm_version=self.config.sm2_algorithm_version if hasattr(self.config, "sm2_algorithm_version") else "sm2-v1",
            )
            db.add(r_state)
            await db.flush()

        # 7. Evaluate Retention Deterministically
        last_event = eval_result.last_evidence_at or r_state.last_reviewed_at
        retention_estimate = RetentionEngine.estimate_retention(
            last_event_at=last_event,
            interval_days=r_state.interval_days,
            ease_factor=r_state.ease_factor,
            now=now,
            config=self.config.retention,
        )

        # 8. Evaluate Prerequisite Readiness
        prereq_graph, student_masteries = await self._fetch_prerequisites_and_masteries(
            db, student_profile_id, concept_id
        )
        readiness_score, health_status = PrerequisiteReadinessEngine.evaluate_readiness(
            target_concept_id=concept_id,
            prerequisite_graph=prereq_graph,
            student_masteries=student_masteries,
        )

        # 9. Upsert StudentConceptKnowledgeState
        if not k_state:
            k_state = StudentConceptKnowledgeState(
                id=str(uuid.uuid4()),
                student_profile_id=student_profile_id,
                concept_id=concept_id,
                current_mastery=eval_result.mastery,
                confidence=eval_result.confidence,
                retention_estimate=retention_estimate,
                state=eval_result.state,
                trend=eval_result.trend,
                evidence_count=eval_result.evidence_count,
                first_evidence_at=eval_result.first_evidence_at,
                last_evidence_at=eval_result.last_evidence_at,
                last_successful_evidence_at=eval_result.last_successful_at,
                last_failed_evidence_at=eval_result.last_failed_at,
                prerequisite_readiness=readiness_score,
                prerequisite_health=health_status,
                algorithm_version=self.config.algorithm_version,
            )
            db.add(k_state)
            await db.flush()
        else:
            k_state.current_mastery = eval_result.mastery
            k_state.confidence = eval_result.confidence
            k_state.retention_estimate = retention_estimate
            k_state.state = eval_result.state
            k_state.trend = eval_result.trend
            k_state.evidence_count = eval_result.evidence_count
            k_state.first_evidence_at = eval_result.first_evidence_at
            k_state.last_evidence_at = eval_result.last_evidence_at
            k_state.last_successful_evidence_at = eval_result.last_successful_at
            k_state.last_failed_evidence_at = eval_result.last_failed_at
            k_state.prerequisite_readiness = readiness_score
            k_state.prerequisite_health = health_status
            k_state.algorithm_version = self.config.algorithm_version

        # 10. Record History Ledger
        change_val = None
        if previous_mastery_val is not None and eval_result.mastery is not None:
            change_val = eval_result.mastery - previous_mastery_val

        history = KnowledgeStateHistory(
            id=str(uuid.uuid4()),
            knowledge_state_id=k_state.id,
            student_profile_id=student_profile_id,
            concept_id=concept_id,
            previous_mastery=previous_mastery_val,
            new_mastery=eval_result.mastery,
            change=change_val,
            confidence=eval_result.confidence,
            retention_estimate=retention_estimate,
            state=eval_result.state,
            trend=eval_result.trend,
            trigger=trigger,
            algorithm_version=self.config.algorithm_version,
            timestamp=now,
        )
        db.add(history)

        # 11. Mark evidence as processed (Idempotency guarantee)
        proc_record = ConceptEvidenceProcessing(
            id=str(uuid.uuid4()),
            evidence_id=evidence_id,
            student_profile_id=student_profile_id,
            concept_id=concept_id,
            evidence_score=evidence.score,
            algorithm_version=self.config.algorithm_version,
            processed_at=now,
        )
        db.add(proc_record)

        await db.commit()
        await db.refresh(k_state)
        return k_state

    # =========================================================================
    # 2. Review Completion & SM-2 Transitions
    # =========================================================================

    async def complete_concept_review(
        self,
        db: AsyncSession,
        student_profile_id: str,
        concept_id: str,
        quality: int,
        duration_seconds: Optional[int] = None,
        trigger: str = "recall_session",
    ) -> Tuple[ConceptReviewState, StudentConceptKnowledgeState]:
        """Records student review recall quality (0-5) and advances SM-2 schedule and retention."""
        if not (0 <= quality <= 5):
            raise ValueError(f"Quality must be between 0 and 5, received {quality}")

        now = self.clock.now()

        # 1. Fetch or initialize Review State
        r_stmt = select(ConceptReviewState).where(
            and_(
                ConceptReviewState.student_profile_id == student_profile_id,
                ConceptReviewState.concept_id == concept_id,
            )
        )
        r_state = (await db.execute(r_stmt)).scalar_one_or_none()

        if not r_state:
            initial = SM2Scheduler.initialize_schedule(now=now, config=self.config.sm2)
            r_state = ConceptReviewState(
                id=str(uuid.uuid4()),
                student_profile_id=student_profile_id,
                concept_id=concept_id,
                repetition=initial.repetition,
                ease_factor=initial.ease_factor,
                interval_days=initial.interval_days,
                last_reviewed_at=now,
                next_review_at=initial.next_review_at,
                review_status=initial.review_status,
                algorithm_version="sm2-v1",
            )
            db.add(r_state)
            await db.flush()

        prev_interval = r_state.interval_days
        prev_ease = r_state.ease_factor
        prev_repetition = r_state.repetition

        # 2. Advance SM-2 Schedule
        schedule_res = SM2Scheduler.calculate_next_schedule(
            quality=quality,
            previous_repetition=prev_repetition,
            previous_interval_days=prev_interval,
            previous_ease_factor=prev_ease,
            now=now,
            config=self.config.sm2,
        )

        r_state.repetition = schedule_res.repetition
        r_state.interval_days = schedule_res.interval_days
        r_state.ease_factor = schedule_res.ease_factor
        r_state.last_reviewed_at = now
        r_state.next_review_at = schedule_res.next_review_at
        r_state.last_quality = quality
        r_state.review_status = schedule_res.review_status

        # 3. Record Review History Audit
        rev_history = ConceptReviewHistory(
            id=str(uuid.uuid4()),
            review_state_id=r_state.id,
            student_profile_id=student_profile_id,
            concept_id=concept_id,
            quality=quality,
            previous_interval=prev_interval,
            new_interval=schedule_res.interval_days,
            previous_ease=prev_ease,
            new_ease=schedule_res.ease_factor,
            duration_seconds=duration_seconds,
            trigger=trigger,
            algorithm_version="sm2-v1",
            reviewed_at=now,
        )
        db.add(rev_history)

        # 4. Update Knowledge State Retention
        k_stmt = select(StudentConceptKnowledgeState).where(
            and_(
                StudentConceptKnowledgeState.student_profile_id == student_profile_id,
                StudentConceptKnowledgeState.concept_id == concept_id,
            )
        )
        k_state = (await db.execute(k_stmt)).scalar_one_or_none()

        new_retention = RetentionEngine.estimate_retention(
            last_event_at=now,
            interval_days=schedule_res.interval_days,
            ease_factor=schedule_res.ease_factor,
            now=now,
            config=self.config.retention,
        )

        if k_state:
            k_state.retention_estimate = new_retention
            if quality >= 3:
                k_state.last_successful_evidence_at = now
            else:
                k_state.last_failed_evidence_at = now

            # If failed recall (quality < 3) and previously mastered, flag as at_risk
            if quality < 3 and k_state.state in ("mastered", "proficient"):
                k_state.state = "at_risk"

            # History entry for review completion
            history = KnowledgeStateHistory(
                id=str(uuid.uuid4()),
                knowledge_state_id=k_state.id,
                student_profile_id=student_profile_id,
                concept_id=concept_id,
                previous_mastery=k_state.current_mastery,
                new_mastery=k_state.current_mastery,
                change=Decimal("0.0000"),
                confidence=k_state.confidence,
                retention_estimate=new_retention,
                state=k_state.state,
                trend=k_state.trend,
                trigger="recall_evidence",
                algorithm_version=self.config.algorithm_version,
                timestamp=now,
            )
            db.add(history)

        await db.commit()
        await db.refresh(r_state)
        if k_state:
            await db.refresh(k_state)
        return r_state, k_state

    # =========================================================================
    # 3. Full Knowledge Rebuild (Deterministic & Safe)
    # =========================================================================

    async def rebuild_student_knowledge_state(
        self,
        db: AsyncSession,
        student_profile_id: str,
    ) -> int:
        """Deterministically rebuilds all student concept knowledge states and SM-2 schedules from source evidence.
        
        Guarantees:
        - Never mutates or deletes historical Domain 5 ConceptEvidence records.
        - Idempotently re-evaluates all concepts.
        """
        now = self.clock.now()

        # 1. Fetch all ConceptEvidence for this student
        ev_stmt = (
            select(ConceptEvidence)
            .where(ConceptEvidence.student_profile_id == student_profile_id)
            .order_by(ConceptEvidence.timestamp.asc())
        )
        all_ev = (await db.execute(ev_stmt)).scalars().all()
        if not all_ev:
            return 0

        # Group by concept_id
        grouped: Dict[str, List[ConceptEvidence]] = {}
        for ev in all_ev:
            grouped.setdefault(ev.concept_id, []).append(ev)

        rebuilt_count = 0
        for concept_id, ev_list in grouped.items():
            for ev in ev_list:
                # Ingest each evidence chronologically
                await self.ingest_concept_evidence(db, ev.id, trigger="system_rebuild")
            rebuilt_count += 1

        return rebuilt_count

    # =========================================================================
    # 4. Learning Priority & Daily Mission Generator
    # =========================================================================

    async def get_student_learning_priorities(
        self,
        db: AsyncSession,
        student_profile_id: str,
        limit: int = 20,
    ) -> List[PriorityEvaluationResult]:
        """Calculates normalized learning priorities across all active student concepts."""
        now = self.clock.now()

        # Fetch all knowledge states with concepts
        stmt = (
            select(StudentConceptKnowledgeState)
            .options(selectinload(StudentConceptKnowledgeState.concept))
            .where(StudentConceptKnowledgeState.student_profile_id == student_profile_id)
        )
        states = (await db.execute(stmt)).scalars().all()
        if not states:
            return []

        # Fetch review states
        r_stmt = select(ConceptReviewState).where(
            ConceptReviewState.student_profile_id == student_profile_id
        )
        review_states = {r.concept_id: r for r in (await db.execute(r_stmt)).scalars().all()}

        # Fetch lesson mappings for concrete referencing
        lesson_stmt = (
            select(LessonConcept)
            .options(selectinload(LessonConcept.lesson))
        )
        lesson_mappings = (await db.execute(lesson_stmt)).scalars().all()
        concept_to_lesson: Dict[str, str] = {}
        for lm in lesson_mappings:
            if lm.concept_id not in concept_to_lesson and lm.lesson_id:
                concept_to_lesson[lm.concept_id] = lm.lesson_id

        priority_results: List[PriorityEvaluationResult] = []

        for st in states:
            r_st = review_states.get(st.concept_id)
            review_status = "upcoming"
            if r_st:
                review_status = SM2Scheduler.classify_status(r_st.next_review_at, now)

            has_recent_failure = False
            if st.last_failed_evidence_at:
                if st.last_successful_evidence_at is None or st.last_failed_evidence_at >= st.last_successful_evidence_at:
                    has_recent_failure = True

            c_name = st.concept.name if st.concept else "Canonical Concept"

            ctx = ConceptStateContext(
                concept_id=st.concept_id,
                concept_name=c_name,
                mastery=st.current_mastery,
                retention_estimate=st.retention_estimate,
                review_status=review_status,
                prerequisite_health=st.prerequisite_health,
                prerequisite_readiness=st.prerequisite_readiness,
                trend=st.trend,
                has_recent_failure=has_recent_failure,
                evidence_count=st.evidence_count,
                lesson_id=concept_to_lesson.get(st.concept_id),
            )

            res = LearningPriorityEngine.evaluate_concept_priority(
                ctx=ctx, weights=self.config.priority_weights
            )
            priority_results.append(res)

        # Sort descending
        priority_results.sort(key=lambda x: x.priority_score, reverse=True)
        return priority_results[:limit]

    async def get_daily_mission(
        self,
        db: AsyncSession,
        student_profile_id: str,
        max_tasks: int = 5,
    ) -> List[DailyMissionTask]:
        """Generates a structured, deterministic daily mission of actionable study tasks."""
        priorities = await self.get_student_learning_priorities(db, student_profile_id, limit=30)
        return LearningPriorityEngine.generate_daily_mission(priorities, max_tasks=max_tasks)

    # =========================================================================
    # 5. Concept Details & Query APIs
    # =========================================================================

    async def get_student_knowledge_summary(
        self,
        db: AsyncSession,
        student_profile_id: str,
    ) -> Dict[str, Any]:
        """Produces aggregate statistics of student knowledge states and reviews."""
        now = self.clock.now()

        # Student info
        p_stmt = select(StudentAcademicProfile).options(selectinload(StudentAcademicProfile.user_id)).where(
            StudentAcademicProfile.id == student_profile_id
        )
        prof = (await db.execute(select(StudentAcademicProfile).where(StudentAcademicProfile.id == student_profile_id))).scalar_one_or_none()

        stmt = select(StudentConceptKnowledgeState).where(
            StudentConceptKnowledgeState.student_profile_id == student_profile_id
        )
        states = (await db.execute(stmt)).scalars().all()

        total = len(states)
        mastered = sum(1 for s in states if s.state == "mastered")
        proficient = sum(1 for s in states if s.state == "proficient")
        developing = sum(1 for s in states if s.state == "developing")
        introduced = sum(1 for s in states if s.state == "introduced")
        at_risk = sum(1 for s in states if s.state == "at_risk")

        mastery_vals = [float(s.current_mastery) for s in states if s.current_mastery is not None]
        avg_mastery = round(sum(mastery_vals) / len(mastery_vals), 4) if mastery_vals else None

        retention_vals = [float(s.retention_estimate) for s in states]
        avg_retention = round(sum(retention_vals) / len(retention_vals), 4) if retention_vals else 1.0

        # Due reviews
        due_stmt = select(func.count(ConceptReviewState.id)).where(
            and_(
                ConceptReviewState.student_profile_id == student_profile_id,
                ConceptReviewState.next_review_at <= now,
            )
        )
        due_count = (await db.execute(due_stmt)).scalar() or 0

        return {
            "student_profile_id": student_profile_id,
            "student_name": prof.enrollment_number if prof else "Student",
            "total_concepts_tracked": total,
            "mastered_count": mastered,
            "proficient_count": proficient,
            "developing_count": developing,
            "introduced_count": introduced,
            "at_risk_count": at_risk,
            "due_reviews_count": due_count,
            "average_mastery": avg_mastery,
            "average_retention": avg_retention,
        }

    async def get_due_reviews(
        self,
        db: AsyncSession,
        student_profile_id: str,
    ) -> List[ConceptReviewState]:
        """Returns review schedule states that are due or overdue."""
        now = self.clock.now()
        stmt = (
            select(ConceptReviewState)
            .options(selectinload(ConceptReviewState.concept))
            .where(
                and_(
                    ConceptReviewState.student_profile_id == student_profile_id,
                    ConceptReviewState.next_review_at <= now,
                )
            )
            .order_by(ConceptReviewState.next_review_at.asc())
        )
        reviews = (await db.execute(stmt)).scalars().all()
        for r in reviews:
            r.review_status = SM2Scheduler.classify_status(r.next_review_at, now)
        return list(reviews)

    async def get_upcoming_reviews(
        self,
        db: AsyncSession,
        student_profile_id: str,
        limit: int = 20,
    ) -> List[ConceptReviewState]:
        """Returns future scheduled reviews."""
        now = self.clock.now()
        stmt = (
            select(ConceptReviewState)
            .options(selectinload(ConceptReviewState.concept))
            .where(
                and_(
                    ConceptReviewState.student_profile_id == student_profile_id,
                    ConceptReviewState.next_review_at > now,
                )
            )
            .order_by(ConceptReviewState.next_review_at.asc())
            .limit(limit)
        )
        return list((await db.execute(stmt)).scalars().all())

    async def get_concept_detail(
        self,
        db: AsyncSession,
        student_profile_id: str,
        concept_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Returns detailed concept knowledge state, prerequisites, evidence history, and review state."""
        c_stmt = select(Concept).where(Concept.id == concept_id)
        concept = (await db.execute(c_stmt)).scalar_one_or_none()
        if not concept:
            return None

        now = self.clock.now()

        # Knowledge State
        k_stmt = (
            select(StudentConceptKnowledgeState)
            .options(selectinload(StudentConceptKnowledgeState.history_entries))
            .where(
                and_(
                    StudentConceptKnowledgeState.student_profile_id == student_profile_id,
                    StudentConceptKnowledgeState.concept_id == concept_id,
                )
            )
        )
        k_state = (await db.execute(k_stmt)).scalar_one_or_none()

        # Review State
        r_stmt = select(ConceptReviewState).where(
            and_(
                ConceptReviewState.student_profile_id == student_profile_id,
                ConceptReviewState.concept_id == concept_id,
            )
        )
        r_state = (await db.execute(r_stmt)).scalar_one_or_none()
        if r_state:
            r_state.review_status = SM2Scheduler.classify_status(r_state.next_review_at, now)

        # Prerequisites
        prereq_stmt = (
            select(ConceptPrerequisite)
            .options(selectinload(ConceptPrerequisite.prerequisite_concept))
            .where(ConceptPrerequisite.concept_id == concept_id)
        )
        prereqs = (await db.execute(prereq_stmt)).scalars().all()

        # Masteries for prerequisites
        prereq_ids = [p.prerequisite_concept_id for p in prereqs]
        p_masteries: Dict[str, StudentConceptKnowledgeState] = {}
        if prereq_ids:
            pm_stmt = select(StudentConceptKnowledgeState).where(
                and_(
                    StudentConceptKnowledgeState.student_profile_id == student_profile_id,
                    StudentConceptKnowledgeState.concept_id.in_(prereq_ids),
                )
            )
            p_masteries = {m.concept_id: m for m in (await db.execute(pm_stmt)).scalars().all()}

        prereq_list = []
        for p in prereqs:
            pm = p_masteries.get(p.prerequisite_concept_id)
            prereq_list.append({
                "concept_id": p.prerequisite_concept_id,
                "concept_name": p.prerequisite_concept.name if p.prerequisite_concept else "Prerequisite",
                "relationship_type": p.relationship_type,
                "mastery": float(pm.current_mastery) if (pm and pm.current_mastery is not None) else None,
                "state": pm.state if pm else "unknown",
            })

        # Evidence records
        ev_stmt = (
            select(ConceptEvidence)
            .where(
                and_(
                    ConceptEvidence.student_profile_id == student_profile_id,
                    ConceptEvidence.concept_id == concept_id,
                )
            )
            .order_by(ConceptEvidence.timestamp.desc())
            .limit(20)
        )
        ev_records = (await db.execute(ev_stmt)).scalars().all()
        evidence_history = [
            {
                "id": ev.id,
                "score": float(ev.score),
                "max_score": float(ev.max_score),
                "evidence_type": ev.evidence_type,
                "timestamp": ev.timestamp.isoformat(),
            }
            for ev in ev_records
        ]

        mastery_history = k_state.history_entries if k_state else []

        # Explanation
        explanation = {
            "evidence_observations": len(ev_records),
            "state": k_state.state if k_state else "unknown",
            "trend": k_state.trend if k_state else "insufficient_data",
            "retention_estimate": float(k_state.retention_estimate) if k_state else 1.0,
            "prerequisite_health": k_state.prerequisite_health if k_state else "healthy",
            "prerequisite_readiness": float(k_state.prerequisite_readiness) if (k_state and k_state.prerequisite_readiness is not None) else None,
            "algorithm_version": self.config.algorithm_version,
            "explainable_summary": (
                f"Mastery categorized as {k_state.state.upper()} based on {k_state.evidence_count} evidence records. "
                f"Retention currently estimated at {int(float(k_state.retention_estimate)*100)}%."
                if k_state
                else "No evidence observations recorded yet. Complete lessons or assessments to establish knowledge state."
            ),
        }

        return {
            "concept_id": concept.id,
            "name": concept.name,
            "slug": concept.slug,
            "description": concept.description,
            "difficulty": concept.difficulty,
            "knowledge_state": k_state,
            "review_state": r_state,
            "prerequisites": prereq_list,
            "prerequisite_readiness": float(k_state.prerequisite_readiness) if (k_state and k_state.prerequisite_readiness is not None) else None,
            "prerequisite_health": k_state.prerequisite_health if k_state else "healthy",
            "evidence_history": evidence_history,
            "mastery_history": mastery_history,
            "explanation": explanation,
        }

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    async def _fetch_prerequisites_and_masteries(
        self,
        db: AsyncSession,
        student_profile_id: str,
        target_concept_id: str,
    ) -> Tuple[Dict[str, List[str]], Dict[str, Optional[Decimal]]]:
        """Fetches prerequisite graph edges and student's current mastery for prerequisite concepts."""
        p_stmt = select(ConceptPrerequisite).where(ConceptPrerequisite.concept_id == target_concept_id)
        prereqs = (await db.execute(p_stmt)).scalars().all()
        if not prereqs:
            return {}, {}

        graph: Dict[str, List[str]] = {target_concept_id: [p.prerequisite_concept_id for p in prereqs]}
        prereq_ids = [p.prerequisite_concept_id for p in prereqs]

        m_stmt = select(StudentConceptKnowledgeState).where(
            and_(
                StudentConceptKnowledgeState.student_profile_id == student_profile_id,
                StudentConceptKnowledgeState.concept_id.in_(prereq_ids),
            )
        )
        states = (await db.execute(m_stmt)).scalars().all()
        masteries: Dict[str, Optional[Decimal]] = {s.concept_id: s.current_mastery for s in states}

        return graph, masteries


# Default service singleton
knowledge_state_service = KnowledgeStateService()
