"""SQLAlchemy implementation of EventRepository."""

from football_engine.domain.entities import Event
from football_engine.domain.value_objects import MatchClock, RollingWindow
from football_engine.infrastructure.db.models import EventModel
from football_engine.infrastructure.mappers.event_mapper import event_from_orm, event_to_orm
from sqlalchemy.orm import Session


class EventRepositoryImpl:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add_event_if_new(self, event: Event) -> bool:
        existing = (
            self._session.query(EventModel)
            .where(EventModel.event_id == event.event_id)
            .first()
        )
        if existing is not None:
            return False
        m = event_to_orm(event)
        self._session.add(m)
        self._session.flush()
        return True

    def list_events_in_window(
        self, match_id: str, end_clock: MatchClock, window: RollingWindow
    ) -> list[Event]:
        start_minute = max(0, end_clock.minute - window.minutes)
        start_sec = start_minute * 60
        end_sec = end_clock.total_seconds_in_period()
        rows = (
            self._session.query(EventModel)
            .where(
                EventModel.match_id == match_id,
                EventModel.period == end_clock.period,
                EventModel.minute * 60 + EventModel.second >= start_sec,
                EventModel.minute * 60 + EventModel.second <= end_sec,
            )
            .order_by(EventModel.period, EventModel.minute, EventModel.second, EventModel.id)
            .all()
        )
        return [event_from_orm(r) for r in rows]

    def list_recent_events(self, match_id: str, limit: int) -> list[Event]:
        rows = (
            self._session.query(EventModel)
            .where(EventModel.match_id == match_id)
            .order_by(EventModel.id.desc())
            .limit(limit)
            .all()
        )
        return [event_from_orm(r) for r in reversed(rows)]
