"""Map AnalyticsSnapshot entity <-> AnalyticsSnapshotModel."""

from football_engine.domain.entities import AnalyticsSnapshot
from football_engine.domain.value_objects import MatchClock
from football_engine.infrastructure.db.models import AnalyticsSnapshotModel


def analytics_snapshot_to_orm(snapshot: AnalyticsSnapshot) -> AnalyticsSnapshotModel:
    return AnalyticsSnapshotModel(
        snapshot_id=snapshot.snapshot_id,
        match_id=snapshot.match_id,
        period=snapshot.clock.period,
        minute=snapshot.clock.minute,
        second=snapshot.clock.second,
        features_by_window=snapshot.features_by_window,
        derived_metrics=snapshot.derived_metrics,
        deltas=snapshot.deltas,
        why=snapshot.why,
        model_version=snapshot.model_version,
        created_at_utc=snapshot.created_at_utc,
    )


def analytics_snapshot_from_orm(m: AnalyticsSnapshotModel) -> AnalyticsSnapshot:
    return AnalyticsSnapshot(
        snapshot_id=m.snapshot_id,
        match_id=m.match_id,
        clock=MatchClock(period=m.period, minute=m.minute, second=m.second),
        features_by_window=m.features_by_window,
        derived_metrics=m.derived_metrics,
        deltas=m.deltas,
        why=m.why,
        model_version=m.model_version,
        created_at_utc=m.created_at_utc,
    )
