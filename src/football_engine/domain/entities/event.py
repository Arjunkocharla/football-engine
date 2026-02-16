"""Event entity. Normalized domain event input."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from football_engine.domain.enums import EventType, TeamSide
from football_engine.domain.value_objects import MatchClock


@dataclass(frozen=True)
class Event:
    event_id: str
    match_id: str
    provider_name: str
    provider_event_id: str | None
    clock: MatchClock
    team_side: TeamSide
    event_type: EventType
    payload: dict[str, Any] | None
    ingested_at_utc: datetime

    def is_attacking_action(self) -> bool:
        return self.event_type in (
            EventType.SHOT,
            EventType.SHOT_ON_TARGET,
            EventType.CORNER,
            EventType.GOAL,
        )

    def xg_value(self) -> float | None:
        if not self.payload:
            return None
        xg = self.payload.get("xg")
        if xg is None:
            return None
        return float(xg)
