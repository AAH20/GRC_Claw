# ADR 0005: Use WebSockets for Real-Time Updates

## Status
Accepted

## Context
The platform needs real-time updates for notifications, application status changes, and interview scheduling.

## Decision
Use WebSocket connections with room-based pub/sub for real-time communication.

## Consequences
- Low-latency updates improve user experience
- Room-based architecture enables targeted broadcasting
- Automatic reconnection improves reliability
