"""
JalRakshak NCR — Real-Time WebSocket Connection & Event Broadcaster (Phase 3)
Engineered for Team NeerNetra (SustainX 2026)
Provides multi-room real-time bi-directional streaming:
- "officials": Control room dispatch dashboard (receives alarms, map movements)
- "drivers": Fleet vehicle operators
- "citizen_{sos_id}": Stranded citizen live rescue tracking
"""

import json
from typing import Dict, List, Set, Any
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        # All active connections
        self._active_connections: Set[WebSocket] = set()
        # Room subscribers: room_name -> set of WebSockets
        self._rooms: Dict[str, Set[WebSocket]] = {
            "officials": set(),
            "drivers": set()
        }

    async def connect(self, websocket: WebSocket, room: str = "general"):
        """Accepts WebSocket connection and subscribes to target room."""
        await websocket.accept()
        self._active_connections.add(websocket)
        
        if room not in self._rooms:
            self._rooms[room] = set()
        self._rooms[room].add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Removes WebSocket from all rooms and active set."""
        self._active_connections.discard(websocket)
        for room_name in list(self._rooms.keys()):
            self._rooms[room_name].discard(websocket)
            if not self._rooms[room_name] and room_name not in ("officials", "drivers"):
                del self._rooms[room_name]

    async def broadcast_to_room(self, room: str, event: str, data: Any):
        """Broadcasts structured event to all subscribers in a specific room."""
        if room not in self._rooms:
            return

        message = json.dumps({"event": event, "data": data})
        stale = []
        for connection in list(self._rooms[room]):
            try:
                await connection.send_text(message)
            except Exception:
                stale.append(connection)

        for dead in stale:
            self.disconnect(dead)

    async def broadcast_to_officials(self, event: str, data: Any):
        """High-priority broadcast to municipal control room operators."""
        await self.broadcast_to_room("officials", event, data)

    async def broadcast_all(self, event: str, data: Any):
        """Broadcasts globally across all connected clients."""
        message = json.dumps({"event": event, "data": data})
        stale = []
        for connection in list(self._active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                stale.append(connection)

        for dead in stale:
            self.disconnect(dead)

    @property
    def total_connected(self) -> int:
        return len(self._active_connections)

ws_manager = WebSocketManager()
