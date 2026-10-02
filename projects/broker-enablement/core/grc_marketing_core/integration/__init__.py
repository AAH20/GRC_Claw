"""Integration module for GRC Marketing Core."""

from .connectors import BaseConnector, ConnectorRegistry
from .mcp import MCPClient

__all__ = ["BaseConnector", "ConnectorRegistry", "MCPClient"]
