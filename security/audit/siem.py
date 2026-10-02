"""Kafka to SIEM pipeline for agentic AI marketing security layer.

Provides real-time audit event streaming to Kafka, SIEM integration,
event enrichment, and alert forwarding.
"""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from audit.events import AuditEvent, AuditSeverity


class SIEMError(Exception):
    """Base exception for SIEM errors."""


class KafkaConnectionError(SIEMError):
    """Raised when Kafka connection fails."""


class SIEMConnectionError(SIEMError):
    """Raised when SIEM connection fails."""


class EventProcessingError(SIEMError):
    """Raised when event processing fails."""


class SIEMProvider(str, Enum):
    """Supported SIEM providers."""

    SPLUNK = "splunk"
    ELASTIC = "elastic"
    DATADOG = "datadog"
    SENTINEL = "sentinel"
    CHRONICLE = "chronicle"
    QRADAR = "qradar"
    ARCSIGHT = "arcsight"
    CUSTOM = "custom"


class KafkaTopic(str, Enum):
    """Kafka topic names."""

    AUDIT_EVENTS = "security.audit.events"
    SECURITY_ALERTS = "security.alerts"
    AGENT_ACTIONS = "security.agent.actions"
    COMPLIANCE_EVENTS = "security.compliance.events"
    THREAT_EVENTS = "security.threat.events"


@dataclass(frozen=True)
class KafkaConfig:
    """Kafka configuration."""

    bootstrap_servers: str = "localhost:9092"
    security_protocol: str = "SASL_SSL"
    sasl_mechanism: str = "SCRAM-SHA-512"
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    ssl_cafile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    client_id: str = "grc-security-pipeline"
    acks: str = "all"
    retries: int = 3
    linger_ms: int = 10
    batch_size: int = 16384
    compression_type: str = "snappy"


@dataclass(frozen=True)
class SIEMConfig:
    """SIEM configuration."""

    provider: SIEMProvider
    endpoint: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    index: str = "security"
    batch_size: int = 100
    flush_interval: float = 5.0
    timeout: float = 30.0
    verify_ssl: bool = True
    custom_headers: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EnrichedEvent:
    """Enriched audit event."""

    original_event: AuditEvent
    enrichment: Dict[str, Any] = field(default_factory=dict)
    risk_score: float = 0.0
    threat_indicators: List[str] = field(default_factory=list)
    geo_location: Optional[Dict[str, Any]] = None
    asset_criticality: str = "medium"
    compliance_tags: List[str] = field(default_factory=list)


class EventEnricher:
    """Enriches audit events with additional context."""

    def __init__(self) -> None:
        self._threat_intel: Dict[str, Any] = {}
        self._asset_inventory: Dict[str, Any] = {}
        self._geo_db: Dict[str, Any] = {}

    def enrich(self, event: AuditEvent) -> EnrichedEvent:
        """Enrich an audit event."""
        enrichment: Dict[str, Any] = {}
        risk_score = 0.0
        threat_indicators: List[str] = []

        # Enrich with actor context
        if event.actor:
            enrichment["actor_risk_score"] = self._calculate_actor_risk(event.actor)
            enrichment["actor_historical_behavior"] = self._get_actor_history(event.actor.id)
            risk_score += enrichment["actor_risk_score"] * 0.3

        # Enrich with resource context
        if event.resource:
            enrichment["resource_criticality"] = self._get_resource_criticality(event.resource.id)
            enrichment["resource_exposure"] = self._get_resource_exposure(event.resource.id)

        # Enrich with action context
        if event.action:
            enrichment["action_risk"] = self._calculate_action_risk(event.action)
            risk_score += enrichment["action_risk"] * 0.4

        # Check for threat indicators
        threat_indicators = self._check_threat_indicators(event)
        risk_score += len(threat_indicators) * 0.1

        # Cap risk score
        risk_score = min(risk_score, 1.0)

        return EnrichedEvent(
            original_event=event,
            enrichment=enrichment,
            risk_score=risk_score,
            threat_indicators=threat_indicators,
            compliance_tags=event.compliance,
        )

    def _calculate_actor_risk(self, actor: Any) -> float:
        """Calculate risk score for an actor."""
        # In production, this would query a risk engine
        return 0.0

    def _get_actor_history(self, actor_id: str) -> Dict[str, Any]:
        """Get historical behavior for an actor."""
        return {}

    def _get_resource_criticality(self, resource_id: str) -> str:
        """Get criticality of a resource."""
        return "medium"

    def _get_resource_exposure(self, resource_id: str) -> str:
        """Get exposure level of a resource."""
        return "internal"

    def _calculate_action_risk(self, action: Any) -> float:
        """Calculate risk score for an action."""
        return 0.0

    def _check_threat_indicators(self, event: AuditEvent) -> List[str]:
        """Check for threat indicators in the event."""
        indicators: List[str] = []
        # In production, this would check against threat intelligence feeds
        return indicators


class KafkaProducer:
    """Kafka producer for security events."""

    def __init__(self, config: KafkaConfig) -> None:
        self.config = config
        self._producer: Optional[Any] = None

    async def connect(self) -> None:
        """Connect to Kafka."""
        try:
            from confluent_kafka import Producer

            conf = {
                "bootstrap.servers": self.config.bootstrap_servers,
                "client.id": self.config.client_id,
                "acks": self.config.acks,
                "retries": self.config.retries,
                "linger.ms": self.config.linger_ms,
                "batch.size": self.config.batch_size,
                "compression.type": self.config.compression_type,
            }

            if self.config.security_protocol == "SASL_SSL":
                conf["security.protocol"] = self.config.security_protocol
                conf["sasl.mechanism"] = self.config.sasl_mechanism
                if self.config.sasl_username:
                    conf["sasl.username"] = self.config.sasl_username
                if self.config.sasl_password:
                    conf["sasl.password"] = self.config.sasl_password

            self._producer = Producer(conf)
        except ImportError:
            raise KafkaConnectionError(
                "confluent-kafka library not installed. "
                "Install with: pip install confluent-kafka"
            )
        except Exception as exc:
            raise KafkaConnectionError(f"Failed to connect to Kafka: {exc}") from exc

    async def send_event(
        self,
        event: AuditEvent,
        topic: KafkaTopic = KafkaTopic.AUDIT_EVENTS,
        key: Optional[str] = None,
    ) -> None:
        """Send an event to Kafka."""
        if not self._producer:
            raise KafkaConnectionError("Producer not connected")

        try:
            self._producer.produce(
                topic=topic.value,
                key=key or event.id,
                value=event.to_json(),
                callback=self._delivery_callback,
            )
            self._producer.poll(0)
        except Exception as exc:
            raise EventProcessingError(f"Failed to send event: {exc}") from exc

    async def flush(self) -> None:
        """Flush pending messages."""
        if self._producer:
            self._producer.flush()

    @staticmethod
    def _delivery_callback(err: Optional[Any], msg: Any) -> None:
        """Delivery callback for Kafka producer."""
        if err:
            print(f"Message delivery failed: {err}")


class KafkaConsumer:
    """Kafka consumer for security events."""

    def __init__(
        self,
        config: KafkaConfig,
        group_id: str = "security-pipeline",
    ) -> None:
        self.config = config
        self.group_id = group_id
        self._consumer: Optional[Any] = None

    async def connect(self) -> None:
        """Connect to Kafka as consumer."""
        try:
            from confluent_kafka import Consumer

            conf = {
                "bootstrap.servers": self.config.bootstrap_servers,
                "group.id": self.group_id,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": True,
            }

            if self.config.security_protocol == "SASL_SSL":
                conf["security.protocol"] = self.config.security_protocol
                conf["sasl.mechanism"] = self.config.sasl_mechanism
                if self.config.sasl_username:
                    conf["sasl.username"] = self.config.sasl_username
                if self.config.sasl_password:
                    conf["sasl.password"] = self.config.sasl_password

            self._consumer = Consumer(conf)
        except ImportError:
            raise KafkaConnectionError("confluent-kafka library not installed")
        except Exception as exc:
            raise KafkaConnectionError(f"Failed to connect to Kafka: {exc}") from exc

    async def subscribe(self, topics: List[KafkaTopic]) -> None:
        """Subscribe to topics."""
        if not self._consumer:
            raise KafkaConnectionError("Consumer not connected")
        self._consumer.subscribe([t.value for t in topics])

    async def consume(self, timeout: float = 1.0) -> Optional[AuditEvent]:
        """Consume a single event."""
        if not self._consumer:
            raise KafkaConnectionError("Consumer not connected")

        msg = self._consumer.poll(timeout)
        if msg is None:
            return None
        if msg.error():
            raise EventProcessingError(f"Consumer error: {msg.error()}")

        try:
            data = json.loads(msg.value().decode("utf-8"))
            return AuditEvent.from_dict(data)
        except Exception as exc:
            raise EventProcessingError(f"Failed to parse event: {exc}") from exc


class SIEMForwarder:
    """Forwards security events to SIEM."""

    def __init__(self, config: SIEMConfig) -> None:
        self.config = config
        self._session: Optional[Any] = None

    async def connect(self) -> None:
        """Connect to SIEM."""
        import httpx

        self._session = httpx.AsyncClient(
            timeout=self.config.timeout,
            verify=self.config.verify_ssl,
            headers=self._get_headers(),
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        headers.update(self.config.custom_headers)
        return headers

    async def forward_event(self, event: EnrichedEvent) -> None:
        """Forward an event to SIEM."""
        if not self._session:
            raise SIEMConnectionError("SIEM not connected")

        try:
            response = await self._session.post(
                self.config.endpoint,
                json=self._format_event(event),
            )
            response.raise_for_status()
        except Exception as exc:
            raise SIEMConnectionError(f"Failed to forward event: {exc}") from exc

    async def forward_batch(self, events: List[EnrichedEvent]) -> None:
        """Forward a batch of events to SIEM."""
        if not self._session:
            raise SIEMConnectionError("SIEM not connected")

        try:
            response = await self._session.post(
                self.config.endpoint,
                json=[self._format_event(e) for e in events],
            )
            response.raise_for_status()
        except Exception as exc:
            raise SIEMConnectionError(f"Failed to forward batch: {exc}") from exc

    def _format_event(self, event: EnrichedEvent) -> Dict[str, Any]:
        """Format event for SIEM."""
        base = event.original_event.to_dict()
        base["enrichment"] = event.enrichment
        base["risk_score"] = event.risk_score
        base["threat_indicators"] = event.threat_indicators
        base["asset_criticality"] = event.asset_criticality
        return base

    async def close(self) -> None:
        """Close SIEM connection."""
        if self._session:
            await self._session.aclose()


class SecurityPipeline:
    """Main security event pipeline."""

    def __init__(
        self,
        kafka_config: KafkaConfig,
        siem_config: SIEMConfig,
    ) -> None:
        self.kafka_config = kafka_config
        self.siem_config = siem_config
        self.enricher = EventEnricher()
        self.producer = KafkaProducer(kafka_config)
        self.consumer = KafkaConsumer(kafka_config)
        self.siem = SIEMForwarder(siem_config)
        self._running = False

    async def start(self) -> None:
        """Start the pipeline."""
        await self.producer.connect()
        await self.consumer.connect()
        await self.siem.connect()
        await self.consumer.subscribe([
            KafkaTopic.AUDIT_EVENTS,
            KafkaTopic.SECURITY_ALERTS,
            KafkaTopic.THREAT_EVENTS,
        ])
        self._running = True

    async def stop(self) -> None:
        """Stop the pipeline."""
        self._running = False
        await self.producer.flush()
        await self.siem.close()

    async def process_event(self, event: AuditEvent) -> EnrichedEvent:
        """Process a single event through the pipeline."""
        # Enrich the event
        enriched = self.enricher.enrich(event)

        # Send to Kafka
        await self.producer.send_event(event)

        # Forward to SIEM if high risk
        if enriched.risk_score > 0.7:
            await self.siem.forward_event(enriched)

        return enriched

    async def run(self) -> None:
        """Run the pipeline."""
        await self.start()
        try:
            while self._running:
                event = await self.consumer.consume(timeout=1.0)
                if event:
                    await self.process_event(event)
        except asyncio.CancelledError:
            pass
        finally:
            await self.stop()
