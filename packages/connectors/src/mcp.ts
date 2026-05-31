import type { McpServerConfig, McpToolDescriptor } from './types.js';
import { ConnectorRegistry } from './registry.js';
import { mcpGatedToolName } from './names.js';

type JsonRpcResponse = {
  jsonrpc?: string;
  id?: number | string;
  result?: Record<string, unknown>;
  error?: { code: number; message: string };
};

let rpcId = 1;

async function mcpRequest(
  server: McpServerConfig,
  registry: ConnectorRegistry,
  method: string,
  params: Record<string, unknown> = {}
): Promise<Record<string, unknown>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json, text/event-stream',
    ...server.headers,
  };
  if (server.apiKeyEnv) {
    const key = registry.resolveApiKey(server.apiKeyEnv);
    if (key) headers.Authorization = `Bearer ${key}`;
  }

  const body = {
    jsonrpc: '2.0',
    id: rpcId++,
    method,
    params,
  };

  const res = await fetch(server.url, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`mcp_http_${res.status}:${detail.slice(0, 200)}`);
  }

  const text = await res.text();
  const parsed = parseMcpResponse(text);
  if (parsed.error) {
    throw new Error(`mcp_rpc:${parsed.error.message}`);
  }
  return parsed.result ?? {};
}

function parseMcpResponse(text: string): JsonRpcResponse {
  const trimmed = text.trim();
  if (trimmed.startsWith('{')) {
    return JSON.parse(trimmed) as JsonRpcResponse;
  }
  const lines = trimmed.split('\n').filter(Boolean);
  for (let i = lines.length - 1; i >= 0; i--) {
    const line = lines[i]!.replace(/^data:\s*/, '');
    if (line.startsWith('{')) {
      try {
        return JSON.parse(line) as JsonRpcResponse;
      } catch {
        continue;
      }
    }
  }
  throw new Error('mcp_invalid_response');
}

const initCache = new Set<string>();

async function ensureInitialized(server: McpServerConfig, registry: ConnectorRegistry): Promise<void> {
  if (initCache.has(server.id)) return;
  await mcpRequest(server, registry, 'initialize', {
    protocolVersion: '2024-11-05',
    capabilities: {},
    clientInfo: { name: 'grc-claw', version: '0.1.0' },
  });
  initCache.add(server.id);
}

export async function listMcpTools(
  registry: ConnectorRegistry,
  serverId: string
): Promise<McpToolDescriptor[]> {
  const server = registry.getMcp(serverId);
  if (!server) throw new Error(`mcp_server_not_found:${serverId}`);
  await ensureInitialized(server, registry);
  const result = await mcpRequest(server, registry, 'tools/list', {});
  const tools = (result.tools ?? []) as { name: string; description?: string }[];
  return tools.map((t) => ({
    name: t.name,
    description: t.description,
    gatedName: mcpGatedToolName(serverId, t.name),
  }));
}

export async function callMcpTool(
  registry: ConnectorRegistry,
  serverId: string,
  toolName: string,
  args: Record<string, unknown>
): Promise<Record<string, unknown>> {
  const server = registry.getMcp(serverId);
  if (!server) throw new Error(`mcp_server_not_found:${serverId}`);
  await ensureInitialized(server, registry);
  const result = await mcpRequest(server, registry, 'tools/call', {
    name: toolName,
    arguments: args,
  });
  return result;
}

export function clearMcpInitCacheForTests(): void {
  initCache.clear();
}
