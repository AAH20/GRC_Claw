"""
WebSocket endpoints for ugc-marketplace.

Provides real-time communication channels:
- /ws/notifications: User-specific notifications
- /ws/activity: Live activity stream
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections with proper lifecycle handling."""

    def __init__(self) -> None:
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "notifications": set(),
            "activity": set(),
        }
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, channel: str) -> None:
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections[channel].add(websocket)
        logger.info(
            "WebSocket connected to %s (total: %d)",
            channel,
            len(self.active_connections[channel]),
        )

    async def disconnect(self, websocket: WebSocket, channel: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            self.active_connections[channel].discard(websocket)
        logger.info(
            "WebSocket disconnected from %s (total: %d)",
            channel,
            len(self.active_connections[channel]),
        )

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: WebSocket
    ) -> None:
        """Send a message to a specific client."""
        try:
            await websocket.send_json(message)
        except Exception as exc:
            logger.warning("Failed to send personal message: %s", exc)

    async def broadcast(
        self, message: Dict[str, Any], channel: str, exclude: Optional[WebSocket] = None
    ) -> None:
        """Broadcast a message to all connections on a channel."""
        disconnected: list[WebSocket] = []
        async with self._lock:
            connections = list(self.active_connections[channel])

        for connection in connections:
            if connection is exclude:
                continue
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        if disconnected:
            async with self._lock:
                for conn in disconnected:
                    self.active_connections[channel].discard(conn)

    async def broadcast_to_all(self, message: Dict[str, Any]) -> None:
        """Broadcast a message to all channels."""
        for channel in self.active_connections:
            await self.broadcast(message, channel)

    def connection_count(self, channel: str) -> int:
        """Return the number of active connections on a channel."""
        return len(self.active_connections[channel])


manager = ConnectionManager()


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time user notifications.

    Clients receive notification events as JSON messages:
    {
        "type": "notification",
        "data": {
            "id": "...",
            "title": "...",
            "message": "...",
            "read": false,
            "created_at": "..."
        }
    }
    """
    await manager.connect(websocket, "notifications")
    try:
        while True:
            # Keep connection alive and handle client messages (e.g., acks)
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"},
                    websocket,
                )
                continue

            msg_type = payload.get("type", "")

            if msg_type == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
            elif msg_type == "ack":
                # Client acknowledges receipt of a notification
                notification_id = payload.get("notification_id")
                logger.debug("Notification %s acknowledged", notification_id)
            elif msg_type == "mark_read":
                # Client marks a notification as read
                notification_id = payload.get("notification_id")
                logger.debug("Notification %s marked as read", notification_id)
            else:
                await manager.send_personal_message(
                    {"type": "error", "message": f"Unknown message type: {msg_type}"},
                    websocket,
                )
    except WebSocketDisconnect:
        logger.info("Client disconnected from /ws/notifications")
    except Exception as exc:
        logger.error("Error in notifications WebSocket: %s", exc)
    finally:
        await manager.disconnect(websocket, "notifications")


@router.websocket("/ws/activity")
async def websocket_activity(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for live activity stream.

    Clients receive activity events as JSON messages:
    {
        "type": "activity",
        "data": {
            "id": "...",
            "actor": "...",
            "action": "...",
            "target": "...",
            "metadata": {},
            "created_at": "..."
        }
    }
    """
    await manager.connect(websocket, "activity")
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    {"type": "error", "message": "Invalid JSON"},
                    websocket,
                )
                continue

            msg_type = payload.get("type", "")

            if msg_type == "ping":
                await manager.send_personal_message({"type": "pong"}, websocket)
            elif msg_type == "subscribe":
                # Client can subscribe to specific activity filters
                filters = payload.get("filters", [])
                logger.debug("Client subscribed to activity filters: %s", filters)
                await manager.send_personal_message(
                    {"type": "subscribed", "filters": filters}, websocket
                )
            elif msg_type == "unsubscribe":
                filters = payload.get("filters", [])
                logger.debug("Client unsubscribed from activity filters: %s", filters)
                await manager.send_personal_message(
                    {"type": "unsubscribed", "filters": filters}, websocket
                )
            else:
                await manager.send_personal_message(
                    {"type": "error", "message": f"Unknown message type: {msg_type}"},
                    websocket,
                )
    except WebSocketDisconnect:
        logger.info("Client disconnected from /ws/activity")
    except Exception as exc:
        logger.error("Error in activity WebSocket: %s", exc)
    finally:
        await manager.disconnect(websocket, "activity")


# ---------------------------------------------------------------------------
# Helper functions for broadcasting from other parts of the application
# ---------------------------------------------------------------------------


async def broadcast_notification(notification: Dict[str, Any]) -> None:
    """Broadcast a notification to all connected notification clients."""
    await manager.broadcast(
        {"type": "notification", "data": notification}, "notifications"
    )


async def broadcast_activity(activity: Dict[str, Any]) -> None:
    """Broadcast an activity event to all connected activity clients."""
    await manager.broadcast(
        {"type": "activity", "data": activity}, "activity"
    )


async def send_notification_to_user(
    user_id: str, notification: Dict[str, Any]
) -> None:
    """
    Send a notification to a specific user.

    In a production system this would route via a user-connection registry.
    For now, broadcast to all notification clients (clients filter by user_id).
    """
    await manager.broadcast(
        {"type": "notification", "user_id": user_id, "data": notification},
        "notifications",
    )
