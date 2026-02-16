"""Analytics snapshot entity. Immutable result at a clock point."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from football_engine.domain.value_objects import MatchClock


@dataclass(frozen=True)
class AnalyticsSnapshot:
    snapshot_id: str
    match_id: str
    clock: MatchClock
    features_by_window: dict[str, Any]
    derived_metrics: dict[str, Any]
    deltas: dict[str, Any]
    why: list[str]
    model_version: str
    created_at_utc: datetime
