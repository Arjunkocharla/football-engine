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

## WebSocket v2 (design target)

### WS `/matches/{id}/stream`

Pushes:

- ingested event
- updated match state
- updated analytics snapshot

## Error Contract

Error payload should contain:

- `error_code`
- `message`
- optional `details`

Mapped statuses:

- 404 not found
- 409 conflict
- 422 validation/domain errors
