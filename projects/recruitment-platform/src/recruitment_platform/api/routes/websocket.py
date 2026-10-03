"""WebSocket API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from recruitment_platform.websockets.manager import manager

router = APIRouter()


@router.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str = "general") -> None:
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            import json
            message = json.loads(data)
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
        manager.disconnect(websocket, room)
