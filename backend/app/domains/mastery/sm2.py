"""Deterministic implementation of the SuperMemo SM-2 Spaced Repetition Algorithm.

CRITICAL: This is a pure mathematical business engine.
The LLM is NOT permitted to calculate or override spaced repetition intervals.
"""

from datetime import datetime, timezone, timedelta
from typing import NamedTuple


class SM2Result(NamedTuple):
    interval_days: int
    repetitions: int
    easiness_factor: float
    next_review_at: datetime


def calculate_sm2(
    grade: int,
    previous_repetitions: int = 0,
    previous_interval: int = 0,
    previous_easiness_factor: float = 2.5,
    now: datetime | None = None,
) -> SM2Result:
    """Calculates the next review schedule using the deterministic SM-2 algorithm.

    Args:
        grade: Response quality rating from 0 (complete blackout) to 5 (perfect recall).
        previous_repetitions: Number of consecutive successful recall reviews.
        previous_interval: Previous interval in days.
        previous_easiness_factor: Previous easiness factor (minimum 1.3).
        now: Reference timestamp for scheduling (defaults to UTC now).

    Returns:
        SM2Result with updated interval, repetitions count, EF, and next review datetime.
    """
    if not (0 <= grade <= 5):
        raise ValueError(f"SM-2 grade must be an integer between 0 and 5, received {grade}")

    if now is None:
        now = datetime.now(timezone.utc)

    # 1. Update Easiness Factor (EF)
    # Formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    delta = 0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)
    new_ef = round(max(1.3, previous_easiness_factor + delta), 4)

    # 2. Update Repetition Count & Interval
    if grade < 3:
        # Failure: reset consecutive repetitions and set interval to 1 day
        new_repetitions = 0
        new_interval = 1
    else:
        # Success: increment repetitions and compute progressive interval
        if previous_repetitions == 0:
            new_interval = 1
        elif previous_repetitions == 1:
            new_interval = 6
        else:
            new_interval = int(round(previous_interval * new_ef))
        new_repetitions = previous_repetitions + 1

    next_review_at = now + timedelta(days=new_interval)

    return SM2Result(
        interval_days=new_interval,
        repetitions=new_repetitions,
        easiness_factor=new_ef,
        next_review_at=next_review_at,
    )
