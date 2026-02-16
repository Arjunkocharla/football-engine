"""Event ingest API route."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from football_engine.api.dependencies.session import get_db
from football_engine.api.dependencies.services import get_ingest_event_service
from football_engine.api.schemas.event_schemas import IngestEventRequest
from football_engine.application.dto import (
    analytics_snapshot_to_dto,
    ingest_result_dto,
    match_to_state_dto,
)
from football_engine.application.services import IngestEventService
from football_engine.domain.entities import Event
from football_engine.domain.enums import EventType, TeamSide
from football_engine.domain.value_objects import MatchClock

events_router = APIRouter(prefix="/events", tags=["events"])


@events_router.post("")
def ingest_event(
    body: IngestEventRequest,
    db: Session = Depends(get_db),
    service: IngestEventService = Depends(get_ingest_event_service),
) -> dict:
    clock = MatchClock(
        period=body.clock.period,
        minute=body.clock.minute,
        second=body.clock.second,
    )
    event = Event(
        event_id=body.event_id,
        match_id=body.match_id,
        provider_name=body.provider_name,
        provider_event_id=body.provider_event_id,
        clock=clock,
        team_side=TeamSide(body.team_side),
        event_type=EventType(body.event_type),
        payload=body.payload,
        ingested_at_utc=datetime.now(timezone.utc),
    )
    accepted, deduplicated, match, snapshot = service.ingest(event)
    if not accepted:
        raise HTTPException(status_code=404, detail="match not found")
    db.commit()
    state_dto = match_to_state_dto(match) if match else {}
    snapshot_dto = analytics_snapshot_to_dto(snapshot) if snapshot else None
    return ingest_result_dto(
        accepted=accepted,
        deduplicated=deduplicated,
        match_state=state_dto,
        analytics_latest=snapshot_dto,
    )
