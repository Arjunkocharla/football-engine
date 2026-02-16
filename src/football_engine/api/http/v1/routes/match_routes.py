"""Match API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from football_engine.api.dependencies.session import get_db
from football_engine.api.dependencies.services import (
    get_analytics_service,
    get_create_match_service,
    get_state_service,
)
from football_engine.api.schemas.match_schemas import CreateMatchRequest
from football_engine.application.dto import analytics_snapshot_to_dto, match_to_state_dto
from football_engine.application.services import (
    CreateMatchService,
    GetLatestAnalyticsService,
    GetMatchStateService,
)
from football_engine.infrastructure.repositories.event_repository_impl import (
    EventRepositoryImpl,
)

matches_router = APIRouter(prefix="/matches", tags=["matches"])


@matches_router.post("", status_code=201)
def create_match(
    body: CreateMatchRequest,
    db: Session = Depends(get_db),
    service: CreateMatchService = Depends(get_create_match_service),
) -> dict:
    try:
        match = service.create(
            match_id=body.match_id,
            home_team=body.home_team,
            away_team=body.away_team,
        )
    except ValueError as e:
        if "already exists" in str(e).lower():
            raise HTTPException(status_code=409, detail="match_id already exists") from e
        raise
    db.commit()
    return match_to_state_dto(match)


@matches_router.get("/{match_id}/state")
def get_match_state(
    match_id: str,
    service: GetMatchStateService = Depends(get_state_service),
) -> dict:
    match = service.get(match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="match not found")
    return match_to_state_dto(match)


@matches_router.get("/{match_id}/analytics/latest")
def get_latest_analytics(
    match_id: str,
    service: GetLatestAnalyticsService = Depends(get_analytics_service),
) -> dict:
    snapshot = service.get(match_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="no analytics snapshot found")
    return analytics_snapshot_to_dto(snapshot)


@matches_router.get("/{match_id}/events/recent")
def get_recent_events(
    match_id: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    state_service: GetMatchStateService = Depends(get_state_service),
) -> list[dict]:
    if state_service.get(match_id) is None:
        raise HTTPException(status_code=404, detail="match not found")
    event_repo = EventRepositoryImpl(db)
    events = event_repo.list_recent_events(match_id, limit=limit)
    return [
        {
            "event_id": e.event_id,
            "match_id": e.match_id,
            "clock": {"period": e.clock.period, "minute": e.clock.minute, "second": e.clock.second},
            "team_side": e.team_side.value,
            "event_type": e.event_type.value,
            "payload": e.payload,
        }
        for e in events
    ]


