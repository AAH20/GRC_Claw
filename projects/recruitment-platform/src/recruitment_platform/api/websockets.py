"""WebSocket endpoints for real-time notifications and live analytics."""

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# Connection managers for each endpoint
_notification_connections: set[WebSocket] = set()
_analytics_connections: set[WebSocket] = set()


async def _broadcast(connections: set[WebSocket], message: dict[str, Any]) -> None:
    """Send a JSON message to all connected clients, removing dead ones."""
    disconnected: list[WebSocket] = []
    for ws in connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        connections.discard(ws)


@router.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time notifications.

    Clients connect here to receive push notifications about
    recruitment events (new applications, interview scheduling, etc.).
    """
    await websocket.accept()
    _notification_connections.add(websocket)
    logger.info(
        "Notification client connected (total: %d)", len(_notification_connections)
    )
    try:
        while True:
            # Keep connection alive; client may send ping/ack messages
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received on notifications socket")
    except WebSocketDisconnect:
        logger.info("Notification client disconnected")
    except Exception:
        logger.exception("Error in notifications WebSocket")
    finally:
        _notification_connections.discard(websocket)


@router.websocket("/ws/analytics")
async def websocket_analytics(websocket: WebSocket) -> None:
    """WebSocket endpoint for live analytics stream.

    Clients connect here to receive periodic analytics updates
    (application counts, pipeline metrics, etc.).
    """
    await websocket.accept()
    _analytics_connections.add(websocket)
    logger.info(
        "Analytics client connected (total: %d)", len(_analytics_connections)
    )
    try:
        while True:
            # Keep connection alive; client may send ping/ack messages
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received on analytics socket")
    except WebSocketDisconnect:
        logger.info("Analytics client disconnected")
    except Exception:
        logger.exception("Error in analytics WebSocket")
    finally:
        _analytics_connections.discard(websocket)


async def broadcast_notification(message: dict[str, Any]) -> None:
    """Broadcast a notification to all connected notification clients."""
    await _broadcast(_notification_connections, message)


async def broadcast_analytics(message: dict[str, Any]) -> None:
    """Broadcast an analytics update to all connected analytics clients."""
    await _broadcast(_analytics_connections, message)
