"""Domain value objects. Immutable."""

from dataclasses import dataclass


@dataclass(frozen=True)
class MatchClock:
    period: int
    minute: int
    second: int

    def __post_init__(self) -> None:
        if self.period < 1:
            raise ValueError("period must be >= 1")
        if not 0 <= self.second <= 59:
            raise ValueError("second must be 0..59")

    def total_seconds_in_period(self) -> int:
        return self.minute * 60 + self.second

    def __lt__(self, other: "MatchClock") -> bool:
        if not isinstance(other, MatchClock):
            return NotImplemented
        if self.period != other.period:
            return self.period < other.period
        return self.total_seconds_in_period() < other.total_seconds_in_period()


@dataclass(frozen=True)
class Score:
    home: int
    away: int

    def __post_init__(self) -> None:
        if self.home < 0 or self.away < 0:
            raise ValueError("scores must be non-negative")

    def goal_diff_for(self, side: str) -> int:
        if side == "HOME":
            return self.home - self.away
        return self.away - self.home


@dataclass(frozen=True)
class RollingWindow:
    minutes: int

    def __post_init__(self) -> None:
        if self.minutes not in (5, 10):
            raise ValueError("minutes must be 5 or 10")

    @property
    def label(self) -> str:
        return f"{self.minutes}m"
