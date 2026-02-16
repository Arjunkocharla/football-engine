#!/usr/bin/env python3
"""Simple WebSocket client to test the streaming API."""

import asyncio
import json
import sys
from typing import Any

import websockets


async def listen_to_match(match_id: str, base_url: str = "ws://localhost:8000") -> None:
    """Connect to WebSocket stream and print all messages."""
    uri = f"{base_url}/ws/v2/matches/{match_id}/stream"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected! Waiting for updates...\n")

            # Receive welcome message
            welcome = await websocket.recv()
            print(f"Welcome: {json.loads(welcome)}\n")

            # Listen for updates
            while True:
                message = await websocket.recv()
                data = json.loads(message)
                print("=" * 60)
                print("UPDATE RECEIVED:")
                print(json.dumps(data, indent=2))
                print("=" * 60)
                print()

    except websockets.exceptions.ConnectionClosed:
        print("\nConnection closed.")
    except KeyboardInterrupt:
        print("\nDisconnecting...")
        await websocket.close()


if __name__ == "__main__":
    match_id = sys.argv[1] if len(sys.argv) > 1 else "sim-match-1"
    print(f"Listening to match: {match_id}")
    print("(Press Ctrl+C to exit)\n")
    asyncio.run(listen_to_match(match_id))
