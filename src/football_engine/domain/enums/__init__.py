"""Domain enums. Use string values for ORM/serialization."""

from enum import StrEnum


class TeamSide(StrEnum):
    HOME = "HOME"
    AWAY = "AWAY"


class MatchStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    LIVE = "LIVE"
    HT = "HT"
    FT = "FT"
    PAUSED = "PAUSED"


class EventType(StrEnum):
    SHOT = "SHOT"
    SHOT_ON_TARGET = "SHOT_ON_TARGET"
    CORNER = "CORNER"
    FOUL = "FOUL"
    YELLOW = "YELLOW"
    RED = "RED"
    SUB = "SUB"
    GOAL = "GOAL"
