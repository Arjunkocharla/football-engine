# API Contract

## HTTP v1

### POST `/matches`

Create a match.

Request includes:

- `match_id`
- `home_team`
- `away_team`

Response:

- created match state

### POST `/events`

Ingest one normalized event (idempotent).

Request includes:

- `event_id`
- `match_id`
- `clock` (`period`, `minute`, `second`)
- `team_side`
- `event_type`
- optional payload (`xg`, metadata)

Response includes:

- accepted/deduplicated indicators
- updated match state
- latest analytics snapshot

### GET `/matches/{id}/state`

Return current match state.

### GET `/matches/{id}/analytics/latest`

Return latest stored snapshot.

### GET `/matches/{id}/events/recent`

Return recent events for debugging.

## WebSocket v2 (implemented)

### WS `/ws/v2/matches/{match_id}/stream`

Real-time push stream for match updates. Connects to a specific match and receives JSON messages on each event ingest.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/v2/matches/{match_id}/stream');
```

**Message format:**
```json
{
  "type": "update",
  "event": {
    "event_id": "...",
    "clock": {"period": 1, "minute": 5, "second": 30},
    "team_side": "HOME",
    "event_type": "SHOT"
  },
  "match_state": {
    "match_id": "...",
    "home_team": "...",
    "away_team": "...",
    "status": "LIVE",
    "clock": {...},
    "score": {"home": 1, "away": 0},
    ...
  },
  "analytics_latest": {
    "snapshot_id": "...",
    "clock": {...},
    "features_by_window": {...},
    "derived_metrics": {
      "pressure_index": {"HOME": 0.7, "AWAY": 0.3},
      "momentum": {...},
      "field_tilt": {...},
      "danger_next_5m": {...}
    },
    "deltas": {...},
    "why": "...",
    ...
  }
}
```

**Initial message:**
```json
{"type": "connected", "match_id": "..."}
```

**Client ping:**
Send `"ping"` text message, receive `{"type": "pong"}`.

**Limits:**
- Max 20 connections per match
- Max 100 total connections
- Connection closed with code 1008 if limit reached

**Performance:**
- Minimal payloads (event summary only, not full nested objects)
- Non-blocking broadcast (doesn't delay HTTP response)
- Automatic cleanup on disconnect

## Error Contract

Error payload should contain:

- `error_code`
- `message`
- optional `details`

Mapped statuses:

- 404 not found
- 409 conflict
- 422 validation/domain errors
