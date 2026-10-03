"""WebSocket endpoint for real-time notifications."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, community_id: str) -> None:
        await websocket.accept()
        if community_id not in self.active_connections:
            self.active_connections[community_id] = []
        self.active_connections[community_id].append(websocket)
        logger.info("websocket_connected", community_id=community_id)

    def disconnect(self, websocket: WebSocket, community_id: str) -> None:
        if community_id in self.active_connections:
            self.active_connections[community_id].remove(websocket)
            if not self.active_connections[community_id]:
                del self.active_connections[community_id]
        logger.info("websocket_disconnected", community_id=community_id)

    async def broadcast(self, message: dict[str, Any], community_id: str) -> None:
        if community_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[community_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            for conn in disconnected:
                self.disconnect(conn, community_id)


manager = ConnectionManager()


@router.websocket("/ws/{community_id}")
async def websocket_endpoint(websocket: WebSocket, community_id: str) -> None:
    """WebSocket endpoint for real-time community updates."""
    await manager.connect(websocket, community_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await manager.broadcast(
                {"type": "message", "community_id": community_id, "data": message},
                community_id,
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, community_id)
