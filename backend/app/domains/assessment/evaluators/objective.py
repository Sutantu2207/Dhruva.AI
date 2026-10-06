"""Deterministic objective evaluation strategies."""

from decimal import Decimal
from typing import Dict, Any, List, Set
from app.domains.assessment.evaluators.base import EvaluationInput, EvaluationResult, EvaluationStrategy


class SingleChoiceEvaluator:
    """Evaluates single-choice questions."""

    def evaluate(self, inp: EvaluationInput) -> EvaluationResult:
        selected_option_id = inp.response_payload.get("selected_option_id")
        options = inp.truth_metadata.get("options", [])
        correct_option_ids = [opt["id"] for opt in options if opt.get("is_correct")]

        if not selected_option_id:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                feedback="Unanswered",
            )

        is_match = selected_option_id in correct_option_ids
        if is_match:
            return EvaluationResult(
                awarded_marks=inp.points,
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=True,
                feedback="Correct",
            )
        else:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=inp.negative_marks,
                max_marks=inp.points,
                is_correct=False,
                feedback="Incorrect",
            )


class MultipleChoiceEvaluator:
    """Evaluates multiple-choice questions with configurable partial credit or all-or-nothing policy."""

    def evaluate(self, inp: EvaluationInput) -> EvaluationResult:
        selected_option_ids: Set[str] = set(inp.response_payload.get("selected_option_ids", []))
        options = inp.truth_metadata.get("options", [])
        correct_option_ids: Set[str] = {opt["id"] for opt in options if opt.get("is_correct")}
        all_option_ids: Set[str] = {opt["id"] for opt in options}

        if not selected_option_ids:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                feedback="Unanswered",
            )

        config = inp.evaluation_config or {}
        mode = config.get("scoring_mode", "all_or_nothing")  # "all_or_nothing" | "partial_credit"

        if mode == "all_or_nothing":
            if selected_option_ids == correct_option_ids:
                return EvaluationResult(
                    awarded_marks=inp.points,
                    penalty_marks=Decimal("0.00"),
                    max_marks=inp.points,
                    is_correct=True,
                    feedback="All correct selections matched",
                )
            else:
                return EvaluationResult(
                    awarded_marks=Decimal("0.00"),
                    penalty_marks=inp.negative_marks,
                    max_marks=inp.points,
                    is_correct=False,
                    feedback="Incorrect selections",
                )

        # Partial credit algorithm:
        # factor = (correct_hits / total_correct) - (incorrect_hits / total_incorrect)
        # clamped to [0.0, 1.0]
        correct_hits = len(selected_option_ids & correct_option_ids)
        incorrect_hits = len(selected_option_ids - correct_option_ids)
        total_correct = max(1, len(correct_option_ids))
        total_incorrect = max(1, len(all_option_ids) - len(correct_option_ids))

        pos_ratio = Decimal(correct_hits) / Decimal(total_correct)
        neg_ratio = Decimal(incorrect_hits) / Decimal(total_incorrect)
        factor = max(Decimal("0.00"), pos_ratio - neg_ratio)

        awarded = round(inp.points * factor, 2)
        is_all_correct = selected_option_ids == correct_option_ids

        return EvaluationResult(
            awarded_marks=awarded,
            penalty_marks=Decimal("0.00"),
            max_marks=inp.points,
            is_correct=is_all_correct,
            feedback=f"Partial credit: {correct_hits}/{total_correct} correct, {incorrect_hits} incorrect",
            details={"correct_hits": correct_hits, "incorrect_hits": incorrect_hits, "ratio": float(factor)},
        )


class TrueFalseEvaluator:
    """Evaluates boolean true/false responses."""

    def evaluate(self, inp: EvaluationInput) -> EvaluationResult:
        student_val = inp.response_payload.get("selected_value")
        if student_val is None:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                feedback="Unanswered",
            )

        expected_val = inp.truth_metadata.get("expected_value")
        if expected_val is None:
            # Check options if true_false options stored as options
            options = inp.truth_metadata.get("options", [])
            for opt in options:
                if opt.get("is_correct"):
                    expected_val = opt.get("option_text", "").strip().lower() in ("true", "t", "yes", "1")
                    break

        if bool(student_val) == bool(expected_val):
            return EvaluationResult(
                awarded_marks=inp.points,
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=True,
                feedback="Correct",
            )
        else:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=inp.negative_marks,
                max_marks=inp.points,
                is_correct=False,
                feedback="Incorrect",
            )


class NumericEvaluator:
    """Evaluates numeric responses with configurable absolute or relative tolerance."""

    def evaluate(self, inp: EvaluationInput) -> EvaluationResult:
        val_str = inp.response_payload.get("value")
        if val_str is None or str(val_str).strip() == "":
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                feedback="Unanswered",
            )

        try:
            student_val = Decimal(str(val_str).strip())
        except Exception:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=inp.negative_marks,
                max_marks=inp.points,
                is_correct=False,
                feedback="Invalid numeric format",
            )

        expected_str = inp.truth_metadata.get("expected_value", "0")
        expected_val = Decimal(str(expected_str))

        config = inp.evaluation_config or {}
        tolerance = Decimal(str(config.get("tolerance", "0.00")))

        diff = abs(student_val - expected_val)
        if diff <= tolerance:
            return EvaluationResult(
                awarded_marks=inp.points,
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=True,
                feedback="Correct numeric value within tolerance",
            )
        else:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=inp.negative_marks,
                max_marks=inp.points,
                is_correct=False,
                feedback="Incorrect numeric value",
            )


class FillBlankEvaluator:
    """Evaluates fill-in-the-blank text responses."""

    def evaluate(self, inp: EvaluationInput) -> EvaluationResult:
        student_text = str(inp.response_payload.get("text_answer", "")).strip()
        if not student_text:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                feedback="Unanswered",
            )

        accepted = inp.truth_metadata.get("accepted_answers", [])
        if not accepted and "options" in inp.truth_metadata:
            accepted = [opt.get("option_text", "") for opt in inp.truth_metadata["options"] if opt.get("is_correct")]

        config = inp.evaluation_config or {}
        case_sensitive = config.get("case_sensitive", False)

        def normalize(s: str) -> str:
            return s.strip() if case_sensitive else s.strip().lower()

        normalized_student = normalize(student_text)
        is_match = any(normalize(str(ans)) == normalized_student for ans in accepted)

        if is_match:
            return EvaluationResult(
                awarded_marks=inp.points,
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=True,
                feedback="Correct text answer",
            )
        else:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=inp.negative_marks,
                max_marks=inp.points,
                is_correct=False,
                feedback="Incorrect text answer",
            )


class OrderingEvaluator:
    """Evaluates sequence ordering questions."""

    def evaluate(self, inp: EvaluationInput) -> EvaluationResult:
        ordered_ids: List[str] = inp.response_payload.get("ordered_option_ids", [])
        options = inp.truth_metadata.get("options", [])
        # Sorted by order_index
        sorted_options = sorted(options, key=lambda x: x.get("order_index", 0))
        expected_ids = [opt["id"] for opt in sorted_options]

        if not ordered_ids:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                feedback="Unanswered",
            )

        if ordered_ids == expected_ids:
            return EvaluationResult(
                awarded_marks=inp.points,
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=True,
                feedback="Correct sequence",
            )

        # Check partial positional correctness
        config = inp.evaluation_config or {}
        allow_partial = config.get("allow_partial_credit", False)
        if allow_partial and len(expected_ids) > 0:
            matches = sum(1 for i, oid in enumerate(ordered_ids) if i < len(expected_ids) and oid == expected_ids[i])
            factor = Decimal(matches) / Decimal(len(expected_ids))
            awarded = round(inp.points * factor, 2)
            return EvaluationResult(
                awarded_marks=awarded,
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                feedback=f"Partially correct order: {matches}/{len(expected_ids)} positions matched",
            )

        return EvaluationResult(
            awarded_marks=Decimal("0.00"),
            penalty_marks=inp.negative_marks,
            max_marks=inp.points,
            is_correct=False,
            feedback="Incorrect order",
        )


class MatchingEvaluator:
    """Evaluates key-value pair matching questions."""

    def evaluate(self, inp: EvaluationInput) -> EvaluationResult:
        pairs: Dict[str, str] = inp.response_payload.get("pairs", {})
        expected_pairs: Dict[str, str] = inp.truth_metadata.get("expected_pairs", {})

        if not pairs:
            return EvaluationResult(
                awarded_marks=Decimal("0.00"),
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                feedback="Unanswered",
            )

        total_pairs = max(1, len(expected_pairs))
        matched_count = sum(1 for k, v in pairs.items() if expected_pairs.get(k) == v)

        if matched_count == total_pairs:
            return EvaluationResult(
                awarded_marks=inp.points,
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=True,
                feedback="All pairs matched correctly",
            )

        config = inp.evaluation_config or {}
        allow_partial = config.get("allow_partial_credit", True)
        if allow_partial:
            factor = Decimal(matched_count) / Decimal(total_pairs)
            awarded = round(inp.points * factor, 2)
            return EvaluationResult(
                awarded_marks=awarded,
                penalty_marks=Decimal("0.00"),
                max_marks=inp.points,
                is_correct=False,
                feedback=f"Matched {matched_count} of {total_pairs} pairs",
            )

        return EvaluationResult(
            awarded_marks=Decimal("0.00"),
            penalty_marks=inp.negative_marks,
            max_marks=inp.points,
            is_correct=False,
            feedback="Incorrect matches",
        )
