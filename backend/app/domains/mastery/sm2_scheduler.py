"""Deterministic SuperMemo SM-2 Spaced Repetition Scheduler."""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import NamedTuple, Optional
from app.domains.mastery.config import SM2Config, DEFAULT_KNOWLEDGE_CONFIG


class SM2ScheduleResult(NamedTuple):
    """Immutable output produced by SM2Scheduler."""
    repetition: int
    interval_days: int
    ease_factor: Decimal
    next_review_at: datetime
    review_status: str  # due, upcoming, overdue, completed


class SM2Scheduler:
    """Pure deterministic scheduler implementing the SuperMemo SM-2 algorithm."""

    @staticmethod
    def initialize_schedule(
        now: Optional[datetime] = None,
        config: SM2Config = DEFAULT_KNOWLEDGE_CONFIG.sm2,
    ) -> SM2ScheduleResult:
        """Deterministically initializes spaced repetition state for a new concept."""
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        first_interval = config.first_interval_days
        next_review = now + timedelta(days=first_interval)

        return SM2ScheduleResult(
            repetition=0,
            interval_days=first_interval,
            ease_factor=config.initial_ease_factor,
            next_review_at=next_review,
            review_status="upcoming",
        )

    @staticmethod
    def calculate_next_schedule(
        quality: int,
        previous_repetition: int = 0,
        previous_interval_days: int = 1,
        previous_ease_factor: Decimal = Decimal("2.5000"),
        now: Optional[datetime] = None,
        config: SM2Config = DEFAULT_KNOWLEDGE_CONFIG.sm2,
    ) -> SM2ScheduleResult:
        """Calculates updated SM-2 interval, ease factor, and next review date.
        
        Args:
            quality: Response recall rating from 0 (complete blackout) to 5 (flawless recall).
            previous_repetition: Number of consecutive successful recall reviews.
            previous_interval_days: Interval in days used for previous review.
            previous_ease_factor: Previous easiness factor (minimum 1.3000).
            now: Authoritative server reference time.
            config: SM-2 configuration constants.
        """
        if not (0 <= quality <= 5):
            raise ValueError(f"Recall quality must be an integer between 0 and 5, received {quality}")

        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        prev_ef_float = float(previous_ease_factor)

        # 1. Update Easiness Factor (EF)
        # Formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        q_diff = 5 - quality
        delta = 0.1 - q_diff * (0.08 + q_diff * 0.02)
        new_ef_float = max(float(config.min_ease_factor), prev_ef_float + delta)
        new_ease_factor = Decimal(str(round(new_ef_float, 4)))

        # 2. Update Repetition Count and Interval
        if quality < 3:
            # Recall Failure: Reset repetition streak to 0 and interval to 1 day
            new_repetition = 0
            new_interval_days = config.first_interval_days
        else:
            # Recall Success: Increment repetition streak and apply progressive spacing
            if previous_repetition == 0:
                new_interval_days = config.first_interval_days
            elif previous_repetition == 1:
                new_interval_days = config.second_interval_days
            else:
                new_interval_days = int(round(previous_interval_days * new_ef_float))

            new_repetition = previous_repetition + 1

        new_interval_days = max(1, new_interval_days)
        next_review_at = now + timedelta(days=new_interval_days)

        # Status determination relative to now
        status = "upcoming"
        if next_review_at <= now:
            status = "due"

        return SM2ScheduleResult(
            repetition=new_repetition,
            interval_days=new_interval_days,
            ease_factor=new_ease_factor,
            next_review_at=next_review_at,
            review_status=status,
        )

    @staticmethod
    def classify_status(next_review_at: datetime, now: Optional[datetime] = None) -> str:
        """Classifies schedule status: overdue, due, or upcoming."""
        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        review_time = (
            next_review_at if next_review_at.tzinfo is not None else next_review_at.replace(tzinfo=timezone.utc)
        )

        diff_seconds = (now - review_time).total_seconds()
        if diff_seconds > 86400:  # More than 24 hours overdue
            return "overdue"
        elif diff_seconds >= 0:
            return "due"
        else:
            return "upcoming"
