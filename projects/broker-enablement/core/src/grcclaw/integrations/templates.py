"""
Integration Templates — pre-built connector templates for common integration patterns.

Provides:
- IntegrationTemplate: base class for creating integration templates
- RESTAPIConnector: pre-configured REST API connector
- DatabaseConnector: database integration connector
- WebhookConnector: webhook-based integration connector
- FileTransferConnector: file transfer (SFTP/S3) connector
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from abc import abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from .sdk.auth import AuthStrategy
from .sdk.base import BaseConnector
from .sdk.config import ConnectorConfig
from .sdk.exceptions import (
    ConnectionError,
    ConnectorError,
    WebhookError,
)
from .sdk.types import (
    ConnectorCapability,
    ConnectorMetadata,
    ConnectorStatus,
    ResponseContext,
)

logger = logging.getLogger(__name__)


class IntegrationTemplate:
    """
    Base class for integration templates.

    Templates provide pre-configured connectors with common patterns
    for specific integration types (REST, database, webhook, file transfer).
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._config: ConnectorConfig | None = None
        self._auth: AuthStrategy | None = None

    @abstractmethod
    def create_connector(self) -> BaseConnector:
        """Create and return a configured connector instance."""
        ...

    @abstractmethod
    def get_default_config(self) -> ConnectorConfig:
        """Return the default configuration for this template."""
        ...

    def get_auth_strategy(self) -> AuthStrategy | None:
        """Get the authentication strategy for this template."""
        return self._auth

    def validate_config(self, config: ConnectorConfig) -> list[str]:
        """Validate a configuration. Returns list of validation errors."""
        errors: list[str] = []
        if not config.name:
            errors.append("Connector name is required")
        if not config.base_url:
            errors.append("Base URL is required")
        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize template to dict."""
        return {
            "name": self.name,
            "description": self.description,
            "config": self._config.__dict__ if self._config else None,
        }


class RESTAPIConnector(BaseConnector):
    """
    Pre-configured REST API connector.

    Features:
    - Automatic pagination handling
    - Rate limit awareness
    - Standard HTTP method helpers
    - JSON request/response handling
    - Automatic retry with backoff
    - Request/response logging
    """

    CAPABILITIES = [
        ConnectorCapability.READ,
        ConnectorCapability.WRITE,
        ConnectorCapability.DELETE,
        ConnectorCapability.PAGINATION,
        ConnectorCapability.BATCH,
        ConnectorCapability.FULL_SYNC,
        ConnectorCapability.INCREMENTAL_SYNC,
    ]

    def __init__(self, config: ConnectorConfig, auth: AuthStrategy | None = None):
        super().__init__(config, auth)
        self._default_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "GRCClaw-RESTConnector/1.0",
        }

    def _define_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            name=self.config.name,
            version="1.0.0",
            vendor="GRC_Claw",
            description="REST API connector for HTTP-based integrations",
            capabilities=self.CAPABILITIES,
            supported_auth=["api_key", "bearer", "oauth2", "basic", "hmac"],
            rate_limit_per_minute=self.config.rate_limit.requests_per_minute,
            category="api",
            tags=["rest", "http", "api"],
        )

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ResponseContext:
        """Execute a GET request."""
        merged_headers = {**self._default_headers, **(headers or {})}
        return self.execute("GET", path, params=params, headers=merged_headers)

    def post(
        self,
        path: str,
        body: Any = None,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ResponseContext:
        """Execute a POST request."""
        merged_headers = {**self._default_headers, **(headers or {})}
        return self.execute("POST", path, params=params, body=body, headers=merged_headers)

    def put(
        self,
        path: str,
        body: Any = None,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ResponseContext:
        """Execute a PUT request."""
        merged_headers = {**self._default_headers, **(headers or {})}
        return self.execute("PUT", path, params=params, body=body, headers=merged_headers)

    def patch(
        self,
        path: str,
        body: Any = None,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ResponseContext:
        """Execute a PATCH request."""
        merged_headers = {**self._default_headers, **(headers or {})}
        return self.execute("PATCH", path, params=params, body=body, headers=merged_headers)

    def delete(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ResponseContext:
        """Execute a DELETE request."""
        merged_headers = {**self._default_headers, **(headers or {})}
        return self.execute("DELETE", path, params=params, headers=merged_headers)

    def get_json(self, path: str, **kwargs) -> Any:
        """Execute GET and return parsed JSON body."""
        response = self.get(path, **kwargs)
        if not response.is_success:
            raise ConnectorError(
                f"GET {path} failed with status {response.status_code}",
                connector=self.config.name,
            )
        return response.body

    def post_json(self, path: str, body: Any, **kwargs) -> Any:
        """Execute POST and return parsed JSON body."""
        response = self.post(path, body, **kwargs)
        if not response.is_success:
            raise ConnectorError(
                f"POST {path} failed with status {response.status_code}",
                connector=self.config.name,
            )
        return response.body

    def put_json(self, path: str, body: Any, **kwargs) -> Any:
        """Execute PUT and return parsed JSON body."""
        response = self.put(path, body, **kwargs)
        if not response.is_success:
            raise ConnectorError(
                f"PUT {path} failed with status {response.status_code}",
                connector=self.config.name,
            )
        return response.body

    def patch_json(self, path: str, body: Any, **kwargs) -> Any:
        """Execute PATCH and return parsed JSON body."""
        response = self.patch(path, body, **kwargs)
        if not response.is_success:
            raise ConnectorError(
                f"PATCH {path} failed with status {response.status_code}",
                connector=self.config.name,
            )
        return response.body

    def delete_json(self, path: str, **kwargs) -> Any:
        """Execute DELETE and return parsed JSON body."""
        response = self.delete(path, **kwargs)
        if not response.is_success:
            raise ConnectorError(
                f"DELETE {path} failed with status {response.status_code}",
                connector=self.config.name,
            )
        return response.body

    def paginate_all(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        page_size: int = 100,
        max_pages: int = 1000,
    ) -> list[Any]:
        """
        Fetch all pages and return combined results.

        Returns a list of all items across all pages.
        """
        all_items: list[Any] = []
        cursor: str | None = None
        page = 0

        while page < max_pages:
            page_params = {**(params or {}), "limit": page_size}
            if cursor:
                page_params["cursor"] = cursor

            response = self.get(path, params=page_params)
            if not response.is_success:
                raise ConnectorError(
                    f"Pagination failed on page {page}: status {response.status_code}",
                    connector=self.config.name,
                )

            body = response.body
            if isinstance(body, dict):
                # Try common result container keys
                items = body.get("data", body.get("items", body.get("results", [])))
                if isinstance(items, list):
                    all_items.extend(items)
                else:
                    all_items.append(body)

                if not response.pagination_has_more or not response.pagination_cursor:
                    break
                cursor = response.pagination_cursor
            elif isinstance(body, list):
                all_items.extend(body)
                break
            else:
                break

            page += 1

        return all_items

    def batch_request(
        self,
        requests: list[dict[str, Any]],
        *,
        max_concurrency: int = 5,
    ) -> list[ResponseContext]:
        """
        Execute multiple requests in batch.

        Args:
            requests: List of request dicts with 'method', 'path', optional 'body', 'params'.
            max_concurrency: Maximum concurrent requests.

        Returns:
            List of ResponseContext objects.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results: list[ResponseContext] = [None] * len(requests)  # type: ignore

        def execute_single(idx_req: tuple[int, dict[str, Any]]) -> tuple[int, ResponseContext]:
            idx, req = idx_req
            method = req.get("method", "GET").upper()
            path = req["path"]
            body = req.get("body")
            params = req.get("params")
            headers = req.get("headers")
            response = self.execute(method, path, params=params, body=body, headers=headers)
            return idx, response

        with ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            futures = {
                executor.submit(execute_single, (i, req)): i
                for i, req in enumerate(requests)
            }
            for future in as_completed(futures):
                idx, response = future.result()
                results[idx] = response

        return results

    def health_check(self) -> dict[str, Any]:
        """Enhanced health check for REST API."""
        base = super().health_check()
        base["connector_type"] = "rest_api"
        base["capabilities"] = [c.value for c in self.CAPABILITIES]
        return base


class DatabaseConnector(BaseConnector):
    """
    Database integration connector.

    Supports:
    - SQL query execution
    - Bulk insert/update
    - Transaction management
    - Connection pooling
    - Schema introspection
    """

    CAPABILITIES = [
        ConnectorCapability.READ,
        ConnectorCapability.WRITE,
        ConnectorCapability.DELETE,
        ConnectorCapability.BATCH,
        ConnectorCapability.FULL_SYNC,
        ConnectorCapability.INCREMENTAL_SYNC,
    ]

    def __init__(self, config: ConnectorConfig, auth: AuthStrategy | None = None):
        super().__init__(config, auth)
        self._connection_string = config.custom.get("connection_string", "")
        self._db_type = config.custom.get("db_type", "postgresql")
        self._pool_size = config.custom.get("pool_size", 5)
        self._pool: list[Any] = []
        self._in_transaction: bool = False
        self._transaction_connection: Any = None

    def _define_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            name=self.config.name,
            version="1.0.0",
            vendor="GRC_Claw",
            description="Database connector for SQL-based integrations",
            capabilities=self.CAPABILITIES,
            supported_auth=["basic", "api_key"],
            category="database",
            tags=["database", "sql", "db"],
        )

    def connect(self) -> Any:
        """Establish a database connection."""
        try:
            if self._db_type == "postgresql":
                import psycopg2
                conn = psycopg2.connect(self._connection_string)
                self._status = ConnectorStatus.CONNECTED
                return conn
            elif self._db_type == "mysql":
                import pymysql
                conn = pymysql.connect(**self._parse_connection_string())
                self._status = ConnectorStatus.CONNECTED
                return conn
            elif self._db_type == "sqlite":
                import sqlite3
                db_path = self._connection_string.replace("sqlite:///", "")
                conn = sqlite3.connect(db_path)
                self._status = ConnectorStatus.CONNECTED
                return conn
            else:
                raise ConnectorError(
                    f"Unsupported database type: {self._db_type}",
                    connector=self.config.name,
                )
        except ImportError as e:
            raise ConnectorError(
                f"Database driver not installed for {self._db_type}: {e}",
                connector=self.config.name,
            )
        except Exception as e:
            self._status = ConnectorStatus.ERROR
            raise ConnectionError(
                f"Database connection failed: {e}",
                connector=self.config.name,
            ) from e

    def _parse_connection_string(self) -> dict[str, Any]:
        """Parse a connection string into kwargs."""
        # Simple parser for key=value pairs
        parts = self._connection_string.split()
        result = {}
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                result[key] = value
        return result

    def query(self, sql: str, params: tuple | None = None) -> list[dict[str, Any]]:
        """
        Execute a SELECT query and return results.

        Args:
            sql: SQL query string.
            params: Query parameters.

        Returns:
            List of row dicts.
        """
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())

            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            return []
        except Exception as e:
            self._error_count += 1
            raise ConnectorError(
                f"Query failed: {e}",
                connector=self.config.name,
                details={"sql": sql},
            ) from e
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple | None = None) -> int:
        """
        Execute a non-SELECT statement.

        Returns:
            Number of affected rows.
        """
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            self._error_count += 1
            raise ConnectorError(
                f"Execute failed: {e}",
                connector=self.config.name,
                details={"sql": sql},
            ) from e
        finally:
            conn.close()

    def bulk_insert(
        self,
        table: str,
        rows: list[dict[str, Any]],
        *,
        batch_size: int = 1000,
    ) -> int:
        """
        Bulk insert rows into a table.

        Args:
            table: Target table name.
            rows: List of row dicts.
            batch_size: Number of rows per batch.

        Returns:
            Total number of rows inserted.
        """
        if not rows:
            return 0

        columns = list(rows[0].keys())
        total_inserted = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            placeholders = ", ".join(["%s"] * len(columns))
            col_names = ", ".join(columns)
            sql = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})"

            conn = self.connect()
            try:
                cursor = conn.cursor()
                for row in batch:
                    values = tuple(row.get(col) for col in columns)
                    cursor.execute(sql, values)
                conn.commit()
                total_inserted += len(batch)
            except Exception as e:
                conn.rollback()
                raise ConnectorError(
                    f"Bulk insert failed: {e}",
                    connector=self.config.name,
                    details={"table": table, "batch": i // batch_size},
                ) from e
            finally:
                conn.close()

        return total_inserted

    def upsert(
        self,
        table: str,
        rows: list[dict[str, Any]],
        conflict_columns: list[str],
        *,
        batch_size: int = 1000,
    ) -> int:
        """
        Perform an upsert (INSERT ... ON CONFLICT UPDATE).

        Args:
            table: Target table name.
            rows: List of row dicts.
            conflict_columns: Columns that define the conflict.
            batch_size: Number of rows per batch.

        Returns:
            Total number of rows upserted.
        """
        if not rows:
            return 0

        columns = list(rows[0].keys())
        total_upserted = 0

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            placeholders = ", ".join(["%s"] * len(columns))
            col_names = ", ".join(columns)
            conflict_cols = ", ".join(conflict_columns)
            update_cols = [c for c in columns if c not in conflict_columns]
            update_clause = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)

            sql = f"""
                INSERT INTO {table} ({col_names}) VALUES ({placeholders})
                ON CONFLICT ({conflict_cols}) DO UPDATE SET {update_clause}
            """

            conn = self.connect()
            try:
                cursor = conn.cursor()
                for row in batch:
                    values = tuple(row.get(col) for col in columns)
                    cursor.execute(sql, values)
                conn.commit()
                total_upserted += len(batch)
            except Exception as e:
                conn.rollback()
                raise ConnectorError(
                    f"Upsert failed: {e}",
                    connector=self.config.name,
                    details={"table": table, "batch": i // batch_size},
                ) from e
            finally:
                conn.close()

        return total_upserted

    def begin_transaction(self) -> None:
        """Begin a transaction."""
        self._in_transaction = True
        self._transaction_connection = self.connect()

    def commit(self) -> None:
        """Commit the current transaction."""
        if self._transaction_connection:
            self._transaction_connection.commit()
            self._transaction_connection.close()
            self._transaction_connection = None
        self._in_transaction = False

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._transaction_connection:
            self._transaction_connection.rollback()
            self._transaction_connection.close()
            self._transaction_connection = None
        self._in_transaction = False

    def get_tables(self) -> list[str]:
        """Get list of tables in the database."""
        if self._db_type == "postgresql":
            return self.query(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            )
        elif self._db_type == "mysql":
            return self.query("SHOW TABLES")
        elif self._db_type == "sqlite":
            return self.query("SELECT name FROM sqlite_master WHERE type='table'")
        return []

    def get_schema(self, table: str) -> list[dict[str, Any]]:
        """Get schema information for a table."""
        if self._db_type == "postgresql":
            return self.query(
                """SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns WHERE table_name = %s""",
                (table,),
            )
        elif self._db_type == "sqlite":
            return self.query(f"PRAGMA table_info({table})")
        return []

    def health_check(self) -> dict[str, Any]:
        """Health check for database connector."""
        base = super().health_check()
        base["connector_type"] = "database"
        base["db_type"] = self._db_type
        try:
            conn = self.connect()
            conn.close()
            base["healthy"] = True
            base["status"] = "connected"
        except Exception as e:
            base["healthy"] = False
            base["status"] = "error"
            base["error"] = str(e)
        return base

    def close(self) -> None:
        """Close all connections."""
        if self._transaction_connection:
            self._transaction_connection.close()
            self._transaction_connection = None
        for conn in self._pool:
            try:
                conn.close()
            except Exception:
                pass
        self._pool.clear()
        self._status = ConnectorStatus.DISCONNECTED


class WebhookConnector(BaseConnector):
    """
    Webhook-based integration connector.

    Supports:
    - Webhook signature verification
    - Event parsing and routing
    - Webhook registration with external services
    - Retry with exponential backoff
    - Event deduplication
    """

    CAPABILITIES = [
        ConnectorCapability.READ,
        ConnectorCapability.WRITE,
        ConnectorCapability.REALTIME,
        ConnectorCapability.WEBHOOK,
    ]

    def __init__(self, config: ConnectorConfig, auth: AuthStrategy | None = None):
        super().__init__(config, auth)
        self._webhook_secret = config.custom.get("webhook_secret", "")
        self._signature_header = config.custom.get("signature_header", "X-Signature")
        self._event_handlers: dict[str, Callable[[dict[str, Any]], None]] = {}
        self._received_events: list[dict[str, Any]] = []
        self._dedup_window_seconds = config.custom.get("dedup_window_seconds", 3600)
        self._processed_event_ids: set[str] = set()

    def _define_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            name=self.config.name,
            version="1.0.0",
            vendor="GRC_Claw",
            description="Webhook connector for event-driven integrations",
            capabilities=self.CAPABILITIES,
            supported_auth=["hmac", "api_key"],
            category="webhook",
            tags=["webhook", "event", "realtime"],
        )

    def register_handler(
        self,
        event_type: str,
        handler: Callable[[dict[str, Any]], None],
    ) -> None:
        """Register an event handler for a specific event type."""
        self._event_handlers[event_type] = handler
        logger.info("Registered webhook handler for event type '%s'", event_type)

    def unregister_handler(self, event_type: str) -> bool:
        """Unregister an event handler."""
        if event_type in self._event_handlers:
            del self._event_handlers[event_type]
            return True
        return False

    def verify_signature(
        self,
        payload: bytes | str,
        signature: str,
        *,
        algorithm: str = "sha256",
    ) -> bool:
        """
        Verify a webhook signature.

        Args:
            payload: The raw request body.
            signature: The signature from the request header.
            algorithm: Hash algorithm (sha256, sha512).

        Returns:
            True if the signature is valid.
        """
        if not self._webhook_secret:
            logger.warning("No webhook secret configured, skipping signature verification")
            return True

        if isinstance(payload, str):
            payload = payload.encode("utf-8")

        expected = hmac.new(
            self._webhook_secret.encode("utf-8"),
            payload,
            getattr(hashlib, algorithm),
        ).hexdigest()

        # Support both hex digest and prefixed signatures (e.g., "sha256=...")
        if signature.startswith(f"{algorithm}="):
            signature = signature.split("=", 1)[1]

        return hmac.compare_digest(expected, signature)

    def process_webhook(
        self,
        payload: bytes | str,
        headers: dict[str, str] | None = None,
        *,
        verify: bool = True,
    ) -> dict[str, Any]:
        """
        Process an incoming webhook.

        Args:
            payload: The raw request body.
            headers: Request headers (for signature verification).
            verify: Whether to verify the signature.

        Returns:
            The parsed event data.

        Raises:
            WebhookError: If signature verification fails or processing fails.
        """
        headers = headers or {}

        # Verify signature
        if verify and self._webhook_secret:
            signature = headers.get(self._signature_header, "")
            if not signature:
                # Try common alternatives
                for alt_header in ("X-Hub-Signature-256", "X-Signature-256", "X-Webhook-Signature"):
                    signature = headers.get(alt_header, "")
                    if signature:
                        break

            if not signature:
                raise WebhookError(
                    "Missing webhook signature",
                    connector=self.config.name,
                )

            if not self.verify_signature(payload, signature):
                raise WebhookError(
                    "Invalid webhook signature",
                    connector=self.config.name,
                )

        # Parse payload
        try:
            if isinstance(payload, bytes):
                event = json.loads(payload.decode("utf-8"))
            else:
                event = json.loads(payload)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise WebhookError(
                f"Failed to parse webhook payload: {e}",
                connector=self.config.name,
            ) from e

        # Deduplication
        event_id = event.get("id", event.get("event_id", ""))
        if event_id:
            if event_id in self._processed_event_ids:
                logger.debug("Duplicate webhook event '%s' ignored", event_id)
                return {"status": "duplicate", "event_id": event_id}
            self._processed_event_ids.add(event_id)

        # Store event
        self._received_events.append({
            "event": event,
            "received_at": datetime.now(UTC).isoformat(),
            "headers": dict(headers),
        })

        # Trim old events
        if len(self._received_events) > 10000:
            self._received_events = self._received_events[-5000:]

        # Route to handler
        event_type = event.get("type", event.get("event_type", "unknown"))
        handler = self._event_handlers.get(event_type)
        if handler:
            try:
                handler(event)
            except Exception as e:
                logger.error("Webhook handler for '%s' failed: %s", event_type, e)
                raise WebhookError(
                    f"Handler failed for event type '{event_type}': {e}",
                    connector=self.config.name,
                ) from e
        else:
            logger.debug("No handler registered for event type '%s'", event_type)

        return {"status": "processed", "event_type": event_type, "event_id": event_id}

    def get_received_events(
        self,
        *,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get received webhook events."""
        events = self._received_events
        if event_type:
            events = [
                e for e in events
                if e["event"].get("type", e["event"].get("event_type")) == event_type
            ]
        return events[-limit:]

    def clear_events(self) -> None:
        """Clear all received events."""
        self._received_events.clear()
        self._processed_event_ids.clear()

    def create_webhook_subscription(
        self,
        target_url: str,
        events: list[str],
        *,
        active: bool = True,
    ) -> dict[str, Any]:
        """
        Create a webhook subscription on the external service.

        Args:
            target_url: URL to receive webhook events.
            events: List of event types to subscribe to.
            active: Whether the subscription is active.

        Returns:
            Subscription details from the external service.
        """
        if not self.config.base_url:
            raise ConnectorError(
                "Base URL is required for webhook subscription",
                connector=self.config.name,
            )

        payload = {
            "url": target_url,
            "events": events,
            "active": active,
            "secret": self._webhook_secret,
        }

        response = self.post("/webhooks/subscriptions", payload)
        if not response.is_success:
            raise ConnectorError(
                f"Failed to create webhook subscription: {response.status_code}",
                connector=self.config.name,
                details={"body": response.body},
            )

        return response.body

    def delete_webhook_subscription(self, subscription_id: str) -> bool:
        """Delete a webhook subscription."""
        response = self.delete(f"/webhooks/subscriptions/{subscription_id}")
        return response.is_success

    def health_check(self) -> dict[str, Any]:
        """Health check for webhook connector."""
        base = super().health_check()
        base["connector_type"] = "webhook"
        base["handlers_registered"] = list(self._event_handlers.keys())
        base["events_received"] = len(self._received_events)
        base["dedup_cache_size"] = len(self._processed_event_ids)
        return base


class FileTransferConnector(BaseConnector):
    """
    File transfer integration connector.

    Supports:
    - SFTP file upload/download
    - S3 file operations
    - Local file system operations
    - File watching
    - Chunked transfers
    - Checksum verification
    """

    CAPABILITIES = [
        ConnectorCapability.READ,
        ConnectorCapability.WRITE,
        ConnectorCapability.DELETE,
        ConnectorCapability.BATCH,
        ConnectorCapability.FULL_SYNC,
        ConnectorCapability.INCREMENTAL_SYNC,
    ]

    def __init__(self, config: ConnectorConfig, auth: AuthStrategy | None = None):
        super().__init__(config, auth)
        self._protocol = config.custom.get("protocol", "sftp")  # sftp, s3, local
        self._host = config.custom.get("host", "")
        self._port = int(config.custom.get("port", 22))
        self._username = config.custom.get("username", "")
        self._password = config.custom.get("password", "")
        self._private_key = config.custom.get("private_key", "")
        self._bucket = config.custom.get("bucket", "")
        self._region = config.custom.get("region", "us-east-1")
        self._base_path = config.custom.get("base_path", "/")
        self._chunk_size = int(config.custom.get("chunk_size", 8192))

    def _define_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            name=self.config.name,
            version="1.0.0",
            vendor="GRC_Claw",
            description="File transfer connector for SFTP/S3/local file operations",
            capabilities=self.CAPABILITIES,
            supported_auth=["basic", "api_key"],
            category="file_transfer",
            tags=["sftp", "s3", "file", "transfer"],
        )

    def upload_file(
        self,
        local_path: str,
        remote_path: str,
        *,
        overwrite: bool = True,
    ) -> dict[str, Any]:
        """
        Upload a file to the remote destination.

        Args:
            local_path: Path to the local file.
            remote_path: Destination path on the remote.
            overwrite: Whether to overwrite existing files.

        Returns:
            Upload result with file details.
        """
        if not os.path.exists(local_path):
            raise ConnectorError(
                f"Local file not found: {local_path}",
                connector=self.config.name,
            )

        file_size = os.path.getsize(local_path)
        checksum = self._calculate_checksum(local_path)

        if self._protocol == "local":
            return self._upload_local(local_path, remote_path, overwrite)
        elif self._protocol == "sftp":
            return self._upload_sftp(local_path, remote_path, overwrite)
        elif self._protocol == "s3":
            return self._upload_s3(local_path, remote_path, overwrite)
        else:
            raise ConnectorError(
                f"Unsupported protocol: {self._protocol}",
                connector=self.config.name,
            )

    def download_file(
        self,
        remote_path: str,
        local_path: str,
        *,
        verify_checksum: bool = False,
    ) -> dict[str, Any]:
        """
        Download a file from the remote source.

        Args:
            remote_path: Path to the remote file.
            local_path: Destination path on the local filesystem.
            verify_checksum: Whether to verify file integrity after download.

        Returns:
            Download result with file details.
        """
        if self._protocol == "local":
            return self._download_local(remote_path, local_path)
        elif self._protocol == "sftp":
            return self._download_sftp(remote_path, local_path)
        elif self._protocol == "s3":
            return self._download_s3(remote_path, local_path)
        else:
            raise ConnectorError(
                f"Unsupported protocol: {self._protocol}",
                connector=self.config.name,
            )

    def list_files(
        self,
        remote_path: str = "/",
        *,
        pattern: str = "*",
        recursive: bool = False,
    ) -> list[dict[str, Any]]:
        """
        List files in a remote directory.

        Args:
            remote_path: Directory path to list.
            pattern: Glob pattern to filter files.
            recursive: Whether to list recursively.

        Returns:
            List of file info dicts.
        """
        if self._protocol == "local":
            return self._list_local(remote_path, pattern, recursive)
        elif self._protocol == "sftp":
            return self._list_sftp(remote_path, pattern, recursive)
        elif self._protocol == "s3":
            return self._list_s3(remote_path, pattern, recursive)
        else:
            raise ConnectorError(
                f"Unsupported protocol: {self._protocol}",
                connector=self.config.name,
            )

    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from the remote destination."""
        if self._protocol == "local":
            return self._delete_local(remote_path)
        elif self._protocol == "sftp":
            return self._delete_sftp(remote_path)
        elif self._protocol == "s3":
            return self._delete_s3(remote_path)
        else:
            raise ConnectorError(
                f"Unsupported protocol: {self._protocol}",
                connector=self.config.name,
            )

    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists on the remote."""
        try:
            if self._protocol == "local":
                return os.path.exists(remote_path)
            elif self._protocol == "sftp":
                ssh = self._get_sftp_client()
                sftp = ssh.open_sftp()
                try:
                    sftp.stat(remote_path)
                    return True
                except FileNotFoundError:
                    return False
                finally:
                    sftp.close()
                    ssh.close()
            elif self._protocol == "s3":
                import boto3
                s3 = boto3.client("s3", region_name=self._region)
                try:
                    s3.head_object(Bucket=self._bucket, Key=remote_path)
                    return True
                except Exception:
                    return False
        except Exception:
            return False

    def get_file_info(self, remote_path: str) -> dict[str, Any]:
        """Get file metadata."""
        if self._protocol == "local":
            if not os.path.exists(remote_path):
                raise ConnectorError(f"File not found: {remote_path}", connector=self.config.name)
            stat = os.stat(remote_path)
            return {
                "path": remote_path,
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime, tz=UTC).isoformat(),
            }
        elif self._protocol == "sftp":
            ssh = self._get_sftp_client()
            sftp = ssh.open_sftp()
            try:
                stat = sftp.stat(remote_path)
                return {
                    "path": remote_path,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
                    "permissions": oct(stat.st_mode)[-3:],
                }
            finally:
                sftp.close()
                ssh.close()
        elif self._protocol == "s3":
            import boto3
            s3 = boto3.client("s3", region_name=self._region)
            try:
                resp = s3.head_object(Bucket=self._bucket, Key=remote_path)
                return {
                    "path": remote_path,
                    "size": resp["ContentLength"],
                    "modified": resp["LastModified"].isoformat(),
                    "etag": resp["ETag"],
                    "content_type": resp.get("ContentType", ""),
                }
            except Exception as e:
                raise ConnectorError(f"File not found: {remote_path}: {e}", connector=self.config.name)
        else:
            raise ConnectorError(f"Unsupported protocol: {self._protocol}", connector=self.config.name)

    def _calculate_checksum(self, file_path: str, algorithm: str = "sha256") -> str:
        """Calculate file checksum."""
        h = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            while chunk := f.read(self._chunk_size):
                h.update(chunk)
        return h.hexdigest()

    def _upload_local(self, local_path: str, remote_path: str, overwrite: bool) -> dict[str, Any]:
        """Upload to local filesystem."""
        if os.path.exists(remote_path) and not overwrite:
            raise ConnectorError(f"File exists: {remote_path}", connector=self.config.name)
        import shutil
        os.makedirs(os.path.dirname(remote_path) or ".", exist_ok=True)
        shutil.copy2(local_path, remote_path)
        return {
            "path": remote_path,
            "size": os.path.getsize(remote_path),
            "checksum": self._calculate_checksum(remote_path),
        }

    def _download_local(self, remote_path: str, local_path: str) -> dict[str, Any]:
        """Download from local filesystem."""
        if not os.path.exists(remote_path):
            raise ConnectorError(f"File not found: {remote_path}", connector=self.config.name)
        import shutil
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        shutil.copy2(remote_path, local_path)
        return {
            "path": local_path,
            "size": os.path.getsize(local_path),
            "checksum": self._calculate_checksum(local_path),
        }

    def _list_local(self, path: str, pattern: str, recursive: bool) -> list[dict[str, Any]]:
        """List local files."""
        import fnmatch
        results = []
        if recursive:
            for root, dirs, files in os.walk(path):
                for f in files:
                    full = os.path.join(root, f)
                    if fnmatch.fnmatch(f, pattern):
                        results.append(self.get_file_info(full))
        else:
            for f in os.listdir(path):
                full = os.path.join(path, f)
                if os.path.isfile(full) and fnmatch.fnmatch(f, pattern):
                    results.append(self.get_file_info(full))
        return results

    def _delete_local(self, path: str) -> bool:
        """Delete local file."""
        try:
            os.remove(path)
            return True
        except FileNotFoundError:
            return False

    def _get_sftp_client(self):
        """Get an SFTP client."""
        try:
            import paramiko
        except ImportError:
            raise ConnectorError(
                "paramiko is required for SFTP support. Install with: pip install paramiko",
                connector=self.config.name,
            )
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        connect_kwargs = {
            "hostname": self._host,
            "port": self._port,
            "username": self._username,
        }
        if self._private_key:
            connect_kwargs["key_filename"] = self._private_key
        else:
            connect_kwargs["password"] = self._password
        ssh.connect(**connect_kwargs)
        return ssh

    def _upload_sftp(self, local_path: str, remote_path: str, overwrite: bool) -> dict[str, Any]:
        """Upload via SFTP."""
        ssh = self._get_sftp_client()
        sftp = ssh.open_sftp()
        try:
            if not overwrite:
                try:
                    sftp.stat(remote_path)
                    raise ConnectorError(f"File exists: {remote_path}", connector=self.config.name)
                except FileNotFoundError:
                    pass
            sftp.put(local_path, remote_path)
            stat = sftp.stat(remote_path)
            return {
                "path": remote_path,
                "size": stat.st_size,
                "checksum": self._calculate_checksum(local_path),
            }
        finally:
            sftp.close()
            ssh.close()

    def _download_sftp(self, remote_path: str, local_path: str) -> dict[str, Any]:
        """Download via SFTP."""
        ssh = self._get_sftp_client()
        sftp = ssh.open_sftp()
        try:
            os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
            sftp.get(remote_path, local_path)
            return {
                "path": local_path,
                "size": os.path.getsize(local_path),
                "checksum": self._calculate_checksum(local_path),
            }
        finally:
            sftp.close()
            ssh.close()

    def _list_sftp(self, path: str, pattern: str, recursive: bool) -> list[dict[str, Any]]:
        """List SFTP files."""
        import fnmatch
        ssh = self._get_sftp_client()
        sftp = ssh.open_sftp()
        results = []
        try:
            for entry in sftp.listdir_attr(path):
                full = f"{path}/{entry.filename}"
                if fnmatch.fnmatch(entry.filename, pattern):
                    results.append({
                        "path": full,
                        "size": entry.st_size,
                        "modified": datetime.fromtimestamp(entry.st_mtime, tz=UTC).isoformat(),
                    })
        finally:
            sftp.close()
            ssh.close()
        return results

    def _delete_sftp(self, path: str) -> bool:
        """Delete SFTP file."""
        ssh = self._get_sftp_client()
        sftp = ssh.open_sftp()
        try:
            sftp.remove(path)
            return True
        except FileNotFoundError:
            return False
        finally:
            sftp.close()
            ssh.close()

    def _upload_s3(self, local_path: str, remote_path: str, overwrite: bool) -> dict[str, Any]:
        """Upload to S3."""
        try:
            import boto3
        except ImportError:
            raise ConnectorError(
                "boto3 is required for S3 support. Install with: pip install boto3",
                connector=self.config.name,
            )
        s3 = boto3.client("s3", region_name=self._region)
        extra_args = {}
        if not overwrite:
            extra_args["IfNoneMatch"] = "*"
        s3.upload_file(local_path, self._bucket, remote_path, ExtraArgs=extra_args or None)
        return {
            "path": remote_path,
            "size": os.path.getsize(local_path),
            "checksum": self._calculate_checksum(local_path),
        }

    def _download_s3(self, remote_path: str, local_path: str) -> dict[str, Any]:
        """Download from S3."""
        try:
            import boto3
        except ImportError:
            raise ConnectorError(
                "boto3 is required for S3 support. Install with: pip install boto3",
                connector=self.config.name,
            )
        s3 = boto3.client("s3", region_name=self._region)
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        s3.download_file(self._bucket, remote_path, local_path)
        return {
            "path": local_path,
            "size": os.path.getsize(local_path),
            "checksum": self._calculate_checksum(local_path),
        }

    def _list_s3(self, prefix: str, pattern: str, recursive: bool) -> list[dict[str, Any]]:
        """List S3 files."""
        import fnmatch
        try:
            import boto3
        except ImportError:
            raise ConnectorError(
                "boto3 is required for S3 support. Install with: pip install boto3",
                connector=self.config.name,
            )
        s3 = boto3.client("s3", region_name=self._region)
        results = []
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                filename = key.split("/")[-1]
                if fnmatch.fnmatch(filename, pattern):
                    results.append({
                        "path": key,
                        "size": obj["Size"],
                        "modified": obj["LastModified"].isoformat(),
                        "etag": obj["ETag"],
                    })
        return results

    def _delete_s3(self, path: str) -> bool:
        """Delete S3 file."""
        try:
            import boto3
        except ImportError:
            raise ConnectorError(
                "boto3 is required for S3 support. Install with: pip install boto3",
                connector=self.config.name,
            )
        s3 = boto3.client("s3", region_name=self._region)
        try:
            s3.delete_object(Bucket=self._bucket, Key=path)
            return True
        except Exception:
            return False

    def health_check(self) -> dict[str, Any]:
        """Health check for file transfer connector."""
        base = super().health_check()
        base["connector_type"] = "file_transfer"
        base["protocol"] = self._protocol
        try:
            if self._protocol == "local":
                base["healthy"] = os.path.isdir(self._base_path) if self._base_path else True
            elif self._protocol == "sftp":
                ssh = self._get_sftp_client()
                ssh.close()
                base["healthy"] = True
            elif self._protocol == "s3":
                import boto3
                s3 = boto3.client("s3", region_name=self._region)
                s3.head_bucket(Bucket=self._bucket)
                base["healthy"] = True
            base["status"] = "connected" if base["healthy"] else "error"
        except Exception as e:
            base["healthy"] = False
            base["status"] = "error"
            base["error"] = str(e)
        return base

    def close(self) -> None:
        """Clean up resources."""
        self._status = ConnectorStatus.DISCONNECTED
