#!/usr/bin/env python3
"""Run the match simulator: create a match and POST generated events to the API."""

import argparse
import sys
import time

import httpx

# Add project src to path when run as script
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "src"))

from football_engine.infrastructure.providers.simulator_provider import generate_events


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic match simulator against API")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--match-id", default="sim-match-1", help="Match ID")
    parser.add_argument("--home", default="Home FC", help="Home team name")
    parser.add_argument("--away", default="Away FC", help="Away team name")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for deterministic replay")
    parser.add_argument(
        "--half-minutes",
        type=int,
        default=5,
        help="Minutes per half (use 5 for quick demo, 45 for full match)",
    )
    parser.add_argument(
        "--event-prob",
        type=float,
        default=0.4,
        help="Probability of an event per minute (0-1)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.0,
        help="Seconds to wait between posting each event (0 = no delay)",
    )
    parser.add_argument(
        "--create",
        action="store_true",
        default=True,
        help="Create match before streaming (default: True)",
    )
    parser.add_argument(
        "--no-create",
        action="store_false",
        dest="create",
        help="Do not create match; assume it exists",
    )
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    api = f"{base}/api/v1"

    with httpx.Client(timeout=30.0) as client:
        if args.create:
            r = client.post(
                f"{api}/matches",
                json={
                    "match_id": args.match_id,
                    "home_team": args.home,
                    "away_team": args.away,
                },
            )
            if r.status_code == 201:
                print(f"Created match {args.match_id}")
            elif r.status_code == 409:
                print(f"Match {args.match_id} already exists, streaming events")
            else:
                print(f"Failed to create match: {r.status_code} {r.text}")
                return 1

        count = 0
        for payload in generate_events(
            args.match_id,
            seed=args.seed,
            half_minutes=args.half_minutes,
            event_probability_per_minute=args.event_prob,
        ):
            r = client.post(f"{api}/events", json=payload)
            if r.status_code != 200:
                print(f"Event failed: {r.status_code} {r.text}")
                return 1
            count += 1
            clock = payload["clock"]
            print(f"  p{clock['period']} {clock['minute']}:{clock['second']:02d} {payload['event_type']}")
            if args.delay > 0:
                time.sleep(args.delay)

        print(f"Done: {count} events posted for {args.match_id}")

        # Summary: match state + v1 analytics (pressure, momentum, tilt, danger, why)
        r_state = client.get(f"{api}/matches/{args.match_id}/state")
        r_analytics = client.get(f"{api}/matches/{args.match_id}/analytics/latest")
        if r_state.status_code == 200:
            s = r_state.json()
            clock = s["clock"]
            print(f"\n--- Match state ---")
            print(f"  {s['home_team']} {s['score']['home']}-{s['score']['away']} {s['away_team']}")
            print(f"  Status: {s['status']}  |  Clock: p{clock['period']} {clock['minute']}:{clock['second']:02d}")
        if r_analytics.status_code == 200:
            a = r_analytics.json()
            dm = a.get("derived_metrics", {})
            print(f"\n--- Analytics (v1) ---")
            print(f"  Pressure:  HOME {dm.get('pressure_index', {}).get('HOME', 0):.2f}  |  AWAY {dm.get('pressure_index', {}).get('AWAY', 0):.2f}")
            print(f"  Momentum:  HOME {dm.get('momentum', {}).get('HOME', 0):.2f}  |  AWAY {dm.get('momentum', {}).get('AWAY', 0):.2f}")
            print(f"  Field tilt: HOME {dm.get('field_tilt', {}).get('HOME', 0):.2f}  |  AWAY {dm.get('field_tilt', {}).get('AWAY', 0):.2f}")
            print(f"  Danger (next 5m): HOME {dm.get('danger_next_5m', {}).get('HOME', 0):.2f}  |  AWAY {dm.get('danger_next_5m', {}).get('AWAY', 0):.2f}")
            why = a.get("why", [])
            if why:
                print(f"  Why: {' | '.join(why)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
