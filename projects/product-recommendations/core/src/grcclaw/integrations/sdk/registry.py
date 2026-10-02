"""
Connector registry — manages registration and discovery of connectors.
"""

from __future__ import annotations

import importlib
import inspect
import logging
from threading import Lock
from typing import Any

from .base import BaseConnector
from .config import ConnectorConfig
from .types import ConnectorCapability, ConnectorMetadata

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """
    Thread-safe registry for connector classes and instances.

    Supports:
    - Registering connector classes by name
    - Creating connector instances from config
    - Discovering connectors by capability
    - Listing all registered connectors
    """

    _instance: ConnectorRegistry | None = None
    _lock: Lock = Lock()

    def __new__(cls) -> ConnectorRegistry:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self._connectors: dict[str, type[BaseConnector]] = {}
        self._instances: dict[str, BaseConnector] = {}
        self._configs: dict[str, ConnectorConfig] = {}
        self._initialized = True

    def register(
        self,
        name: str,
        connector_class: type[BaseConnector],
        config: ConnectorConfig | None = None,
    ) -> None:
        """Register a connector class."""
        if not issubclass(connector_class, BaseConnector):
            raise TypeError(f"{connector_class} must be a subclass of BaseConnector")

        with self._lock:
            self._connectors[name] = connector_class
            if config:
                self._configs[name] = config
            logger.info("Registered connector: %s", name)

    def unregister(self, name: str) -> None:
        """Unregister a connector."""
        with self._lock:
            if name in self._instances:
                self._instances[name].close()
                del self._instances[name]
            self._connectors.pop(name, None)
            self._configs.pop(name, None)
            logger.info("Unregistered connector: %s", name)

    def create(self, name: str, config: ConnectorConfig | None = None) -> BaseConnector:
        """Create a connector instance by name."""
        with self._lock:
            if name not in self._connectors:
                raise KeyError(f"Connector '{name}' is not registered")

            connector_class = self._connectors[name]
            effective_config = config or self._configs.get(name)
            if not effective_config:
                raise ValueError(f"No configuration provided for connector '{name}'")

            instance = connector_class(effective_config)
            self._instances[name] = instance
            return instance

    def get(self, name: str) -> BaseConnector | None:
        """Get an existing connector instance."""
        return self._instances.get(name)

    def list_connectors(self) -> list[str]:
        """List all registered connector names."""
        return list(self._connectors.keys())

    def list_instances(self) -> list[str]:
        """List all active connector instance names."""
        return list(self._instances.keys())

    def find_by_capability(self, capability: ConnectorCapability) -> list[str]:
        """Find connectors that support a given capability."""
        results = []
        for name, connector_class in self._connectors.items():
            try:
                # Check if the class defines the capability in its metadata
                temp_instance = connector_class.__new__(connector_class)
                if hasattr(temp_instance, "_define_metadata"):
                    # We can't call _define_metadata without init, so check class attributes
                    pass
                # Alternative: check if capability is in class annotations or attributes
                caps = getattr(connector_class, "CAPABILITIES", [])
                if capability in caps:
                    results.append(name)
            except Exception:
                continue
        return results

    def get_metadata(self, name: str) -> ConnectorMetadata | None:
        """Get metadata for a registered connector."""
        connector_class = self._connectors.get(name)
        if not connector_class:
            return None
        try:
            temp = connector_class.__new__(connector_class)
            if hasattr(temp, "_define_metadata"):
                return temp._define_metadata()
        except Exception:
            pass
        return None

    def discover(self, module_path: str) -> int:
        """
        Auto-discover connectors in a module.

        Scans a module for BaseConnector subclasses and registers them.
        Returns the number of connectors discovered.
        """
        count = 0
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            logger.warning("Failed to import module %s: %s", module_path, e)
            return 0

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, BaseConnector) and obj is not BaseConnector and not inspect.isabstract(obj):
                try:
                    self.register(name, obj)
                    count += 1
                except Exception as e:
                    logger.warning("Failed to register connector %s: %s", name, e)

        return count

    def health_check_all(self) -> dict[str, dict[str, Any]]:
        """Run health checks on all active connector instances."""
        results = {}
        for name, instance in self._instances.items():
            try:
                results[name] = instance.health_check()
            except Exception as e:
                results[name] = {
                    "name": name,
                    "status": "error",
                    "healthy": False,
                    "error": str(e),
                }
        return results

    def clear(self) -> None:
        """Clear all registered connectors and instances."""
        with self._lock:
            for instance in self._instances.values():
                try:
                    instance.close()
                except Exception:
                    pass
            self._connectors.clear()
            self._instances.clear()
            self._configs.clear()

    def __contains__(self, name: str) -> bool:
        return name in self._connectors

    def __len__(self) -> int:
        return len(self._connectors)
