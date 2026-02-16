"""Get latest analytics snapshot for a match."""

from football_engine.domain.entities import AnalyticsSnapshot
from football_engine.domain.repositories import AnalyticsRepository


class GetLatestAnalyticsService:
    def __init__(self, analytics_repository: AnalyticsRepository) -> None:
        self._analytics_repo = analytics_repository

    def get(self, match_id: str) -> AnalyticsSnapshot | None:
        return self._analytics_repo.get_latest_snapshot(match_id)
