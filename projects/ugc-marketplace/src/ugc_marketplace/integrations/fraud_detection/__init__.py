"""Integration modules for fraud detection."""

from ugc_marketplace.integrations.fraud_detection.database import (
    close_db, get_db_session, init_db)
from ugc_marketplace.integrations.fraud_detection.kafka_producer import (
    close_kafka, get_kafka_producer, send_alert)
from ugc_marketplace.integrations.fraud_detection.redis_client import (
    cache_transaction, close_redis, get_cached_transaction, get_redis_client)

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
