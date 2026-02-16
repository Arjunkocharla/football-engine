#!/usr/bin/env python3
"""Test full WebSocket flow: create match, connect WS, send events, verify updates."""

import asyncio
import json
import sys
import uuid
from datetime import datetime, timezone

import httpx
import websockets


async def check_server_running(base_url: str) -> bool:
    """Check if API server is running."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{base_url}/")
            return resp.status_code == 200
    except Exception:
        return False


async def test_full_flow() -> None:
    """Test complete WebSocket streaming flow."""
    base_url = "http://localhost:8000"
    ws_url = "ws://localhost:8000"
    match_id = f"test-ws-{uuid.uuid4().hex[:8]}"
    
    print(f"Testing WebSocket flow for match: {match_id}\n")
    
    # Check server is running
    print("0. Checking API server...")
    if not await check_server_running(base_url):
        print(f"   ✗ API server not running at {base_url}")
        print(f"   Please start it with: make run")
        return
    print(f"   ✓ Server is running\n")
    
    # Step 1: Create match
    print("1. Creating match...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{base_url}/api/v1/matches",
            json={
                "match_id": match_id,
                "home_team": "Team A",
                "away_team": "Team B",
            },
        )
        if resp.status_code not in (201, 409):
            print(f"   ✗ Failed to create match: {resp.status_code} {resp.text}")
            return
        print(f"   ✓ Match created/exists\n")
    
    # Step 2: Connect WebSocket
    print("2. Connecting WebSocket...")
    ws_uri = f"{ws_url}/ws/v2/matches/{match_id}/stream"
    
    try:
        async with websockets.connect(ws_uri) as websocket:
            # Receive welcome
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"   ✓ Connected: {welcome_data}\n")
            
            # Step 3: Send events and verify WebSocket receives them
            print("3. Sending events and waiting for WebSocket updates...\n")
            
            events_sent = []
            events_received = []
            
            async def send_events():
                """Send events in background - using FRESH event IDs to avoid deduplication."""
                async with httpx.AsyncClient(timeout=10.0) as client:
                    for i in range(3):
                        # Use UUID-based event IDs to ensure they're always new
                        event_id = f"test-{uuid.uuid4().hex}"
                        event_data = {
                            "event_id": event_id,
                            "match_id": match_id,
                            "provider_name": "test",
                            "provider_event_id": f"p{i}-{uuid.uuid4().hex[:8]}",
                            "clock": {"period": 1, "minute": i + 1, "second": i * 10},
                            "team_side": "HOME",
                            "event_type": "SHOT",
                            "payload": {},
                        }
                        
                        resp = await client.post(
                            f"{base_url}/api/v1/events",
                            json=event_data,
                        )
                        
                        if resp.status_code == 200:
                            result = resp.json()
                            deduplicated = result.get("deduplicated", False)
                            events_sent.append((event_id, deduplicated))
                            print(f"   → Sent event {event_id} (deduplicated={deduplicated})")
                        else:
                            print(f"   ✗ Failed to send event: {resp.status_code}")
                        
                        await asyncio.sleep(0.5)  # Small delay between events
            
            async def receive_updates():
                """Receive WebSocket updates."""
                try:
                    while True:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        if data.get("type") == "update":
                            event_id = data["event"]["event_id"]
                            events_received.append(event_id)
                            print(f"   ← Received update for event {event_id}")
                except asyncio.TimeoutError:
                    print(f"   ⏱ No more updates (timeout)")
            
            # Run both concurrently
            await asyncio.gather(
                send_events(),
                receive_updates(),
                return_exceptions=True,
            )
            
            print(f"\n4. Summary:")
            print(f"   Events sent: {len(events_sent)}")
            print(f"   Events received via WebSocket: {len(events_received)}")
            
            if len(events_received) > 0:
                print(f"   ✓ WebSocket streaming works!")
                print(f"   Received events: {events_received}")
            else:
                print(f"   ✗ No WebSocket updates received")
                print(f"   Check if events were deduplicated: {[e[1] for e in events_sent]}")
                
    except Exception as e:
        print(f"   ✗ WebSocket error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_full_flow())
