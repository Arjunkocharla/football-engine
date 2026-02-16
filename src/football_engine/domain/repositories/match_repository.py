"""Match repository port."""

from typing import Protocol

from football_engine.domain.entities import Match


class MatchRepository(Protocol):
    """Create, get, and persist matches."""

    def create_match(self, match: Match) -> Match:
        ...

    def get_match(self, match_id: str) -> Match | None:
        ...

    def save_match(self, match: Match) -> Match:
        ...
