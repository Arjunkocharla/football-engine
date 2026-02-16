#!/usr/bin/env python3
"""Load test WebSocket streaming: multiple matches, continuous events, logging."""

import asyncio
import json
import logging
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path

import httpx
import websockets

# Setup logging to file
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"websocket_load_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class WebSocketListener:
    """Listens to a match stream and logs received events."""
    
    def __init__(self, match_id: str, ws_url: str):
        self.match_id = match_id
        self.ws_url = ws_url
        self.events_received = []
        self.running = False
        
    async def listen(self) -> None:
        """Connect and listen for updates."""
        uri = f"{self.ws_url}/ws/v2/matches/{self.match_id}/stream"
        try:
            async with websockets.connect(uri) as websocket:
                welcome = await websocket.recv()
                welcome_data = json.loads(welcome)
                logger.info(f"[{self.match_id}] WebSocket connected: {welcome_data}")
                self.running = True
                
                while self.running:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        if data.get("type") == "update":
                            event_id = data["event"]["event_id"]
                            event_type = data["event"]["event_type"]
                            clock = data["event"]["clock"]
                            self.events_received.append({
                                "event_id": event_id,
                                "event_type": event_type,
                                "clock": clock,
                                "received_at": time.time(),
                            })
                            logger.info(
                                f"[{self.match_id}] ← Event: {event_id} | "
                                f"Type: {event_type} | Clock: p{clock['period']} {clock['minute']}:{clock['second']:02d}"
                            )
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        logger.error(f"[{self.match_id}] WebSocket error: {e}")
                        break
        except Exception as e:
            logger.error(f"[{self.match_id}] Connection failed: {e}")
        finally:
            self.running = False
    
    def stop(self) -> None:
        """Stop listening."""
        self.running = False
    
    def get_stats(self) -> dict:
        """Get statistics."""
        return {
            "match_id": self.match_id,
            "events_received": len(self.events_received),
            "event_ids": [e["event_id"] for e in self.events_received],
        }


async def send_match_events_compressed(
    match_id: str,
    base_url: str,
    stop_event: asyncio.Event,
) -> dict:
    """Send events simulating a compressed 5-minute match (90 min compressed to 5 min)."""
    api_url = f"{base_url}/api/v1"
    events_sent = 0
    events_deduplicated = 0
    
    # Compressed timeline: 90 minutes compressed to 5 minutes (18x speed)
    # Real match events happen at specific times, we'll simulate key moments
    match_timeline = [
        # Period 1 events (compressed: 0-2.5 min represents 0-45 min)
        (1, 0, 15, "HOME", "SHOT"),      # Early chance
        (1, 0, 30, "AWAY", "FOUL"),      # Foul
        (1, 1, 0, "HOME", "CORNER"),     # Corner kick
        (1, 1, 20, "AWAY", "SHOT"),      # Away chance
        (1, 1, 45, "HOME", "YELLOW"),    # Yellow card
        (1, 2, 10, "HOME", "SHOT_ON_TARGET"),  # Shot on target
        (1, 2, 30, "AWAY", "FOUL"),      # Another foul
        (1, 2, 50, "HOME", "GOAL"),      # GOAL!
        (1, 3, 15, "AWAY", "CORNER"),    # Away corner
        (1, 3, 40, "HOME", "SHOT"),      # Home shot
        (1, 4, 0, "AWAY", "YELLOW"),     # Away yellow
        (1, 4, 30, "HOME", "SHOT_ON_TARGET"),  # Shot on target
        
        # Period 2 events (compressed: 2.5-5 min represents 45-90 min)
        (2, 0, 20, "AWAY", "SHOT"),      # Early second half chance
        (2, 0, 45, "HOME", "FOUL"),      # Foul
        (2, 1, 10, "AWAY", "CORNER"),    # Away corner
        (2, 1, 35, "HOME", "SHOT"),      # Home shot
        (2, 2, 0, "AWAY", "GOAL"),       # AWAY GOAL!
        (2, 2, 25, "HOME", "YELLOW"),    # Yellow card
        (2, 2, 50, "AWAY", "SHOT_ON_TARGET"),  # Shot on target
        (2, 3, 15, "HOME", "CORNER"),    # Home corner
        (2, 3, 40, "AWAY", "FOUL"),      # Foul
        (2, 4, 10, "HOME", "SHOT"),      # Late chance
        (2, 4, 30, "AWAY", "SHOT"),       # Away chance
        (2, 4, 55, "HOME", "SHOT_ON_TARGET"),  # Final chance
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        start_time = time.time()
        last_event_time = 0
        
        for period, minute, second, team_side, event_type in match_timeline:
            if stop_event.is_set():
                break
            
            # Calculate compressed time: 90 min match compressed to 5 min (18x speed)
            # Period 1: 0-45 min → 0-150 sec (2.5 min)
            # Period 2: 45-90 min → 150-300 sec (2.5 min)
            if period == 1:
                compressed_seconds = (minute * 60 + second) / 18  # Compress by 18x
            else:  # period == 2
                compressed_seconds = 150 + ((minute * 60 + second) / 18)  # Start at 150s
            
            # Wait until it's time for this event
            elapsed = time.time() - start_time
            wait_time = compressed_seconds - elapsed
            
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            elif wait_time < -1:  # More than 1 second late, skip
                logger.warning(f"[{match_id}] Skipping late event: p{period} {minute}:{second:02d}")
                continue
            
            event_id = f"load-{match_id}-p{period}-{minute:02d}-{second:02d}-{uuid.uuid4().hex[:6]}"
            event_data = {
                "event_id": event_id,
                "match_id": match_id,
                "provider_name": "load_test",
                "provider_event_id": f"p{period}-{minute:02d}-{second:02d}",
                "clock": {
                    "period": period,
                    "minute": minute,
                    "second": second,
                },
                "team_side": team_side,
                "event_type": event_type,
                "payload": {"xg": 0.3} if event_type in ("SHOT", "SHOT_ON_TARGET", "GOAL") else None,
            }
            
            try:
                resp = await client.post(f"{api_url}/events", json=event_data)
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get("deduplicated"):
                        events_deduplicated += 1
                        logger.debug(f"[{match_id}] Event deduplicated: {event_id}")
                    else:
                        events_sent += 1
                        logger.info(
                            f"[{match_id}] → Sent: p{period} {minute}:{second:02d} "
                            f"{team_side} {event_type}"
                        )
                else:
                    logger.warning(f"[{match_id}] Failed to send event: {resp.status_code}")
            except Exception as e:
                logger.error(f"[{match_id}] Error sending event: {e}")
    
    return {
        "events_sent": events_sent,
        "events_deduplicated": events_deduplicated,
        "total_attempted": len(match_timeline),
    }


async def run_load_test(
    base_url: str = "http://localhost:8000",
    ws_url: str = "ws://localhost:8000",
) -> None:
    """Run load test with a single match, compressed 5-minute timeline."""
    logger.info("=" * 80)
    logger.info("Starting WebSocket Load Test - Compressed 5-Minute Match")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("=" * 80)
    
    # Create single match
    match_id = f"load-test-{uuid.uuid4().hex[:8]}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{base_url}/api/v1/matches",
            json={
                "match_id": match_id,
                "home_team": "Home FC",
                "away_team": "Away FC",
            },
        )
        if resp.status_code in (201, 409):
            logger.info(f"Created match: {match_id}")
        else:
            logger.error(f"Failed to create match: {resp.status_code}")
            return
    
    # Start WebSocket listener
    listener = WebSocketListener(match_id, ws_url)
    listener_task = asyncio.create_task(listener.listen())
    
    logger.info("WebSocket listener started")
    await asyncio.sleep(2)  # Wait for connection to establish
    
    # Start sending events (compressed 5-minute match)
    stop_event = asyncio.Event()
    sender_task = asyncio.create_task(
        send_match_events_compressed(match_id, base_url, stop_event)
    )
    
    logger.info("Event sender started - simulating compressed 5-minute match")
    logger.info("Timeline: Period 1 (0-2.5 min) → Period 2 (2.5-5 min)")
    
    # Wait for events to complete (should take ~5 minutes compressed)
    try:
        await asyncio.wait_for(sender_task, timeout=400)  # Max 6.5 minutes
    except asyncio.TimeoutError:
        logger.warning("Event sending timed out")
    
    # Stop everything
    logger.info("Stopping load test...")
    stop_event.set()
    listener.stop()
    
    # Wait for tasks to complete
    await asyncio.sleep(2)
    await asyncio.gather(sender_task, listener_task, return_exceptions=True)
    
    # Print summary
    logger.info("=" * 80)
    logger.info("Load Test Summary")
    logger.info("=" * 80)
    
    try:
        stats = sender_task.result()
        events_sent = stats.get("events_sent", 0)
        events_deduplicated = stats.get("events_deduplicated", 0)
    except Exception as e:
        logger.error(f"Error getting sender stats: {e}")
        events_sent = 0
        events_deduplicated = 0
    
    listener_stats = listener.get_stats()
    events_received = listener_stats["events_received"]
    
    logger.info(f"\nMatch: {match_id}")
    logger.info(f"  Events sent: {events_sent}")
    logger.info(f"  Events deduplicated: {events_deduplicated}")
    logger.info(f"  Events received via WebSocket: {events_received}")
    
    if events_sent > 0:
        delivery_rate = (events_received / events_sent * 100)
        logger.info(f"  Delivery rate: {delivery_rate:.1f}%")
    else:
        logger.warning("  No events sent!")
    
    logger.info(f"\nWebSocket Events Received:")
    for event in listener_stats.get("event_ids", [])[:10]:  # Show first 10
        logger.info(f"  - {event}")
    if len(listener_stats.get("event_ids", [])) > 10:
        logger.info(f"  ... and {len(listener_stats['event_ids']) - 10} more")
    
    logger.info(f"\nLog file: {LOG_FILE}")
    logger.info("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test WebSocket streaming - compressed 5-min match")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--ws-url", default="ws://localhost:8000", help="WebSocket URL")
    
    args = parser.parse_args()
    
    asyncio.run(run_load_test(
        base_url=args.base_url,
        ws_url=args.ws_url,
    ))
