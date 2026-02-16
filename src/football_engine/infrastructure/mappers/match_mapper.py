"""Map Match entity <-> MatchModel."""

from football_engine.domain.entities import Match
from football_engine.domain.enums import MatchStatus
from football_engine.domain.value_objects import MatchClock, Score
from football_engine.infrastructure.db.models import MatchModel


def match_to_orm(match: Match) -> MatchModel:
    return MatchModel(
        match_id=match.match_id,
        home_team=match.home_team,
        away_team=match.away_team,
        status=match.status.value,
        period=match.clock.period,
        minute=match.clock.minute,
        second=match.clock.second,
        home_score=match.score.home,
        away_score=match.score.away,
        home_red_cards=match.home_red_cards,
        away_red_cards=match.away_red_cards,
        version=match.version,
    )


def match_from_orm(m: MatchModel) -> Match:
    return Match(
        match_id=m.match_id,
        home_team=m.home_team,
        away_team=m.away_team,
        status=MatchStatus(m.status),
        clock=MatchClock(period=m.period, minute=m.minute, second=m.second),
        score=Score(home=m.home_score, away=m.away_score),
        home_red_cards=m.home_red_cards,
        away_red_cards=m.away_red_cards,
        version=m.version,
    )
