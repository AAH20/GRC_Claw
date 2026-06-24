import type { IncomingMessage, ServerResponse } from 'node:http';
import { BUILTIN_AGENT_TOOLS, AgentSession, ExecPolicy, PersistentMemoryStore } from '@grc-claw/agent-runtime';

const store = new PersistentMemoryStore();
import { CLAW_SKILL_TOOLS } from '@grc-claw/skill-executor';
import {
  buildConnectorToolDefinitions,
  chatViaProvider,
  dispatchConnectorTool,
  getConnectorRegistry,
  isConnectorTool,
  listMcpTools,
  type ConnectorRegistry,
} from '@grc-claw/connectors';

export type ReadJson = (req: IncomingMessage) => Promise<Record<string, unknown>>;

export async function buildExecPolicyWithConnectors(
  registry: ConnectorRegistry
): Promise<ExecPolicy> {
  const mcpTools: Record<string, Awaited<ReturnType<typeof listMcpTools>>> = {};
  for (const server of registry.listMcp()) {
    try {
      mcpTools[server.id] = await listMcpTools(registry, server.id);
    } catch {
      mcpTools[server.id] = [];
    }
  }
  const connectorTools = buildConnectorToolDefinitions(registry, mcpTools);
  return new ExecPolicy([...BUILTIN_AGENT_TOOLS, ...CLAW_SKILL_TOOLS, ...connectorTools]);
}

export function matchConnectorPath(path: string): {
  kind: 'list' | 'reload' | 'llm_chat' | 'mcp_tools' | 'mcp_call' | null;
  llmId?: string;
  mcpId?: string;
} {
  if (path === '/api/connectors') return { kind: 'list' };
  if (path === '/api/connectors/reload') return { kind: 'reload' };
  const llmChat = path.match(/^\/api\/connectors\/llm\/([^/]+)\/chat$/);
  if (llmChat) return { kind: 'llm_chat', llmId: decodeURIComponent(llmChat[1]!) };
  const mcpTools = path.match(/^\/api\/connectors\/mcp\/([^/]+)\/tools$/);
  if (mcpTools) return { kind: 'mcp_tools', mcpId: decodeURIComponent(mcpTools[1]!) };
  const mcpCall = path.match(/^\/api\/connectors\/mcp\/([^/]+)\/call$/);
  if (mcpCall) return { kind: 'mcp_call', mcpId: decodeURIComponent(mcpCall[1]!) };
  return { kind: null };
}

export async function handleConnectorsRoute(
  req: IncomingMessage,
  res: ServerResponse,
  path: string,
  authOk: (req: IncomingMessage) => boolean,
  readJson: ReadJson,
  getExecPolicy: () => Promise<ExecPolicy>,
  reloadPolicy: () => Promise<void>
): Promise<boolean> {
  const route = matchConnectorPath(path);
  if (!route.kind) return false;

  if (route.kind === 'list') {
    if (req.method !== 'GET') {
      res.writeHead(405);
      res.end(JSON.stringify({ error: 'method_not_allowed' }));
      return true;
    }
    const registry = getConnectorRegistry();
    const counts: Record<string, number> = {};
    for (const s of registry.listMcp()) {
      try {
        counts[s.id] = (await listMcpTools(registry, s.id)).length;
      } catch {
        counts[s.id] = 0;
      }
    }
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, byoc: true, ...registry.toPublicSummary(counts) }));
    return true;
  }

  if (!authOk(req)) {
    res.writeHead(401);
    res.end(JSON.stringify({ error: 'unauthorized' }));
    return true;
  }

  const registry = getConnectorRegistry();

  if (route.kind === 'reload') {
    if (req.method !== 'POST') {
      res.writeHead(405);
      res.end(JSON.stringify({ error: 'method_not_allowed' }));
      return true;
    }
    registry.loadFromEnv();
    await reloadPolicy();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ ok: true, reloaded: true }));
    return true;
  }

  if (route.kind === 'llm_chat' && route.llmId) {
    if (req.method !== 'POST') {
      res.writeHead(405);
      res.end(JSON.stringify({ error: 'method_not_allowed' }));
      return true;
    }
    const body = await readJson(req);
    try {
      const messages = (body.messages as { role: string; content: string }[]) ?? [];
      const maxTokens =
        typeof body.maxTokens === 'number'
          ? body.maxTokens
          : typeof body.max_tokens === 'number'
            ? body.max_tokens
            : 8192;
      const temperature =
        typeof body.temperature === 'number' ? body.temperature : undefined;
      const result = await chatViaProvider(registry, route.llmId, {
        messages,
        model: typeof body.model === 'string' ? body.model : undefined,
        maxTokens,
        temperature,
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...result }));
    } catch (e) {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false, error: e instanceof Error ? e.message : 'llm_failed' }));
    }
    return true;
  }

  if (route.kind === 'mcp_tools' && route.mcpId) {
    if (req.method !== 'GET') {
      res.writeHead(405);
      res.end(JSON.stringify({ error: 'method_not_allowed' }));
      return true;
    }
    try {
      const tools = await listMcpTools(registry, route.mcpId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, serverId: route.mcpId, tools }));
    } catch (e) {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false, error: e instanceof Error ? e.message : 'mcp_list_failed' }));
    }
    return true;
  }

  if (route.kind === 'mcp_call' && route.mcpId) {
    if (req.method !== 'POST') {
      res.writeHead(405);
      res.end(JSON.stringify({ error: 'method_not_allowed' }));
      return true;
    }
    const body = await readJson(req);
    const toolName = String(body.tool ?? '');
    const args = (body.arguments as Record<string, unknown>) ?? {};
    const gatedTool = toolName.includes('.') ? toolName : `mcp.${route.mcpId}.${toolName}`;
    const execPolicy = await getExecPolicy();
    const session = new AgentSession(String(body.sessionId ?? 'mcp-call'), execPolicy, store);
    const decision = await session.invoke({
      tool: gatedTool,
      args,
      approvalToken: body.approvalToken as string | undefined,
      idempotencyKey: body.idempotencyKey as string | undefined,
    });
    if (!decision.allowed) {
      res.writeHead(403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false, decision, audit: session.getAuditLog() }));
      return true;
    }
    try {
      const output = await dispatchConnectorTool(registry, gatedTool, args);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: true,
          decision,
          output: output.output,
          audit: session.getAuditLog(),
        })
      );
    } catch (e) {
      res.writeHead(502, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: false,
          error: e instanceof Error ? e.message : 'mcp_call_failed',
          audit: session.getAuditLog(),
        })
      );
    }
    return true;
  }

  return false;
}

export async function invokeWithConnectorDispatch(
  registry: ConnectorRegistry,
  tool: string,
  args: Record<string, unknown>
): Promise<Record<string, unknown> | undefined> {
  if (!isConnectorTool(tool)) return undefined;
  const result = await dispatchConnectorTool(registry, tool, args);
  return result.output;
}
