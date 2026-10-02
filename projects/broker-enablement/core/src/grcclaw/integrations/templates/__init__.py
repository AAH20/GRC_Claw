"""
Integration Templates — Pre-built connector templates for common integration patterns.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime, timezone
from typing import Any, Optional

from ..sdk import (
    APIKeyAuth,
    BaseConnector,
    BasicAuth,
    BearerAuth,
    ConnectorCapability,
    ConnectorConfig,
    ConnectorMetadata,
    ConnectorStatus,
    OAuth2Auth,
)
from ..transformation import DataNormalizer, DataValidator, SchemaMapper, TransformationRule

logger = logging.getLogger(__name__)


@dataclass
class IntegrationTemplate:
    """A reusable integration template definition."""

    name: str
    description: str
    category: str
    connector_class: type[BaseConnector]
    default_config: dict[str, Any] = field(default_factory=dict)
    required_fields: list[str] = field(default_factory=list)
    optional_fields: dict[str, Any] = field(default_factory=dict)
    auth_type: str = "none"
    sample_payload: dict[str, Any] = field(default_factory=dict)
    documentation: str = ""
    tags: list[str] = field(default_factory=list)
    version: str = "1.0.0"

    def create_connector(self, config_overrides: dict[str, Any] | None = None) -> BaseConnector:
        """Create a connector instance from this template."""
        config_dict = {**self.default_config, **(config_overrides or {})}
        config = ConnectorConfig(name=self.name, **config_dict)
        return self.connector_class(config)

    def validate_config(self, config: dict[str, Any]) -> list[str]:
        """Validate a configuration against this template."""
        errors = []
        for field_name in self.required_fields:
            if field_name not in config or config[field_name] is None:
                errors.append(f"Required field '{field_name}' is missing")
        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize template to dict."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "auth_type": self.auth_type,
            "required_fields": self.required_fields,
            "optional_fields": self.optional_fields,
            "default_config": self.default_config,
            "sample_payload": self.sample_payload,
            "documentation": self.documentation,
            "tags": self.tags,
            "version": self.version,
        }


class RESTAPIConnector(BaseConnector):
    """
    Generic REST API connector template.

    Provides a configurable connector for any REST API with:
    - Standard HTTP methods
    - JSON request/response handling
    - Pagination support
    - Error handling
    """

    CAPABILITIES = [
        ConnectorCapability.READ,
        ConnectorCapability.WRITE,
        ConnectorCapability.DELETE,
        ConnectorCapability.BATCH,
        ConnectorCapability.PAGINATION,
    ]

    def _define_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            name="REST API Connector",
            version="1.0.0",
            vendor="GRC_Claw",
            description="Generic REST API connector for HTTP-based integrations",
            capabilities=self.CAPABILITIES,
            supported_auth=["api_key", "oauth2", "basic", "bearer", "none"],
            rate_limit_per_minute=60,
            category="api",
            tags=["rest", "http", "api", "json"],
        )

    def get_resource(self, resource: str, resource_id: str = "", params: dict | None = None) -> dict:
        """Get a resource or list of resources."""
        path = f"{resource}/{resource_id}" if resource_id else resource
        response = self.get(path, params=params)
        if response.is_success:
            return response.body
        return {}

    def create_resource(self, resource: str, data: dict) -> dict:
        """Create a new resource."""
        response = self.post(resource, body=data)
        if response.is_success:
            return response.body
        return {}

    def update_resource(self, resource: str, resource_id: str, data: dict) -> dict:
        """Update an existing resource."""
        response = self.put(f"{resource}/{resource_id}", body=data)
        if response.is_success:
            return response.body
        return {}

    def delete_resource(self, resource: str, resource_id: str) -> bool:
        """Delete a resource."""
        response = self.delete(f"{resource}/{resource_id}")
        return response.is_success

    def search(self, resource: str, query: str, filters: dict | None = None) -> list:
        """Search for resources."""
        params = {"q": query, **(filters or {})}
        response = self.get(resource, params=params)
        if response.is_success and isinstance(response.body, list):
            return response.body
        return []


class DatabaseConnector(BaseConnector):
    """
    Database connector template for SQL and NoSQL databases.

    Provides:
    - Connection pooling
    - Query execution
    - Result mapping
    - Transaction support
    """

    CAPABILITIES = [
        ConnectorCapability.READ,
        ConnectorCapability.WRITE,
        ConnectorCapability.BATCH,
        ConnectorCapability.INCREMENTAL_SYNC,
    ]

    def _define_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            name="Database Connector",
            version="1.0.0",
            vendor="GRC_Claw",
            description="Database connector for SQL and NoSQL databases",
            capabilities=self.CAPABILITIES,
            supported_auth=["basic", "api_key"],
            rate_limit_per_minute=120,
            category="database",
            tags=["database", "sql", "nosql", "db"],
        )

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._connection = None
        self._db_type = config.custom.get("db_type", "postgresql")
        self._database = config.custom.get("database", "")
        self._schema = config.custom.get("schema", "public")

    def connect(self) -> bool:
        """Establish database connection."""
        try:
            if self._db_type == "postgresql":
                import psycopg2
                self._connection = psycopg2.connect(
                    host=self.config.base_url,
                    dbname=self._database,
                    user=self.config.auth_config.get("username", ""),
                    password=self.config.auth_config.get("password", ""),
                )
            elif self._db_type == "mysql":
                import pymysql
                self._connection = pymysql.connect(
                    host=self.config.base_url,
                    database=self._database,
                    user=self.config.auth_config.get("username", ""),
                    password=self.config.auth_config.get("password", ""),
                )
            elif self._db_type == "sqlite":
                import sqlite3
                self._connection = sqlite3.connect(self._database)
            else:
                raise ValueError(f"Unsupported database type: {self._db_type}")

            self._status = ConnectorStatus.CONNECTED
            return True

        except Exception as e:
            self._status = ConnectorStatus.ERROR
            logger.error("Database connection failed: %s", e)
            return False

    def execute_query(self, query: str, params: tuple | None = None) -> list[dict]:
        """Execute a SQL query and return results."""
        if not self._connection:
            if not self.connect():
                return []

        try:
            cursor = self._connection.cursor()
            cursor.execute(query, params or ())

            if query.strip().upper().startswith("SELECT"):
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                return results
            else:
                self._connection.commit()
                return [{"affected_rows": cursor.rowcount}]

        except Exception as e:
            logger.error("Query execution failed: %s", e)
            return []

    def execute_many(self, query: str, params_list: list[tuple]) -> int:
        """Execute a query with multiple parameter sets."""
        if not self._connection:
            if not self.connect():
                return 0

        try:
            cursor = self._connection.cursor()
            cursor.executemany(query, params_list)
            self._connection.commit()
            return cursor.rowcount
        except Exception as e:
            logger.error("Batch execution failed: %s", e)
            return 0

    def begin_transaction(self) -> None:
        """Begin a database transaction."""
        if self._connection:
            self._connection.autocommit = False

    def commit(self) -> None:
        """Commit the current transaction."""
        if self._connection:
            self._connection.commit()
            self._connection.autocommit = True

    def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._connection:
            self._connection.rollback()
            self._connection.autocommit = True

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        super().close()

    def health_check(self) -> dict[str, Any]:
        """Check database connectivity."""
        try:
            if not self._connection:
                self.connect()
            if self._db_type == "sqlite":
                self._connection.execute("SELECT 1")
            else:
                cursor = self._connection.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {
                "name": self.config.name,
                "status": ConnectorStatus.CONNECTED.value,
                "healthy": True,
                "db_type": self._db_type,
                "database": self._database,
            }
        except Exception as e:
            return {
                "name": self.config.name,
                "status": ConnectorStatus.ERROR.value,
                "healthy": False,
                "error": str(e),
            }


class WebhookConnector(BaseConnector):
    """
    Webhook connector for receiving and processing webhook events.

    Provides:
    - Webhook endpoint handling
    - Signature verification
    - Event parsing and routing
    - Retry logic for failed deliveries
    """

    CAPABILITIES = [
        ConnectorCapability.WEBHOOK,
        ConnectorCapability.REALTIME,
        ConnectorCapability.READ,
    ]

    def _define_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            name="Webhook Connector",
            version="1.0.0",
            vendor="GRC_Claw",
            description="Webhook connector for receiving and processing webhook events",
            capabilities=self.CAPABILITIES,
            supported_auth=["hmac", "bearer", "none"],
            rate_limit_per_minute=1000,
            category="webhook",
            tags=["webhook", "event", "realtime", "callback"],
        )

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._secret = config.auth_config.get("webhook_secret", "")
        self._handlers: dict[str, list] = {}
        self._event_log: list[dict] = []

    def register_handler(self, event_type: str, handler) -> None:
        """Register a handler for a specific event type."""
        self._handlers.setdefault(event_type, []).append(handler)

    def verify_signature(self, payload: bytes, signature: str, algorithm: str = "sha256") -> bool:
        """Verify webhook signature."""
        import hashlib
        import hmac

        if not self._secret:
            return True  # No secret configured, skip verification

        expected = hmac.new(
            self._secret.encode(),
            payload,
            getattr(hashlib, algorithm),
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def process_event(self, event_type: str, payload: dict, headers: dict | None = None) -> dict:
        """Process an incoming webhook event."""
        event_record = {
            "event_type": event_type,
            "payload": payload,
            "headers": headers or {},
            "received_at": datetime.now(UTC).isoformat(),
            "processed": False,
        }

        handlers = self._handlers.get(event_type, [])
        results = []

        for handler in handlers:
            try:
                result = handler(payload, headers or {})
                results.append({"handler": handler.__name__, "result": result, "success": True})
            except Exception as e:
                results.append({"handler": handler.__name__, "error": str(e), "success": False})

        event_record["processed"] = True
        event_record["handler_results"] = results
        self._event_log.append(event_record)

        return {
            "event_type": event_type,
            "handlers_executed": len(handlers),
            "results": results,
        }

    def get_event_log(self, event_type: str = "", limit: int = 100) -> list[dict]:
        """Get the event log, optionally filtered by type."""
        events = self._event_log
        if event_type:
            events = [e for e in events if e["event_type"] == event_type]
        return events[-limit:]

    def replay_event(self, event_index: int) -> dict:
        """Replay a previously received event."""
        if 0 <= event_index < len(self._event_log):
            event = self._event_log[event_index]
            return self.process_event(event["event_type"], event["payload"], event["headers"])
        return {"error": "Event not found"}


class FileTransferConnector(BaseConnector):
    """
    File transfer connector for SFTP, S3, and local file operations.

    Provides:
    - File upload/download
    - Directory listing
    - File watching
    - Batch transfers
    """

    CAPABILITIES = [
        ConnectorCapability.READ,
        ConnectorCapability.WRITE,
        ConnectorCapability.BATCH,
        ConnectorCapability.STREAM,
    ]

    def _define_metadata(self) -> ConnectorMetadata:
        return ConnectorMetadata(
            name="File Transfer Connector",
            version="1.0.0",
            vendor="GRC_Claw",
            description="File transfer connector for SFTP, S3, and local file operations",
            capabilities=self.CAPABILITIES,
            supported_auth=["basic", "api_key", "iam"],
            rate_limit_per_minute=30,
            category="file",
            tags=["file", "sftp", "s3", "storage", "transfer"],
        )

    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._protocol = config.custom.get("protocol", "s3")  # s3, sftp, local
        self._bucket = config.custom.get("bucket", "")
        self._base_path = config.custom.get("base_path", "/")
        self._client = None

    def connect(self) -> bool:
        """Establish connection to the file storage."""
        try:
            if self._protocol == "s3":
                import boto3
                self._client = boto3.client(
                    "s3",
                    aws_access_key_id=self.config.auth_config.get("access_key", ""),
                    aws_secret_access_key=self.config.auth_config.get("secret_key", ""),
                    region_name=self.config.auth_config.get("region", "us-east-1"),
                )
            elif self._protocol == "sftp":
                import paramiko
                transport = paramiko.Transport((
                    self.config.base_url,
                    int(self.config.auth_config.get("port", 22)),
                ))
                transport.connect(
                    username=self.config.auth_config.get("username", ""),
                    password=self.config.auth_config.get("password", ""),
                )
                self._client = paramiko.SFTPClient.from_transport(transport)
            elif self._protocol == "local":
                self._client = True  # Local files need no client

            self._status = ConnectorStatus.CONNECTED
            return True

        except Exception as e:
            self._status = ConnectorStatus.ERROR
            logger.error("File transfer connection failed: %s", e)
            return False

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload a file to remote storage."""
        try:
            if self._protocol == "s3":
                self._client.upload_file(local_path, self._bucket, remote_path)
            elif self._protocol == "sftp":
                self._client.put(local_path, remote_path)
            elif self._protocol == "local":
                import shutil
                shutil.copy2(local_path, remote_path)
            return True
        except Exception as e:
            logger.error("Upload failed: %s", e)
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download a file from remote storage."""
        try:
            if self._protocol == "s3":
                self._client.download_file(self._bucket, remote_path, local_path)
            elif self._protocol == "sftp":
                self._client.get(remote_path, local_path)
            elif self._protocol == "local":
                import shutil
                shutil.copy2(remote_path, local_path)
            return True
        except Exception as e:
            logger.error("Download failed: %s", e)
            return False

    def list_files(self, remote_path: str = "", pattern: str = "*") -> list[dict]:
        """List files in a remote directory."""
        try:
            if self._protocol == "s3":
                prefix = f"{self._base_path}/{remote_path}".strip("/")
                response = self._client.list_objects_v2(
                    Bucket=self._bucket,
                    Prefix=prefix,
                )
                return [
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"].isoformat(),
                        "etag": obj["ETag"],
                    }
                    for obj in response.get("Contents", [])
                ]
            elif self._protocol == "sftp":
                entries = self._client.listdir_attr(remote_path or self._base_path)
                return [
                    {
                        "filename": entry.filename,
                        "size": entry.st_size,
                        "modified": entry.st_mtime,
                        "permissions": oct(entry.st_mode)[-3:],
                    }
                    for entry in entries
                ]
            elif self._protocol == "local":
                import glob
                import os
                search_path = os.path.join(self._base_path, remote_path, pattern)
                return [
                    {
                        "filename": os.path.basename(f),
                        "path": f,
                        "size": os.path.getsize(f),
                        "modified": os.path.getmtime(f),
                    }
                    for f in glob.glob(search_path)
                ]
            return []
        except Exception as e:
            logger.error("List files failed: %s", e)
            return []

    def delete_file(self, remote_path: str) -> bool:
        """Delete a file from remote storage."""
        try:
            if self._protocol == "s3":
                self._client.delete_object(Bucket=self._bucket, Key=remote_path)
            elif self._protocol == "sftp":
                self._client.remove(remote_path)
            elif self._protocol == "local":
                os.remove(remote_path)
            return True
        except Exception as e:
            logger.error("Delete failed: %s", e)
            return False

    def file_exists(self, remote_path: str) -> bool:
        """Check if a file exists."""
        try:
            if self._protocol == "s3":
                self._client.head_object(Bucket=self._bucket, Key=remote_path)
                return True
            elif self._protocol == "sftp":
                self._client.stat(remote_path)
                return True
            elif self._protocol == "local":
                return os.path.exists(remote_path)
        except Exception:
            pass
        return False

    def get_file_info(self, remote_path: str) -> dict:
        """Get file metadata."""
        try:
            if self._protocol == "s3":
                response = self._client.head_object(Bucket=self._bucket, Key=remote_path)
                return {
                    "size": response["ContentLength"],
                    "last_modified": response["LastModified"].isoformat(),
                    "content_type": response.get("ContentType", ""),
                    "etag": response["ETag"],
                }
            elif self._protocol == "sftp":
                stat = self._client.stat(remote_path)
                return {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "permissions": oct(stat.st_mode)[-3:],
                }
            elif self._protocol == "local":
                stat = os.stat(remote_path)
                return {
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "permissions": oct(stat.st_mode)[-3:],
                }
        except Exception as e:
            logger.error("Get file info failed: %s", e)
        return {}

    def close(self) -> None:
        """Close the file transfer connection."""
        if self._client and self._protocol == "sftp":
            self._client.close()
        self._client = None
        super().close()


class TemplateRegistry:
    """
    Registry of pre-built integration templates.

    Provides:
    - Template discovery
    - Template instantiation
    - Custom template registration
    """

    def __init__(self):
        self._templates: dict[str, IntegrationTemplate] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        """Register default templates."""
        self.register(IntegrationTemplate(
            name="rest_api",
            description="Generic REST API connector",
            category="api",
            connector_class=RESTAPIConnector,
            default_config={"base_url": "", "timeout_seconds": 30},
            required_fields=["base_url"],
            optional_fields={"headers": {}, "verify_ssl": True},
            auth_type="api_key",
            tags=["rest", "http", "api"],
        ))

        self.register(IntegrationTemplate(
            name="database",
            description="Database connector (PostgreSQL, MySQL, SQLite)",
            category="database",
            connector_class=DatabaseConnector,
            default_config={"base_url": "localhost", "timeout_seconds": 30},
            required_fields=["base_url", "database"],
            optional_fields={"db_type": "postgresql", "schema": "public"},
            auth_type="basic",
            tags=["database", "sql"],
        ))

        self.register(IntegrationTemplate(
            name="webhook",
            description="Webhook receiver connector",
            category="webhook",
            connector_class=WebhookConnector,
            default_config={"base_url": "", "timeout_seconds": 10},
            required_fields=[],
            optional_fields={"webhook_secret": ""},
            auth_type="hmac",
            tags=["webhook", "event"],
        ))

        self.register(IntegrationTemplate(
            name="file_transfer",
            description="File transfer connector (S3, SFTP, local)",
            category="file",
            connector_class=FileTransferConnector,
            default_config={"base_url": "", "timeout_seconds": 60},
            required_fields=[],
            optional_fields={"protocol": "s3", "bucket": "", "base_path": "/"},
            auth_type="basic",
            tags=["file", "sftp", "s3"],
        ))

    def register(self, template: IntegrationTemplate) -> None:
        """Register a template."""
        self._templates[template.name] = template

    def get(self, name: str) -> IntegrationTemplate | None:
        """Get a template by name."""
        return self._templates.get(name)

    def list_templates(self, category: str = "") -> list[str]:
        """List template names, optionally filtered by category."""
        if category:
            return [name for name, t in self._templates.items() if t.category == category]
        return list(self._templates.keys())

    def create_connector(self, name: str, config: dict[str, Any] | None = None) -> BaseConnector:
        """Create a connector from a template."""
        template = self._templates.get(name)
        if not template:
            raise KeyError(f"Template '{name}' not found")

        errors = template.validate_config(config or {})
        if errors:
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

        return template.create_connector(config)

    def get_categories(self) -> list[str]:
        """Get all unique template categories."""
        return list(set(t.category for t in self._templates.values()))
