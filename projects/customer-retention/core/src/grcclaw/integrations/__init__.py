"""
GRC_Claw Integration & Connector Framework

Unified integration system for connecting GRC_Claw with external systems.
Provides connector SDK, integration engine, data transformation, monitoring,
and pre-built integration templates.
"""

from .engine import (
    IntegrationOrchestrator,
    IntegrationPipeline,
    IntegrationScheduler,
    IntegrationState,
    PipelineResult,
    PipelineStep,
)
from .monitoring import (
    AlertManager,
    AlertSeverity,
    HealthChecker,
    HealthStatus,
    IntegrationMetrics,
    IntegrationTracer,
)
from .sdk import (
    APIKeyAuth,
    AuthStrategy,
    BaseConnector,
    BasicAuth,
    BearerAuth,
    ConnectorCapability,
    ConnectorConfig,
    ConnectorRegistry,
    ConnectorStatus,
    OAuth2Auth,
)
from .templates import (
    DatabaseConnector,
    FileTransferConnector,
    IntegrationTemplate,
    RESTAPIConnector,
    WebhookConnector,
)
from .transformation import (
    DataNormalizer,
    DataValidator,
    FieldTransformer,
    SchemaMapper,
    TransformationResult,
    TransformationRule,
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
