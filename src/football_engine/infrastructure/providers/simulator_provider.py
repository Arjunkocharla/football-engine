"""Deterministic match event simulator. Seeded RNG for repeatable demos."""

import random
from typing import Any, Iterator

from football_engine.domain.enums import EventType, TeamSide

PROVIDER_NAME = "simulator"

# Event type weights by phase: (0-15 min), (15-30), (30-45). Higher = more likely.
# Order: SHOT, SHOT_ON_TARGET, CORNER, FOUL, YELLOW, RED, SUB, GOAL
_EARLY = (2, 1, 1, 4, 2, 0, 1, 0)
_MID = (3, 2, 2, 3, 1, 0, 0, 1)
_LATE = (4, 3, 3, 2, 1, 0, 0, 2)

_EVENT_TYPES = [
    EventType.SHOT,
    EventType.SHOT_ON_TARGET,
    EventType.CORNER,
    EventType.FOUL,
    EventType.YELLOW,
    EventType.RED,
    EventType.SUB,
    EventType.GOAL,
]


def _phase_weights(minute: int) -> tuple[int, ...]:
    if minute < 15:
        return _EARLY
    if minute < 30:
        return _MID
    return _LATE


def _random_xg(rng: random.Random) -> float:
    """Return 0.02–0.85 xG for shots (deterministic with seed)."""
    return round(rng.uniform(0.02, 0.85), 3)


def generate_events(
    match_id: str,
    seed: int,
    half_minutes: int = 45,
    event_probability_per_minute: float = 0.35,
) -> Iterator[dict[str, Any]]:
    """
    Yield event payloads in clock order. Each payload is ready for POST /api/v1/events.
    Deterministic: same seed -> same sequence.
    """
    rng = random.Random(seed)
    event_index = 0

    for period in (1, 2):
        for minute in range(half_minutes):
            if rng.random() > event_probability_per_minute:
                continue
            weights = _phase_weights(minute)
            event_type = rng.choices(_EVENT_TYPES, weights=weights, k=1)[0]
            side = rng.choice([TeamSide.HOME, TeamSide.AWAY])
            second = rng.randint(0, 59)
            event_index += 1
            event_id = f"sim-{match_id}-p{period}-{minute:02d}-{second:02d}-{event_index}"

            payload: dict[str, Any] | None = None
            if event_type in (EventType.SHOT, EventType.SHOT_ON_TARGET, EventType.GOAL):
                payload = {"xg": _random_xg(rng)}

            yield {
                "event_id": event_id,
                "match_id": match_id,
                "clock": {"period": period, "minute": minute, "second": second},
                "team_side": side.value,
                "event_type": event_type.value,
                "payload": payload,
                "provider_name": PROVIDER_NAME,
                "provider_event_id": event_id,
            }


def generate_events_list(
    match_id: str,
    seed: int,
    half_minutes: int = 45,
    event_probability_per_minute: float = 0.35,
) -> list[dict[str, Any]]:
    """Return all events as a list (for tests or replay)."""
    return list(generate_events(match_id, seed, half_minutes, event_probability_per_minute))
