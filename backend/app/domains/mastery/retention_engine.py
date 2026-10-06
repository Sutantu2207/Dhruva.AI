"""Deterministic Retention Engine.

Computes retention estimates [0.0000, 1.0000] independently from mastery.
Uses an Ebbinghaus-derived exponential decay model conditioned by memory stability
and spacing intervals.
"""

import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from app.domains.mastery.config import RetentionConfig, DEFAULT_KNOWLEDGE_CONFIG


class RetentionEngine:
    """Pure deterministic engine estimating current student concept retention."""

    @staticmethod
    def estimate_retention(
        last_event_at: Optional[datetime],
        interval_days: int = 1,
        ease_factor: Decimal = Decimal("2.5000"),
        now: Optional[datetime] = None,
        config: RetentionConfig = DEFAULT_KNOWLEDGE_CONFIG.retention,
    ) -> Decimal:
        """Estimates retention probability from elapsed time and memory stability.
        
        Formula:
        stability S = max(1.0, interval_days * (ease_factor / 2.5))
        elapsed_days = max(0.0, (now - last_event_at).total_seconds() / 86400.0)
        retention = exp(-elapsed_days / S)
        """
        if last_event_at is None:
            # If no review or evidence has ever occurred, retention defaults to 1.0 until learned
            return Decimal("1.0000")

        if now is None:
            now = datetime.now(timezone.utc)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        event_time = (
            last_event_at if last_event_at.tzinfo is not None else last_event_at.replace(tzinfo=timezone.utc)
        )

        elapsed_seconds = max(0.0, (now - event_time).total_seconds())
        elapsed_days = elapsed_seconds / 86400.0

        # Memory Stability (S): longer intervals and higher ease indicate stronger stability
        ef_float = float(ease_factor)
        stability = max(1.0, float(interval_days) * (ef_float / 2.5000))

        # Retention decay curve
        raw_retention = math.exp(-elapsed_days / stability)
        clamped_retention = max(0.0, min(1.0, raw_retention))

        return Decimal(str(round(clamped_retention, 4)))
