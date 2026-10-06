"""Manual subjective evaluation strategy for short-answer, essay, and case-study questions."""

from decimal import Decimal
from app.domains.assessment.evaluators.base import EvaluationInput, EvaluationResult


class ManualEvaluator:
    """Designates a question as requiring instructor manual grading using rubrics."""

    def evaluate(self, inp: EvaluationInput) -> EvaluationResult:
        student_text = inp.response_payload.get("text_answer", "")
        is_empty = not student_text or not str(student_text).strip()

        return EvaluationResult(
            awarded_marks=Decimal("0.00"),
            penalty_marks=Decimal("0.00"),
            max_marks=inp.points,
            is_correct=False,
            evaluation_type="manual",
            feedback="Pending faculty evaluation" if not is_empty else "Unanswered",
            details={
                "has_submission": not is_empty,
                "character_count": len(str(student_text)),
                "rubric_id": inp.truth_metadata.get("rubric_id"),
            },
        )
