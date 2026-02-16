"""Simulator determinism and shape."""

from football_engine.infrastructure.providers.simulator_provider import (
    generate_events_list,
    generate_events,
    PROVIDER_NAME,
)


def test_same_seed_same_events() -> None:
    a = generate_events_list("m1", seed=99, half_minutes=5, event_probability_per_minute=0.5)
    b = generate_events_list("m1", seed=99, half_minutes=5, event_probability_per_minute=0.5)
    assert [e["event_id"] for e in a] == [e["event_id"] for e in b]
    assert [e["event_type"] for e in a] == [e["event_type"] for e in b]


def test_different_seed_different_events() -> None:
    a = generate_events_list("m1", seed=1, half_minutes=5, event_probability_per_minute=0.5)
    b = generate_events_list("m1", seed=2, half_minutes=5, event_probability_per_minute=0.5)
    # May occasionally be same by chance, but with 0.5 prob over 10 minutes we expect difference
    assert [e["event_id"] for e in a] != [e["event_id"] for e in b]


def test_events_have_required_fields() -> None:
    events = generate_events_list("m2", seed=42, half_minutes=3, event_probability_per_minute=0.6)
    for e in events:
        assert e["match_id"] == "m2"
        assert e["event_id"].startswith("sim-")
        assert "clock" in e and "period" in e["clock"] and "minute" in e["clock"] and "second" in e["clock"]
        assert e["team_side"] in ("HOME", "AWAY")
        assert e["event_type"] in ("SHOT", "SHOT_ON_TARGET", "CORNER", "FOUL", "YELLOW", "RED", "SUB", "GOAL")
        assert e["provider_name"] == PROVIDER_NAME


def test_events_ordered_by_clock() -> None:
    events = generate_events_list("m3", seed=123, half_minutes=5, event_probability_per_minute=0.4)
    for i in range(1, len(events)):
        prev = events[i - 1]["clock"]
        curr = events[i]["clock"]
        assert (prev["period"], prev["minute"], prev["second"]) <= (curr["period"], curr["minute"], curr["second"])


def test_generate_events_iterator_matches_list() -> None:
    events_iter = list(generate_events("m4", seed=7, half_minutes=2, event_probability_per_minute=0.5))
    events_list = generate_events_list("m4", seed=7, half_minutes=2, event_probability_per_minute=0.5)
    assert [e["event_id"] for e in events_iter] == [e["event_id"] for e in events_list]
