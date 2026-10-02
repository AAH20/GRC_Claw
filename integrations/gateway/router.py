"""API Gateway router for integration endpoints."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional, Pattern, Tuple, Union

logger = logging.getLogger(__name__)


class HTTPMethod(str, Enum):
    """Supported HTTP methods."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


@dataclass
class Route:
    """API route definition."""

    pattern: str
    methods: List[HTTPMethod]
    handler: Callable[..., Awaitable[Any]]
    name: str = ""
    middleware: List[Callable[..., Awaitable[Any]]] = field(default_factory=list)
    auth_required: bool = True
    rate_limit_key: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    summary: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"{self.methods[0].value}_{self.pattern}"


@dataclass
class RouteMatch:
    """Result of matching a request to a route."""

    route: Route
    path_params: Dict[str, str]
    query_params: Dict[str, List[str]]


class Router:
    """API Gateway router.

    Handles request routing with path parameter extraction,
    method matching, and middleware execution.
    """

    def __init__(self) -> None:
        self._routes: List[Route] = []
        self._middleware: List[Callable[..., Awaitable[Any]]] = []
        self._error_handlers: Dict[int, Callable[..., Awaitable[Any]]] = {}
        self._not_found_handler: Optional[Callable[..., Awaitable[Any]]] = None

    # ─── Registration ───────────────────────────────────────────────────

    def add_route(
        self,
        pattern: str,
        methods: Union[HTTPMethod, List[HTTPMethod]],
        handler: Callable[..., Awaitable[Any]],
        *,
        name: str = "",
        middleware: Optional[List[Callable[..., Awaitable[Any]]]] = None,
        auth_required: bool = True,
        rate_limit_key: Optional[str] = None,
        tags: Optional[List[str]] = None,
        summary: str = "",
        description: str = "",
    ) -> Route:
        """Add a route to the router.

        Args:
            pattern: URL pattern (supports {param} and {param:type} placeholders).
            methods: Allowed HTTP method(s).
            handler: Async handler function.
            name: Route name.
            middleware: Route-specific middleware.
            auth_required: Whether authentication is required.
            rate_limit_key: Key for rate limiting.
            tags: Route tags for documentation.
            summary: Short summary.
            description: Detailed description.

        Returns:
            The created Route.
        """
        if isinstance(methods, HTTPMethod):
            methods = [methods]

        route = Route(
            pattern=pattern,
            methods=methods,
            handler=handler,
            name=name,
            middleware=middleware or [],
            auth_required=auth_required,
            rate_limit_key=rate_limit_key,
            tags=tags or [],
            summary=summary,
            description=description,
        )
        self._routes.append(route)
        logger.debug("Registered route: %s %s", methods, pattern)
        return route

    def get(
        self, pattern: str, handler: Callable[..., Awaitable[Any]], **kwargs: Any
    ) -> Route:
        """Register a GET route."""
        return self.add_route(pattern, HTTPMethod.GET, handler, **kwargs)

    def post(
        self, pattern: str, handler: Callable[..., Awaitable[Any]], **kwargs: Any
    ) -> Route:
        """Register a POST route."""
        return self.add_route(pattern, HTTPMethod.POST, handler, **kwargs)

    def put(
        self, pattern: str, handler: Callable[..., Awaitable[Any]], **kwargs: Any
    ) -> Route:
        """Register a PUT route."""
        return self.add_route(pattern, HTTPMethod.PUT, handler, **kwargs)

    def patch(
        self, pattern: str, handler: Callable[..., Awaitable[Any]], **kwargs: Any
    ) -> Route:
        """Register a PATCH route."""
        return self.add_route(pattern, HTTPMethod.PATCH, handler, **kwargs)

    def delete(
        self, pattern: str, handler: Callable[..., Awaitable[Any]], **kwargs: Any
    ) -> Route:
        """Register a DELETE route."""
        return self.add_route(pattern, HTTPMethod.DELETE, handler, **kwargs)

    def add_middleware(self, middleware: Callable[..., Awaitable[Any]]) -> None:
        """Add global middleware."""
        self._middleware.append(middleware)

    def set_error_handler(
        self, status_code: int, handler: Callable[..., Awaitable[Any]]
    ) -> None:
        """Set an error handler for a specific status code."""
        self._error_handlers[status_code] = handler

    def set_not_found_handler(self, handler: Callable[..., Awaitable[Any]]) -> None:
        """Set the 404 handler."""
        self._not_found_handler = handler

    # ─── Matching ───────────────────────────────────────────────────────

    def match(
        self, method: str, path: str, query_string: str = ""
    ) -> Optional[RouteMatch]:
        """Match a request to a route.

        Args:
            method: HTTP method.
            path: Request path.
            query_string: Raw query string.

        Returns:
            RouteMatch if a route matches, None otherwise.
        """
        from urllib.parse import parse_qs

        query_params = parse_qs(query_string)

        for route in self._routes:
            # Check method
            if HTTPMethod(method.upper()) not in route.methods:
                continue

            # Match path
            path_params = self._match_path(route.pattern, path)
            if path_params is not None:
                return RouteMatch(
                    route=route,
                    path_params=path_params,
                    query_params=query_params,
                )

        return None

    def _match_path(
        self, pattern: str, path: str) -> Optional[Dict[str, str]]:
        """Match a path against a route pattern.

        Supports {param} and {param:type} placeholders.
        Types: str, int, float, path, uuid.

        Returns:
            Dictionary of path parameters if matched, None otherwise.
        """
        # Convert pattern to regex
        param_types: Dict[str, str] = {}
        regex_pattern = self._pattern_to_regex(pattern, param_types)

        match = re.match(f"^{regex_pattern}$", path)
        if not match:
            return None

        # Extract parameters
        params: Dict[str, str] = {}
        groups = match.groups()
        param_names = re.findall(r"{(\w+)(?::(\w+))?}", pattern)

        for i, (name, type_hint) in enumerate(param_names):
            value = groups[i] if i < len(groups) else ""
            if type_hint:
                value = self._convert_param(value, type_hint)
            params[name] = value

        return params

    @staticmethod
    def _pattern_to_regex(
        pattern: str, param_types: Dict[str, str]
    ) -> str:
        """Convert a route pattern to a regex string."""
        type_patterns = {
            "str": r"[^/]+",
            "int": r"\d+",
            "float": r"\d+\.?\d*",
            "path": r".+",
            "uuid": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
        }

        result = pattern
        # Find all {param} or {param:type} placeholders
        for match in re.finditer(r"{(\w+)(?::(\w+))?}", pattern):
            name = match.group(1)
            type_hint = match.group(2) or "str"
            param_types[name] = type_hint

            regex_type = type_patterns.get(type_hint, type_patterns["str"])
            result = result.replace(match.group(0), f"({regex_type})")

        # Escape special regex characters except our placeholders
        result = re.sub(r"[.+^${}()|[\]\\]", r"\\\g<0>", result)
        # Unescape our capture groups
        result = result.replace(r"\(", "(").replace(r"\)", ")")

        return result

    @staticmethod
    def _convert_param(value: str, type_hint: str) -> Union[str, int, float]:
        """Convert a path parameter to the specified type."""
        if type_hint == "int":
            return int(value)
        if type_hint == "float":
            return float(value)
        return value

    # ─── Dispatch ───────────────────────────────────────────────────────

    async def dispatch(
        self,
        method: str,
        path: str,
        *,
        query_string: str = "",
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Dispatch a request to the matching route handler.

        Args:
            method: HTTP method.
            path: Request path.
            query_string: Raw query string.
            headers: Request headers.
            body: Request body.
            context: Request context.

        Returns:
            Handler response.

        Raises:
            RouteNotFoundError: If no route matches.
            MethodNotAllowedError: If the method is not allowed for the matched path.
        """
        headers = headers or {}
        context = context or {}

        match = self.match(method, path, query_string)
        if not match:
            # Check if path exists with different method
            for route in self._routes:
                if self._match_path(route.pattern, path) is not None:
                    raise MethodNotAllowedError(
                        f"Method {method} not allowed for {path}"
                    )
            raise RouteNotFoundError(f"No route found for {method} {path}")

        route = match.route

        # Build request context
        request_context = {
            "method": method,
            "path": path,
            "headers": headers,
            "body": body,
            "path_params": match.path_params,
            "query_params": match.query_params,
            "route_name": route.name,
            **context,
        }

        # Execute global middleware
        handler = route.handler
        for mw in reversed(self._middleware):
            handler = self._wrap_middleware(mw, handler)

        # Execute route-specific middleware
        for mw in reversed(route.middleware):
            handler = self._wrap_middleware(mw, handler)

        try:
            return await handler(request_context)
        except Exception as e:
            logger.exception("Error in route handler: %s", route.name)
            error_handler = self._error_handlers.get(500)
            if error_handler:
                return await error_handler(request_context, e)
            raise

    @staticmethod
    def _wrap_middleware(
        middleware: Callable[..., Awaitable[Any]],
        handler: Callable[..., Awaitable[Any]],
    ) -> Callable[..., Awaitable[Any]]:
        """Wrap a handler with middleware."""
        async def wrapped(request_context: Dict[str, Any]) -> Any:
            return await middleware(request_context, handler)
        return wrapped

    # ─── Utility ────────────────────────────────────────────────────────

    def get_routes(self) -> List[Route]:
        """Get all registered routes."""
        return list(self._routes)

    def get_openapi_spec(self) -> Dict[str, Any]:
        """Generate an OpenAPI-compatible specification from registered routes."""
        paths: Dict[str, Any] = {}

        for route in self._routes:
            path = route.pattern
            if path not in paths:
                paths[path] = {}

            for method in route.methods:
                operation: Dict[str, Any] = {
                    "summary": route.summary,
                    "description": route.description,
                    "tags": route.tags,
                    "responses": {
                        "200": {"description": "Success"},
                        "401": {"description": "Unauthorized"},
                        "404": {"description": "Not Found"},
                        "500": {"description": "Internal Server Error"},
                    },
                }

                # Extract parameters
                parameters = []
                for match in re.finditer(r"{(\w+)(?::(\w+))?}", route.pattern):
                    param_name = match.group(1)
                    param_type = match.group(2) or "str"
                    parameters.append({
                        "name": param_name,
                        "in": "path",
                        "required": True,
                        "schema": {"type": param_type},
                    })

                if parameters:
                    operation["parameters"] = parameters

                paths[path][method.value.lower()] = operation

        return {
            "openapi": "3.0.0",
            "info": {
                "title": "GRC Claw Integration Hub API",
                "version": "1.0.0",
            },
            "paths": paths,
        }


class RouteNotFoundError(Exception):
    """Raised when no route matches the request."""


class MethodNotAllowedError(Exception):
    """Raised when the HTTP method is not allowed for the matched path."""
