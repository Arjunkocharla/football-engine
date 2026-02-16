"""Map Event entity <-> EventModel."""

from football_engine.domain.entities import Event
from football_engine.domain.enums import EventType, TeamSide
from football_engine.domain.value_objects import MatchClock
from football_engine.infrastructure.db.models import EventModel


def event_to_orm(event: Event) -> EventModel:
    return EventModel(
        event_id=event.event_id,
        match_id=event.match_id,
        provider_name=event.provider_name,
        provider_event_id=event.provider_event_id,
        period=event.clock.period,
        minute=event.clock.minute,
        second=event.clock.second,
        team_side=event.team_side.value,
        event_type=event.event_type.value,
        payload=event.payload,
        ingested_at_utc=event.ingested_at_utc,
    )


def event_from_orm(m: EventModel) -> Event:
    return Event(
        event_id=m.event_id,
        match_id=m.match_id,
        provider_name=m.provider_name,
        provider_event_id=m.provider_event_id,
        clock=MatchClock(period=m.period, minute=m.minute, second=m.second),
        team_side=TeamSide(m.team_side),
        event_type=EventType(m.event_type),
        payload=m.payload,
        ingested_at_utc=m.ingested_at_utc,
    )
