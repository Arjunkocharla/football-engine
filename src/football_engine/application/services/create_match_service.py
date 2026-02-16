"""Create a new match."""

from football_engine.domain.entities import Match
from football_engine.domain.enums import MatchStatus
from football_engine.domain.repositories import MatchRepository
from football_engine.domain.value_objects import MatchClock, Score


class CreateMatchService:
    def __init__(self, match_repository: MatchRepository) -> None:
        self._match_repo = match_repository

    def create(self, match_id: str, home_team: str, away_team: str) -> Match:
        if self._match_repo.get_match(match_id) is not None:
            raise ValueError("match_id already exists")
        match = Match(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            status=MatchStatus.SCHEDULED,
            clock=MatchClock(period=1, minute=0, second=0),
            score=Score(home=0, away=0),
            home_red_cards=0,
            away_red_cards=0,
            version=1,
        )
        return self._match_repo.create_match(match)
