"""SQLAlchemy ORM models. Schema only; domain mapping lives in mappers."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""

    pass


class MatchModel(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    home_team: Mapped[str] = mapped_column(String(256), nullable=False)
    away_team: Mapped[str] = mapped_column(String(256), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    minute: Mapped[int] = mapped_column(Integer, nullable=False)
    second: Mapped[int] = mapped_column(Integer, nullable=False)
    home_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    away_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    home_red_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    away_red_cards: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    events = relationship("EventModel", back_populates="match", order_by="EventModel.id")
    analytics_snapshots = relationship(
        "AnalyticsSnapshotModel", back_populates="match", order_by="AnalyticsSnapshotModel.id"
    )


class EventModel(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    match_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    minute: Mapped[int] = mapped_column(Integer, nullable=False)
    second: Mapped[int] = mapped_column(Integer, nullable=False)
    team_side: Mapped[str] = mapped_column(String(16), nullable=False)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ingested_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    match = relationship("MatchModel", back_populates="events")


class AnalyticsSnapshotModel(Base):
    __tablename__ = "analytics_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    match_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("matches.match_id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[int] = mapped_column(Integer, nullable=False)
    minute: Mapped[int] = mapped_column(Integer, nullable=False)
    second: Mapped[int] = mapped_column(Integer, nullable=False)
    features_by_window: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    derived_metrics: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    deltas: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    why: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    match = relationship("MatchModel", back_populates="analytics_snapshots")
