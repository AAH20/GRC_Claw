"""MCP (Model Context Protocol) client implementation."""

from __future__ import annotations

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class MCPToolInfo:
    """MCP tool information returned by tools/list."""

    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Optional[Dict[str, Any]] = None


@dataclass
class MCPResourceInfo:
    """MCP resource information returned by resources/list."""

    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


@dataclass
class MCPPromptInfo:
    """MCP prompt information returned by prompts/list."""

    name: str
    description: str
    arguments: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MCPCallResult:
    """Result of a tool call."""

    content: List[Dict[str, Any]]
    is_error: bool = False
    structured_content: Optional[Dict[str, Any]] = None


class MCPClient:
    """MCP client for connecting to MCP servers.

    Supports stdio and HTTP/SSE transports.
    """

    PROTOCOL_VERSION = "2024-11-05"

    def __init__(
        self,
        *,
        command: Optional[List[str]] = None,
        url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> None:
        """
        Args:
            command: Command to start the MCP server (stdio transport).
            url: URL of the MCP server (HTTP transport).
            headers: Additional HTTP headers.
            timeout: Request timeout in seconds.
        """
        if not command and not url:
            raise ValueError("Either command or url must be provided")

        self._command = command
        self._url = url
        self._headers = headers or {}
        self._timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        self._process: Optional[asyncio.subprocess.Process] = None
        self._request_id = 0
        self._server_info: Optional[Dict[str, Any]] = None
        self._server_capabilities: Optional[Dict[str, Any]] = None
        self._tools: Dict[str, MCPToolInfo] = {}
        self._resources: Dict[str, MCPResourceInfo] = {}
        self._prompts: Dict[str, MCPPromptInfo] = {}
        self._initialized = False

    async def __aenter__(self) -> MCPClient:
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.disconnect()

    @property
    def is_connected(self) -> bool:
        """Whether the client is connected."""
        return self._initialized

    @property
    def tools(self) -> Dict[str, MCPToolInfo]:
        """Available tools."""
        return dict(self._tools)

    @property
    def resources(self) -> Dict[str, MCPResourceInfo]:
        """Available resources."""
        return dict(self._resources)

    @property
    def prompts(self) -> Dict[str, MCPPromptInfo]:
        """Available prompts."""
        return dict(self._prompts)

    # ─── Connection ─────────────────────────────────────────────────────

    async def connect(self) -> None:
        """Connect to the MCP server."""
        if self._initialized:
            return

        if self._command:
            await self._connect_stdio()
        elif self._url:
            await self._connect_http()

        await self._initialize()
        self._initialized = True

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self._process.kill()
            self._process = None

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

        self._initialized = False

    async def _connect_stdio(self) -> None:
        """Connect via stdio transport."""
        if not self._command:
            raise ValueError("No command specified for stdio transport")

        self._process = await asyncio.create_subprocess_exec(
            *self._command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        logger.info("Started MCP server process: %s", self._command)

    async def _connect_http(self) -> None:
        """Connect via HTTP transport."""
        if not self._url:
            raise ValueError("No URL specified for HTTP transport")

        timeout = aiohttp.ClientTimeout(total=self._timeout)
        self._session = aiohttp.ClientSession(
            timeout=timeout,
            headers=self._headers,
        )
        logger.info("Connected to MCP server at %s", self._url)

    async def _initialize(self) -> None:
        """Send initialize request and fetch server capabilities."""
        response = await self._send_request("initialize", {
            "protocolVersion": self.PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {
                "name": "grc-claw-mcp-client",
                "version": "1.0.0",
            },
        })

        self._server_info = response.get("serverInfo", {})
        self._server_capabilities = response.get("capabilities", {})

        # Send initialized notification
        await self._send_notification("initialized", {})

        # Fetch available tools, resources, and prompts
        await self.list_tools()
        await self.list_resources()
        await self.list_prompts()

    # ─── Tool Operations ────────────────────────────────────────────────

    async def list_tools(self) -> Dict[str, MCPToolInfo]:
        """List available tools from the server.

        Returns:
            Dictionary of tool name to MCPToolInfo.
        """
        response = await self._send_request("tools/list", {})
        tools = []
        for tool_data in response.get("tools", []):
            tool_info = MCPToolInfo(
                name=tool_data["name"],
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {}),
                output_schema=tool_data.get("outputSchema"),
            )
            tools.append(tool_info)
            self._tools[tool_info.name] = tool_info
        return dict(self._tools)

    async def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> MCPCallResult:
        """Call a tool on the MCP server.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            MCPCallResult with the tool output.

        Raises:
            ValueError: If the tool is not found.
            RuntimeError: If the tool call fails.
        """
        if name not in self._tools:
            raise ValueError(f"Tool not found: {name}")

        response = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments or {},
        })

        is_error = response.get("isError", False)
        content = response.get("content", [])
        structured = response.get("structuredContent")

        if is_error:
            error_text = "\n".join(
                c.get("text", "") for c in content if c.get("type") == "text"
            )
            raise RuntimeError(f"Tool call failed: {error_text}")

        return MCPCallResult(
            content=content,
            is_error=is_error,
            structured_content=structured,
        )

    # ─── Resource Operations ────────────────────────────────────────────

    async def list_resources(self) -> Dict[str, MCPResourceInfo]:
        """List available resources from the server.

        Returns:
            Dictionary of resource URI to MCPResourceInfo.
        """
        response = await self._send_request("resources/list", {})
        resources = []
        for res_data in response.get("resources", []):
            res_info = MCPResourceInfo(
                uri=res_data["uri"],
                name=res_data.get("name", ""),
                description=res_data.get("description", ""),
                mime_type=res_data.get("mimeType", "application/json"),
            )
            resources.append(res_info)
            self._resources[res_info.uri] = res_info
        return dict(self._resources)

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from the server.

        Args:
            uri: Resource URI.

        Returns:
            Resource content.
        """
        response = await self._send_request("resources/read", {"uri": uri})
        contents = response.get("contents", [])
        if contents:
            return json.loads(contents[0].get("text", "{}"))
        return {}

    async def subscribe_resource(self, uri: str) -> None:
        """Subscribe to resource updates.

        Args:
            uri: Resource URI to subscribe to.
        """
        await self._send_request("resources/subscribe", {"uri": uri})

    async def unsubscribe_resource(self, uri: str) -> None:
        """Unsubscribe from resource updates.

        Args:
            uri: Resource URI to unsubscribe from.
        """
        await self._send_request("resources/unsubscribe", {"uri": uri})

    # ─── Prompt Operations ──────────────────────────────────────────────

    async def list_prompts(self) -> Dict[str, MCPPromptInfo]:
        """List available prompts from the server.

        Returns:
            Dictionary of prompt name to MCPPromptInfo.
        """
        response = await self._send_request("prompts/list", {})
        prompts = []
        for prompt_data in response.get("prompts", []):
            prompt_info = MCPPromptInfo(
                name=prompt_data["name"],
                description=prompt_data.get("description", ""),
                arguments=prompt_data.get("arguments", []),
            )
            prompts.append(prompt_info)
            self._prompts[prompt_info.name] = prompt_info
        return dict(self._prompts)

    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get a prompt from the server.

        Args:
            name: Prompt name.
            arguments: Prompt arguments.

        Returns:
            Prompt with messages.
        """
        params: Dict[str, Any] = {"name": name}
        if arguments:
            params["arguments"] = arguments
        return await self._send_request("prompts/get", params)

    # ─── Transport ──────────────────────────────────────────────────────

    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request and return the result.

        Args:
            method: JSON-RPC method.
            params: Method parameters.

        Returns:
            Response result.

        Raises:
            RuntimeError: If the request fails.
        """
        self._request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params,
        }

        if self._process:
            response = await self._send_stdio(request)
        elif self._session:
            response = await self._send_http(request)
        else:
            raise RuntimeError("Not connected to MCP server")

        if "error" in response:
            error = response["error"]
            raise RuntimeError(f"MCP error {error['code']}: {error['message']}")

        return response.get("result", {})

    async def _send_notification(self, method: str, params: Dict[str, Any]) -> None:
        """Send a JSON-RPC notification (no response expected).

        Args:
            method: JSON-RPC method.
            params: Method parameters.
        """
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }

        if self._process:
            await self._send_stdio(notification, expect_response=False)
        elif self._session:
            await self._send_http(notification)

    async def _send_stdio(
        self, request: Dict[str, Any], *, expect_response: bool = True
    ) -> Dict[str, Any]:
        """Send a request via stdio transport.

        Args:
            request: JSON-RPC request.
            expect_response: Whether to wait for a response.

        Returns:
            Response dictionary.
        """
        if not self._process or not self._process.stdin or not self._process.stdout:
            raise RuntimeError("Stdio process not available")

        message = json.dumps(request) + "\n"
        self._process.stdin.write(message.encode("utf-8"))
        await self._process.stdin.drain()

        if not expect_response:
            return {}

        line = await self._process.stdout.readline()
        if not line:
            raise RuntimeError("MCP server closed stdout")

        return json.loads(line.decode("utf-8"))

    async def _send_http(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a request via HTTP transport.

        Args:
            request: JSON-RPC request.

        Returns:
            Response dictionary.
        """
        if not self._session or not self._url:
            raise RuntimeError("HTTP session not available")

        async with self._session.post(
            self._url,
            json=request,
            headers={"Content-Type": "application/json", **self._headers},
        ) as resp:
            if resp.status == 204:
                return {}
            return await resp.json()
