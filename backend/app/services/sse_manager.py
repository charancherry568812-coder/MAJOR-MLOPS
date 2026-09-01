"""Server-Sent Events manager for real-time updates."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Set

logger = logging.getLogger(__name__)


class SSEManager:
    """Manages SSE connections and broadcasts events."""

    def __init__(self):
        self._queues: Set[asyncio.Queue] = set()

    async def connect(self) -> asyncio.Queue:
        """Register a new SSE client connection."""
        queue: asyncio.Queue = asyncio.Queue()
        self._queues.add(queue)
        logger.info(f"SSE client connected. Total: {len(self._queues)}")
        return queue

    def disconnect(self, queue: asyncio.Queue) -> None:
        """Remove an SSE client connection."""
        self._queues.discard(queue)
        logger.info(f"SSE client disconnected. Total: {len(self._queues)}")

    async def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast an event to all connected clients."""
        message = json.dumps({"type": event_type, "data": data})
        dead_queues = set()
        for queue in self._queues:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                dead_queues.add(queue)
        for q in dead_queues:
            self._queues.discard(q)

    def broadcast_sync(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast from sync code by scheduling on the event loop."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self.broadcast(event_type, data))
            else:
                loop.run_until_complete(self.broadcast(event_type, data))
        except RuntimeError:
            pass  # No event loop available (e.g., in background thread)

    @property
    def client_count(self) -> int:
        return len(self._queues)


# Singleton
sse_manager = SSEManager()
