"""Analytics snapshot repository port."""

from typing import Protocol

from football_engine.domain.entities import AnalyticsSnapshot


class AnalyticsRepository(Protocol):
    """Store and retrieve latest snapshot (and optional history)."""

    def save_snapshot(self, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        ...

    def get_latest_snapshot(self, match_id: str) -> AnalyticsSnapshot | None:
        ...

    def list_recent_snapshots(self, match_id: str, limit: int) -> list[AnalyticsSnapshot]:
        ...
