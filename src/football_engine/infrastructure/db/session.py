"""SQLAlchemy engine and session factory."""

from collections.abc import Generator
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine


def create_engine_and_factory(
    database_url: str,
) -> tuple["Engine", sessionmaker[Session]]:
    """Create engine and session factory. Use for app bootstrap."""
    # SQLite: enable foreign keys and WAL for concurrency
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        echo=False,
    )

    if database_url.startswith("sqlite"):
        from sqlalchemy import event

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragma(dbapi_connection: object, _: object) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
    return engine, factory


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    """Return a session factory for the given database URL."""
    _, factory = create_engine_and_factory(database_url)
    return factory


def get_session(
    session_factory: sessionmaker[Session],
) -> Generator[Session, None, None]:
    """Yield a request-scoped session. Use as FastAPI dependency."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
