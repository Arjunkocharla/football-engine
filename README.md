# Football Real-Time Analytics Engine (Raspberry Pi)

Production-style football analytics service designed for deterministic event ingest, rolling analytics, and provider-agnostic extension.

## Purpose

This repository hosts Phase A + v1 foundations for:

- live (simulated) match event ingestion
- deterministic match state updates
- near real-time rolling analytics (5m and 10m windows)
- HTTP APIs (v1) and WebSocket stream design (v2)
- future provider adapters without core engine changes

## Architecture At A Glance

The codebase is organized in layered boundaries:

- `src/football_engine/domain`: entities, value objects, strategy contracts
- `src/football_engine/application`: use-case orchestration services
- `src/football_engine/infrastructure`: ORM, repository implementations, providers
- `src/football_engine/api`: FastAPI transport contracts and endpoints

Design docs live in `docs/` and are the source of truth before coding implementation details.

## Documentation Index

Start here when onboarding or when you need to reorient:

- `docs/INDEX.md`
- `docs/architecture.md`
- `docs/domain_model.md`
- `docs/api_contract.md`
- `docs/analytics_v1.md`
- `docs/development_plan.md`

## Current Status

- Project skeleton, design docs, and FastAPI entrypoint are in place.
- SQLAlchemy ORM (matches, events, analytics_snapshots) and Alembic migrations are set up.
- Domain layer: entities (Match, Event, AnalyticsSnapshot), value objects, enums, repository interfaces.
- Infrastructure: repository implementations, mappers, AnalyticsEngine v1 (rolling 5m/10m, pressure, momentum, tilt, danger, explainability).
- Application: CreateMatchService, IngestEventService, GetMatchStateService, GetLatestAnalyticsService.
- HTTP v1: POST /matches, POST /events, GET /matches/{id}/state, GET /matches/{id}/analytics/latest, GET /matches/{id}/events/recent.
- **SimulatorProvider**: deterministic, seeded event stream; script to run a full (or short) match against the API.

## Run (Bootstrap)

1. Create venv and install: `make install-dev`
2. Apply migrations: `make migrate`
3. Start API: `make run`
4. Verify: `GET /`, `GET /api/v1/health`, `GET /api/v1/ready`

## Makefile targets

- `make migrate` — apply migrations (alembic upgrade head)
- `make migrate-down` — roll back one revision
- `make simulate` — run simulator (create match + stream events to http://localhost:8000). Start the API first in another terminal.

## Example (after `make run`)

```bash
# Create a match
curl -X POST http://localhost:8000/api/v1/matches \
  -H "Content-Type: application/json" \
  -d '{"match_id": "m1", "home_team": "Team A", "away_team": "Team B"}'

# Ingest an event
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{"event_id": "e1", "match_id": "m1", "clock": {"period": 1, "minute": 5, "second": 0}, "team_side": "HOME", "event_type": "SHOT"}'

# Get state and analytics
curl http://localhost:8000/api/v1/matches/m1/state
curl http://localhost:8000/api/v1/matches/m1/analytics/latest
```

## Replay demo (simulator)

With the API running (`make run`), in another terminal:

```bash
# Quick demo: 5-minute halves, seed 42 (deterministic)
make simulate

# Or with options: full 45-min halves, seed 123, 0.5s between events
.venv/bin/python scripts/run_simulator.py --seed 123 --half-minutes 45 --delay 0.5

# Same seed → same event sequence every time
.venv/bin/python scripts/run_simulator.py --seed 42 --no-create   # reuse existing match
```

Then inspect state and analytics:

```bash
curl http://localhost:8000/api/v1/matches/sim-match-1/state
curl http://localhost:8000/api/v1/matches/sim-match-1/analytics/latest
```

## Next Milestones

1. WebSocket stream (v2) for live updates.
2. Optional: systemd unit for Pi; external provider adapters (API-Football, etc.).
