"""Event repository port."""

from typing import Protocol

from football_engine.domain.entities import Event
from football_engine.domain.value_objects import MatchClock, RollingWindow


class EventRepository(Protocol):
    """Events with dedup and window queries."""

    def add_event_if_new(self, event: Event) -> bool:
        """Persist event if not duplicate. Return True if inserted, False if duplicate."""
        ...

    def list_events_in_window(
        self, match_id: str, end_clock: MatchClock, window: RollingWindow
    ) -> list[Event]:
        """Events in the window ending at end_clock (inclusive). Sorted by clock."""
        ...

    def list_recent_events(self, match_id: str, limit: int) -> list[Event]:
        """Most recent events for the match (newest first)."""
        ...
