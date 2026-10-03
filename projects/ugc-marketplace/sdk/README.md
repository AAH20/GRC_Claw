# UGC Marketplace Python SDK

A production-grade Python client for the [UGC Marketplace](https://ugc-marketplace.example.com) API. Built with type hints, Pydantic models, automatic token refresh, and configurable retries.

## Features

- **OAuth2 Authentication** — Client credentials flow with automatic token refresh
- **Full CRUD Support** — Users, Categories, Products, Orders, and Reviews
- **Type-Safe** — Pydantic models for all request/response schemas
- **Automatic Retries** — Exponential backoff for transient failures (5xx, timeouts)
- **Rate Limit Handling** — Respects `Retry-After` headers with automatic retry
- **Pagination** — Generic paginated response wrapper for list endpoints
- **Context Manager** — Use with `with` statement for automatic resource cleanup

## Installation

```bash
pip install ugc-marketplace-sdk
```

Or install from source:

```bash
cd ugc-marketplace/sdk
pip install -e .
```

## Quick Start

```python
from ugc_marketplace import UGCMarketplaceClient

# Initialize with OAuth2 credentials
client = UGCMarketplaceClient(
    base_url="https://api.ugc-marketplace.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
)

# List products
products = client.list_products(page=1, per_page=20)
for product in products.items:
    print(f"{product.title} — ${product.price}")

# Get a specific product
product = client.get_product("prod_123")
print(product.description)

# Create an order
from ugc_marketplace import CreateOrderRequest
order = client.create_order(CreateOrderRequest(product_id="prod_123", quantity=2))
print(f"Order created: {order.id}")
```

## Authentication

The SDK uses OAuth2 client credentials flow. Provide your `client_id` and `client_secret` during initialization:

```python
client = UGCMarketplaceClient(
    base_url="https://api.ugc-marketplace.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
)
```

Tokens are automatically obtained and refreshed before expiry. You can also provide a pre-existing token:

```python
client = UGCMarketplaceClient(
    base_url="https://api.ugc-marketplace.example.com",
    access_token="your-existing-token",
)
```

## Usage Examples

### Context Manager (Recommended)

```python
from ugc_marketplace import UGCMarketplaceClient

with UGCMarketplaceClient(
    base_url="https://api.ugc-marketplace.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
) as client:
    user = client.get_current_user()
    print(f"Logged in as {user.username}")
```

### Users

```python
# Get current user profile
me = client.get_current_user()
print(me.email)

# Get a specific user
user = client.get_user("user_456")
print(user.bio)
```

### Categories

```python
# List all categories
categories = client.list_categories(page=1, per_page=50)
for cat in categories.items:
    print(f"{cat.name} ({cat.slug})")

# Get a specific category
category = client.get_category("cat_789")
```

### Products

```python
# List products with filters
products = client.list_products(
    page=1,
    per_page=20,
    category_id="cat_electronics",
    min_price=10.0,
    max_price=500.0,
    search="wireless headphones",
)

# Check pagination
print(f"Page {products.page}, showing {len(products.items)} of {products.total}")
if products.has_next:
    next_page = client.list_products(page=2, per_page=20)

# Get a single product
product = client.get_product("prod_abc123")

# Create a new product
from ugc_marketplace import Product
from datetime import datetime

new_product = Product(
    seller_id="user_456",
    title="Handmade Leather Wallet",
    description="Premium full-grain leather wallet",
    price=49.99,
    category_id="cat_accessories",
    images=["https://example.com/wallet1.jpg"],
    tags=["leather", "handmade", "accessories"],
    created_at=datetime.now(),
    updated_at=datetime.now(),
)
created = client.create_product(new_product)

# Update a product
from ugc_marketplace import UpdateProductRequest
updated = client.update_product(
    "prod_abc123",
    UpdateProductRequest(price=39.99, status="active"),
)

# Delete a product
client.delete_product("prod_abc123")
```

### Orders

```python
# List orders
orders = client.list_orders(page=1, per_page=20, status="pending")

# Get a specific order
order = client.get_order("order_xyz789")

# Create an order
from ugc_marketplace import CreateOrderRequest
order = client.create_order(CreateOrderRequest(product_id="prod_abc123", quantity=1))

# Cancel an order
cancelled = client.cancel_order("order_xyz789")
```

### Reviews

```python
# List reviews for a product
reviews = client.list_reviews(product_id="prod_abc123", page=1, per_page=10)
avg_rating = sum(r.rating for r in reviews.items) / len(reviews.items) if reviews.items else 0

# Get a specific review
review = client.get_review("rev_111")

# Create a review
from ugc_marketplace import CreateReviewRequest
review = client.create_review(
    CreateReviewRequest(
        product_id="prod_abc123",
        rating=5,
        title="Excellent quality",
        body="Exceeded my expectations. Highly recommended!",
    )
)

# Delete a review
client.delete_review("rev_111")
```

## Error Handling

All SDK errors inherit from `UGCMarketplaceError`:

```python
from ugc_marketplace import (
    UGCMarketplaceClient,
    UGCAuthenticationError,
    UGCNotFoundError,
    UGCRateLimitError,
    UGCValidationError,
    UGCServerError,
)

client = UGCMarketplaceClient(
    base_url="https://api.ugc-marketplace.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
)

try:
    product = client.get_product("prod_nonexistent")
except UGCNotFoundError:
    print("Product not found")
except UGCAuthenticationError:
    print("Authentication failed — check your credentials")
except UGCRateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
except UGCValidationError as e:
    print(f"Validation failed: {e.errors}")
except UGCServerError:
    print("Server error — please try again later")
except UGCMarketplaceError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
```

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_url` | `https://api.ugc-marketplace.example.com` | API base URL |
| `client_id` | `None` | OAuth2 client ID |
| `client_secret` | `None` | OAuth2 client secret |
| `access_token` | `None` | Pre-existing access token |
| `timeout` | `30.0` | Request timeout in seconds |
| `max_retries` | `3` | Maximum retry attempts |
| `retry_delay` | `1.0` | Initial retry delay (exponential backoff) |

## API Reference

### `UGCMarketplaceClient`

#### Authentication
- `authenticate() -> TokenResponse` — Obtain an access token
- `close() -> None` — Close the HTTP client

#### Users
- `get_current_user() -> User`
- `get_user(user_id: str) -> User`

#### Categories
- `list_categories(page, per_page) -> PaginatedResponse[Category]`
- `get_category(category_id: str) -> Category`

#### Products
- `list_products(page, per_page, category_id?, seller_id?, status?, min_price?, max_price?, search?) -> PaginatedResponse[Product]`
- `get_product(product_id: str) -> Product`
- `create_product(product: Product) -> Product`
- `update_product(product_id: str, updates: UpdateProductRequest) -> Product`
- `delete_product(product_id: str) -> None`

#### Orders
- `list_orders(page, per_page, status?, buyer_id?, seller_id?) -> PaginatedResponse[Order]`
- `get_order(order_id: str) -> Order`
- `create_order(request: CreateOrderRequest) -> Order`
- `cancel_order(order_id: str) -> Order`

#### Reviews
- `list_reviews(page, per_page, product_id?, reviewer_id?) -> PaginatedResponse[Review]`
- `get_review(review_id: str) -> Review`
- `create_review(request: CreateReviewRequest) -> Review`
- `delete_review(review_id: str) -> None`

## Requirements

- Python 3.10+
- `httpx` >= 0.27
- `pydantic` >= 2.0

## License

MIT
