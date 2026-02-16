"""Event API schemas."""

from typing import Any

from pydantic import BaseModel, Field


class ClockSchema(BaseModel):
    period: int = Field(..., ge=1)
    minute: int = Field(..., ge=0)
    second: int = Field(..., ge=0, le=59)


class IngestEventRequest(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=128)
    match_id: str = Field(..., min_length=1, max_length=64)
    clock: ClockSchema
    team_side: str = Field(..., pattern="^(HOME|AWAY)$")
    event_type: str = Field(
        ...,
        pattern="^(SHOT|SHOT_ON_TARGET|CORNER|FOUL|YELLOW|RED|SUB|GOAL)$",
    )
    payload: dict[str, Any] | None = None
    provider_name: str = Field(default="api", max_length=64)
    provider_event_id: str | None = Field(default=None, max_length=128)
