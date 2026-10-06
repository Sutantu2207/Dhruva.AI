"""Assessment Engine, Question Bank, and Evaluation Service (Domain 5).

Handles:
- Question Bank & Question Authoring with Immutable Versioning
- Concept & Skill Mapping
- Assessment Definition, Blueprinting & Deterministic Selection
- Frozen Assessment Versions
- Attempt Lifecycle: Start, Gating, Server-Authoritative Timer, Autosave, Submit
- Deterministic Evaluation Pipeline & Scoring
- Rubrics & Manual Grading
- Results Release Lifecycle
- Immutable Concept & Skill Evidence Generation
"""

import uuid
import random
from datetime import datetime, timezone, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, and_, or_, func, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.domains.assessment.models import (
    QuestionBank,
    Question,
    QuestionVersion,
    QuestionOption,
    QuestionConcept,
    QuestionSkill,
    CodingConfiguration,
    CodingTestCase,
    EvaluationRubric,
    RubricCriterion,
    Assessment,
    AssessmentBlueprint,
    AssessmentVersion,
    AssessmentQuestion,
    AssessmentAttempt,
    AssessmentResponse,
    AssessmentEvaluation,
    ManualEvaluation,
    AssessmentResult,
    ConceptEvidence,
    SkillEvidence,
    GradeScheme,
    AssessmentIntegrityEvent,
    AssessmentReview,
)
from app.domains.academic.models import CourseOffering, StudentEnrollment, StudentAcademicProfile
from app.domains.content.models import Concept
from app.domains.catalog.models import SkillCatalog
from app.domains.assessment.evaluators import get_evaluator, EvaluationInput
from app.domains.assessment.engine import (
    AssessmentScoringEngine,
    EvaluatedQuestionScore,
    DeterministicScoreSummary,
)
from app.domains.assessment.schemas import (
    QuestionBankCreate,
    QuestionBankUpdate,
    QuestionCreate,
    QuestionUpdate,
    EvaluationRubricCreate,
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentBlueprintCreate,
    AssessmentQuestionAttach,
    AssessmentResponseAutosave,
    GradeSchemeCreate,
)


def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class AssessmentService:
    """Service layer for Question Banks, Assessments, Evaluation, and Evidence."""

    # =========================================================================
    # 1. Question Bank Management
    # =========================================================================

    async def create_question_bank(
        self,
        db: AsyncSession,
        institution_id: str,
        owner_id: str,
        data: QuestionBankCreate,
    ) -> QuestionBank:
        bank = QuestionBank(
            institution_id=institution_id,
            owner_id=owner_id,
            department_id=data.department_id,
            course_id=data.course_id,
            title=data.title,
            description=data.description,
            visibility=data.visibility,
            status="active",
        )
        db.add(bank)
        await db.commit()
        await db.refresh(bank)
        return bank

    async def get_question_banks(
        self,
        db: AsyncSession,
        institution_id: str,
        department_id: Optional[str] = None,
        course_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[QuestionBank]:
        stmt = (
            select(QuestionBank)
            .where(QuestionBank.institution_id == institution_id)
            .options(selectinload(QuestionBank.questions))
            .offset(skip)
            .limit(limit)
        )
        if department_id:
            stmt = stmt.where(QuestionBank.department_id == department_id)
        if course_id:
            stmt = stmt.where(QuestionBank.course_id == course_id)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_question_bank_by_id(
        self,
        db: AsyncSession,
        bank_id: str,
        institution_id: Optional[str] = None,
    ) -> QuestionBank:
        stmt = (
            select(QuestionBank)
            .where(QuestionBank.id == bank_id)
            .options(
                selectinload(QuestionBank.questions).selectinload(Question.versions)
            )
        )
        if institution_id:
            stmt = stmt.where(QuestionBank.institution_id == institution_id)

        result = await db.execute(stmt)
        bank = result.scalar_one_or_none()
        if not bank:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question bank not found")
        return bank

    # =========================================================================
    # 2. Evaluation Rubrics
    # =========================================================================

    async def create_rubric(
        self,
        db: AsyncSession,
        institution_id: str,
        user_id: str,
        data: EvaluationRubricCreate,
    ) -> EvaluationRubric:
        rubric = EvaluationRubric(
            institution_id=institution_id,
            title=data.title,
            description=data.description,
            created_by=user_id,
            version=1,
        )
        db.add(rubric)
        await db.flush()

        for idx, crit in enumerate(data.criteria):
            rc = RubricCriterion(
                rubric_id=rubric.id,
                title=crit.title,
                description=crit.description,
                max_points=crit.max_points,
                weight=crit.weight,
                order_index=crit.order_index or idx,
            )
            db.add(rc)

        await db.commit()
        await db.refresh(rubric)
        return rubric

    async def get_rubrics(
        self,
        db: AsyncSession,
        institution_id: str,
    ) -> List[EvaluationRubric]:
        stmt = (
            select(EvaluationRubric)
            .where(EvaluationRubric.institution_id == institution_id)
            .options(selectinload(EvaluationRubric.criteria))
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # 3. Question Authoring & Versioning
    # =========================================================================

    async def create_question(
        self,
        db: AsyncSession,
        bank_id: str,
        author_id: str,
        institution_id: str,
        data: QuestionCreate,
    ) -> Question:
        # Verify bank exists and belongs to authorized institution
        bank = await self.get_question_bank_by_id(db, bank_id, institution_id)

        question = Question(
            bank_id=bank.id,
            question_type=data.question_type,
            title=data.title,
            difficulty=data.difficulty,
            status="draft",
            author_id=author_id,
            current_version=1,
        )
        db.add(question)
        await db.flush()

        # Create Version 1
        q_version = QuestionVersion(
            question_id=question.id,
            version_number=1,
            prompt=data.prompt,
            instructions=data.instructions,
            explanation=data.explanation,
            points=data.points,
            negative_marks=data.negative_marks,
            estimated_seconds=data.estimated_seconds,
            difficulty=data.difficulty,
            rubric_id=data.rubric_id,
            evaluation_config=data.evaluation_config or {},
            created_by=author_id,
        )
        db.add(q_version)
        await db.flush()

        # Add Options
        for idx, opt in enumerate(data.options):
            qo = QuestionOption(
                question_version_id=q_version.id,
                option_text=opt.option_text,
                order_index=opt.order_index or idx,
                is_correct=opt.is_correct,
                explanation=opt.explanation,
                metadata_payload=opt.metadata_payload,
            )
            db.add(qo)

        # Add Concept Mappings
        for cm in data.concepts:
            qc = QuestionConcept(
                question_version_id=q_version.id,
                concept_id=cm.concept_id,
                importance=cm.importance,
                is_primary=cm.is_primary,
                weight=cm.weight,
            )
            db.add(qc)

        # Add Skill Mappings
        for sm in data.skills:
            qs = QuestionSkill(
                question_version_id=q_version.id,
                skill_id=sm.skill_id,
                weight=sm.weight,
                evidence_type=sm.evidence_type,
            )
            db.add(qs)

        # Add Coding Config if question_type == "coding"
        if data.question_type == "coding" and data.coding_config:
            cc = CodingConfiguration(
                question_version_id=q_version.id,
                language=data.coding_config.language,
                starter_code=data.coding_config.starter_code,
                function_signature=data.coding_config.function_signature,
                time_limit_ms=data.coding_config.time_limit_ms,
                memory_limit_mb=data.coding_config.memory_limit_mb,
                constraints_text=data.coding_config.constraints_text,
                input_format=data.coding_config.input_format,
                output_format=data.coding_config.output_format,
            )
            db.add(cc)
            await db.flush()

            for tc in data.coding_config.test_cases:
                ctc = CodingTestCase(
                    coding_config_id=cc.id,
                    input_data=tc.input_data,
                    expected_output=tc.expected_output,
                    is_hidden=tc.is_hidden,
                    points_weight=tc.points_weight,
                )
                db.add(ctc)

        await db.commit()
        await db.refresh(question)
        return question

    async def create_new_question_version(
        self,
        db: AsyncSession,
        question_id: str,
        author_id: str,
        institution_id: str,
        data: QuestionCreate,
    ) -> QuestionVersion:
        """Creates a new immutable question version without mutating previous versions."""
        stmt = (
            select(Question)
            .join(QuestionBank, Question.bank_id == QuestionBank.id)
            .where(Question.id == question_id, QuestionBank.institution_id == institution_id)
        )
        res = await db.execute(stmt)
        question = res.scalar_one_or_none()
        if not question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

        next_ver = question.current_version + 1
        q_version = QuestionVersion(
            question_id=question.id,
            version_number=next_ver,
            prompt=data.prompt,
            instructions=data.instructions,
            explanation=data.explanation,
            points=data.points,
            negative_marks=data.negative_marks,
            estimated_seconds=data.estimated_seconds,
            difficulty=data.difficulty,
            rubric_id=data.rubric_id,
            evaluation_config=data.evaluation_config or {},
            created_by=author_id,
        )
        db.add(q_version)
        await db.flush()

        # Options
        for idx, opt in enumerate(data.options):
            qo = QuestionOption(
                question_version_id=q_version.id,
                option_text=opt.option_text,
                order_index=opt.order_index or idx,
                is_correct=opt.is_correct,
                explanation=opt.explanation,
                metadata_payload=opt.metadata_payload,
            )
            db.add(qo)

        # Concepts
        for cm in data.concepts:
            qc = QuestionConcept(
                question_version_id=q_version.id,
                concept_id=cm.concept_id,
                importance=cm.importance,
                is_primary=cm.is_primary,
                weight=cm.weight,
            )
            db.add(qc)

        # Skills
        for sm in data.skills:
            qs = QuestionSkill(
                question_version_id=q_version.id,
                skill_id=sm.skill_id,
                weight=sm.weight,
                evidence_type=sm.evidence_type,
            )
            db.add(qs)

        # Coding
        if data.question_type == "coding" and data.coding_config:
            cc = CodingConfiguration(
                question_version_id=q_version.id,
                language=data.coding_config.language,
                starter_code=data.coding_config.starter_code,
                function_signature=data.coding_config.function_signature,
                time_limit_ms=data.coding_config.time_limit_ms,
                memory_limit_mb=data.coding_config.memory_limit_mb,
                constraints_text=data.coding_config.constraints_text,
                input_format=data.coding_config.input_format,
                output_format=data.coding_config.output_format,
            )
            db.add(cc)
            await db.flush()
            for tc in data.coding_config.test_cases:
                ctc = CodingTestCase(
                    coding_config_id=cc.id,
                    input_data=tc.input_data,
                    expected_output=tc.expected_output,
                    is_hidden=tc.is_hidden,
                    points_weight=tc.points_weight,
                )
                db.add(ctc)

        question.current_version = next_ver
        question.difficulty = data.difficulty
        await db.commit()
        await db.refresh(q_version)
        return q_version

    async def get_question_detail(
        self,
        db: AsyncSession,
        question_id: str,
        institution_id: Optional[str] = None,
    ) -> Question:
        stmt = (
            select(Question)
            .where(Question.id == question_id)
            .options(
                selectinload(Question.versions).selectinload(QuestionVersion.options),
                selectinload(Question.versions).selectinload(QuestionVersion.concepts),
                selectinload(Question.versions).selectinload(QuestionVersion.skills),
                selectinload(Question.versions).selectinload(QuestionVersion.coding_config).selectinload(CodingConfiguration.test_cases),
            )
        )
        if institution_id:
            stmt = stmt.join(QuestionBank, Question.bank_id == QuestionBank.id).where(QuestionBank.institution_id == institution_id)

        res = await db.execute(stmt)
        q = res.scalar_one_or_none()
        if not q:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        return q

    async def search_questions(
        self,
        db: AsyncSession,
        institution_id: str,
        bank_id: Optional[str] = None,
        question_type: Optional[str] = None,
        difficulty: Optional[str] = None,
        status_filter: Optional[str] = None,
        concept_id: Optional[str] = None,
        skill_id: Optional[str] = None,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[Question]:
        stmt = (
            select(Question)
            .join(QuestionBank, Question.bank_id == QuestionBank.id)
            .where(QuestionBank.institution_id == institution_id)
            .options(
                selectinload(Question.versions).selectinload(QuestionVersion.options),
                selectinload(Question.versions).selectinload(QuestionVersion.concepts),
                selectinload(Question.versions).selectinload(QuestionVersion.skills),
            )
            .offset(skip)
            .limit(limit)
        )
        if bank_id:
            stmt = stmt.where(Question.bank_id == bank_id)
        if question_type:
            stmt = stmt.where(Question.question_type == question_type)
        if difficulty:
            stmt = stmt.where(Question.difficulty == difficulty)
        if status_filter:
            stmt = stmt.where(Question.status == status_filter)
        if query:
            stmt = stmt.where(Question.title.ilike(f"%{query}%"))

        res = await db.execute(stmt)
        questions = list(res.scalars().all())

        # Optional concept/skill filtering
        if concept_id:
            questions = [
                q for q in questions
                if any(any(c.concept_id == concept_id for c in v.concepts) for v in q.versions)
            ]
        if skill_id:
            questions = [
                q for q in questions
                if any(any(s.skill_id == skill_id for s in v.skills) for v in q.versions)
            ]

        return questions

    async def update_question_status(
        self,
        db: AsyncSession,
        question_id: str,
        new_status: str,
        reviewer_id: str,
        institution_id: str,
    ) -> Question:
        q = await self.get_question_detail(db, question_id, institution_id)
        valid_statuses = {"draft", "in_review", "approved", "archived"}
        if new_status not in valid_statuses:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {new_status}")

        q.status = new_status
        if new_status == "approved":
            q.reviewer_id = reviewer_id
        await db.commit()
        await db.refresh(q)
        return q

    # =========================================================================
    # 4. Assessment Definition & Blueprinting
    # =========================================================================

    async def create_assessment(
        self,
        db: AsyncSession,
        institution_id: str,
        author_id: str,
        data: AssessmentCreate,
    ) -> Assessment:
        assessment = Assessment(
            institution_id=institution_id,
            course_offering_id=data.course_offering_id,
            title=data.title,
            description=data.description,
            instructions=data.instructions,
            assessment_type=data.assessment_type,
            status="draft",
            duration_minutes=data.duration_minutes,
            total_marks=data.total_marks,
            passing_marks=data.passing_marks,
            attempts_allowed=data.attempts_allowed,
            randomization_config=data.randomization_config or {},
            feedback_policy=data.feedback_policy,
            start_at=data.start_at,
            end_at=data.end_at,
            late_submission_allowed=data.late_submission_allowed,
            current_version=1,
            created_by=author_id,
        )
        db.add(assessment)
        await db.commit()
        await db.refresh(assessment)
        return assessment

    async def get_assessment_detail(
        self,
        db: AsyncSession,
        assessment_id: str,
        institution_id: Optional[str] = None,
    ) -> Assessment:
        stmt = (
            select(Assessment)
            .where(Assessment.id == assessment_id)
            .options(
                selectinload(Assessment.blueprints),
                selectinload(Assessment.versions).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.options),
                selectinload(Assessment.versions).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.concepts),
                selectinload(Assessment.versions).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.skills),
            )
        )
        if institution_id:
            stmt = stmt.where(Assessment.institution_id == institution_id)

        res = await db.execute(stmt)
        a = res.scalar_one_or_none()
        if not a:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
        return a

    async def create_blueprint(
        self,
        db: AsyncSession,
        assessment_id: str,
        institution_id: str,
        data: AssessmentBlueprintCreate,
    ) -> AssessmentBlueprint:
        assessment = await self.get_assessment_detail(db, assessment_id, institution_id)
        blueprint = AssessmentBlueprint(
            assessment_id=assessment.id,
            title=data.title,
            description=data.description,
            total_questions=data.total_questions,
            rules_config=data.rules_config,
            is_active=True,
        )
        db.add(blueprint)
        await db.commit()
        await db.refresh(blueprint)
        return blueprint

    async def publish_assessment_version(
        self,
        db: AsyncSession,
        assessment_id: str,
        institution_id: str,
        user_id: str,
        question_version_ids: Optional[List[str]] = None,
        use_blueprint_id: Optional[str] = None,
        deterministic_seed: int = 42,
    ) -> AssessmentVersion:
        """Freezes an assessment into an immutable AssessmentVersion."""
        assessment = await self.get_assessment_detail(db, assessment_id, institution_id)

        chosen_q_versions: List[QuestionVersion] = []

        if question_version_ids:
            # Fixed question selection
            q_stmt = (
                select(QuestionVersion)
                .where(QuestionVersion.id.in_(question_version_ids))
            )
            q_res = await db.execute(q_stmt)
            chosen_q_versions = list(q_res.scalars().all())
        elif use_blueprint_id:
            # Deterministic selection via blueprint
            bp_stmt = select(AssessmentBlueprint).where(AssessmentBlueprint.id == use_blueprint_id)
            bp_res = await db.execute(bp_stmt)
            bp = bp_res.scalar_one_or_none()
            if not bp:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blueprint not found")

            # Deterministic seed ensures reproducible selection
            rng = random.Random(deterministic_seed)
            diff_rules = bp.rules_config.get("difficulty", {})  # e.g. {"easy": 2, "medium": 3, "hard": 1}

            for diff, count in diff_rules.items():
                cand_stmt = (
                    select(QuestionVersion)
                    .join(Question, QuestionVersion.question_id == Question.id)
                    .join(QuestionBank, Question.bank_id == QuestionBank.id)
                    .where(
                        QuestionBank.institution_id == institution_id,
                        Question.difficulty == diff,
                        Question.status == "approved",
                    )
                )
                c_res = await db.execute(cand_stmt)
                candidates = list(c_res.scalars().all())
                rng.shuffle(candidates)
                chosen_q_versions.extend(candidates[:count])

        if not chosen_q_versions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish assessment version with 0 questions",
            )

        # Calculate total marks from question versions
        total_marks = sum((Decimal(str(qv.points)) for qv in chosen_q_versions), Decimal("0.00"))

        ver_num = assessment.current_version
        if assessment.versions:
            ver_num = max(v.version_number for v in assessment.versions) + 1

        assessment_version = AssessmentVersion(
            assessment_id=assessment.id,
            version_number=ver_num,
            title=assessment.title,
            instructions=assessment.instructions,
            total_marks=total_marks,
            passing_marks=assessment.passing_marks or (total_marks * Decimal("0.40")),
            duration_minutes=assessment.duration_minutes,
            feedback_policy=assessment.feedback_policy,
            rules_snapshot={"question_count": len(chosen_q_versions), "seed": deterministic_seed},
            is_frozen=True,
            created_by=user_id,
        )
        db.add(assessment_version)
        await db.flush()

        for idx, qv in enumerate(chosen_q_versions):
            aq = AssessmentQuestion(
                assessment_version_id=assessment_version.id,
                question_version_id=qv.id,
                order_index=idx,
                section_name="Default",
                custom_points=qv.points,
                custom_negative_marks=qv.negative_marks,
            )
            db.add(aq)

        assessment.status = "open"
        assessment.total_marks = total_marks
        assessment.current_version = ver_num
        await db.commit()

        ver_stmt = (
            select(AssessmentVersion)
            .where(AssessmentVersion.id == assessment_version.id)
            .options(
                selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.options),
                selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.concepts),
                selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.skills),
            )
        )
        ver_res = await db.execute(ver_stmt)
        return ver_res.scalar_one()

    # =========================================================================
    # 5. Student Attempt Lifecycle
    # =========================================================================

    async def start_assessment_attempt(
        self,
        db: AsyncSession,
        assessment_id: str,
        student_profile_id: str,
        institution_id: str,
    ) -> AssessmentAttempt:
        """Starts a timed attempt after verifying enrollment, attempt limits, and availability."""
        assessment = await self.get_assessment_detail(db, assessment_id, institution_id)

        # 1. Validate status
        if assessment.status not in ("open", "scheduled"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assessment is not currently open for student attempts",
            )

        now = datetime.now(timezone.utc)
        # 2. Validate availability window
        if assessment.start_at and now < to_utc(assessment.start_at):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assessment availability window has not opened yet",
            )
        if assessment.end_at and now > to_utc(assessment.end_at):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Assessment availability window has closed",
            )

        # 3. Validate course offering enrollment if offering bound
        if assessment.course_offering_id:
            enr_stmt = select(StudentEnrollment).where(
                StudentEnrollment.student_profile_id == student_profile_id,
                StudentEnrollment.course_offering_id == assessment.course_offering_id,
                StudentEnrollment.enrollment_status == "enrolled",
            )
            enr_res = await db.execute(enr_stmt)
            if not enr_res.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Student is not enrolled in the course offering delivering this assessment",
                )

        # 4. Get active frozen assessment version
        if not assessment.versions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Assessment has no published version ready for delivery",
            )
        latest_version = max(assessment.versions, key=lambda v: v.version_number)

        # 5. Check existing attempts & attempt limit
        att_stmt = select(AssessmentAttempt).where(
            AssessmentAttempt.assessment_version_id == latest_version.id,
            AssessmentAttempt.student_profile_id == student_profile_id,
        )
        att_res = await db.execute(att_stmt)
        existing_attempts = list(att_res.scalars().all())

        # Check if an in-progress attempt already exists
        for att in existing_attempts:
            if att.status == "in_progress":
                if now < to_utc(att.expires_at):
                    return att  # Resume active attempt
                else:
                    att.status = "expired"
                    await db.flush()

        if len(existing_attempts) >= assessment.attempts_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Maximum attempts ({assessment.attempts_allowed}) reached for this assessment",
            )

        # 6. Calculate server-authoritative timer
        duration = latest_version.duration_minutes or 60
        expires_at = now + timedelta(minutes=duration)
        if assessment.end_at and expires_at > to_utc(assessment.end_at):
            expires_at = assessment.end_at

        attempt_num = len(existing_attempts) + 1
        attempt = AssessmentAttempt(
            assessment_version_id=latest_version.id,
            student_profile_id=student_profile_id,
            attempt_number=attempt_num,
            status="in_progress",
            started_at=now,
            expires_at=expires_at,
            attempt_token=str(uuid.uuid4()).replace("-", ""),
        )
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)
        return attempt

    async def get_attempt_delivery(
        self,
        db: AsyncSession,
        attempt_id: str,
        student_profile_id: str,
    ) -> Tuple[AssessmentAttempt, List[Dict[str, Any]], Dict[str, Any]]:
        """Returns the student delivery view of an attempt, strictly stripping answer keys and hidden tests."""
        stmt = (
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.id == attempt_id,
                AssessmentAttempt.student_profile_id == student_profile_id,
            )
            .options(
                selectinload(AssessmentAttempt.assessment_version).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.question),
                selectinload(AssessmentAttempt.assessment_version).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.options),
                selectinload(AssessmentAttempt.assessment_version).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.coding_config).selectinload(CodingConfiguration.test_cases),
                selectinload(AssessmentAttempt.assessment_version).selectinload(AssessmentVersion.assessment),
                selectinload(AssessmentAttempt.responses),
            )
        )
        res = await db.execute(stmt)
        attempt = res.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

        # Auto-expire if expired
        now = datetime.now(timezone.utc)
        if attempt.status == "in_progress" and now > to_utc(attempt.expires_at):
            attempt.status = "expired"
            await db.commit()

        # Build sanitized delivery payload
        sanitized_questions = []
        for aq in sorted(attempt.assessment_version.assessment_questions, key=lambda q: q.order_index):
            qv = aq.question_version

            # Sanitize options: exclude is_correct and explanation
            safe_options = [
                {
                    "id": opt.id,
                    "option_text": opt.option_text,
                    "order_index": opt.order_index,
                }
                for opt in sorted(qv.options, key=lambda o: o.order_index)
            ]

            # Sanitize coding: exclude hidden tests
            starter_code = None
            coding_lang = None
            public_tests = []
            if qv.coding_config:
                starter_code = qv.coding_config.starter_code
                coding_lang = qv.coding_config.language
                public_tests = [
                    {
                        "input_data": tc.input_data,
                        "expected_output": tc.expected_output,
                    }
                    for tc in qv.coding_config.test_cases
                    if not tc.is_hidden
                ]

            sanitized_questions.append({
                "assessment_question_id": aq.id,
                "question_version_id": qv.id,
                "question_type": qv.question.question_type if hasattr(qv, "question") and qv.question else "single_choice",
                "title": qv.question.title if hasattr(qv, "question") and qv.question else "Question",
                "prompt": qv.prompt,
                "instructions": qv.instructions,
                "order_index": aq.order_index,
                "section_name": aq.section_name,
                "points": aq.custom_points or qv.points,
                "negative_marks": aq.custom_negative_marks or qv.negative_marks,
                "options": safe_options,
                "coding_starter_code": starter_code,
                "coding_language": coding_lang,
                "public_test_cases": public_tests,
            })

        existing_responses = {
            r.question_version_id: r.response_payload
            for r in attempt.responses
        }

        return attempt, sanitized_questions, existing_responses

    async def autosave_response(
        self,
        db: AsyncSession,
        attempt_id: str,
        student_profile_id: str,
        data: AssessmentResponseAutosave,
    ) -> AssessmentResponse:
        """Autosaves a single question response in real time."""
        stmt = select(AssessmentAttempt).where(
            AssessmentAttempt.id == attempt_id,
            AssessmentAttempt.student_profile_id == student_profile_id,
        )
        res = await db.execute(stmt)
        attempt = res.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

        if attempt.status != "in_progress":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot autosave in state '{attempt.status}'")

        now = datetime.now(timezone.utc)
        if now > to_utc(attempt.expires_at):
            attempt.status = "expired"
            await db.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attempt timer has expired")

        # Find existing or create response
        r_stmt = select(AssessmentResponse).where(
            AssessmentResponse.attempt_id == attempt.id,
            AssessmentResponse.question_version_id == data.question_version_id,
        )
        r_res = await db.execute(r_stmt)
        resp = r_res.scalar_one_or_none()

        if resp:
            resp.response_type = data.response_type
            resp.response_payload = data.response_payload
            resp.is_flagged = data.is_flagged
            resp.answered_at = now
        else:
            resp = AssessmentResponse(
                attempt_id=attempt.id,
                question_version_id=data.question_version_id,
                response_type=data.response_type,
                response_payload=data.response_payload,
                is_flagged=data.is_flagged,
                started_at=now,
                answered_at=now,
            )
            db.add(resp)

        await db.commit()
        await db.refresh(resp)
        return resp

    # =========================================================================
    # 6. Transactional Submission & Deterministic Scoring
    # =========================================================================

    async def submit_assessment_attempt(
        self,
        db: AsyncSession,
        attempt_id: str,
        student_profile_id: str,
        responses_payload: Optional[List[AssessmentResponseAutosave]] = None,
    ) -> AssessmentResult:
        """Submits an attempt transactionally, runs evaluators, calculates scores, and generates evidence."""
        stmt = (
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.id == attempt_id,
                AssessmentAttempt.student_profile_id == student_profile_id,
            )
            .options(
                selectinload(AssessmentAttempt.assessment_version).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.options),
                selectinload(AssessmentAttempt.assessment_version).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.coding_config).selectinload(CodingConfiguration.test_cases),
                selectinload(AssessmentAttempt.assessment_version).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.concepts),
                selectinload(AssessmentAttempt.assessment_version).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version).selectinload(QuestionVersion.skills),
                selectinload(AssessmentAttempt.assessment_version).selectinload(AssessmentVersion.assessment),
                selectinload(AssessmentAttempt.responses),
                selectinload(AssessmentAttempt.evaluations),
                selectinload(AssessmentAttempt.result),
            )
        )
        res = await db.execute(stmt)
        attempt = res.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

        # Idempotency check: if already evaluated or submitted, return existing result
        if attempt.status in ("submitted", "evaluated", "under_evaluation") and attempt.result:
            return attempt.result

        now = datetime.now(timezone.utc)
        if attempt.status == "expired":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attempt has expired")
        if attempt.expires_at and now > to_utc(attempt.expires_at) + timedelta(seconds=60):
            attempt.status = "expired"
            await db.commit()
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attempt timer has expired")

        attempt.submitted_at = now

        # Save any final responses in payload
        if responses_payload:
            for item in responses_payload:
                existing = next((r for r in attempt.responses if r.question_version_id == item.question_version_id), None)
                if existing:
                    existing.response_payload = item.response_payload
                    existing.is_flagged = item.is_flagged
                    existing.answered_at = now
                else:
                    nr = AssessmentResponse(
                        attempt_id=attempt.id,
                        question_version_id=item.question_version_id,
                        response_type=item.response_type,
                        response_payload=item.response_payload,
                        is_flagged=item.is_flagged,
                        answered_at=now,
                    )
                    db.add(nr)
                    attempt.responses.append(nr)
            await db.flush()

        # Build response mapping
        response_map = {r.question_version_id: r for r in attempt.responses}

        evaluated_questions: List[EvaluatedQuestionScore] = []
        evaluations_to_add: List[AssessmentEvaluation] = []
        concept_evidences: List[ConceptEvidence] = []
        skill_evidences: List[SkillEvidence] = []

        assessment_version = attempt.assessment_version
        assessment = assessment_version.assessment

        for aq in assessment_version.assessment_questions:
            qv = aq.question_version
            resp = response_map.get(qv.id)
            resp_payload = resp.response_payload if resp else {}

            # Build author truth metadata
            options_data = [
                {"id": o.id, "option_text": o.option_text, "order_index": o.order_index, "is_correct": o.is_correct}
                for o in qv.options
            ]
            coding_data = {}
            if qv.coding_config:
                coding_data = {
                    "language": qv.coding_config.language,
                    "time_limit_ms": qv.coding_config.time_limit_ms,
                    "memory_limit_mb": qv.coding_config.memory_limit_mb,
                    "test_cases": [
                        {
                            "input_data": tc.input_data,
                            "expected_output": tc.expected_output,
                            "is_hidden": tc.is_hidden,
                            "points_weight": tc.points_weight,
                        }
                        for tc in qv.coding_config.test_cases
                    ],
                }

            truth_metadata = {
                "options": options_data,
                "coding_config": coding_data,
                "rubric_id": qv.rubric_id,
                "expected_value": (qv.evaluation_config or {}).get("expected_value"),
                "expected_pairs": (qv.evaluation_config or {}).get("expected_pairs", {}),
                "expected_order_ids": (qv.evaluation_config or {}).get("expected_order_ids", []),
                "accepted_answers": (qv.evaluation_config or {}).get("accepted_answers", []),
            }

            q_points = aq.custom_points or qv.points
            q_neg = aq.custom_negative_marks or qv.negative_marks
            eval_input = EvaluationInput(
                question_version_id=qv.id,
                question_type=qv.question.question_type if hasattr(qv, "question") and qv.question else "single_choice",
                response_payload=resp_payload,
                points=q_points,
                negative_marks=q_neg,
                evaluation_config=qv.evaluation_config,
                truth_metadata=truth_metadata,
            )

            evaluator = get_evaluator(eval_input.question_type)
            res_eval = evaluator.evaluate(eval_input)

            # Record AssessmentEvaluation
            evaluation = AssessmentEvaluation(
                attempt_id=attempt.id,
                question_version_id=qv.id,
                awarded_marks=res_eval.awarded_marks,
                penalty_marks=res_eval.penalty_marks,
                max_marks=res_eval.max_marks,
                is_correct=res_eval.is_correct,
                evaluation_type=res_eval.evaluation_type,
                feedback=res_eval.feedback,
                evaluated_at=now,
            )
            evaluations_to_add.append(evaluation)

            evaluated_questions.append(
                EvaluatedQuestionScore(
                    question_version_id=qv.id,
                    max_marks=res_eval.max_marks,
                    awarded_marks=res_eval.awarded_marks,
                    penalty_marks=res_eval.penalty_marks,
                    is_correct=res_eval.is_correct,
                    evaluation_type=res_eval.evaluation_type,
                    feedback=res_eval.feedback,
                )
            )

            # Generate Concept Evidence
            norm_score = (res_eval.awarded_marks / res_eval.max_marks) if res_eval.max_marks > 0 else Decimal("0.00")
            norm_score = max(Decimal("0.00"), min(Decimal("1.00"), norm_score))

            for qc in qv.concepts:
                ce = ConceptEvidence(
                    student_profile_id=student_profile_id,
                    concept_id=qc.concept_id,
                    question_version_id=qv.id,
                    assessment_id=assessment.id,
                    attempt_id=attempt.id,
                    score=norm_score,
                    max_score=Decimal("1.0000"),
                    evidence_type="assessment",
                    evaluation_method=res_eval.evaluation_type,
                    timestamp=now,
                )
                concept_evidences.append(ce)

            # Generate Skill Evidence
            for qs in qv.skills:
                se = SkillEvidence(
                    student_profile_id=student_profile_id,
                    skill_id=qs.skill_id,
                    question_version_id=qv.id,
                    assessment_id=assessment.id,
                    attempt_id=attempt.id,
                    score=norm_score,
                    weight=qs.weight,
                    evidence_type=qs.evidence_type,
                    evaluation_method=res_eval.evaluation_type,
                    timestamp=now,
                )
                skill_evidences.append(se)

        # Persist evaluations
        for ev in evaluations_to_add:
            db.add(ev)
        for ce in concept_evidences:
            db.add(ce)
        for se in skill_evidences:
            db.add(se)

        # Run Deterministic Scoring
        summary = AssessmentScoringEngine.calculate_attempt_score(
            evaluated_questions=evaluated_questions,
            passing_marks=assessment_version.passing_marks,
        )

        attempt.score = summary.net_marks
        attempt.percentage = summary.percentage
        attempt.is_passed = summary.is_passed
        attempt.evaluated_at = now

        if summary.has_pending_manual_evaluation:
            attempt.status = "under_evaluation"
            res_status = "draft"
        else:
            attempt.status = "evaluated"
            res_status = "internal"  # ready for release according to feedback policy

        # Create or update AssessmentResult
        result = AssessmentResult(
            attempt_id=attempt.id,
            total_marks_obtained=summary.net_marks,
            maximum_marks=summary.maximum_marks,
            percentage=summary.percentage,
            grade=summary.grade,
            is_passed=summary.is_passed,
            status=res_status,
            evaluated_at=now,
        )
        db.add(result)

        await db.commit()
        await db.refresh(result)
        return result

    # =========================================================================
    # 7. Manual Grading & Regrading
    # =========================================================================

    async def grade_manual_question(
        self,
        db: AsyncSession,
        evaluation_id: str,
        instructor_id: str,
        awarded_marks: Decimal,
        evaluator_notes: Optional[str] = None,
        rubric_criterion_id: Optional[str] = None,
    ) -> AssessmentEvaluation:
        """Manual rubric grading of a subjective response by authorized faculty."""
        stmt = (
            select(AssessmentEvaluation)
            .where(AssessmentEvaluation.id == evaluation_id)
            .options(
                selectinload(AssessmentEvaluation.attempt).selectinload(AssessmentAttempt.evaluations),
                selectinload(AssessmentEvaluation.attempt).selectinload(AssessmentAttempt.assessment_version),
                selectinload(AssessmentEvaluation.attempt).selectinload(AssessmentAttempt.result),
            )
        )
        res = await db.execute(stmt)
        evaluation = res.scalar_one_or_none()
        if not evaluation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")

        # Clamp awarded marks between 0 and max_marks
        bounded_marks = max(Decimal("0.00"), min(evaluation.max_marks, awarded_marks))
        evaluation.awarded_marks = bounded_marks
        evaluation.is_correct = (bounded_marks == evaluation.max_marks)
        evaluation.evaluator_id = instructor_id
        evaluation.feedback = evaluator_notes

        # Create manual evaluation sub-record
        me = ManualEvaluation(
            evaluation_id=evaluation.id,
            rubric_criterion_id=rubric_criterion_id,
            awarded_points=bounded_marks,
            evaluator_notes=evaluator_notes,
            graded_by=instructor_id,
        )
        db.add(me)

        attempt = evaluation.attempt
        # Recalculate total score for attempt
        all_evals = attempt.evaluations
        evaluated_q = [
            EvaluatedQuestionScore(
                question_version_id=e.question_version_id,
                max_marks=e.max_marks,
                awarded_marks=e.awarded_marks,
                penalty_marks=e.penalty_marks,
                is_correct=e.is_correct,
                evaluation_type=e.evaluation_type,
            )
            for e in all_evals
        ]

        summary = AssessmentScoringEngine.calculate_attempt_score(
            evaluated_questions=evaluated_q,
            passing_marks=attempt.assessment_version.passing_marks,
        )

        attempt.score = summary.net_marks
        attempt.percentage = summary.percentage
        attempt.is_passed = summary.is_passed

        # Check if all manual evaluations complete
        pending = any(e.evaluation_type == "manual" and e.evaluator_id is None for e in all_evals)
        if not pending:
            attempt.status = "evaluated"

        if attempt.result:
            attempt.result.total_marks_obtained = summary.net_marks
            attempt.result.percentage = summary.percentage
            attempt.result.grade = summary.grade
            attempt.result.is_passed = summary.is_passed

        await db.commit()
        await db.refresh(evaluation)
        return evaluation

    # =========================================================================
    # 8. Result Release Lifecycle
    # =========================================================================

    async def release_assessment_result(
        self,
        db: AsyncSession,
        attempt_id: str,
        released_by: str,
    ) -> AssessmentResult:
        """Publishes student result to released status."""
        stmt = (
            select(AssessmentResult)
            .where(AssessmentResult.attempt_id == attempt_id)
            .options(selectinload(AssessmentResult.attempt))
        )
        res = await db.execute(stmt)
        result = res.scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment result not found")

        now = datetime.now(timezone.utc)
        result.status = "released"
        result.released_at = now
        result.released_by = released_by

        if result.attempt:
            result.attempt.result_status = "released"

        await db.commit()
        await db.refresh(result)
        return result

    async def recall_assessment_result(
        self,
        db: AsyncSession,
        attempt_id: str,
    ) -> AssessmentResult:
        """Recalls a previously released result."""
        stmt = (
            select(AssessmentResult)
            .where(AssessmentResult.attempt_id == attempt_id)
            .options(selectinload(AssessmentResult.attempt))
        )
        res = await db.execute(stmt)
        result = res.scalar_one_or_none()
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment result not found")

        result.status = "recalled"
        if result.attempt:
            result.attempt.result_status = "recalled"

        await db.commit()
        await db.refresh(result)
        return result

    # =========================================================================
    # 9. Student Results & Evidence Queries
    # =========================================================================

    async def get_student_attempt_result(
        self,
        db: AsyncSession,
        attempt_id: str,
        student_profile_id: str,
    ) -> Dict[str, Any]:
        """Queries an attempt's result, strictly respecting release and feedback policies."""
        stmt = (
            select(AssessmentAttempt)
            .where(
                AssessmentAttempt.id == attempt_id,
                AssessmentAttempt.student_profile_id == student_profile_id,
            )
            .options(
                selectinload(AssessmentAttempt.assessment_version).selectinload(AssessmentVersion.assessment),
                selectinload(AssessmentAttempt.evaluations),
                selectinload(AssessmentAttempt.result),
            )
        )
        res = await db.execute(stmt)
        attempt = res.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attempt not found")

        assessment_version = attempt.assessment_version
        feedback_policy = assessment_version.feedback_policy

        # Check release gating
        if feedback_policy == "never":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Feedback is disabled for this assessment")

        if feedback_policy == "after_release":
            if not attempt.result or attempt.result.status != "released":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Results have not been released by the instructor yet",
                )

        if not attempt.result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result is not ready yet")

        return {
            "attempt_id": attempt.id,
            "assessment_title": assessment_version.title,
            "total_marks_obtained": attempt.result.total_marks_obtained,
            "maximum_marks": attempt.result.maximum_marks,
            "percentage": attempt.result.percentage,
            "grade": attempt.result.grade,
            "is_passed": attempt.result.is_passed,
            "status": attempt.result.status,
            "evaluated_at": attempt.result.evaluated_at,
            "released_at": attempt.result.released_at,
            "evaluations": [
                {
                    "question_version_id": e.question_version_id,
                    "awarded_marks": e.awarded_marks,
                    "penalty_marks": e.penalty_marks,
                    "max_marks": e.max_marks,
                    "is_correct": e.is_correct,
                    "evaluation_type": e.evaluation_type,
                    "feedback": e.feedback,
                }
                for e in attempt.evaluations
            ],
        }

    async def get_student_concept_evidences(
        self,
        db: AsyncSession,
        student_profile_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ConceptEvidence]:
        stmt = (
            select(ConceptEvidence)
            .where(ConceptEvidence.student_profile_id == student_profile_id)
            .order_by(ConceptEvidence.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())

    async def get_student_skill_evidences(
        self,
        db: AsyncSession,
        student_profile_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> List[SkillEvidence]:
        stmt = (
            select(SkillEvidence)
            .where(SkillEvidence.student_profile_id == student_profile_id)
            .order_by(SkillEvidence.timestamp.desc())
            .offset(skip)
            .limit(limit)
        )
        res = await db.execute(stmt)
        return list(res.scalars().all())


# Global singleton instance
assessment_service = AssessmentService()
