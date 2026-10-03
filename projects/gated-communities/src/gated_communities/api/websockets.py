"""WebSocket endpoints for real-time messaging and presence tracking."""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections for messaging and presence."""

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.presence: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, room: str, user_id: str) -> None:
        """Accept a WebSocket connection and register it in a room."""
        await websocket.accept()
        async with self._lock:
            if room not in self.active_connections:
                self.active_connections[room] = []
            self.active_connections[room].append(websocket)
            self.presence[user_id] = {
                "status": "online",
                "rooms": self.presence.get(user_id, {}).get("rooms", []) + [room],
            }
        logger.info("User %s connected to room %s", user_id, room)

    async def disconnect(self, websocket: WebSocket, room: str, user_id: str) -> None:
        """Remove a WebSocket connection and update presence."""
        async with self._lock:
            if room in self.active_connections:
                try:
                    self.active_connections[room].remove(websocket)
                except ValueError:
                    pass
                if not self.active_connections[room]:
                    del self.active_connections[room]
            if user_id in self.presence:
                rooms = self.presence[user_id].get("rooms", [])
                if room in rooms:
                    rooms.remove(room)
                if not rooms:
                    self.presence[user_id]["status"] = "offline"
                else:
                    self.presence[user_id]["rooms"] = rooms
        logger.info("User %s disconnected from room %s", user_id, room)

    async def broadcast(self, message: dict[str, Any], room: str) -> None:
        """Broadcast a message to all connections in a room."""
        disconnected: list[WebSocket] = []
        async with self._lock:
            connections = list(self.active_connections.get(room, []))
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for connection in disconnected:
            async with self._lock:
                try:
                    self.active_connections[room].remove(connection)
                except (ValueError, KeyError):
                    pass

    async def broadcast_presence(self, user_id: str, status: str) -> None:
        """Broadcast a presence update to all connected clients."""
        message = {"type": "presence", "user_id": user_id, "status": status}
        async with self._lock:
            all_connections = [
                ws
                for conns in self.active_connections.values()
                for ws in conns
            ]
        disconnected: list[WebSocket] = []
        for connection in all_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for connection in disconnected:
            async with self._lock:
                for conns in self.active_connections.values():
                    try:
                        conns.remove(connection)
                    except ValueError:
                        pass

    def get_online_users(self) -> list[str]:
        """Return a list of currently online user IDs."""
        return [uid for uid, info in self.presence.items() if info["status"] == "online"]


manager = ConnectionManager()


@router.websocket("/ws/messages")
async def websocket_messages(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time messaging.

    Clients connect and send JSON messages of the form:
        {"room": "room_name", "user_id": "user123", "content": "Hello!"}

    Messages are broadcast to all clients in the same room.
    """
    await websocket.accept()
    user_id: str | None = None
    room: str | None = None
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = data.get("type", "message")

            if msg_type == "join":
                user_id = data.get("user_id")
                room = data.get("room")
                if not user_id or not room:
                    await websocket.send_json(
                        {"type": "error", "message": "user_id and room are required"}
                    )
                    continue
                await manager.connect(websocket, room, user_id)
                await manager.broadcast(
                    {"type": "system", "content": f"{user_id} joined {room}"}, room
                )
                await manager.broadcast_presence(user_id, "online")

            elif msg_type == "message":
                if not user_id or not room:
                    await websocket.send_json(
                        {"type": "error", "message": "Join a room first"}
                    )
                    continue
                await manager.broadcast(
                    {
                        "type": "message",
                        "user_id": user_id,
                        "room": room,
                        "content": data.get("content", ""),
                    },
                    room,
                )

            elif msg_type == "leave":
                if user_id and room:
                    await manager.disconnect(websocket, room, user_id)
                    await manager.broadcast(
                        {"type": "system", "content": f"{user_id} left {room}"}, room
                    )
                    await manager.broadcast_presence(user_id, "offline")
                await websocket.close()
                break

    except WebSocketDisconnect:
        if user_id and room:
            await manager.disconnect(websocket, room, user_id)
            await manager.broadcast(
                {"type": "system", "content": f"{user_id} left {room}"}, room
            )
            await manager.broadcast_presence(user_id, "offline")
    except Exception:
        logger.exception("Error in messages websocket")
        if user_id and room:
            await manager.disconnect(websocket, room, user_id)
            await manager.broadcast_presence(user_id, "offline")


@router.websocket("/ws/presence")
async def websocket_presence(websocket: WebSocket) -> None:
    """WebSocket endpoint for online presence tracking.

    Clients connect and receive real-time presence updates.
    Clients can send {"type": "ping"} to keep the connection alive.
    Clients can send {"user_id": "user123"} to register their presence.
    """
    await websocket.accept()
    user_id: str | None = None
    try:
        await websocket.send_json(
            {"type": "presence_init", "online_users": manager.get_online_users()}
        )
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = data.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "register":
                user_id = data.get("user_id")
                if not user_id:
                    await websocket.send_json(
                        {"type": "error", "message": "user_id is required"}
                    )
                    continue
                async with manager._lock:
                    manager.presence[user_id] = {
                        "status": "online",
                        "rooms": manager.presence.get(user_id, {}).get("rooms", []),
                    }
                await manager.broadcast_presence(user_id, "online")

            elif msg_type == "unregister":
                if user_id:
                    async with manager._lock:
                        if user_id in manager.presence:
                            manager.presence[user_id]["status"] = "offline"
                    await manager.broadcast_presence(user_id, "offline")
                    user_id = None

    except WebSocketDisconnect:
        if user_id:
            async with manager._lock:
                if user_id in manager.presence:
                    manager.presence[user_id]["status"] = "offline"
            await manager.broadcast_presence(user_id, "offline")
    except Exception:
        logger.exception("Error in presence websocket")
        if user_id:
            async with manager._lock:
                if user_id in manager.presence:
                    manager.presence[user_id]["status"] = "offline"
            await manager.broadcast_presence(user_id, "offline")
