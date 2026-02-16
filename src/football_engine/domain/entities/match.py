"""Match entity. Applies event side effects to state."""

from dataclasses import dataclass

from football_engine.domain.entities.event import Event
from football_engine.domain.enums import EventType, MatchStatus, TeamSide
from football_engine.domain.value_objects import MatchClock, Score


@dataclass
class Match:
    match_id: str
    home_team: str
    away_team: str
    status: MatchStatus
    clock: MatchClock
    score: Score
    home_red_cards: int
    away_red_cards: int
    version: int

    def apply_event(self, event: Event) -> "Match":
        """Return a new Match with event applied. Does not mutate."""
        new_score = self.score
        new_home_red = self.home_red_cards
        new_away_red = self.away_red_cards
        new_status = self.status

        if self.status == MatchStatus.SCHEDULED:
            new_status = MatchStatus.LIVE
        if event.event_type == EventType.GOAL:
            if event.team_side == TeamSide.HOME:
                new_score = Score(home=self.score.home + 1, away=self.score.away)
            else:
                new_score = Score(home=self.score.home, away=self.score.away + 1)
        elif event.event_type == EventType.RED:
            if event.team_side == TeamSide.HOME:
                new_home_red = self.home_red_cards + 1
            else:
                new_away_red = self.away_red_cards + 1

        return Match(
            match_id=self.match_id,
            home_team=self.home_team,
            away_team=self.away_team,
            status=new_status,
            clock=event.clock,
            score=new_score,
            home_red_cards=new_home_red,
            away_red_cards=new_away_red,
            version=self.version + 1,
        )
