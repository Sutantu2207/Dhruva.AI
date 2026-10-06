"""Evaluator factory and registry for question types."""

from typing import Dict
from app.domains.assessment.evaluators.base import EvaluationStrategy
from app.domains.assessment.evaluators.objective import (
    SingleChoiceEvaluator,
    MultipleChoiceEvaluator,
    TrueFalseEvaluator,
    NumericEvaluator,
    FillBlankEvaluator,
    OrderingEvaluator,
    MatchingEvaluator,
)
from app.domains.assessment.evaluators.manual import ManualEvaluator
from app.domains.assessment.evaluators.coding import CodingEvaluator

_REGISTRY: Dict[str, EvaluationStrategy] = {
    "single_choice": SingleChoiceEvaluator(),
    "multiple_choice": MultipleChoiceEvaluator(),
    "true_false": TrueFalseEvaluator(),
    "numeric": NumericEvaluator(),
    "fill_blank": FillBlankEvaluator(),
    "ordering": OrderingEvaluator(),
    "matching": MatchingEvaluator(),
    "short_answer": ManualEvaluator(),
    "long_answer": ManualEvaluator(),
    "case_study": ManualEvaluator(),
    "coding": CodingEvaluator(),
}


def get_evaluator(question_type: str) -> EvaluationStrategy:
    """Retrieves the evaluator strategy for the given question type."""
    if question_type not in _REGISTRY:
        # Default fallback to manual evaluator for unknown custom types
        return ManualEvaluator()
    return _REGISTRY[question_type]
