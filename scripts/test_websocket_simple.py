#!/usr/bin/env python3
"""Simple test to verify WebSocket can receive messages directly."""

import asyncio
import json
import sys

import websockets


async def test_direct_broadcast(match_id: str, base_url: str = "ws://localhost:8000") -> None:
    """Test if we can manually send messages to WebSocket."""
    uri = f"{base_url}/ws/v2/matches/{match_id}/stream"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✓ Connected! Waiting for messages...\n")

            # Receive welcome message
            welcome = await websocket.recv()
            print(f"Welcome: {json.loads(welcome)}\n")

            # Wait a bit for any updates
            print("Waiting 5 seconds for any updates...")
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print(f"✓ Received: {json.loads(message)}")
            except asyncio.TimeoutError:
                print("✗ No message received within 5 seconds")
                print("\nThis means the broadcast is not working.")
                print("The WebSocket connection works, but no updates are being sent.")

    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    match_id = sys.argv[1] if len(sys.argv) > 1 else "sim-match-1"
    print(f"Testing WebSocket for match: {match_id}\n")
    asyncio.run(test_direct_broadcast(match_id))
