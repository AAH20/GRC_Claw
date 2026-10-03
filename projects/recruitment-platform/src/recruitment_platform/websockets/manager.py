"""WebSocket connection manager for real-time updates."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.user_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, room: str = "general") -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        if room not in self.active_connections:
            self.active_connections[room] = []
        self.active_connections[room].append(websocket)
        logger.info(f"WebSocket connected to room: {room}")

    def disconnect(self, websocket: WebSocket, room: str = "general") -> None:
        """Remove a WebSocket connection."""
        if room in self.active_connections:
            self.active_connections[room] = [
                conn for conn in self.active_connections[room] if conn != websocket
            ]
            if not self.active_connections[room]:
                del self.active_connections[room]
        logger.info(f"WebSocket disconnected from room: {room}")

    async def send_personal_message(self, message: dict[str, Any], websocket: WebSocket) -> None:
        """Send message to a specific connection."""
        await websocket.send_text(json.dumps(message))

    async def broadcast(self, message: dict[str, Any], room: str = "general") -> None:
        """Broadcast message to all connections in a room."""
        if room in self.active_connections:
            disconnected = []
            for connection in self.active_connections[room]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception:
                    disconnected.append(connection)

            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[room].remove(conn)

    async def broadcast_to_all(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        for room in self.active_connections:
            await self.broadcast(message, room)


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, room: str = "general") -> None:
    """WebSocket endpoint handler."""
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            if message.get("type") == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
            elif message.get("type") == "subscribe":
                new_room = message.get("room", "general")
                manager.disconnect(websocket, room)
                await manager.connect(websocket, new_room)
                room = new_room

    except WebSocketDisconnect:
        manager.disconnect(websocket, room)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, room)
