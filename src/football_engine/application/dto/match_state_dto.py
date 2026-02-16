"""Match state as a plain dict for API response."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from football_engine.domain.entities import AnalyticsSnapshot, Match


def match_to_state_dto(match: Match) -> dict[str, Any]:
    """Build state dict from Match entity."""
    from football_engine.domain.entities import Match as MatchEntity

    if not isinstance(match, MatchEntity):
        raise TypeError("match must be Match")
    return {
        "match_id": match.match_id,
        "home_team": match.home_team,
        "away_team": match.away_team,
        "status": match.status.value,
        "clock": {
            "period": match.clock.period,
            "minute": match.clock.minute,
            "second": match.clock.second,
        },
        "score": {"home": match.score.home, "away": match.score.away},
        "home_red_cards": match.home_red_cards,
        "away_red_cards": match.away_red_cards,
        "version": match.version,
    }


def analytics_snapshot_to_dto(snapshot: AnalyticsSnapshot) -> dict[str, Any]:
    from football_engine.domain.entities import AnalyticsSnapshot as SnapshotEntity

    if not isinstance(snapshot, SnapshotEntity):
        raise TypeError("snapshot must be AnalyticsSnapshot")
    return {
        "snapshot_id": snapshot.snapshot_id,
        "match_id": snapshot.match_id,
        "clock": {
            "period": snapshot.clock.period,
            "minute": snapshot.clock.minute,
            "second": snapshot.clock.second,
        },
        "features_by_window": snapshot.features_by_window,
        "derived_metrics": snapshot.derived_metrics,
        "deltas": snapshot.deltas,
        "why": snapshot.why,
        "model_version": snapshot.model_version,
        "created_at_utc": snapshot.created_at_utc.isoformat(),
    }
