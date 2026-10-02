"""Integrations module."""

from fraud_detection.integrations.database import close_db, get_db_session, init_db
from fraud_detection.integrations.kafka_producer import close_kafka, get_kafka_producer, send_alert
from fraud_detection.integrations.redis_client import (
    cache_transaction,
    close_redis,
    get_cached_transaction,
    get_redis_client,
)

__all__ = [
    "cache_transaction",
    "close_db",
    "close_kafka",
    "close_redis",
    "get_cached_transaction",
    "get_db_session",
    "get_kafka_producer",
    "get_redis_client",
    "init_db",
    "send_alert",
]
