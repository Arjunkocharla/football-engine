"""SQLAlchemy implementation of AnalyticsRepository."""

from football_engine.domain.entities import AnalyticsSnapshot
from football_engine.infrastructure.db.models import AnalyticsSnapshotModel
from football_engine.infrastructure.mappers.analytics_mapper import (
    analytics_snapshot_from_orm,
    analytics_snapshot_to_orm,
)
from sqlalchemy.orm import Session


class AnalyticsRepositoryImpl:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_snapshot(self, snapshot: AnalyticsSnapshot) -> AnalyticsSnapshot:
        m = analytics_snapshot_to_orm(snapshot)
        self._session.add(m)
        self._session.flush()
        return analytics_snapshot_from_orm(m)

    def get_latest_snapshot(self, match_id: str) -> AnalyticsSnapshot | None:
        row = (
            self._session.query(AnalyticsSnapshotModel)
            .where(AnalyticsSnapshotModel.match_id == match_id)
            .order_by(AnalyticsSnapshotModel.id.desc())
            .first()
        )
        if row is None:
            return None
        return analytics_snapshot_from_orm(row)

    def list_recent_snapshots(self, match_id: str, limit: int) -> list[AnalyticsSnapshot]:
        rows = (
            self._session.query(AnalyticsSnapshotModel)
            .where(AnalyticsSnapshotModel.match_id == match_id)
            .order_by(AnalyticsSnapshotModel.id.desc())
            .limit(limit)
            .all()
        )
        return [analytics_snapshot_from_orm(r) for r in rows]
