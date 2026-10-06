"""Clock abstraction for deterministic time testing across Knowledge State and SM-2."""

from datetime import datetime, timezone, timedelta
from typing import Protocol


class Clock(Protocol):
    """Protocol for timezone-aware UTC clock providers."""

    def now(self) -> datetime:
        """Returns the current timezone-aware UTC datetime."""
        ...


class SystemClock:
    """Standard system clock returning true UTC time."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FrozenClock:
    """Deterministic, controllable clock for property and simulation testing."""

    def __init__(self, initial_time: datetime | None = None):
        if initial_time is None:
            self._current_time = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
        else:
            if initial_time.tzinfo is None:
                self._current_time = initial_time.replace(tzinfo=timezone.utc)
            else:
                self._current_time = initial_time

    def now(self) -> datetime:
        return self._current_time

    def set_time(self, new_time: datetime) -> None:
        if new_time.tzinfo is None:
            self._current_time = new_time.replace(tzinfo=timezone.utc)
        else:
            self._current_time = new_time

    def advance(self, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> datetime:
        self._current_time += timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return self._current_time
