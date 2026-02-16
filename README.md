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
- **WebSocket v2**: `/ws/v2/matches/{match_id}/stream` — real-time push updates on event ingest (Pi-optimized: minimal payloads, connection limits).
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

## WebSocket Streaming (v2)

### Testing the WebSocket Stream

**Step 1: Start the API server**
```bash
make run
# Server starts on http://localhost:8000
```

**Step 2: Create a match (if needed)**
```bash
curl -X POST http://localhost:8000/api/v1/matches \
  -H "Content-Type: application/json" \
  -d '{"match_id": "test-match-1", "home_team": "Team A", "away_team": "Team B"}'
```

**Step 3: Connect WebSocket client**

**Option A: Use the test script (recommended)**
```bash
# In a new terminal
make install  # Install websockets dependency if not already installed
.venv/bin/python scripts/test_websocket.py test-match-1
```

**Option B: Use wscat (if you have Node.js)**
```bash
npm install -g wscat
wscat -c ws://localhost:8000/ws/v2/matches/test-match-1/stream
```

**Option C: Use Python directly**
```bash
.venv/bin/python -c "
import asyncio
import websockets
import json

async def listen():
    async with websockets.connect('ws://localhost:8000/ws/v2/matches/test-match-1/stream') as ws:
        welcome = await ws.recv()
        print('Connected:', json.loads(welcome))
        while True:
            msg = await ws.recv()
            print(json.dumps(json.loads(msg), indent=2))

asyncio.run(listen())
"
```

**Step 4: Trigger events (in another terminal)**

**Option A: Use the simulator**
```bash
make simulate
# Or for a specific match:
.venv/bin/python scripts/run_simulator.py --match-id test-match-1 --no-create
```

**Option B: Send events manually**
```bash
curl -X POST http://localhost:8000/api/v1/events \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "e1",
    "match_id": "test-match-1",
    "clock": {"period": 1, "minute": 5, "second": 30},
    "team_side": "HOME",
    "event_type": "SHOT"
  }'
```

**What you'll see:**

1. **Welcome message** when you connect:
   ```json
   {"type": "connected", "match_id": "test-match-1"}
   ```

2. **Update messages** for each event ingested:
   ```json
   {
     "type": "update",
     "event": {
       "event_id": "e1",
       "clock": {"period": 1, "minute": 5, "second": 30},
       "team_side": "HOME",
       "event_type": "SHOT"
     },
     "match_state": { /* full match state */ },
     "analytics_latest": { /* latest analytics snapshot */ }
   }
   ```

**Performance considerations:**
- Minimal payloads (event summary, not full nested objects)
- Connection limits: 20 per match, 100 total
- Non-blocking broadcast (doesn't delay HTTP ingest response)
- Automatic cleanup on client disconnect

## Next Milestones

1. WebSocket stream (v2) for live updates.
2. Optional: systemd unit for Pi; external provider adapters (API-Football, etc.).
