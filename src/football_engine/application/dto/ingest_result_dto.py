"""Result of ingesting an event."""

from typing import Any


def ingest_result_dto(
    accepted: bool,
    deduplicated: bool,
    match_state: dict[str, Any],
    analytics_latest: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "accepted": accepted,
        "deduplicated": deduplicated,
        "match_state": match_state,
        "analytics_latest": analytics_latest,
    }
