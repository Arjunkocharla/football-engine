"""WebSocket v2 streaming routes. Minimal payloads for Pi efficiency."""

import logging

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from football_engine.api.ws.v2.stream_manager import get_stream_manager

logger = logging.getLogger(__name__)

ws_v2_router = APIRouter(prefix="/ws/v2", tags=["websocket"])


@ws_v2_router.websocket("/matches/{match_id}/stream")
async def stream_match_updates(websocket: WebSocket, match_id: str) -> None:
    """
    WebSocket stream for live match updates.
    
    Pushes JSON messages on each event ingest:
    {
      "type": "update",
      "event": {...},
      "match_state": {...},
      "analytics_latest": {...}
    }
    """
    await websocket.accept()
    manager = get_stream_manager()

    if not manager.subscribe(match_id, websocket):
        await websocket.close(code=1008, reason="Connection limit reached")
        return

    try:
        # Send initial welcome (optional)
        await websocket.send_json({"type": "connected", "match_id": match_id})

        # Keep connection alive, wait for client disconnect
        while True:
            # Client can send ping or we just wait
            try:
                data = await websocket.receive_text()
                # Echo or handle client messages if needed
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error for {match_id}: {e}")
    finally:
        manager.unsubscribe(match_id, websocket)


@ws_v2_router.post("/matches/{match_id}/test-broadcast")
async def test_broadcast(match_id: str) -> dict:
    """Test endpoint to manually trigger a WebSocket broadcast."""
    manager = get_stream_manager()
    subscriber_count = manager.get_subscriber_count(match_id)
    
    if subscriber_count == 0:
        raise HTTPException(status_code=404, detail=f"No WebSocket subscribers for match {match_id}")
    
    test_payload = {
        "type": "update",
        "event": {
            "event_id": "test-event",
            "clock": {"period": 1, "minute": 0, "second": 0},
            "team_side": "HOME",
            "event_type": "SHOT",
        },
        "match_state": {
            "match_id": match_id,
            "status": "LIVE",
            "clock": {"period": 1, "minute": 0, "second": 0},
        },
        "analytics_latest": None,
    }
    
    await manager.broadcast(match_id, test_payload["event"], test_payload["match_state"], test_payload["analytics_latest"])
    
    return {
        "status": "broadcast_sent",
        "match_id": match_id,
        "subscriber_count": subscriber_count,
    }
