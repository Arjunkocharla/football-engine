"""Ingest one event: dedup, persist, update match state, compute and store analytics."""

from __future__ import annotations

from typing import TYPE_CHECKING

from football_engine.domain.entities import Event, Match
from football_engine.domain.repositories import AnalyticsRepository, EventRepository, MatchRepository
from football_engine.domain.services import AnalyticsEngine
from football_engine.domain.value_objects import RollingWindow

if TYPE_CHECKING:
    from football_engine.domain.entities import AnalyticsSnapshot


class IngestEventService:
    def __init__(
        self,
        match_repository: MatchRepository,
        event_repository: EventRepository,
        analytics_repository: AnalyticsRepository,
        analytics_engine: AnalyticsEngine,
    ) -> None:
        self._match_repo = match_repository
        self._event_repo = event_repository
        self._analytics_repo = analytics_repository
        self._engine = analytics_engine

    def ingest(self, event: Event) -> tuple[bool, bool, Match | None, "AnalyticsSnapshot | None"]:
        """Returns (accepted, deduplicated, match_state, analytics_latest)."""
        match = self._match_repo.get_match(event.match_id)
        if match is None:
            return False, False, None, None

        inserted = self._event_repo.add_event_if_new(event)
        if not inserted:
            match = self._match_repo.get_match(event.match_id)
            snapshot = self._analytics_repo.get_latest_snapshot(event.match_id)
            return True, True, match, snapshot

        updated_match = match.apply_event(event)
        self._match_repo.save_match(updated_match)

        clock = event.clock
        window_5 = RollingWindow(minutes=5)
        window_10 = RollingWindow(minutes=10)
        events_5m = self._event_repo.list_events_in_window(
            event.match_id, clock, window_5
        )
        events_10m = self._event_repo.list_events_in_window(
            event.match_id, clock, window_10
        )
        previous = self._analytics_repo.get_latest_snapshot(event.match_id)
        snapshot = self._engine.compute(
            updated_match, events_5m, events_10m, clock, previous
        )
        self._analytics_repo.save_snapshot(snapshot)

        return True, False, updated_match, snapshot
