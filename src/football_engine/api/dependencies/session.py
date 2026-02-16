"""Request-scoped database session dependency."""

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from football_engine.api.dependencies.container import AppContainer
from football_engine.infrastructure.db.session import get_session


def get_db(request: Request) -> Generator[Session, None, None]:
    """Yield a request-scoped DB session. Commit on success, rollback on error."""
    container: AppContainer = request.app.state.container
    yield from get_session(container.session_factory)
