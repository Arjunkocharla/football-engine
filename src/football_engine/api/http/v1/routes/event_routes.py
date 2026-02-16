"""Event ingest API route."""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from football_engine.api.dependencies.session import get_db
from football_engine.api.dependencies.services import get_ingest_event_service
from football_engine.api.schemas.event_schemas import IngestEventRequest
from football_engine.api.ws.v2.payloads import event_to_minimal_dto
from football_engine.api.ws.v2.stream_manager import get_stream_manager
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
async def ingest_event(
    body: IngestEventRequest,
    background_tasks: BackgroundTasks,
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

    # Broadcast to WebSocket subscribers (non-blocking, runs after response)
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Event ingested: match={event.match_id}, deduplicated={deduplicated}, match_obj={match is not None}")
    
    # Broadcast if match exists AND (event is new OR there are subscribers who might need current state)
    if match:
        manager = get_stream_manager()
        has_subscribers = manager.get_subscriber_count(event.match_id) > 0
        
        if not deduplicated:
            logger.info(f"Scheduling broadcast for NEW event in match {event.match_id}")
            background_tasks.add_task(_broadcast_update, event, state_dto, snapshot_dto)
        elif has_subscribers:
            # Even if deduplicated, broadcast to subscribers who might have just connected
            logger.info(f"Scheduling broadcast for DEDUPLICATED event (subscribers present) in match {event.match_id}")
            background_tasks.add_task(_broadcast_update, event, state_dto, snapshot_dto)
        else:
            logger.debug(f"Skipping broadcast: deduplicated={deduplicated}, no subscribers")

    return ingest_result_dto(
        accepted=accepted,
        deduplicated=deduplicated,
        match_state=state_dto,
        analytics_latest=snapshot_dto,
    )


async def _broadcast_update(
    event: Event,
    match_state: dict[str, Any],
    analytics_latest: dict[str, Any] | None,
) -> None:
    """Non-blocking broadcast to WebSocket subscribers."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        manager = get_stream_manager()
        event_dto = event_to_minimal_dto(event)
        logger.info(f"Broadcasting update for match {event.match_id} to {manager.get_subscriber_count(event.match_id)} subscribers")
        await manager.broadcast(event.match_id, event_dto, match_state, analytics_latest)
        logger.debug(f"Broadcast completed for match {event.match_id}")
    except Exception as e:
        # Log but don't fail the HTTP request
        logger.warning(f"WebSocket broadcast failed for match {event.match_id}: {e}", exc_info=True)
