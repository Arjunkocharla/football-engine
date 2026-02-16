"""Repository interfaces (ports). Implementations live in infrastructure."""

from football_engine.domain.repositories.analytics_repository import AnalyticsRepository
from football_engine.domain.repositories.event_repository import EventRepository
from football_engine.domain.repositories.match_repository import MatchRepository

__all__ = ["MatchRepository", "EventRepository", "AnalyticsRepository"]
