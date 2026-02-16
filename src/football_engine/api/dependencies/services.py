"""Build application services from request-scoped session."""

from fastapi import Depends
from sqlalchemy.orm import Session

from football_engine.api.dependencies.session import get_db
from football_engine.application.services import (
    CreateMatchService,
    GetLatestAnalyticsService,
    GetMatchStateService,
    IngestEventService,
)
from football_engine.domain.services import AnalyticsEngine
from football_engine.infrastructure.repositories.analytics_repository_impl import (
    AnalyticsRepositoryImpl,
)
from football_engine.infrastructure.repositories.event_repository_impl import (
    EventRepositoryImpl,
)
from football_engine.infrastructure.repositories.match_repository_impl import (
    MatchRepositoryImpl,
)


def get_create_match_service(db: Session = Depends(get_db)) -> CreateMatchService:
    return CreateMatchService(match_repository=MatchRepositoryImpl(db))


def get_ingest_event_service(db: Session = Depends(get_db)) -> IngestEventService:
    match_repo = MatchRepositoryImpl(db)
    event_repo = EventRepositoryImpl(db)
    analytics_repo = AnalyticsRepositoryImpl(db)
    engine = AnalyticsEngine()
    return IngestEventService(
        match_repository=match_repo,
        event_repository=event_repo,
        analytics_repository=analytics_repo,
        analytics_engine=engine,
    )


def get_state_service(db: Session = Depends(get_db)) -> GetMatchStateService:
    return GetMatchStateService(match_repository=MatchRepositoryImpl(db))


def get_analytics_service(db: Session = Depends(get_db)) -> GetLatestAnalyticsService:
    return GetLatestAnalyticsService(analytics_repository=AnalyticsRepositoryImpl(db))
