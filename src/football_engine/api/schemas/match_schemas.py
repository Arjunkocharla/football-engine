"""Match API schemas."""

from pydantic import BaseModel, Field


class CreateMatchRequest(BaseModel):
    match_id: str = Field(..., min_length=1, max_length=64)
    home_team: str = Field(..., min_length=1, max_length=256)
    away_team: str = Field(..., min_length=1, max_length=256)
