"""WebSocket endpoint for real-time community events."""

from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections per community."""

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


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time community updates."""
    community_id = websocket.query_params.get("community_id", "default")
    await manager.connect(websocket, community_id)

    # Send initial connection confirmation
    await websocket.send_json({
        "type": "connection_established",
        "community_id": community_id,
        "message": "Connected to community websocket",
    })

    try:
        while True:
            data = await websocket.receive_text()
            event = json.loads(data)

            response = {
                "type": event.get("type", "unknown"),
                "community_id": community_id,
                "data": event.get("data", {}),
                "status": "received",
            }
            await websocket.send_json(response)

    except WebSocketDisconnect:
        manager.disconnect(websocket, community_id)
        await manager.broadcast(
            {"type": "member_disconnected", "community_id": community_id},
            community_id,
        )
