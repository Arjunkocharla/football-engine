"""Minimal payload builders for WebSocket. Keep small for Pi efficiency."""

from typing import Any

from football_engine.domain.entities import Event


def event_to_minimal_dto(event: Event) -> dict[str, Any]:
    """Minimal event summary for WebSocket (small payload)."""
    return {
        "event_id": event.event_id,
        "clock": {
            "period": event.clock.period,
            "minute": event.clock.minute,
            "second": event.clock.second,
        },
        "team_side": event.team_side.value,
        "event_type": event.event_type.value,
    }
