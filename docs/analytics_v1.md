# Analytics V1

**Status: Implemented.** Rolling pressure, momentum, field tilt, danger, and explainability are in place. Spatial/area analytics are out of scope for v1.

## Rolling Windows

Per team, compute over:

- 5-minute window
- 10-minute window

## Rolling Features

- shots
- shots_on_target
- corners
- fouls
- yellows
- reds
- xg_sum (if available)
- attacking_actions_count (shots + corners in v1)

## Derived Metrics

- Pressure Index
  - weighted attacking and threat events
  - may include game-state modifier
- Momentum
  - pressure share by team in the selected window
- Field Tilt Proxy
  - attacking action share by team
- Danger Next 5 Minutes
  - bounded score from pressure plus man-advantage factor
- Delta vs Previous Snapshot
  - analyst-friendly directional change tracking

## Explainability Requirement

Each snapshot must include human-readable "why" drivers, for example:

- `AWAY: 3 shots (2 on target) + 2 corners in last 10m`

## Deterministic Computation Rules

- input must be normalized domain events only
- ordering must be stable for equal clock timestamps
- formulas must be pure (no wall-clock dependence)
- rounding policy must be consistent for replay equality

## API Response Shape (GET /matches/{id}/analytics/latest and POST /events response.analytics_latest)

- `snapshot_id`, `match_id`, `clock` (period, minute, second), `model_version`, `created_at_utc`
- `features_by_window`: `{ "5m": { "HOME": {...}, "AWAY": {...} }, "10m": { ... } }` with keys shots, shots_on_target, corners, fouls, yellows, reds, xg_sum, attacking_actions_count
- `derived_metrics`: `{ "pressure_index": { "HOME", "AWAY" }, "momentum": { ... }, "field_tilt": { ... }, "danger_next_5m": { ... } }`
- `deltas`: same structure vs previous snapshot (or empty if first)
- `why`: list of human-readable strings (e.g. "HOME: 2 shots (1 on target) + 1 corners in last 5m")
