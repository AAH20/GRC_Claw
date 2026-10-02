"""MCP (Model Context Protocol) server implementation."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class MCPErrorCode(str, Enum):
    """JSON-RPC 2.0 error codes."""

    PARSE_ERROR = "-32700"
    INVALID_REQUEST = "-32600"
    METHOD_NOT_FOUND = "-32601"
    INVALID_PARAMS = "-32602"
    INTERNAL_ERROR = "-32603"
    SERVER_ERROR = "-32000"


@dataclass
class MCPError:
    """MCP error response."""

    code: int
    message: str
    data: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.data is not None:
            result["data"] = self.data
        return result


@dataclass
class MCPTool:
    """MCP tool definition."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable[..., Coroutine[Any, Any, Any]]
    output_schema: Optional[Dict[str, Any]] = None


@dataclass
class MCPResource:
    """MCP resource definition."""

    uri: str
    name: str
    description: str
    mime_type: str = "application/json"
    handler: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None


@dataclass
class MCPPrompt:
    """MCP prompt definition."""

    name: str
    description: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)
    handler: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None


class MCPServer:
    """MCP server for exposing tools, resources, and prompts.

    Implements the Model Context Protocol for AI agent integrations.
    Supports JSON-RPC 2.0 over stdio or HTTP transports.
    """

    PROTOCOL_VERSION = "2024-11-05"

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        *,
        instructions: str = "",
    ) -> None:
        self.name = name
        self.version = version
        self.instructions = instructions
        self._tools: Dict[str, MCPTool] = {}
        self._resources: Dict[str, MCPResource] = {}
        self._prompts: Dict[str, MCPPrompt] = {}
        self._subscriptions: Set[str] = set()
        self._request_handlers: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {}
        self._initialized = False
        self._client_capabilities: Dict[str, Any] = {}

        # Register built-in handlers
        self._register_builtin_handlers()

    def _register_builtin_handlers(self) -> None:
        """Register built-in JSON-RPC method handlers."""
        self._request_handlers["initialize"] = self._handle_initialize
        self._request_handlers["initialized"] = self._handle_noop
        self._request_handlers["ping"] = self._handle_ping
        self._request_handlers["tools/list"] = self._handle_tools_list
        self._request_handlers["tools/call"] = self._handle_tools_call
        self._request_handlers["resources/list"] = self._handle_resources_list
        self._request_handlers["resources/read"] = self._handle_resources_read
        self._request_handlers["resources/subscribe"] = self._handle_resources_subscribe
        self._request_handlers["resources/unsubscribe"] = self._handle_resources_unsubscribe
        self._request_handlers["prompts/list"] = self._handle_prompts_list
        self._request_handlers["prompts/get"] = self._handle_prompts_get
        self._request_handlers["completion/complete"] = self._handle_completion
        self._request_handlers["logging/setLevel"] = self._handle_set_log_level
        self._request_handlers["roots/list"] = self._handle_roots_list

    # ─── Registration ───────────────────────────────────────────────────

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[..., Coroutine[Any, Any, Any]],
        *,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a tool.

        Args:
            name: Tool name.
            description: Tool description.
            input_schema: JSON Schema for tool inputs.
            handler: Async handler function.
            output_schema: Optional JSON Schema for tool outputs.
        """
        self._tools[name] = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
            output_schema=output_schema,
        )
        logger.info("Registered tool: %s", name)

    def register_resource(
        self,
        uri: str,
        name: str,
        description: str,
        *,
        mime_type: str = "application/json",
        handler: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None,
    ) -> None:
        """Register a resource.

        Args:
            uri: Resource URI.
            name: Resource name.
            description: Resource description.
            mime_type: MIME type.
            handler: Optional handler for dynamic resources.
        """
        self._resources[uri] = MCPResource(
            uri=uri,
            name=name,
            description=description,
            mime_type=mime_type,
            handler=handler,
        )
        logger.info("Registered resource: %s", uri)

    def register_prompt(
        self,
        name: str,
        description: str,
        *,
        arguments: Optional[List[Dict[str, Any]]] = None,
        handler: Optional[Callable[..., Coroutine[Any, Any, Any]]] = None,
    ) -> None:
        """Register a prompt.

        Args:
            name: Prompt name.
            description: Prompt description.
            arguments: Prompt arguments.
            handler: Optional handler for dynamic prompts.
        """
        self._prompts[name] = MCPPrompt(
            name=name,
            description=description,
            arguments=arguments or [],
            handler=handler,
        )
        logger.info("Registered prompt: %s", name)

    def tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        *,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> Callable:
        """Decorator to register a tool."""
        def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable:
            self.register_tool(name, description, input_schema, func, output_schema=output_schema)
            return func
        return decorator

    def resource(
        self,
        uri: str,
        name: str,
        description: str,
        *,
        mime_type: str = "application/json",
    ) -> Callable:
        """Decorator to register a resource."""
        def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable:
            self.register_resource(uri, name, description, mime_type=mime_type, handler=func)
            return func
        return decorator

    def prompt(
        self,
        name: str,
        description: str,
        *,
        arguments: Optional[List[Dict[str, Any]]] = None,
    ) -> Callable:
        """Decorator to register a prompt."""
        def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable:
            self.register_prompt(name, description, arguments=arguments, handler=func)
            return func
        return decorator

    # ─── Request Handling ───────────────────────────────────────────────

    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a JSON-RPC request.

        Args:
            request: Parsed JSON-RPC request.

        Returns:
            JSON-RPC response or None for notifications.
        """
        request_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        # Validate request
        if not method:
            return self._error_response(request_id, MCPErrorCode.INVALID_REQUEST, "Method is required")

        handler = self._request_handlers.get(method)
        if not handler:
            return self._error_response(
                request_id, MCPErrorCode.METHOD_NOT_FOUND, f"Method not found: {method}"
            )

        try:
            result = await handler(params)
            if request_id is None:
                return None  # Notification, no response
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as e:
            logger.exception("Error handling request: %s", method)
            if request_id is None:
                return None
            return self._error_response(
                request_id, MCPErrorCode.INTERNAL_ERROR, str(e)
            )

    async def handle_message(self, message: str) -> Optional[str]:
        """Handle a raw JSON-RPC message.

        Args:
            message: JSON string.

        Returns:
            JSON response string or None.
        """
        try:
            request = json.loads(message)
        except json.JSONDecodeError as e:
            response = self._error_response(None, MCPErrorCode.PARSE_ERROR, f"Parse error: {e}")
            return json.dumps(response)

        # Handle batch requests
        if isinstance(request, list):
            responses = []
            for req in request:
                resp = await self.handle_request(req)
                if resp is not None:
                    responses.append(resp)
            return json.dumps(responses) if responses else None

        response = await self.handle_request(request)
        return json.dumps(response) if response else None

    # ─── Built-in Handlers ──────────────────────────────────────────────

    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        self._client_capabilities = params.get("capabilities", {})
        self._initialized = True
        return {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"subscribe": True, "listChanged": True},
                "prompts": {"listChanged": True},
                "logging": {},
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version,
            },
            "instructions": self.instructions,
        }

    async def _handle_noop(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle notification (no-op)."""
        return {}

    async def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping request."""
        return {}

    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        tools = []
        for tool in self._tools.values():
            tool_def: Dict[str, Any] = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            if tool.output_schema:
                tool_def["outputSchema"] = tool.output_schema
            tools.append(tool_def)
        return {"tools": tools}

    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        result = await tool.handler(**arguments)

        # Format result as MCP content
        if isinstance(result, dict) and "content" in result:
            return result
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, default=str),
                }
            ]
        }

    async def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        resources = []
        for resource in self._resources.values():
            resources.append({
                "uri": resource.uri,
                "name": resource.name,
                "description": resource.description,
                "mimeType": resource.mime_type,
            })
        return {"resources": resources}

    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri", "")
        resource = self._resources.get(uri)
        if not resource:
            raise ValueError(f"Resource not found: {uri}")

        if resource.handler:
            content = await resource.handler()
        else:
            content = {"uri": uri, "name": resource.name}

        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": resource.mime_type,
                    "text": json.dumps(content, default=str),
                }
            ]
        }

    async def _handle_resources_subscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/subscribe request."""
        uri = params.get("uri", "")
        self._subscriptions.add(uri)
        return {}

    async def _handle_resources_unsubscribe(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/unsubscribe request."""
        uri = params.get("uri", "")
        self._subscriptions.discard(uri)
        return {}

    async def _handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        prompts = []
        for prompt in self._prompts.values():
            prompts.append({
                "name": prompt.name,
                "description": prompt.description,
                "arguments": prompt.arguments,
            })
        return {"prompts": prompts}

    async def _handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request."""
        prompt_name = params.get("name", "")
        arguments = params.get("arguments", {})

        prompt = self._prompts.get(prompt_name)
        if not prompt:
            raise ValueError(f"Prompt not found: {prompt_name}")

        if prompt.handler:
            messages = await prompt.handler(**arguments)
        else:
            messages = [{"role": "user", "content": prompt.description}]

        return {
            "description": prompt.description,
            "messages": messages,
        }

    async def _handle_completion(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle completion/complete request."""
        return {"completion": {"values": [], "total": 0}}

    async def _handle_set_log_level(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle logging/setLevel request."""
        level = params.get("level", "info")
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        return {}

    async def _handle_roots_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle roots/list request."""
        return {"roots": []}

    # ─── Helpers ────────────────────────────────────────────────────────

    @staticmethod
    def _error_response(
        request_id: Optional[Any], code: MCPErrorCode, message: str
    ) -> Dict[str, Any]:
        """Build an error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": int(code.value), "message": message},
        }

    # ─── Stdio Transport ────────────────────────────────────────────────

    async def run_stdio(self) -> None:
        """Run the server over stdio transport."""
        logger.info("MCP server starting on stdio")

        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, input
                )
                if not line.strip():
                    continue

                response = await self.handle_message(line)
                if response:
                    print(response, flush=True)
            except EOFError:
                break
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.exception("Error in stdio loop")
                error_resp = self._error_response(
                    None, MCPErrorCode.INTERNAL_ERROR, str(e)
                )
                print(json.dumps(error_resp), flush=True)

    # ─── HTTP Transport ─────────────────────────────────────────────────

    async def run_http(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """Run the server over HTTP transport using aiohttp."""
        from aiohttp import web

        async def handle_http(request: web.Request) -> web.Response:
            try:
                body = await request.text()
                response = await self.handle_message(body)
                if response:
                    return web.Response(
                        text=response,
                        content_type="application/json",
                    )
                return web.Response(status=204)
            except Exception as e:
                logger.exception("HTTP handler error")
                return web.json_response(
                    self._error_response(None, MCPErrorCode.INTERNAL_ERROR, str(e)),
                    status=500,
                )

        app = web.Application()
        app.router.add_post("/", handle_http)
        app.router.add_get("/", handle_http)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        logger.info("MCP server listening on %s:%d", host, port)

        # Keep running
        while True:
            await asyncio.sleep(3600)
