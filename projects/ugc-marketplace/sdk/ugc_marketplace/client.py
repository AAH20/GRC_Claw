"""UGC Marketplace API client with authentication, async support, retry logic, rate limiting, caching, and structured logging."""

from __future__ import annotations

import asyncio
import time
from typing import Any, TypeVar

import httpx
from pydantic import BaseModel

from .cache import AsyncRedisCache, RedisCache
from .exceptions import (UGCAuthenticationError, UGCMarketplaceError,
                         UGCNotFoundError, UGCRateLimitError, UGCServerError,
                         UGCValidationError)
from .logging_config import setup_logging
from .models import (Category, CreateOrderRequest, CreateReviewRequest, Order,
                     PaginatedResponse, Product, Review, TokenResponse,
                     UpdateProductRequest, User)
from .rate_limiter import AsyncTokenBucketRateLimiter, TokenBucketRateLimiter

T = TypeVar("T", bound=BaseModel)


class UGCMarketplaceClient:
    """Production-grade client for the UGC Marketplace API.

    Supports OAuth2 token-based authentication, automatic token refresh,
    configurable retries, rate limiting, caching, structured logging,
    and full CRUD operations for all resources.

    Usage:
        >>> client = UGCMarketplaceClient(
        ...     base_url="https://api.ugc-marketplace.example.com",
        ...     client_id="your-client-id",
        ...     client_secret="your-client-secret",
        ... )
        >>> products = client.list_products(page=1, per_page=20)
        >>> for product in products.items:
        ...     print(product.title)
    """

    DEFAULT_BASE_URL = "https://api.ugc-marketplace.example.com"
    DEFAULT_TIMEOUT = 30.0
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0
    DEFAULT_RATE_LIMIT = 10.0
    DEFAULT_RATE_CAPACITY = 10
    DEFAULT_CACHE_TTL = 300

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        client_id: str | None = None,
        client_secret: str | None = None,
        access_token: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        rate_limit: float = DEFAULT_RATE_LIMIT,
        rate_capacity: int = DEFAULT_RATE_CAPACITY,
        cache_ttl: int = DEFAULT_CACHE_TTL,
        redis_url: str = "redis://localhost:6379",
        enable_cache: bool = True,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the UGC Marketplace client.

        Args:
            base_url: The base URL of the UGC Marketplace API.
            client_id: OAuth2 client ID for token-based authentication.
            client_secret: OAuth2 client secret for token-based authentication.
            access_token: Pre-existing access token (skips OAuth2 flow).
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts for failed requests.
            retry_delay: Initial delay between retries in seconds (exponential backoff).
            rate_limit: Tokens per second for rate limiting.
            rate_capacity: Maximum token bucket capacity.
            cache_ttl: Cache TTL in seconds.
            redis_url: Redis connection URL for caching.
            enable_cache: Whether to enable response caching.
            enable_logging: Whether to enable structured logging.
        """
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: str | None = access_token
        self._refresh_token: str | None = None
        self._token_expires_at: float = 0.0
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self._rate_limiter = TokenBucketRateLimiter(
            rate=rate_limit, capacity=rate_capacity
        )
        self._async_rate_limiter = AsyncTokenBucketRateLimiter(
            rate=rate_limit, capacity=rate_capacity
        )

        self._cache: RedisCache | None = None
        self._async_cache: AsyncRedisCache | None = None
        if enable_cache:
            self._cache = RedisCache(redis_url=redis_url, ttl=cache_ttl)
            self._async_cache = AsyncRedisCache(redis_url=redis_url, ttl=cache_ttl)

        self._logger = setup_logging() if enable_logging else None

        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "ugc-marketplace-python-sdk/2.0.0",
            },
        )
        self._async_client: httpx.AsyncClient | None = None

    def __enter__(self) -> UGCMarketplaceClient:
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()

    async def __aenter__(self) -> UGCMarketplaceClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()

    def close(self) -> None:
        """Close the underlying HTTP client and release resources."""
        self._client.close()

    async def aclose(self) -> None:
        """Close the async HTTP client and release resources."""
        if self._async_client:
            await self._async_client.aclose()

    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "ugc-marketplace-python-sdk/2.0.0",
                },
            )
        return self._async_client

    # ── Authentication ──────────────────────────────────────────────────

    def authenticate(self) -> TokenResponse:
        """Authenticate with the API using client credentials flow.

        Returns:
            TokenResponse containing the access token and metadata.

        Raises:
            UGCAuthenticationError: If authentication fails.
            UGCMarketplaceError: For other request errors.
        """
        if not self.client_id or not self.client_secret:
            raise UGCAuthenticationError(
                "client_id and client_secret are required for authentication"
            )

        response = self._client.post(
            "/v1/auth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )

        if response.status_code == 200:
            token_data = TokenResponse.model_validate(response.json())
            self._access_token = token_data.access_token
            self._refresh_token = token_data.refresh_token
            self._token_expires_at = time.time() + token_data.expires_in
            if self._logger:
                self._logger.info("Authentication successful")
            return token_data
        self._handle_error_response(response)
        raise UGCAuthenticationError("Authentication failed with unexpected response")

    async def aauthenticate(self) -> TokenResponse:
        """Async authenticate with the API using client credentials flow.

        Returns:
            TokenResponse containing the access token and metadata.

        Raises:
            UGCAuthenticationError: If authentication fails.
            UGCMarketplaceError: For other request errors.
        """
        if not self.client_id or not self.client_secret:
            raise UGCAuthenticationError(
                "client_id and client_secret are required for authentication"
            )

        client = self._get_async_client()
        response = await client.post(
            "/v1/auth/token",
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
        )

        if response.status_code == 200:
            token_data = TokenResponse.model_validate(response.json())
            self._access_token = token_data.access_token
            self._refresh_token = token_data.refresh_token
            self._token_expires_at = time.time() + token_data.expires_in
            if self._logger:
                self._logger.info("Async authentication successful")
            return token_data
        self._handle_error_response(response)
        raise UGCAuthenticationError("Authentication failed with unexpected response")

    def _ensure_authenticated(self) -> None:
        """Ensure a valid access token is available, refreshing if necessary."""
        if not self._access_token:
            self.authenticate()
        elif time.time() >= self._token_expires_at - 60:
            self._refresh_access_token()

    async def _aensure_authenticated(self) -> None:
        """Async ensure a valid access token is available, refreshing if necessary."""
        if not self._access_token:
            await self.aauthenticate()
        elif time.time() >= self._token_expires_at - 60:
            await self._arefresh_access_token()

    def _refresh_access_token(self) -> None:
        """Refresh the access token using the refresh token."""
        if not self._refresh_token:
            self.authenticate()
            return

        response = self._client.post(
            "/v1/auth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
        )

        if response.status_code == 200:
            token_data = TokenResponse.model_validate(response.json())
            self._access_token = token_data.access_token
            self._refresh_token = token_data.refresh_token
            self._token_expires_at = time.time() + token_data.expires_in
        else:
            self.authenticate()

    async def _arefresh_access_token(self) -> None:
        """Async refresh the access token using the refresh token."""
        if not self._refresh_token:
            await self.aauthenticate()
            return

        client = self._get_async_client()
        response = await client.post(
            "/v1/auth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._refresh_token,
            },
        )

        if response.status_code == 200:
            token_data = TokenResponse.model_validate(response.json())
            self._access_token = token_data.access_token
            self._refresh_token = token_data.refresh_token
            self._token_expires_at = time.time() + token_data.expires_in
        else:
            await self.aauthenticate()

    def _get_auth_headers(self) -> dict[str, str]:
        """Get headers with authentication token.

        Returns:
            Dictionary of HTTP headers including Authorization.

        Raises:
            UGCAuthenticationError: If no token is available and authentication fails.
        """
        self._ensure_authenticated()
        return {"Authorization": f"Bearer {self._access_token}"}

    async def _aget_auth_headers(self) -> dict[str, str]:
        """Async get headers with authentication token.

        Returns:
            Dictionary of HTTP headers including Authorization.

        Raises:
            UGCAuthenticationError: If no token is available and authentication fails.
        """
        await self._aensure_authenticated()
        return {"Authorization": f"Bearer {self._access_token}"}

    # ── HTTP Helpers ────────────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        auth: bool = True,
        use_cache: bool = False,
    ) -> httpx.Response:
        """Make an HTTP request with retry logic, rate limiting, and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API endpoint path.
            params: Query parameters.
            json_data: JSON request body.
            auth: Whether to include authentication headers.
            use_cache: Whether to use response caching.

        Returns:
            The HTTP response object.

        Raises:
            UGCMarketplaceError: On request failure after all retries.
        """
        cache_key = f"{method}:{path}:{str(params)}"
        if use_cache and method == "GET" and self._cache:
            cached = self._cache.get(cache_key)
            if cached is not None:
                if self._logger:
                    self._logger.debug(f"Cache hit for {path}")
                return httpx.Response(200, json=cached)

        headers = self._get_auth_headers() if auth else {}
        last_exception: Exception | None = None

        for attempt in range(self.max_retries):
            wait_time = self._rate_limiter.wait_time()
            if wait_time > 0:
                time.sleep(wait_time)
            self._rate_limiter.acquire()

            try:
                response = self._client.request(
                    method,
                    path,
                    params=params,
                    json=json_data,
                    headers=headers,
                )

                if response.status_code < 400:
                    if use_cache and method == "GET" and self._cache:
                        try:
                            self._cache.set(cache_key, response.json())
                        except Exception:
                            pass
                    return response

                if response.status_code == 429:
                    retry_after = int(
                        response.headers.get("Retry-After", self.retry_delay)
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(retry_after)
                        continue
                    self._handle_error_response(response)

                if 400 <= response.status_code < 500:
                    self._handle_error_response(response)

                if response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2**attempt)
                        if self._logger:
                            self._logger.warning(
                                f"Server error {response.status_code}, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                            )
                        time.sleep(delay)
                        continue
                    self._handle_error_response(response)

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    if self._logger:
                        self._logger.warning(
                            f"Timeout, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                    time.sleep(delay)
                    continue
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    if self._logger:
                        self._logger.warning(
                            f"Request error: {e}, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                    time.sleep(delay)
                    continue

        raise UGCMarketplaceError(
            f"Request failed after {self.max_retries} retries: {last_exception}"
        )

    async def _arequest(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        auth: bool = True,
        use_cache: bool = False,
    ) -> httpx.Response:
        """Async make an HTTP request with retry logic, rate limiting, and error handling.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE).
            path: API endpoint path.
            params: Query parameters.
            json_data: JSON request body.
            auth: Whether to include authentication headers.
            use_cache: Whether to use response caching.

        Returns:
            The HTTP response object.

        Raises:
            UGCMarketplaceError: On request failure after all retries.
        """
        cache_key = f"{method}:{path}:{str(params)}"
        if use_cache and method == "GET" and self._async_cache:
            cached = await self._async_cache.get(cache_key)
            if cached is not None:
                if self._logger:
                    self._logger.debug(f"Async cache hit for {path}")
                return httpx.Response(200, json=cached)

        headers = await self._aget_auth_headers() if auth else {}
        last_exception: Exception | None = None
        client = self._get_async_client()

        for attempt in range(self.max_retries):
            wait_time = await self._async_rate_limiter.wait_time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            await self._async_rate_limiter.acquire()

            try:
                response = await client.request(
                    method,
                    path,
                    params=params,
                    json=json_data,
                    headers=headers,
                )

                if response.status_code < 400:
                    if use_cache and method == "GET" and self._async_cache:
                        try:
                            await self._async_cache.set(cache_key, response.json())
                        except Exception:
                            pass
                    return response

                if response.status_code == 429:
                    retry_after = int(
                        response.headers.get("Retry-After", self.retry_delay)
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(retry_after)
                        continue
                    self._handle_error_response(response)

                if 400 <= response.status_code < 500:
                    self._handle_error_response(response)

                if response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2**attempt)
                        if self._logger:
                            self._logger.warning(
                                f"Async server error {response.status_code}, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                            )
                        await asyncio.sleep(delay)
                        continue
                    self._handle_error_response(response)

            except httpx.TimeoutException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    if self._logger:
                        self._logger.warning(
                            f"Async timeout, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                    await asyncio.sleep(delay)
                    continue
            except httpx.RequestError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2**attempt)
                    if self._logger:
                        self._logger.warning(
                            f"Async request error: {e}, retrying in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                        )
                    await asyncio.sleep(delay)
                    continue

        raise UGCMarketplaceError(
            f"Async request failed after {self.max_retries} retries: {last_exception}"
        )

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Raise the appropriate exception based on the error response.

        Args:
            response: The HTTP error response.

        Raises:
            UGCAuthenticationError: For 401 responses.
            UGCNotFoundError: For 404 responses.
            UGCRateLimitError: For 429 responses.
            UGCValidationError: For 422 responses.
            UGCServerError: For 5xx responses.
            UGCMarketplaceError: For other error responses.
        """
        try:
            body = response.json()
        except Exception:
            body = None

        message = (
            body.get("message", body.get("error", response.text))
            if body
            else response.text
        )

        if self._logger:
            self._logger.error(f"Error {response.status_code}: {message}")

        if response.status_code == 401:
            raise UGCAuthenticationError(str(message), response=body)
        elif response.status_code == 404:
            raise UGCNotFoundError(str(message), response=body)
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 0)) or None
            raise UGCRateLimitError(
                str(message), retry_after=retry_after, response=body
            )
        elif response.status_code == 422:
            errors = body.get("errors", {}) if body else None
            raise UGCValidationError(str(message), errors=errors, response=body)
        elif response.status_code >= 500:
            raise UGCServerError(str(message), response=body)
        else:
            raise UGCMarketplaceError(
                str(message), status_code=response.status_code, response=body
            )

    def _parse_response(self, response: httpx.Response, model_class: type[T]) -> T:
        """Parse a JSON response into a Pydantic model.

        Args:
            response: The HTTP response.
            model_class: The Pydantic model class to parse into.

        Returns:
            An instance of the specified model class.
        """
        return model_class.model_validate(response.json())

    def _parse_paginated(
        self, response: httpx.Response, item_class: type[T]
    ) -> PaginatedResponse[T]:
        """Parse a paginated JSON response.

        Args:
            response: The HTTP response.
            item_class: The Pydantic model class for individual items.

        Returns:
            A PaginatedResponse containing the parsed items.
        """
        data = response.json()
        items = [item_class.model_validate(item) for item in data.get("items", [])]
        return PaginatedResponse[item_class](
            items=items,
            total=data.get("total", len(items)),
            page=data.get("page", 1),
            per_page=data.get("per_page", len(items)),
            has_next=data.get("has_next", False),
            has_prev=data.get("has_prev", False),
        )

    # ── User Endpoints ──────────────────────────────────────────────────

    def get_current_user(self) -> User:
        """Get the currently authenticated user's profile.

        Returns:
            The current user's profile.
        """
        response = self._request("GET", "/v1/users/me")
        return self._parse_response(response, User)

    async def aget_current_user(self) -> User:
        """Async get the currently authenticated user's profile.

        Returns:
            The current user's profile.
        """
        response = await self._arequest("GET", "/v1/users/me")
        return self._parse_response(response, User)

    def get_user(self, user_id: str) -> User:
        """Get a user by ID.

        Args:
            user_id: The unique user identifier.

        Returns:
            The requested user.
        """
        response = self._request("GET", f"/v1/users/{user_id}")
        return self._parse_response(response, User)

    async def aget_user(self, user_id: str) -> User:
        """Async get a user by ID.

        Args:
            user_id: The unique user identifier.

        Returns:
            The requested user.
        """
        response = await self._arequest("GET", f"/v1/users/{user_id}")
        return self._parse_response(response, User)

    # ── Category Endpoints ──────────────────────────────────────────────

    def list_categories(
        self, *, page: int = 1, per_page: int = 20
    ) -> PaginatedResponse[Category]:
        """List all product categories.

        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.

        Returns:
            Paginated list of categories.
        """
        response = self._request(
            "GET",
            "/v1/categories",
            params={"page": page, "per_page": per_page},
            use_cache=True,
        )
        return self._parse_paginated(response, Category)

    async def alist_categories(
        self, *, page: int = 1, per_page: int = 20
    ) -> PaginatedResponse[Category]:
        """Async list all product categories.

        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.

        Returns:
            Paginated list of categories.
        """
        response = await self._arequest(
            "GET",
            "/v1/categories",
            params={"page": page, "per_page": per_page},
            use_cache=True,
        )
        return self._parse_paginated(response, Category)

    def get_category(self, category_id: str) -> Category:
        """Get a category by ID.

        Args:
            category_id: The unique category identifier.

        Returns:
            The requested category.
        """
        response = self._request("GET", f"/v1/categories/{category_id}", use_cache=True)
        return self._parse_response(response, Category)

    async def aget_category(self, category_id: str) -> Category:
        """Async get a category by ID.

        Args:
            category_id: The unique category identifier.

        Returns:
            The requested category.
        """
        response = await self._arequest(
            "GET", f"/v1/categories/{category_id}", use_cache=True
        )
        return self._parse_response(response, Category)

    # ── Product Endpoints ───────────────────────────────────────────────

    def list_products(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        category_id: str | None = None,
        seller_id: str | None = None,
        status: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[Product]:
        """List products with optional filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.
            category_id: Filter by category.
            seller_id: Filter by seller.
            status: Filter by status.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            search: Search query string.

        Returns:
            Paginated list of products.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if category_id:
            params["category_id"] = category_id
        if seller_id:
            params["seller_id"] = seller_id
        if status:
            params["status"] = status
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if search:
            params["search"] = search

        response = self._request("GET", "/v1/products", params=params, use_cache=True)
        return self._parse_paginated(response, Product)

    async def alist_products(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        category_id: str | None = None,
        seller_id: str | None = None,
        status: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[Product]:
        """Async list products with optional filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.
            category_id: Filter by category.
            seller_id: Filter by seller.
            status: Filter by status.
            min_price: Minimum price filter.
            max_price: Maximum price filter.
            search: Search query string.

        Returns:
            Paginated list of products.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if category_id:
            params["category_id"] = category_id
        if seller_id:
            params["seller_id"] = seller_id
        if status:
            params["status"] = status
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        if search:
            params["search"] = search

        response = await self._arequest(
            "GET", "/v1/products", params=params, use_cache=True
        )
        return self._parse_paginated(response, Product)

    def get_product(self, product_id: str) -> Product:
        """Get a product by ID.

        Args:
            product_id: The unique product identifier.

        Returns:
            The requested product.
        """
        response = self._request("GET", f"/v1/products/{product_id}", use_cache=True)
        return self._parse_response(response, Product)

    async def aget_product(self, product_id: str) -> Product:
        """Async get a product by ID.

        Args:
            product_id: The unique product identifier.

        Returns:
            The requested product.
        """
        response = await self._arequest(
            "GET", f"/v1/products/{product_id}", use_cache=True
        )
        return self._parse_response(response, Product)

    def create_product(self, product: Product) -> Product:
        """Create a new product listing.

        Args:
            product: The product to create.

        Returns:
            The created product with server-assigned fields.
        """
        response = self._request(
            "POST", "/v1/products", json_data=product.model_dump(mode="json")
        )
        return self._parse_response(response, Product)

    async def acreate_product(self, product: Product) -> Product:
        """Async create a new product listing.

        Args:
            product: The product to create.

        Returns:
            The created product with server-assigned fields.
        """
        response = await self._arequest(
            "POST", "/v1/products", json_data=product.model_dump(mode="json")
        )
        return self._parse_response(response, Product)

    def update_product(self, product_id: str, updates: UpdateProductRequest) -> Product:
        """Update an existing product.

        Args:
            product_id: The unique product identifier.
            updates: The fields to update.

        Returns:
            The updated product.
        """
        response = self._request(
            "PATCH",
            f"/v1/products/{product_id}",
            json_data=updates.model_dump(mode="json", exclude_unset=True),
        )
        return self._parse_response(response, Product)

    async def aupdate_product(
        self, product_id: str, updates: UpdateProductRequest
    ) -> Product:
        """Async update an existing product.

        Args:
            product_id: The unique product identifier.
            updates: The fields to update.

        Returns:
            The updated product.
        """
        response = await self._arequest(
            "PATCH",
            f"/v1/products/{product_id}",
            json_data=updates.model_dump(mode="json", exclude_unset=True),
        )
        return self._parse_response(response, Product)

    def delete_product(self, product_id: str) -> None:
        """Delete a product listing.

        Args:
            product_id: The unique product identifier.
        """
        self._request("DELETE", f"/v1/products/{product_id}")

    async def adelete_product(self, product_id: str) -> None:
        """Async delete a product listing.

        Args:
            product_id: The unique product identifier.
        """
        await self._arequest("DELETE", f"/v1/products/{product_id}")

    # ── Order Endpoints ─────────────────────────────────────────────────

    def list_orders(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
        buyer_id: str | None = None,
        seller_id: str | None = None,
    ) -> PaginatedResponse[Order]:
        """List orders with optional filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.
            status: Filter by order status.
            buyer_id: Filter by buyer.
            seller_id: Filter by seller.

        Returns:
            Paginated list of orders.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
        if buyer_id:
            params["buyer_id"] = buyer_id
        if seller_id:
            params["seller_id"] = seller_id

        response = self._request("GET", "/v1/orders", params=params)
        return self._parse_paginated(response, Order)

    async def alist_orders(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        status: str | None = None,
        buyer_id: str | None = None,
        seller_id: str | None = None,
    ) -> PaginatedResponse[Order]:
        """Async list orders with optional filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.
            status: Filter by order status.
            buyer_id: Filter by buyer.
            seller_id: Filter by seller.

        Returns:
            Paginated list of orders.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if status:
            params["status"] = status
        if buyer_id:
            params["buyer_id"] = buyer_id
        if seller_id:
            params["seller_id"] = seller_id

        response = await self._arequest("GET", "/v1/orders", params=params)
        return self._parse_paginated(response, Order)

    def get_order(self, order_id: str) -> Order:
        """Get an order by ID.

        Args:
            order_id: The unique order identifier.

        Returns:
            The requested order.
        """
        response = self._request("GET", f"/v1/orders/{order_id}")
        return self._parse_response(response, Order)

    async def aget_order(self, order_id: str) -> Order:
        """Async get an order by ID.

        Args:
            order_id: The unique order identifier.

        Returns:
            The requested order.
        """
        response = await self._arequest("GET", f"/v1/orders/{order_id}")
        return self._parse_response(response, Order)

    def create_order(self, request: CreateOrderRequest) -> Order:
        """Create a new order.

        Args:
            request: The order creation request.

        Returns:
            The created order.
        """
        response = self._request(
            "POST", "/v1/orders", json_data=request.model_dump(mode="json")
        )
        return self._parse_response(response, Order)

    async def acreate_order(self, request: CreateOrderRequest) -> Order:
        """Async create a new order.

        Args:
            request: The order creation request.

        Returns:
            The created order.
        """
        response = await self._arequest(
            "POST", "/v1/orders", json_data=request.model_dump(mode="json")
        )
        return self._parse_response(response, Order)

    def cancel_order(self, order_id: str) -> Order:
        """Cancel an existing order.

        Args:
            order_id: The unique order identifier.

        Returns:
            The cancelled order.
        """
        response = self._request("POST", f"/v1/orders/{order_id}/cancel")
        return self._parse_response(response, Order)

    async def acancel_order(self, order_id: str) -> Order:
        """Async cancel an existing order.

        Args:
            order_id: The unique order identifier.

        Returns:
            The cancelled order.
        """
        response = await self._arequest("POST", f"/v1/orders/{order_id}/cancel")
        return self._parse_response(response, Order)

    # ── Review Endpoints ────────────────────────────────────────────────

    def list_reviews(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        product_id: str | None = None,
        reviewer_id: str | None = None,
    ) -> PaginatedResponse[Review]:
        """List reviews with optional filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.
            product_id: Filter by product.
            reviewer_id: Filter by reviewer.

        Returns:
            Paginated list of reviews.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if product_id:
            params["product_id"] = product_id
        if reviewer_id:
            params["reviewer_id"] = reviewer_id

        response = self._request("GET", "/v1/reviews", params=params, use_cache=True)
        return self._parse_paginated(response, Review)

    async def alist_reviews(
        self,
        *,
        page: int = 1,
        per_page: int = 20,
        product_id: str | None = None,
        reviewer_id: str | None = None,
    ) -> PaginatedResponse[Review]:
        """Async list reviews with optional filtering.

        Args:
            page: Page number (1-indexed).
            per_page: Number of items per page.
            product_id: Filter by product.
            reviewer_id: Filter by reviewer.

        Returns:
            Paginated list of reviews.
        """
        params: dict[str, Any] = {"page": page, "per_page": per_page}
        if product_id:
            params["product_id"] = product_id
        if reviewer_id:
            params["reviewer_id"] = reviewer_id

        response = await self._arequest(
            "GET", "/v1/reviews", params=params, use_cache=True
        )
        return self._parse_paginated(response, Review)

    def get_review(self, review_id: str) -> Review:
        """Get a review by ID.

        Args:
            review_id: The unique review identifier.

        Returns:
            The requested review.
        """
        response = self._request("GET", f"/v1/reviews/{review_id}", use_cache=True)
        return self._parse_response(response, Review)

    async def aget_review(self, review_id: str) -> Review:
        """Async get a review by ID.

        Args:
            review_id: The unique review identifier.

        Returns:
            The requested review.
        """
        response = await self._arequest(
            "GET", f"/v1/reviews/{review_id}", use_cache=True
        )
        return self._parse_response(response, Review)

    def create_review(self, request: CreateReviewRequest) -> Review:
        """Create a new review.

        Args:
            request: The review creation request.

        Returns:
            The created review.
        """
        response = self._request(
            "POST", "/v1/reviews", json_data=request.model_dump(mode="json")
        )
        return self._parse_response(response, Review)

    async def acreate_review(self, request: CreateReviewRequest) -> Review:
        """Async create a new review.

        Args:
            request: The review creation request.

        Returns:
            The created review.
        """
        response = await self._arequest(
            "POST", "/v1/reviews", json_data=request.model_dump(mode="json")
        )
        return self._parse_response(response, Review)

    def delete_review(self, review_id: str) -> None:
        """Delete a review.

        Args:
            review_id: The unique review identifier.
        """
        self._request("DELETE", f"/v1/reviews/{review_id}")

    async def adelete_review(self, review_id: str) -> None:
        """Async delete a review.

        Args:
            review_id: The unique review identifier.
        """
        await self._arequest("DELETE", f"/v1/reviews/{review_id}")
