"""
GRC_Claw Integration & Connector Framework

Unified integration system for connecting GRC_Claw with external systems.
Provides connector SDK, integration engine, data transformation, monitoring,
and pre-built integration templates.
"""

from .sdk import (
    BaseConnector,
    ConnectorConfig,
    AuthStrategy,
    APIKeyAuth,
    OAuth2Auth,
    BasicAuth,
    BearerAuth,
    ConnectorRegistry,
    ConnectorCapability,
    ConnectorStatus,
)
from .engine import (
    IntegrationOrchestrator,
    IntegrationPipeline,
    PipelineStep,
    PipelineResult,
    IntegrationScheduler,
    IntegrationState,
)
from .transformation import (
    SchemaMapper,
    FieldTransformer,
    DataNormalizer,
    DataValidator,
    TransformationRule,
    TransformationResult,
)
from .monitoring import (
    HealthChecker,
    IntegrationMetrics,
    AlertManager,
    IntegrationTracer,
    HealthStatus,
    AlertSeverity,
)
from .templates import (
    IntegrationTemplate,
    RESTAPIConnector,
    DatabaseConnector,
    WebhookConnector,
    FileTransferConnector,
)

__all__ = [
    # SDK
    "BaseConnector",
    "ConnectorConfig",
    "AuthStrategy",
    "APIKeyAuth",
    "OAuth2Auth",
    "BasicAuth",
    "BearerAuth",
    "ConnectorRegistry",
    "ConnectorCapability",
    "ConnectorStatus",
    # Engine
    "IntegrationOrchestrator",
    "IntegrationPipeline",
    "PipelineStep",
    "PipelineResult",
    "IntegrationScheduler",
    "IntegrationState",
    # Transformation
    "SchemaMapper",
    "FieldTransformer",
    "DataNormalizer",
    "DataValidator",
    "TransformationRule",
    "TransformationResult",
    # Monitoring
    "HealthChecker",
    "IntegrationMetrics",
    "AlertManager",
    "IntegrationTracer",
    "HealthStatus",
    "AlertSeverity",
    # Templates
    "IntegrationTemplate",
    "RESTAPIConnector",
    "DatabaseConnector",
    "WebhookConnector",
    "FileTransferConnector",
]
