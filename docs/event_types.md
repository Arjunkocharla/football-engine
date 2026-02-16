# Event Types Reference

## Supported Event Types

The system currently handles **8 event types**:

### 1. **SHOT**
- **Description**: A shot attempt (may or may not be on target)
- **Match State Impact**: None (doesn't change score or cards)
- **Analytics Impact**: 
  - Counted in `shots` feature
  - Weight: 1.0 for pressure calculation
  - Contributes to attacking actions count
- **xG Support**: Optional (can include `xg` in payload)

### 2. **SHOT_ON_TARGET**
- **Description**: A shot that is on target (saved or goal)
- **Match State Impact**: None
- **Analytics Impact**:
  - Counted in `shots_on_target` feature
  - Weight: 1.5 for pressure calculation (higher than SHOT)
  - Contributes to attacking actions count
- **xG Support**: Optional

### 3. **CORNER**
- **Description**: Corner kick awarded
- **Match State Impact**: None
- **Analytics Impact**:
  - Counted in `corners` feature
  - Weight: 0.8 for pressure calculation
  - Contributes to attacking actions count
- **xG Support**: No

### 4. **FOUL**
- **Description**: Foul committed
- **Match State Impact**: None
- **Analytics Impact**:
  - Counted in `fouls` feature
  - Does NOT contribute to pressure (defensive event)
- **xG Support**: No

### 5. **YELLOW**
- **Description**: Yellow card shown
- **Match State Impact**: None (tracked but doesn't affect score)
- **Analytics Impact**:
  - Counted in `yellows` feature
  - Does NOT contribute to pressure
- **xG Support**: No

### 6. **RED**
- **Description**: Red card shown
- **Match State Impact**: 
  - Increments red card count for the team
  - Tracked in `home_red_cards` or `away_red_cards`
- **Analytics Impact**:
  - Counted in `reds` feature
  - Does NOT contribute to pressure
- **xG Support**: No

### 7. **SUB**
- **Description**: Substitution made
- **Match State Impact**: None
- **Analytics Impact**:
  - Currently tracked but not used in analytics calculations
  - Does NOT contribute to pressure
- **xG Support**: No

### 8. **GOAL**
- **Description**: Goal scored
- **Match State Impact**:
  - **Increments score** for the scoring team
  - Updates `score.home` or `score.away`
- **Analytics Impact**:
  - Weight: 3.0 for pressure calculation (highest weight)
  - Contributes to attacking actions count
  - Major impact on momentum and danger metrics
- **xG Support**: Optional (can include `xg` in payload)

## Event Processing Flow

1. **Ingestion**: Event received via `POST /api/v1/events`
2. **Deduplication**: Checked for duplicate `event_id`
3. **Match State Update**: 
   - GOAL → Updates score
   - RED → Updates red card count
   - Any event → Updates match clock and status (SCHEDULED → LIVE)
4. **Analytics Computation**:
   - Events aggregated into 5m and 10m rolling windows
   - Features extracted (shots, corners, fouls, etc.)
   - Derived metrics calculated (pressure, momentum, field tilt, danger)
5. **WebSocket Broadcast**: Update sent to all subscribers

## Event Categories

### Attacking Events (contribute to pressure)
- SHOT
- SHOT_ON_TARGET
- CORNER
- GOAL

### Defensive/Disciplinary Events (do NOT contribute to pressure)
- FOUL
- YELLOW
- RED
- SUB

## Pressure Calculation Weights

```python
PRESSURE_WEIGHTS = {
    "SHOT": 1.0,
    "SHOT_ON_TARGET": 1.5,
    "CORNER": 0.8,
    "GOAL": 3.0,
}
```

Plus: `xg_sum * 2.0` (if xG data available)

## API Schema Validation

Events must match this pattern:
```regex
^(SHOT|SHOT_ON_TARGET|CORNER|FOUL|YELLOW|RED|SUB|GOAL)$
```

## Simulator Support

All 8 event types are supported by the simulator with phase-based probabilities:
- **Early phase (0-15 min)**: More fouls and yellows
- **Mid phase (15-30 min)**: More shots and corners
- **Late phase (30-45 min)**: More shots on target and goals
