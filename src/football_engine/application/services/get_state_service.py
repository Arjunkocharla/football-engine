"""Get current match state."""

from football_engine.domain.entities import Match
from football_engine.domain.repositories import MatchRepository


class GetMatchStateService:
    def __init__(self, match_repository: MatchRepository) -> None:
        self._match_repo = match_repository

    def get(self, match_id: str) -> Match | None:
        return self._match_repo.get_match(match_id)
