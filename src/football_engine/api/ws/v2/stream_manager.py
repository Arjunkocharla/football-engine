"""Lightweight WebSocket stream manager. Pi-optimized: minimal memory, async broadcast."""

import logging
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# Limits for Pi: max connections per match, max total
MAX_CONNECTIONS_PER_MATCH = 20
MAX_TOTAL_CONNECTIONS = 100


class StreamManager:
    """Manages WebSocket subscriptions per match. Thread-safe for async FastAPI."""

    def __init__(self) -> None:
        # match_id -> list of WebSocket connections
        self._subscribers: dict[str, list[WebSocket]] = defaultdict(list)
        self._total_connections = 0

    def subscribe(self, match_id: str, websocket: WebSocket) -> bool:
        """Add subscriber. Returns True if added, False if limit reached."""
        if self._total_connections >= MAX_TOTAL_CONNECTIONS:
            logger.warning(f"Max total connections ({MAX_TOTAL_CONNECTIONS}) reached")
            return False
        if len(self._subscribers[match_id]) >= MAX_CONNECTIONS_PER_MATCH:
            logger.warning(f"Max connections for match {match_id} reached")
            return False
        self._subscribers[match_id].append(websocket)
        self._total_connections += 1
        return True

    def unsubscribe(self, match_id: str, websocket: WebSocket) -> None:
        """Remove subscriber."""
        if match_id in self._subscribers:
            try:
                self._subscribers[match_id].remove(websocket)
                self._total_connections -= 1
                if not self._subscribers[match_id]:
                    del self._subscribers[match_id]
            except ValueError:
                pass

    async def broadcast(
        self,
        match_id: str,
        event: dict[str, Any],
        match_state: dict[str, Any],
        analytics_latest: dict[str, Any] | None,
    ) -> None:
        """Broadcast update to all subscribers for match_id. Non-blocking, handles disconnects."""
        if match_id not in self._subscribers:
            return

        payload = {
            "type": "update",
            "event": event,
            "match_state": match_state,
            "analytics_latest": analytics_latest,
        }

        disconnected: list[WebSocket] = []
        for ws in self._subscribers[match_id]:
            try:
                await ws.send_json(payload)
            except Exception as e:
                logger.debug(f"Failed to send to subscriber: {e}")
                disconnected.append(ws)

        for ws in disconnected:
            self.unsubscribe(match_id, ws)

    def get_subscriber_count(self, match_id: str) -> int:
        """Return number of active subscribers for a match."""
        return len(self._subscribers.get(match_id, []))


# Global singleton (FastAPI app will hold reference)
_stream_manager: StreamManager | None = None


def get_stream_manager() -> StreamManager:
    """Get or create global stream manager."""
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = StreamManager()
    return _stream_manager
