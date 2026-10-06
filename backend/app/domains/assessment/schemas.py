"""Pydantic schemas for Assessment Engine, Question Banks, and Evaluation (Domain 5)."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


# =========================================================================
# 1. Question Bank & Rubrics
# =========================================================================

class QuestionBankCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    department_id: Optional[str] = None
    course_id: Optional[str] = None
    visibility: str = "institution"  # institution, department, course, public


class QuestionBankUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None


class QuestionBankResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    owner_id: Optional[str] = None
    department_id: Optional[str] = None
    course_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: str
    visibility: str
    created_at: datetime
    updated_at: datetime


class RubricCriterionCreate(BaseModel):
    title: str
    description: Optional[str] = None
    max_points: Decimal = Decimal("10.00")
    weight: Decimal = Decimal("1.00")
    order_index: int = 0


class RubricCriterionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    rubric_id: str
    title: str
    description: Optional[str] = None
    max_points: Decimal
    weight: Decimal
    order_index: int
    created_at: datetime


class EvaluationRubricCreate(BaseModel):
    title: str
    description: Optional[str] = None
    criteria: List[RubricCriterionCreate] = []


class EvaluationRubricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    title: str
    description: Optional[str] = None
    version: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    criteria: List[RubricCriterionResponse] = []


# =========================================================================
# 2. Options, Coding, Concepts, Skills, & Questions
# =========================================================================

class QuestionOptionCreate(BaseModel):
    option_text: str
    order_index: int = 0
    is_correct: bool = False
    explanation: Optional[str] = None
    metadata_payload: Optional[Dict[str, Any]] = None


class QuestionOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_version_id: str
    option_text: str
    order_index: int
    is_correct: bool
    explanation: Optional[str] = None
    metadata_payload: Optional[Dict[str, Any]] = None


class QuestionOptionStudentView(BaseModel):
    """Student delivery view strictly stripping is_correct and teacher explanation."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    option_text: str
    order_index: int


class CodingTestCaseCreate(BaseModel):
    input_data: str
    expected_output: str
    is_hidden: bool = False
    points_weight: Decimal = Decimal("1.00")


class CodingTestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    input_data: str
    expected_output: str
    is_hidden: bool
    points_weight: Decimal


class CodingConfigCreate(BaseModel):
    language: str = "python"
    starter_code: Optional[str] = None
    function_signature: Optional[str] = None
    time_limit_ms: int = 2000
    memory_limit_mb: int = 256
    constraints_text: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    test_cases: List[CodingTestCaseCreate] = []


class CodingConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    language: str
    starter_code: Optional[str] = None
    function_signature: Optional[str] = None
    time_limit_ms: int
    memory_limit_mb: int
    constraints_text: Optional[str] = None
    input_format: Optional[str] = None
    output_format: Optional[str] = None
    test_cases: List[CodingTestCaseResponse] = []


class QuestionConceptCreate(BaseModel):
    concept_id: str
    importance: float = 1.0
    is_primary: bool = False
    weight: Decimal = Decimal("1.00")


class QuestionConceptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_version_id: str
    concept_id: str
    importance: float
    is_primary: bool
    weight: Decimal


class QuestionSkillCreate(BaseModel):
    skill_id: str
    weight: Decimal = Decimal("1.00")
    evidence_type: str = "assessment"


class QuestionSkillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_version_id: str
    skill_id: str
    weight: Decimal
    evidence_type: str


class QuestionVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_id: str
    version_number: int
    prompt: str
    instructions: Optional[str] = None
    explanation: Optional[str] = None
    points: Decimal
    negative_marks: Decimal
    estimated_seconds: Optional[int] = None
    difficulty: str
    rubric_id: Optional[str] = None
    evaluation_config: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None
    created_at: datetime
    options: List[QuestionOptionResponse] = []
    concepts: List[QuestionConceptResponse] = []
    skills: List[QuestionSkillResponse] = []
    coding_config: Optional[CodingConfigResponse] = None


class QuestionCreate(BaseModel):
    question_type: str
    title: str = Field(..., max_length=255)
    prompt: str
    instructions: Optional[str] = None
    explanation: Optional[str] = None
    difficulty: str = "medium"
    points: Decimal = Decimal("1.00")
    negative_marks: Decimal = Decimal("0.00")
    estimated_seconds: Optional[int] = None
    rubric_id: Optional[str] = None
    evaluation_config: Optional[Dict[str, Any]] = None
    options: List[QuestionOptionCreate] = []
    concepts: List[QuestionConceptCreate] = []
    skills: List[QuestionSkillCreate] = []
    coding_config: Optional[CodingConfigCreate] = None


class QuestionUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    difficulty: Optional[str] = None


class QuestionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    bank_id: str
    question_type: str
    title: str
    difficulty: str
    current_version: int
    status: str
    author_id: Optional[str] = None
    reviewer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    versions: List[QuestionVersionResponse] = []


# =========================================================================
# 3. Assessment & Blueprints
# =========================================================================

class AssessmentBlueprintCreate(BaseModel):
    title: str
    description: Optional[str] = None
    total_questions: int
    rules_config: Dict[str, Any]  # {"difficulty": {"easy": 40, "medium": 40, "hard": 20}, "concepts": [...]}


class AssessmentBlueprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    assessment_id: str
    title: str
    description: Optional[str] = None
    total_questions: int
    rules_config: Dict[str, Any]
    is_active: bool
    created_at: datetime


class AssessmentCreate(BaseModel):
    course_offering_id: Optional[str] = None
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None
    assessment_type: str = "quiz"
    duration_minutes: Optional[int] = None
    total_marks: Decimal = Decimal("0.00")
    passing_marks: Decimal = Decimal("0.00")
    attempts_allowed: int = 1
    randomization_config: Optional[Dict[str, Any]] = None
    feedback_policy: str = "after_submission"
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    late_submission_allowed: bool = False


class AssessmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    status: Optional[str] = None
    duration_minutes: Optional[int] = None
    total_marks: Optional[Decimal] = None
    passing_marks: Optional[Decimal] = None
    attempts_allowed: Optional[int] = None
    feedback_policy: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    late_submission_allowed: Optional[bool] = None


class AssessmentQuestionAttach(BaseModel):
    question_version_id: str
    order_index: int = 0
    section_name: str = "Default"
    custom_points: Optional[Decimal] = None
    custom_negative_marks: Optional[Decimal] = None


class AssessmentQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    assessment_version_id: str
    question_version_id: str
    order_index: int
    section_name: str
    custom_points: Optional[Decimal] = None
    custom_negative_marks: Optional[Decimal] = None
    question_version: Optional[QuestionVersionResponse] = None


class AssessmentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    assessment_id: str
    version_number: int
    title: str
    instructions: Optional[str] = None
    total_marks: Decimal
    passing_marks: Decimal
    duration_minutes: Optional[int] = None
    feedback_policy: str
    rules_snapshot: Optional[Dict[str, Any]] = None
    is_frozen: bool
    created_at: datetime
    assessment_questions: List[AssessmentQuestionResponse] = []


class AssessmentDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    course_offering_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    instructions: Optional[str] = None
    assessment_type: str
    status: str
    duration_minutes: Optional[int] = None
    total_marks: Decimal
    passing_marks: Decimal
    attempts_allowed: int
    randomization_config: Optional[Dict[str, Any]] = None
    feedback_policy: str
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    late_submission_allowed: bool
    current_version: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    versions: List[AssessmentVersionResponse] = []
    blueprints: List[AssessmentBlueprintResponse] = []


# =========================================================================
# 4. Student Question Delivery & In-Progress Attempt
# =========================================================================

class StudentQuestionDelivery(BaseModel):
    """Question representation delivered to student during active attempt."""
    assessment_question_id: str
    question_version_id: str
    question_type: str
    title: str
    prompt: str
    instructions: Optional[str] = None
    order_index: int
    section_name: str
    points: Decimal
    negative_marks: Decimal
    options: List[QuestionOptionStudentView] = []
    # Coding questions receive public test cases and starter templates only
    coding_starter_code: Optional[str] = None
    coding_language: Optional[str] = None
    public_test_cases: List[Dict[str, Any]] = []


class AssessmentAttemptDelivery(BaseModel):
    """Complete attempt view delivered to student."""
    attempt_id: str
    assessment_id: str
    assessment_title: str
    instructions: Optional[str] = None
    attempt_number: int
    started_at: datetime
    expires_at: datetime
    duration_minutes: Optional[int] = None
    status: str
    questions: List[StudentQuestionDelivery]
    existing_responses: Dict[str, Any] = {}


class AssessmentResponseAutosave(BaseModel):
    question_version_id: str
    response_type: str
    response_payload: Dict[str, Any]
    is_flagged: bool = False


class AssessmentSubmitPayload(BaseModel):
    responses: Optional[List[AssessmentResponseAutosave]] = None


# =========================================================================
# 5. Results & Evidence
# =========================================================================

class QuestionEvaluationDetail(BaseModel):
    question_version_id: str
    awarded_marks: Decimal
    penalty_marks: Decimal
    max_marks: Decimal
    is_correct: bool
    evaluation_type: str
    feedback: Optional[str] = None


class AssessmentResultDetail(BaseModel):
    attempt_id: str
    assessment_title: str
    total_marks_obtained: Decimal
    maximum_marks: Decimal
    percentage: Decimal
    grade: Optional[str] = None
    is_passed: bool
    status: str
    evaluated_at: datetime
    released_at: Optional[datetime] = None
    question_evaluations: List[QuestionEvaluationDetail] = []


class ManualGradePayload(BaseModel):
    awarded_marks: Decimal
    evaluator_notes: Optional[str] = None
    rubric_criterion_id: Optional[str] = None


class ConceptEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_profile_id: str
    concept_id: str
    question_version_id: str
    assessment_id: Optional[str] = None
    score: Decimal
    max_score: Decimal
    evidence_type: str
    evaluation_method: str
    timestamp: datetime


class SkillEvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    student_profile_id: str
    skill_id: str
    question_version_id: str
    assessment_id: Optional[str] = None
    score: Decimal
    weight: Decimal
    evidence_type: str
    evaluation_method: str
    timestamp: datetime


class GradeSchemeCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    is_default: bool = False
    rules_payload: List[Dict[str, Any]]  # [{"grade": "A+", "min_percentage": 90.0, "max_percentage": 100.0}]


class GradeSchemeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    institution_id: str
    name: str
    description: Optional[str] = None
    is_default: bool
    rules_payload: List[Dict[str, Any]]
    created_at: datetime
