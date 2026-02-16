# Domain Model

## Entities

### Match

- identity: `match_id`
- fields: teams, status, clock, score, discipline state
- responsibility: apply event side effects to match state

### Event

- identity: canonical `event_id` (idempotency key)
- fields: match reference, clock, team side, type, payload
- responsibility: represent normalized domain event input

### AnalyticsSnapshot

- identity: `snapshot_id`
- fields: rolling features, derived metrics, deltas, explainability strings
- responsibility: immutable analytics result at a given clock point

## Value Objects

- `MatchClock(period, minute, second)`
- `Score(home, away)`
- `RollingWindow(minutes)` (v1: 5 and 10)

## Enums

- `TeamSide`: HOME, AWAY
- `MatchStatus`: SCHEDULED, LIVE, HT, FT, PAUSED
- `EventType`: SHOT, SHOT_ON_TARGET, CORNER, FOUL, YELLOW, RED, SUB, GOAL

## Strategy Contracts

- `PressureModel`
- `MomentumModel`
- `FieldTiltModel`
- `DangerModel`
- `ExplainabilityPolicy`

Each strategy accepts normalized feature inputs and returns deterministic outputs.

## Repository Contracts

- `MatchRepository`
  - create, get, save
- `EventRepository`
  - add with dedup semantics
  - list window events
  - list recent events
- `AnalyticsRepository`
  - save latest snapshot
  - get latest snapshot
  - optional snapshot history

## Domain Invariants

- Event must reference existing match.
- Event ordering must be deterministic.
- Score cannot be negative.
- Match clock values must remain valid.
- Duplicate events must not mutate state twice.
