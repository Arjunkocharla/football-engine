"""Analytics engine v1: rolling features, derived metrics, explainability."""

import uuid
from datetime import datetime, timezone
from typing import Any

from football_engine.domain.entities import AnalyticsSnapshot, Event, Match
from football_engine.domain.enums import EventType
from football_engine.domain.value_objects import MatchClock


MODEL_VERSION = "v1"

# Weights for pressure (attacking events)
PRESSURE_WEIGHTS: dict[str, float] = {
    EventType.SHOT: 1.0,
    EventType.SHOT_ON_TARGET: 1.5,
    EventType.CORNER: 0.8,
    EventType.GOAL: 3.0,
}


def _aggregate_events_by_team(events: list[Event]) -> dict[str, dict[str, Any]]:
    """Build feature counts per team from events."""
    out: dict[str, dict[str, Any]] = {"HOME": _empty_features(), "AWAY": _empty_features()}
    for e in events:
        side = e.team_side.value
        f = out[side]
        if e.event_type == EventType.SHOT:
            f["shots"] += 1
        if e.event_type == EventType.SHOT_ON_TARGET:
            f["shots_on_target"] += 1
        if e.event_type == EventType.CORNER:
            f["corners"] += 1
        if e.event_type == EventType.FOUL:
            f["fouls"] += 1
        if e.event_type == EventType.YELLOW:
            f["yellows"] += 1
        if e.event_type == EventType.RED:
            f["reds"] += 1
        xg = e.xg_value()
        if xg is not None:
            f["xg_sum"] += xg
        if e.is_attacking_action():
            f["attacking_actions_count"] += 1
    return out


def _empty_features() -> dict[str, Any]:
    return {
        "shots": 0,
        "shots_on_target": 0,
        "corners": 0,
        "fouls": 0,
        "yellows": 0,
        "reds": 0,
        "xg_sum": 0.0,
        "attacking_actions_count": 0,
    }


def _pressure_score(features: dict[str, Any]) -> float:
    """Single pressure score from features (weighted attacking events)."""
    return (
        features["shots"] * PRESSURE_WEIGHTS.get(EventType.SHOT, 1.0)
        + features["shots_on_target"] * PRESSURE_WEIGHTS.get(EventType.SHOT_ON_TARGET, 1.5)
        + features["corners"] * PRESSURE_WEIGHTS.get(EventType.CORNER, 0.8)
        + (features.get("xg_sum") or 0) * 2.0
    )


def _build_derived(
    features_by_window: dict[str, Any], match: Match
) -> dict[str, Any]:
    """Derived metrics from 10m window and match state."""
    f10 = features_by_window.get("10m", {})
    home_f = f10.get("HOME", _empty_features())
    away_f = f10.get("AWAY", _empty_features())
    p_home = _pressure_score(home_f)
    p_away = _pressure_score(away_f)
    total = p_home + p_away
    if total <= 0:
        momentum_home = momentum_away = 0.5
        tilt_home = tilt_away = 0.5
    else:
        momentum_home = round(p_home / total, 4)
        momentum_away = round(p_away / total, 4)
        att_home = home_f["attacking_actions_count"]
        att_away = away_f["attacking_actions_count"]
        att_total = att_home + att_away
        if att_total <= 0:
            tilt_home = tilt_away = 0.5
        else:
            tilt_home = round(att_home / att_total, 4)
            tilt_away = round(att_away / att_total, 4)

    # Danger next 5m: bounded 0..1 from momentum and man-advantage
    man_adv = match.home_red_cards - match.away_red_cards
    danger_home = min(1.0, max(0.0, momentum_home + 0.1 * (-man_adv)))
    danger_away = min(1.0, max(0.0, momentum_away + 0.1 * man_adv))

    return {
        "pressure_index": {"HOME": round(p_home, 4), "AWAY": round(p_away, 4)},
        "momentum": {"HOME": momentum_home, "AWAY": momentum_away},
        "field_tilt": {"HOME": tilt_home, "AWAY": tilt_away},
        "danger_next_5m": {"HOME": round(danger_home, 4), "AWAY": round(danger_away, 4)},
    }


def _build_deltas(
    features_by_window: dict[str, Any],
    derived_metrics: dict[str, Any],
    previous: AnalyticsSnapshot | None,
) -> dict[str, Any]:
    """Delta vs previous snapshot (simple diff)."""
    if previous is None:
        return {"features_by_window": {}, "derived_metrics": {}}
    prev_f = previous.features_by_window
    prev_d = previous.derived_metrics
    delta_f: dict[str, Any] = {}
    for win, teams in features_by_window.items():
        delta_f[win] = {}
        for side, feats in teams.items():
            prev_feats = (prev_f.get(win) or {}).get(side) or _empty_features()
            delta_f[win][side] = {k: feats.get(k, 0) - prev_feats.get(k, 0) for k in feats}
    delta_d: dict[str, Any] = {}
    for metric, sides in derived_metrics.items():
        delta_d[metric] = {}
        for side, v in sides.items():
            prev_v = (prev_d.get(metric) or {}).get(side, 0)
            delta_d[metric][side] = round(v - prev_v, 4)
    return {"features_by_window": delta_f, "derived_metrics": delta_d}


def _build_why(features_by_window: dict[str, Any]) -> list[str]:
    """Human-readable drivers per window."""
    lines: list[str] = []
    for window in ("5m", "10m"):
        wins = features_by_window.get(window, {})
        for side in ("HOME", "AWAY"):
            f = wins.get(side, _empty_features())
            shot = f.get("shots", 0)
            sot = f.get("shots_on_target", 0)
            cor = f.get("corners", 0)
            if shot or cor:
                lines.append(f"{side}: {shot} shots ({sot} on target) + {cor} corners in last {window}")
    return lines if lines else ["No attacking actions in window"]


class AnalyticsEngine:
    """Compute analytics snapshot from match state and window events."""

    def compute(
        self,
        match: Match,
        events_5m: list[Event],
        events_10m: list[Event],
        clock: MatchClock,
        previous: AnalyticsSnapshot | None,
    ) -> AnalyticsSnapshot:
        features_5m = _aggregate_events_by_team(events_5m)
        features_10m = _aggregate_events_by_team(events_10m)
        features_by_window = {"5m": features_5m, "10m": features_10m}
        derived_metrics = _build_derived(features_by_window, match)
        deltas = _build_deltas(features_by_window, derived_metrics, previous)
        why = _build_why(features_by_window)
        return AnalyticsSnapshot(
            snapshot_id=str(uuid.uuid4()),
            match_id=match.match_id,
            clock=clock,
            features_by_window=features_by_window,
            derived_metrics=derived_metrics,
            deltas=deltas,
            why=why,
            model_version=MODEL_VERSION,
            created_at_utc=datetime.now(timezone.utc),
        )
