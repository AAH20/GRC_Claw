"""Kafka producer integration for fraud detection."""

from __future__ import annotations

import json
from typing import Any

from ugc_marketplace.config import get_settings
from ugc_marketplace.config.logging_config import get_logger

logger = get_logger(__name__)

_producer: Any = None


async def get_kafka_producer() -> Any:
    """Get or create Kafka producer.

    Returns:
        Kafka producer instance.
    """
    global _producer
    if _producer is None:
        try:
            from aiokafka import AIOKafkaProducer

            settings = get_settings()
            _producer = AIOKafkaProducer(
                bootstrap_servers=settings.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await _producer.start()
            logger.info("Kafka producer started")
        except ImportError:
            logger.warning("aiokafka not installed, Kafka integration disabled")
            return None
    return _producer


async def send_alert(alert: dict[str, Any]) -> None:
    """Send fraud alert to Kafka.

    Args:
        alert: Alert data to send.
    """
    producer = await get_kafka_producer()
    if producer is not None:
        settings = get_settings()
        await producer.send(settings.kafka_topic_alerts, alert)
        logger.info("Alert sent to Kafka", alert_id=alert.get("alert_id"))


async def close_kafka() -> None:
    """Close Kafka producer."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None
        logger.info("Kafka producer stopped")
