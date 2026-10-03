"""UGC Marketplace Python SDK.

A production-grade Python client for the UGC Marketplace API.
"""

from .client import UGCMarketplaceClient
from .exceptions import (
    UGCMarketplaceError,
    UGCAuthenticationError,
    UGCNotFoundError,
    UGCRateLimitError,
    UGCValidationError,
    UGCServerError,
)
from .models import (
    User,
    Product,
    Order,
    Review,
    Category,
    PaginatedResponse,
    CreateOrderRequest,
    CreateReviewRequest,
    UpdateProductRequest,
)

__version__ = "1.0.0"
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
]
