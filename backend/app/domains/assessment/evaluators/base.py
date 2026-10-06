"""Base protocol and data contracts for assessment evaluation strategies."""

from decimal import Decimal
from typing import Protocol, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict


class EvaluationInput(BaseModel):
    """Input payload delivered to an evaluator."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    question_version_id: str
    question_type: str
    response_payload: Dict[str, Any]
    points: Decimal
    negative_marks: Decimal = Decimal("0.00")
    evaluation_config: Optional[Dict[str, Any]] = None
    # Authoritative teacher metadata (options, expected answers, test cases, rubrics)
    truth_metadata: Dict[str, Any]


class EvaluationResult(BaseModel):
    """Deterministic result produced by an evaluator."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    awarded_marks: Decimal
    penalty_marks: Decimal = Decimal("0.00")
    max_marks: Decimal
    is_correct: bool
    evaluation_type: str = "deterministic"
    feedback: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class EvaluationStrategy(Protocol):
    """Strategy interface for question evaluators."""

    def evaluate(self, inp: EvaluationInput) -> EvaluationResult:
        """Evaluates a response deterministically against author truth metadata."""
        ...
