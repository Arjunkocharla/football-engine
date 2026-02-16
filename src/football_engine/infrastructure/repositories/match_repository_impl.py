"""SQLAlchemy implementation of MatchRepository."""

from football_engine.domain.entities import Match
from football_engine.infrastructure.db.models import MatchModel
from football_engine.infrastructure.mappers.match_mapper import match_from_orm, match_to_orm
from sqlalchemy.orm import Session


class MatchRepositoryImpl:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_match(self, match: Match) -> Match:
        m = match_to_orm(match)
        self._session.add(m)
        self._session.flush()
        return match_from_orm(m)

    def get_match(self, match_id: str) -> Match | None:
        row = (
            self._session.query(MatchModel)
            .where(MatchModel.match_id == match_id)
            .first()
        )
        if row is None:
            return None
        return match_from_orm(row)

    def save_match(self, match: Match) -> Match:
        row = (
            self._session.query(MatchModel)
            .where(MatchModel.match_id == match.match_id)
            .first()
        )
        if row is None:
            m = match_to_orm(match)
            self._session.add(m)
            self._session.flush()
            return match_from_orm(m)
        row.home_team = match.home_team
        row.away_team = match.away_team
        row.status = match.status.value
        row.period = match.clock.period
        row.minute = match.clock.minute
        row.second = match.clock.second
        row.home_score = match.score.home
        row.away_score = match.score.away
        row.home_red_cards = match.home_red_cards
        row.away_red_cards = match.away_red_cards
        row.version = match.version
        self._session.flush()
        return match_from_orm(row)
