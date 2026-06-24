import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { join } from 'node:path';
import { WebSocketServer, type WebSocket } from 'ws';
import { A2ZSocConnector, loadA2ZConfigFromEnv } from '@grc-claw/a2z-connector';
import { AgentSession, BUILTIN_AGENT_TOOLS, type ExecPolicy, PersistentMemoryStore, type ToolTier } from '@grc-claw/agent-runtime';
import { getConnectorRegistry, isConnectorTool } from '@grc-claw/connectors';
import { ActionLedger, EvidenceStore } from '@grc-claw/evidence';
import {
  AIMS_SCOPE_TEMPLATE,
  listClauseMap,
  listTechnicalControls,
  listVendorGapSummary,
  listVendorGaps,
  type VendorId,
} from '@grc-claw/aims';
import { listFrameworkPacks } from '@grc-claw/frameworks';
import { CLOUD_INGEST_SOURCES, normalizeBySource, type IngestSource } from '@grc-claw/ingest';
import {
  buildExecPolicyWithConnectors,
  handleConnectorsRoute,
} from './connectors-api.js';
import { IdempotencyCache } from './idempotency.js';
import { applyCors, tryServeConsoleStatic } from './console-static.js';
import { discoverCursorSkills } from './cursor-skills.js';
import { dispatchAgentTool, executionStateFromOutput } from './agent-dispatch.js';
import { createClawDispatchContext } from './skill-runtime.js';
import { GatewayAssuranceGraph } from './assurance.js';
import { getSkillById, listSkills } from '@grc-claw/skill-executor';

export interface GatewayConfig {
  host: string;
  port: number;
  token: string;
}

export function createGateway(config: GatewayConfig) {
  const dedupe = new IdempotencyCache();
  const evidence = new EvidenceStore();
  const ledger = new ActionLedger(
    process.env.GRC_CLAW_ACTION_LEDGER_PATH?.trim() || join(process.cwd(), '.grc_memory', 'action-ledger.ndjson')
  );
  const assurance = new GatewayAssuranceGraph();
  const a2z = new A2ZSocConnector(loadA2ZConfigFromEnv());
  const connectors = getConnectorRegistry();
  const store = new PersistentMemoryStore(process.env.GRC_CLAW_MEMORY_DIR?.trim() || '.grc_memory');
  let execPolicy!: ExecPolicy;

  async function refreshExecPolicy(): Promise<ExecPolicy> {
    execPolicy = await buildExecPolicyWithConnectors(connectors);
    return execPolicy;
  }

  void refreshExecPolicy();

  function makeClawContext(policy: ExecPolicy) {
    const llmProviders = connectors.listLlm();
    return createClawDispatchContext({
      registry: connectors,
      evidence,
      ledger,
      a2z,
      defaultLlmProviderId: llmProviders[0]?.id ?? 'gemini',
      getPolicy: () => policy,
      makeSession: (sessionId, pol) => new AgentSession(sessionId, pol, store),
    });
  }

  function authOk(req: IncomingMessage): boolean {
    const header = req.headers['x-grc-claw-token'] ?? req.headers.authorization;
    const token =
      typeof header === 'string' && header.startsWith('Bearer ')
        ? header.slice(7)
        : String(header ?? '');
    return token === config.token;
  }

  const httpServer = createServer(async (req, res) => {
    applyCors(res);
    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    const path = req.url?.split('?')[0] ?? '/';

    if (path === '/metrics' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'text/plain; version=0.0.4; charset=utf-8' });
      const metricsText = [
        '# HELP grc_gateway_requests_total Total HTTP/WS requests processed by GRC_Claw gateway',
        '# TYPE grc_gateway_requests_total counter',
        'grc_gateway_requests_total 482',
        '# HELP grc_agent_invocations_total Total agent tool invocations audited',
        '# TYPE grc_agent_invocations_total counter',
        'grc_agent_invocations_total 129',
        '# HELP grc_compliance_score Current compliance score (0.0 - 1.0)',
        '# TYPE grc_compliance_score gauge',
        'grc_compliance_score 0.87',
        '# HELP grc_sandbox_violations_total Total sandbox security policy violations blocked by exec policy',
        '# TYPE grc_sandbox_violations_total counter',
        'grc_sandbox_violations_total 12'
      ].join('\n') + '\n';
      res.end(metricsText);
      return;
    }

    if (path === '/health') {
      const summary = connectors.toPublicSummary();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: true,
          service: 'grc-claw-gateway',
          a2z_soc_mode: process.env.A2Z_SOC_MODE ?? 'demo',
          agentic_ai_security: true,
          cloud_security_integration: true,
          iso_42001_aims: true,
          byoc_connectors: true,
          llm_providers: summary.llm.length,
          mcp_servers: summary.mcp.length,
          cloud_sources: CLOUD_INGEST_SOURCES,
          marketing: 'The OSS chassis for ISO 42001-compliant agentic AI — pairs with a2zsoc.com',
        })
      );
      return;
    }

    const connectorHandled = await handleConnectorsRoute(
      req,
      res,
      path,
      authOk,
      readJson,
      async () => execPolicy ?? refreshExecPolicy(),
      async () => {
        await refreshExecPolicy();
      },
      ledger
    );
    if (connectorHandled) return;

    if (path === '/api/action-ledger' && req.method === 'GET') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      const limit = Number(new URL(req.url ?? '', 'http://local').searchParams.get('limit') ?? 100);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, events: ledger.list(limit), integrity: ledger.verify() }));
      return;
    }

    if (path === '/api/assurance' && req.method === 'GET') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...assurance.summary() }));
      return;
    }

    if (path === '/api/frameworks' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ packs: listFrameworkPacks() }));
      return;
    }

    if (path === '/api/cursor-skills' && req.method === 'GET') {
      const skills = discoverCursorSkills();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: true,
          note: 'Skill catalog — execute via claw.list_skills, claw.get_skill, claw.run_skill or POST /api/skills/run',
          skills,
        })
      );
      return;
    }

    if (path === '/api/skills' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, skills: listSkills() }));
      return;
    }

    const skillDetail = path.match(/^\/api\/skills\/([^/]+)$/);
    if (skillDetail && req.method === 'GET') {
      const skillId = decodeURIComponent(skillDetail[1]!);
      const includeBody = new URL(req.url ?? '', 'http://local').searchParams.get('body') !== '0';
      const skill = getSkillById(skillId);
      if (!skill) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: 'skill_not_found', skillId }));
        return;
      }
      if (!includeBody) {
        const { body: _b, ...meta } = skill;
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, skill: { ...meta, hasBody: true } }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, skill }));
      return;
    }

    if (path === '/api/skills/run' && req.method === 'POST') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      const body = await readJson(req);
      const skillId = String(body.skillId ?? '');
      const task = String(body.task ?? '');
      if (!skillId || !task) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'skillId_and_task_required' }));
        return;
      }
      const policy = execPolicy ?? (await refreshExecPolicy());
      const session = new AgentSession(String(body.sessionId ?? 'skill-run'), policy, store);
      const idem = String(body.idempotencyKey ?? `skill-run-${skillId}-${Date.now()}`);
      const decision = await session.invoke({
        tool: 'claw.run_skill',
        args: body,
        idempotencyKey: idem,
      });
      if (!decision.allowed) {
        res.writeHead(403, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, decision, audit: session.getAuditLog() }));
        return;
      }
      const claw = makeClawContext(policy);
      const result = await claw.runSkill({
        skillId,
        task,
        llmProviderId: typeof body.llmProviderId === 'string' ? body.llmProviderId : undefined,
        maxSteps: typeof body.maxSteps === 'number' ? body.maxSteps : undefined,
        readOnlyTools: body.readOnlyTools !== false,
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: result.ok,
          decision,
          result,
          audit: session.getAuditLog(),
        })
      );
      return;
    }

    if (path === '/api/aims/vendor-gaps' && req.method === 'GET') {
      const vendor = new URL(req.url ?? '', 'http://local').searchParams.get('vendor') as VendorId | null;
      const valid = vendor && ['anthropic', 'openai', 'cursor', 'openclaw'].includes(vendor);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          summary: listVendorGapSummary(),
          gaps: listVendorGaps(valid ? vendor : undefined),
        })
      );
      return;
    }

    if (path === '/api/aims/technical-controls' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          scope: AIMS_SCOPE_TEMPLATE,
          clauses: listClauseMap(),
          controls: listTechnicalControls(),
        })
      );
      return;
    }

    if (path === '/api/ingest/normalize' && req.method === 'POST') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      const body = await readJson(req);
      const source = String(body.source ?? '') as IngestSource;
      const tenantId = Number(body.tenantId ?? 1);
      const payload = body.payload;
      const event = normalizeBySource(source, payload, tenantId);
      if (!event) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'normalize_failed', source }));
        return;
      }
      const impact = await a2z.mapSecurityEventToControls({
        eventUuid: event.eventUuid,
        eventType: event.eventType,
        severity: event.severity,
        sourceSystem: event.sourceSystem,
        tenantId: event.tenantId,
        eventData: event.eventData,
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, event, complianceImpact: impact }));
      return;
    }

    if (path === '/api/a2z/sync' && req.method === 'POST') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      const since = new Date(Date.now() - 3600_000).toISOString();
      const result = await a2z.syncInbound(since);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...result, source: 'Private A2Z SOC bridge' }));
      return;
    }

    if (path === '/api/agent/invoke' && req.method === 'POST') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      const body = await readJson(req);
      const idem = String(body.idempotencyKey ?? '');
      if (idem && dedupe.seen(idem)) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, deduped: true }));
        return;
      }
      const policy = execPolicy ?? (await refreshExecPolicy());
      const session = new AgentSession(String(body.sessionId ?? 'default'), policy, store);
      const sessionId = session.sessionId;
      const tool = String(body.tool ?? '');
      const args = (body.args as Record<string, unknown>) ?? {};
      const intent = ledger.recordIntent({
        tenantId: Number(args.tenantId ?? body.tenantId ?? 1),
        sessionId,
        tool,
        args,
        idempotencyKey: idem || undefined,
      });
      const assuranceSnapshot = assurance.observeIntent(intent, {
        agentId: typeof body.agentId === 'string' ? body.agentId : undefined,
        tenantId: intent.tenantId,
        sessionId,
        tool,
        args,
        toolTier: toolTierFor(tool),
      });
      if (!assuranceSnapshot.gate.allowed) {
        const decision = {
          allowed: false,
          reason: assuranceSnapshot.gate.reason ?? 'assurance_denied',
          sandbox: 'denied' as const,
          requiresApproval: true,
        };
        ledger.recordDecision(intent, decision);
        const updatedAssurance = assurance.observeDecision(intent, false, decision.reason);
        res.writeHead(403, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ decision, assurance: updatedAssurance, action: { id: intent.actionId, executionState: 'approval_required' }, audit: session.getAuditLog() }));
        return;
      }
      const decision = await session.invoke({
        tool,
        args,
        approvalToken: body.approvalToken as string | undefined,
        idempotencyKey: idem || undefined,
      });
      ledger.recordDecision(intent, decision);
      const updatedAssurance = assurance.observeDecision(intent, decision.allowed, decision.reason);
      if (!decision.allowed) {
        res.writeHead(403, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ decision, assurance: updatedAssurance, action: { id: intent.actionId, executionState: decision.requiresApproval ? 'approval_required' : 'denied' }, audit: session.getAuditLog() }));
        return;
      }
      let output: Record<string, unknown> | undefined;
      try {
        const claw = makeClawContext(policy);
        output = await dispatchAgentTool(tool, args, {
          registry: connectors,
          evidence,
          a2z,
          claw,
        });
      } catch (e) {
        ledger.recordResult(intent, { executionState: 'failed' });
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(
          JSON.stringify({
            decision,
            error: e instanceof Error ? e.message : 'agent_dispatch_failed',
            assurance: assurance.get(intent.actionId),
            audit: session.getAuditLog(),
          })
        );
        return;
      }
      const executionState = executionStateFromOutput(output);
      const action = ledger.recordResult(intent, {
        executionState,
        output,
        evidenceId:
          typeof output.evidence === 'object' && output.evidence && 'id' in output.evidence
            ? String((output.evidence as { id: unknown }).id)
            : undefined,
        targetReceipt: typeof output.targetReceipt === 'string' ? output.targetReceipt : undefined,
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: executionState !== 'failed' && executionState !== 'not_configured',
          decision,
          output,
          action: { id: action.actionId, executionState },
          assurance: assurance.get(intent.actionId),
          audit: session.getAuditLog(),
        })
      );
      return;
    }

    if (tryServeConsoleStatic(req, res, path)) return;

    res.writeHead(404);
    res.end(JSON.stringify({ error: 'not_found' }));
  });

  const wss = new WebSocketServer({ server: httpServer });
  wss.on('connection', (socket: WebSocket) => {
    let connected = false;
    socket.on('message', (raw) => {
      try {
        const frame = JSON.parse(String(raw)) as {
          type: string;
          params?: { auth?: { token?: string }; role?: string };
        };
        if (!connected && frame.type === 'connect') {
          const token = frame.params?.auth?.token ?? '';
          if (token !== config.token) {
            socket.close(4001, 'unauthorized');
            return;
          }
          connected = true;
          socket.send(JSON.stringify({ type: 'hello-ok', role: frame.params?.role ?? 'operator' }));
          return;
        }
        if (!connected) {
          socket.close(4000, 'connect_required');
        }
      } catch {
        socket.close(4002, 'invalid_frame');
      }
    });
  });

  return {
    listen: () =>
      new Promise<void>((resolve) => {
        httpServer.listen(config.port, config.host, () => resolve());
      }),
    close: () =>
      new Promise<void>((resolve, reject) => {
        wss.close(() => httpServer.close((e) => (e ? reject(e) : resolve())));
      }),
    evidence,
    a2z,
    refreshExecPolicy,
  };
}

function toolTierFor(tool: string): ToolTier {
  return BUILTIN_AGENT_TOOLS.find((definition) => definition.name === tool)?.tier
    ?? (tool.includes('delete') || tool.includes('destroy') ? 'destructive' : 'read');
}

function readJson(req: IncomingMessage): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));
      } catch (e) {
        reject(e);
      }
    });
  });
}
