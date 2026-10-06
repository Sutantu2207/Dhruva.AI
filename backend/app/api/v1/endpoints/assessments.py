"""API Endpoints for Assessment Engine, Question Banks, Evaluation & Evidence (Domain 5)."""

from typing import List, Optional, Dict, Any
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user, require_roles
from app.core.security import UserRole
from app.domains.identity.models import User
from app.domains.academic.models import StudentAcademicProfile
from app.domains.assessment.service import assessment_service
from app.domains.assessment.schemas import (
    QuestionBankCreate,
    QuestionBankUpdate,
    QuestionBankResponse,
    QuestionCreate,
    QuestionUpdate,
    QuestionDetailResponse,
    QuestionVersionResponse,
    EvaluationRubricCreate,
    EvaluationRubricResponse,
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentDetailResponse,
    AssessmentBlueprintCreate,
    AssessmentBlueprintResponse,
    AssessmentVersionResponse,
    AssessmentAttemptDelivery,
    AssessmentResponseAutosave,
    AssessmentSubmitPayload,
    ManualGradePayload,
    ConceptEvidenceResponse,
    SkillEvidenceResponse,
)

router = APIRouter()


async def _resolve_student_profile(db: AsyncSession, user_id: str) -> StudentAcademicProfile:
    stmt = select(StudentAcademicProfile).where(StudentAcademicProfile.user_id == user_id)
    res = await db.execute(stmt)
    prof = res.scalar_one_or_none()
    if not prof:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student academic profile not provisioned",
        )
    return prof


# =========================================================================
# 1. Question Banks & Rubrics
# =========================================================================

@router.get("/question-banks", response_model=List[QuestionBankResponse])
async def list_question_banks(
    department_id: Optional[str] = None,
    course_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Lists question banks scoped to user's institution."""
    inst_id = current_user.institution_id or "default"
    return await assessment_service.get_question_banks(
        db,
        institution_id=inst_id,
        department_id=department_id,
        course_id=course_id,
        skip=skip,
        limit=limit,
    )


@router.post("/question-banks", response_model=QuestionBankResponse, status_code=status.HTTP_201_CREATED)
async def create_question_bank(
    payload: QuestionBankCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Creates a new institutional question bank."""
    inst_id = current_user.institution_id or "default"
    return await assessment_service.create_question_bank(
        db,
        institution_id=inst_id,
        owner_id=current_user.id,
        data=payload,
    )


@router.get("/question-banks/{bank_id}", response_model=QuestionBankResponse)
async def get_question_bank(
    bank_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    inst_id = current_user.institution_id if current_user.role != UserRole.SUPER_ADMIN else None
    return await assessment_service.get_question_bank_by_id(db, bank_id, inst_id)


@router.get("/rubrics", response_model=List[EvaluationRubricResponse])
async def list_rubrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    inst_id = current_user.institution_id or "default"
    return await assessment_service.get_rubrics(db, inst_id)


@router.post("/rubrics", response_model=EvaluationRubricResponse, status_code=status.HTTP_201_CREATED)
async def create_rubric(
    payload: EvaluationRubricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    inst_id = current_user.institution_id or "default"
    return await assessment_service.create_rubric(db, inst_id, current_user.id, payload)


# =========================================================================
# 2. Questions & Versions
# =========================================================================

@router.get("/questions", response_model=List[QuestionDetailResponse])
async def search_questions(
    bank_id: Optional[str] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    status_filter: Optional[str] = None,
    concept_id: Optional[str] = None,
    skill_id: Optional[str] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Searches questions within the institution's question banks."""
    inst_id = current_user.institution_id or "default"
    return await assessment_service.search_questions(
        db,
        institution_id=inst_id,
        bank_id=bank_id,
        question_type=question_type,
        difficulty=difficulty,
        status_filter=status_filter,
        concept_id=concept_id,
        skill_id=skill_id,
        query=q,
        skip=skip,
        limit=limit,
    )


@router.post("/question-banks/{bank_id}/questions", response_model=QuestionDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_question_in_bank(
    bank_id: str,
    payload: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Authors a new question with Version 1."""
    inst_id = current_user.institution_id or "default"
    question = await assessment_service.create_question(
        db,
        bank_id=bank_id,
        author_id=current_user.id,
        institution_id=inst_id,
        data=payload,
    )
    return await assessment_service.get_question_detail(db, question.id, inst_id)


@router.get("/questions/{question_id}", response_model=QuestionDetailResponse)
async def get_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    inst_id = current_user.institution_id if current_user.role != UserRole.SUPER_ADMIN else None
    return await assessment_service.get_question_detail(db, question_id, inst_id)


@router.post("/questions/{question_id}/versions", response_model=QuestionVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_question_version(
    question_id: str,
    payload: QuestionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Appends a new immutable version of an existing question."""
    inst_id = current_user.institution_id or "default"
    return await assessment_service.create_new_question_version(
        db,
        question_id=question_id,
        author_id=current_user.id,
        institution_id=inst_id,
        data=payload,
    )


@router.patch("/questions/{question_id}/status", response_model=QuestionDetailResponse)
async def update_question_status(
    question_id: str,
    new_status: str = Query(..., pattern="^(draft|in_review|approved|archived)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Reviews and updates question status."""
    inst_id = current_user.institution_id or "default"
    await assessment_service.update_question_status(
        db,
        question_id=question_id,
        new_status=new_status,
        reviewer_id=current_user.id,
        institution_id=inst_id,
    )
    return await assessment_service.get_question_detail(db, question_id, inst_id)


# =========================================================================
# 3. Assessment Definition & Blueprints
# =========================================================================

@router.get("/assessments", response_model=List[AssessmentDetailResponse])
async def list_assessments(
    course_offering_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lists assessments available to the user's institution."""
    inst_id = current_user.institution_id or "default"
    stmt = (
        select(Assessment)
        .where(Assessment.institution_id == inst_id)
        .options(
            selectinload(Assessment.blueprints),
            selectinload(Assessment.versions).selectinload(AssessmentVersion.assessment_questions).selectinload(AssessmentQuestion.question_version),
        )
    )
    if course_offering_id:
        stmt = stmt.where(Assessment.course_offering_id == course_offering_id)
    if current_user.role == UserRole.STUDENT:
        # Students only see scheduled or open assessments
        stmt = stmt.where(Assessment.status.in_(["scheduled", "open", "closed", "graded"]))

    res = await db.execute(stmt)
    return list(res.scalars().all())


@router.post("/assessments", response_model=AssessmentDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    payload: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Creates a new assessment container."""
    inst_id = current_user.institution_id or "default"
    assessment = await assessment_service.create_assessment(
        db,
        institution_id=inst_id,
        author_id=current_user.id,
        data=payload,
    )
    return await assessment_service.get_assessment_detail(db, assessment.id, inst_id)


@router.get("/assessments/{assessment_id}", response_model=AssessmentDetailResponse)
async def get_assessment(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inst_id = current_user.institution_id if current_user.role != UserRole.SUPER_ADMIN else None
    return await assessment_service.get_assessment_detail(db, assessment_id, inst_id)


@router.post("/assessments/{assessment_id}/blueprints", response_model=AssessmentBlueprintResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment_blueprint(
    assessment_id: str,
    payload: AssessmentBlueprintCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    inst_id = current_user.institution_id or "default"
    return await assessment_service.create_blueprint(db, assessment_id, inst_id, payload)


@router.post("/assessments/{assessment_id}/publish", response_model=AssessmentVersionResponse, status_code=status.HTTP_201_CREATED)
async def publish_assessment_version(
    assessment_id: str,
    question_version_ids: Optional[List[str]] = Query(None),
    blueprint_id: Optional[str] = None,
    seed: int = 42,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Freezes questions and configurations into an immutable AssessmentVersion."""
    inst_id = current_user.institution_id or "default"
    return await assessment_service.publish_assessment_version(
        db,
        assessment_id=assessment_id,
        institution_id=inst_id,
        user_id=current_user.id,
        question_version_ids=question_version_ids,
        use_blueprint_id=blueprint_id,
        deterministic_seed=seed,
    )


# =========================================================================
# 4. Student Attempt Lifecycle & Delivery
# =========================================================================

@router.post("/assessments/{assessment_id}/attempts", status_code=status.HTTP_201_CREATED)
async def start_attempt(
    assessment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Starts a timed attempt after checking enrollment and limits."""
    inst_id = current_user.institution_id or "default"
    student_profile = await _resolve_student_profile(db, current_user.id)

    attempt = await assessment_service.start_assessment_attempt(
        db,
        assessment_id=assessment_id,
        student_profile_id=student_profile.id,
        institution_id=inst_id,
    )
    return {
        "attempt_id": attempt.id,
        "status": attempt.status,
        "started_at": attempt.started_at,
        "expires_at": attempt.expires_at,
        "attempt_number": attempt.attempt_number,
    }


@router.get("/attempts/{attempt_id}", response_model=AssessmentAttemptDelivery)
async def get_attempt_delivery(
    attempt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Returns question delivery for active attempt strictly without answer keys."""
    student_profile = await _resolve_student_profile(db, current_user.id)
    attempt, questions, responses = await assessment_service.get_attempt_delivery(
        db,
        attempt_id=attempt_id,
        student_profile_id=student_profile.id,
    )

    assessment_version = attempt.assessment_version
    assessment = assessment_version.assessment

    return AssessmentAttemptDelivery(
        attempt_id=attempt.id,
        assessment_id=assessment.id,
        assessment_title=assessment_version.title,
        instructions=assessment_version.instructions,
        attempt_number=attempt.attempt_number,
        started_at=attempt.started_at,
        expires_at=attempt.expires_at,
        duration_minutes=assessment_version.duration_minutes,
        status=attempt.status,
        questions=questions,
        existing_responses=responses,
    )


@router.post("/attempts/{attempt_id}/autosave")
async def autosave_attempt_response(
    attempt_id: str,
    payload: AssessmentResponseAutosave,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Idempotently autosaves an in-progress response."""
    student_profile = await _resolve_student_profile(db, current_user.id)
    resp = await assessment_service.autosave_response(
        db,
        attempt_id=attempt_id,
        student_profile_id=student_profile.id,
        data=payload,
    )
    return {"status": "saved", "question_version_id": resp.question_version_id, "updated_at": resp.updated_at}


@router.post("/attempts/{attempt_id}/submit")
async def submit_attempt(
    attempt_id: str,
    payload: Optional[AssessmentSubmitPayload] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Transactionally submits an attempt, evaluates objective answers, and derives marks."""
    student_profile = await _resolve_student_profile(db, current_user.id)
    resps = payload.responses if payload else None
    result = await assessment_service.submit_assessment_attempt(
        db,
        attempt_id=attempt_id,
        student_profile_id=student_profile.id,
        responses_payload=resps,
    )
    return {
        "status": "submitted",
        "attempt_id": attempt_id,
        "is_evaluated": result.status in ("internal", "released"),
        "result_status": result.status,
        "submitted_at": result.evaluated_at,
    }


# =========================================================================
# 5. Manual Evaluation, Regrading & Result Release
# =========================================================================

@router.post("/evaluations/{evaluation_id}/grade")
async def grade_manual_evaluation(
    evaluation_id: str,
    payload: ManualGradePayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Allows authorized instructors to evaluate subjective responses using rubrics."""
    evaluation = await assessment_service.grade_manual_question(
        db,
        evaluation_id=evaluation_id,
        instructor_id=current_user.id,
        awarded_marks=payload.awarded_marks,
        evaluator_notes=payload.evaluator_notes,
        rubric_criterion_id=payload.rubric_criterion_id,
    )
    return {
        "evaluation_id": evaluation.id,
        "awarded_marks": evaluation.awarded_marks,
        "is_correct": evaluation.is_correct,
        "evaluated_at": evaluation.evaluated_at,
    }


@router.post("/results/{attempt_id}/release")
async def release_result(
    attempt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Releases result to student view according to assessment policy."""
    result = await assessment_service.release_assessment_result(
        db,
        attempt_id=attempt_id,
        released_by=current_user.id,
    )
    return {"status": "released", "attempt_id": attempt_id, "released_at": result.released_at}


@router.post("/results/{attempt_id}/recall")
async def recall_result(
    attempt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.TEACHER, UserRole.HOD, UserRole.INSTITUTION_ADMIN, UserRole.SUPER_ADMIN)),
):
    """Recalls released result for regrading."""
    result = await assessment_service.recall_assessment_result(db, attempt_id=attempt_id)
    return {"status": "recalled", "attempt_id": attempt_id}


# =========================================================================
# 6. Student Results & Evidence Queries
# =========================================================================

@router.get("/attempts/{attempt_id}/result")
async def get_student_attempt_result(
    attempt_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Queries student attempt result respecting release and feedback policies."""
    student_profile = await _resolve_student_profile(db, current_user.id)
    return await assessment_service.get_student_attempt_result(
        db,
        attempt_id=attempt_id,
        student_profile_id=student_profile.id,
    )


@router.get("/students/me/evidence/concepts", response_model=List[ConceptEvidenceResponse])
async def get_my_concept_evidences(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Fetches immutable concept evidence generated by assessments."""
    student_profile = await _resolve_student_profile(db, current_user.id)
    return await assessment_service.get_student_concept_evidences(
        db,
        student_profile_id=student_profile.id,
        skip=skip,
        limit=limit,
    )


@router.get("/students/me/evidence/skills", response_model=List[SkillEvidenceResponse])
async def get_my_skill_evidences(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.STUDENT)),
):
    """Fetches immutable skill evidence generated by assessments referencing SkillCatalog."""
    student_profile = await _resolve_student_profile(db, current_user.id)
    return await assessment_service.get_student_skill_evidences(
        db,
        student_profile_id=student_profile.id,
        skip=skip,
        limit=limit,
    )
