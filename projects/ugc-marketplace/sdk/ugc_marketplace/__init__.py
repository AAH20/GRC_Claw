"""UGC Marketplace Python SDK.

A production-grade Python client for the UGC Marketplace API.
"""

from .cache import AsyncRedisCache, RedisCache
from .client import UGCMarketplaceClient
from .exceptions import (UGCAuthenticationError, UGCMarketplaceError,
                         UGCNotFoundError, UGCRateLimitError, UGCServerError,
                         UGCValidationError)
from .logging_config import JsonFormatter, setup_logging
from .models import (Category, CreateOrderRequest, CreateReviewRequest, Order,
                     PaginatedResponse, Product, Review, UpdateProductRequest,
                     User)
from .rate_limiter import AsyncTokenBucketRateLimiter, TokenBucketRateLimiter

__version__ = "2.0.0"
__author__ = "UGC Marketplace"
__all__ = [
    "UGCMarketplaceClient",
    "UGCMarketplaceError",
    "UGCAuthenticationError",
    "UGCNotFoundError",
    "UGCRateLimitError",
    "UGCValidationError",
    "UGCServerError",
    "User",
    "Product",
    "Order",
    "Review",
    "Category",
    "PaginatedResponse",
    "CreateOrderRequest",
    "CreateReviewRequest",
    "UpdateProductRequest",
    "TokenBucketRateLimiter",
    "AsyncTokenBucketRateLimiter",
    "RedisCache",
    "AsyncRedisCache",
    "setup_logging",
    "JsonFormatter",
]
