"""Rate limiting and abuse prevention abstraction.

Architecture:
- In development/single-instance: Implements an in-memory sliding window rate limiter.
- In distributed production: Designed for drop-in replacement with a Redis-backed token bucket.
"""

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from fastapi import HTTPException, status
from app.core.logging import logger


class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter for abuse prevention."""

    def __init__(self):
        # Maps bucket_key -> list of timestamp floats
        self._hits: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Evaluates whether the key has exceeded max_requests within window_seconds.

        Returns True if the request should be blocked.
        """
        now = datetime.now(timezone.utc).timestamp()
        cutoff = now - window_seconds

        # Prune older entries
        self._hits[key] = [ts for ts in self._hits[key] if ts > cutoff]

        if len(self._hits[key]) >= max_requests:
            logger.warning(f"Rate limit exceeded for key '{key}' ({len(self._hits[key])}/{max_requests} in {window_seconds}s)")
            return True

        self._hits[key].append(now)
        return False

    def check_or_raise(self, key: str, max_requests: int, window_seconds: int, action_name: str = "request") -> None:
        """Enforces rate limit and raises 429 Too Many Requests if exceeded."""
        if self.is_rate_limited(key, max_requests, window_seconds):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many {action_name} attempts. Please wait before retrying.",
            )


# Global instance for authentication endpoints
auth_rate_limiter = InMemoryRateLimiter()
