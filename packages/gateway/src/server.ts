import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { timingSafeEqual } from 'node:crypto';
import { join } from 'node:path';
import { WebSocketServer, type WebSocket } from 'ws';
import { A2ZSocConnector, loadA2ZConfigFromEnv } from '@grc-claw/a2z-connector';
import { AgentSession, BUILTIN_AGENT_TOOLS, type ExecPolicy, PersistentMemoryStore, type ToolTier } from '@grc-claw/agent-runtime';
import { getConnectorRegistry, isConnectorTool } from '@grc-claw/connectors';
import { ActionLedger, createAssuranceEnvelope, EvidenceStore, type ActionLedgerEvent } from '@grc-claw/evidence';
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
import { dispatchAgentTool, executionStateFromOutput, setSecurityGraph } from './agent-dispatch.js';
import { createClawDispatchContext } from './skill-runtime.js';
import { GatewayAssuranceGraph } from './assurance.js';
import { initSecurityGraph } from './graph-init.js';
import { getSkillById, listSkills } from '@grc-claw/skill-executor';
import { createRateLimiter } from './rate-limiter.js';
import { applySecurityHeaders } from './security-headers.js';
import { metricsCollector } from './metrics.js';
import { initPersistence, getPersistence, isPersistenceEnabled, closePersistence } from './persistence-init.js';
import type { PersistenceLayer } from '@grc-claw/persistence';
import { MonteCarloEngine, FAIRCalculator, RiskRegister } from '@grc-claw/risk-quantification';
import { EntityManager } from '@grc-claw/entity-management';
import { ACCMEngine, type FrameworkCode as ACCMFrameworkCode, type ControlRecord as ACCMControlRecord, type GapDetector } from '@grc-claw/accm';
import { AgentBuilder, PREBUILT_AGENTS, type AgentDefinition } from '@grc-claw/agent-builder';
import { FrameworkCrosswalk } from '@grc-claw/framework-crosswalk';
import { ChatGRC } from '@grc-claw/chat-grc';
import { BoardReportGenerator } from '@grc-claw/board-reporting';
import { VendorRegistry } from '@grc-claw/third-party-risk';
import { QuestionnaireAutomation, QuestionnaireAnswerEngine } from '@grc-claw/questionnaire-automation';
import { ComplianceProver } from '@grc-claw/zk-compliance';
import { AgentTracer } from '@grc-claw/observability';

const REQUEST_TIMEOUT_MS = 30_000;
const MAX_BODY_BYTES = 1 * 1024 * 1024;

// SOC event broadcaster — pushes normalized events to all subscribed WS clients
const socClients = new Set<WebSocket>();

// Compliance update broadcaster — pushes real-time compliance posture changes
const complianceClients = new Set<WebSocket>();

function broadcastSocEvent(event: unknown): void {
  const msg = JSON.stringify({ type: 'soc_event', data: event, ts: new Date().toISOString() });
  for (const client of socClients) {
    try {
      if (client.readyState === 1 /* OPEN */) {
        client.send(msg);
      } else {
        socClients.delete(client);
      }
    } catch {
      socClients.delete(client);
    }
  }
}

function broadcastComplianceUpdate(compliance: Record<string, unknown>): void {
  const msg = JSON.stringify({ type: 'compliance_update', data: compliance, ts: new Date().toISOString() });
  for (const client of complianceClients) {
    try {
      if (client.readyState === 1 /* OPEN */) {
        client.send(msg);
      } else {
        complianceClients.delete(client);
      }
    } catch {
      complianceClients.delete(client);
    }
  }
}

export interface GatewayConfig {
  host: string;
  port: number;
  token: string;
}

export function createGateway(config: GatewayConfig, persistence?: PersistenceLayer | null) {
  const seededGraph = initSecurityGraph();
  setSecurityGraph(seededGraph);

  const tracer = new AgentTracer({
    serviceName: 'grc-claw-gateway',
    version: '1.0.0',
    environment: process.env.NODE_ENV ?? 'development',
  });

  const dedupe = new IdempotencyCache();
  const pg = persistence ?? getPersistence();
  const evidence = new EvidenceStore(pg?.database);
  const ledger = new ActionLedger(
    process.env.GRC_CLAW_ACTION_LEDGER_PATH?.trim() || join(process.cwd(), '.grc_memory', 'action-ledger.ndjson')
  );
  const assurance = new GatewayAssuranceGraph();
  const a2z = new A2ZSocConnector(loadA2ZConfigFromEnv());
  const connectors = getConnectorRegistry();
  const store = new PersistentMemoryStore(process.env.GRC_CLAW_MEMORY_DIR?.trim() || '.grc_memory');
  const rateLimiter = createRateLimiter();
  const riskRegister = new RiskRegister();
  const entityManager = new EntityManager(pg?.database);
  const agentBuilder = new AgentBuilder(pg?.database ? { database: pg.database } : undefined);
  const frameworkCrosswalk = new FrameworkCrosswalk();
  const chatGRC = new ChatGRC();

  // Load persisted data from database into in-memory stores on startup
  if (pg?.database) {
    evidence.loadFromDatabase().catch((err) => {
      console.warn('[STARTUP] evidence.loadFromDatabase failed:', err instanceof Error ? err.message : err);
    });
    entityManager.loadFromDatabase().catch((err) => {
      console.warn('[STARTUP] entityManager.loadFromDatabase failed:', err instanceof Error ? err.message : err);
    });
    agentBuilder.initializeStore().catch((err) => {
      console.warn('[STARTUP] agentBuilder.initializeStore failed:', err instanceof Error ? err.message : err);
    });
  }

  // ACCM GapDetector: bridges framework packs + evidence store to ACCMEngine
  const accmGapDetector: GapDetector = {
    async getControls(frameworkCode: ACCMFrameworkCode): Promise<ACCMControlRecord[]> {
      const packs = listFrameworkPacks();
      const records: ACCMControlRecord[] = [];
      for (const pack of packs) {
        if (pack.code !== frameworkCode) continue;
        for (const ctrl of pack.controls) {
          const evidenceItems = evidence.listByControl(ctrl.id);
          records.push({
            controlId: ctrl.id,
            controlCode: ctrl.controlCode,
            title: ctrl.title,
            frameworkCode: frameworkCode as ACCMFrameworkCode,
            implemented: evidenceItems.length > 0,
            evidenceHashes: evidenceItems.map((e) => e.sha256),
            lastVerifiedAt: new Date().toISOString(),
            owner: 'system',
          });
        }
      }
      return records;
    },
  };
  const accmEngine = new ACCMEngine(accmGapDetector, { tenantId: 'default', autoRemediate: true });
  const boardReporter = new BoardReportGenerator();
  const vendorRegistry = new VendorRegistry();
  const questionnaireAutomation = new QuestionnaireAutomation();
  const questionnaireAnswerEngine = new QuestionnaireAnswerEngine();
  const complianceProver = new ComplianceProver();

  let execPolicy!: ExecPolicy;

  async function persistAssuranceEnvelope(
    intent: ActionLedgerEvent,
    decision: ActionLedgerEvent,
    result: ActionLedgerEvent | undefined,
    snapshot: ReturnType<GatewayAssuranceGraph['get']>
  ): Promise<{ envelopeId?: string; actionId: string; executionState: 'recorded' | 'not_configured' | 'failed' }> {
    const envelope = createAssuranceEnvelope({
      intent,
      decision,
      result,
      identity: snapshot ? { agentDid: snapshot.agentDid, status: snapshot.identityStatus } : undefined,
      assurance: snapshot
        ? {
            riskScore: snapshot.risk.overallRisk,
            blastRadiusImpact: snapshot.blastRadius?.impactScore,
            controlId: snapshot.blastRadius?.controlId,
          }
        : undefined,
    });
    try {
      return await a2z.recordAssuranceEnvelope(
        intent.tenantId,
        envelope,
        `assurance-${intent.actionId}`
      );
    } catch {
      return { actionId: intent.actionId, executionState: 'failed' };
    }
  }

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

    const secretBuf = Buffer.from(config.token, 'utf8');
    const tokenBuf = Buffer.from(token, 'utf8');

    if (secretBuf.length !== tokenBuf.length) {
      logAuthFailure(req, 'length_mismatch');
      return false;
    }

    const match = timingSafeEqual(secretBuf, tokenBuf);
    if (!match) {
      logAuthFailure(req, 'token_mismatch');
    }
    return match;
  }

  function logAuthFailure(req: IncomingMessage, reason: string): void {
    const ip = req.headers['x-forwarded-for'] ?? req.socket.remoteAddress ?? 'unknown';
    const endpoint = req.url ?? '/';
    console.warn(
      `[SECURITY] auth_failure ip=${ip} reason=${reason} endpoint=${endpoint} timestamp=${new Date().toISOString()}`
    );
  }

  const httpServer = createServer(async (req, res) => {
    applySecurityHeaders(res);
    applyCors(res);

    const requestStart = Date.now();
    metricsCollector.incCounter('grc_gateway_requests_total');

    let timedOut = false;
    const timeout = setTimeout(() => {
      timedOut = true;
      try {
        if (!res.headersSent) {
          res.writeHead(508, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'request_timeout' }));
        }
      } catch {}
    }, REQUEST_TIMEOUT_MS);
    const clearTimer = () => {
      clearTimeout(timeout);
      const duration = Date.now() - requestStart;
      metricsCollector.observeHistogram('grc_request_duration_ms', duration);
    };
    res.on('finish', clearTimer);
    res.on('close', clearTimer);

    if (req.method === 'OPTIONS') {
      res.writeHead(204);
      res.end();
      return;
    }

    if (timedOut) return;

    if (!rateLimiter.middleware(req, res, req.method ?? 'GET')) return;

    if (timedOut) return;

    const path = req.url?.split('?')[0] ?? '/';

    if (path === '/metrics' && req.method === 'GET') {
      const packs = listFrameworkPacks();
      let totalControls = 0;
      let controlsWithEvidence = 0;
      for (const pack of packs) {
        for (const ctrl of pack.controls) {
          totalControls++;
          if (evidence.listByControl(ctrl.id).length > 0) controlsWithEvidence++;
        }
      }
      const realScore = totalControls > 0 ? controlsWithEvidence / totalControls : 0;
      metricsCollector.setGauge('grc_compliance_score', Math.round(realScore * 100) / 100);
      const metricsText = metricsCollector.getPrometheusFormat();
      res.writeHead(200, { 'Content-Type': 'text/plain; version=0.0.4; charset=utf-8' });
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
          persistence: isPersistenceEnabled() ? 'postgresql' : 'demo',
          soc_stream: 'ws://host/ws — subscribe with {"type":"subscribe","channel":"soc_events","token":"<token>"} to receive real-time normalized SOC events',
          marketing: 'The OSS chassis for ISO 42001-compliant agentic AI — pairs with a2zsoc.com',
        })
      );
      return;
    }

    if (path === '/api/db/health') {
      if (!authOk(req)) {
        res.writeHead(401);
        res.end(JSON.stringify({ error: 'unauthorized' }));
        return;
      }
      if (!pg) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, mode: 'demo', postgresql: false, message: 'No DATABASE_URL — running in demo mode' }));
        return;
      }
      try {
        const healthy = await pg.database.healthCheck();
        res.writeHead(healthy ? 200 : 503, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: healthy, mode: 'production', postgresql: true }));
      } catch {
        res.writeHead(503, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, mode: 'production', postgresql: true, error: 'health_check_failed' }));
      }
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
      let events: unknown[] = ledger.list(limit);
      let source = 'in-memory';
      if (pg) {
        try {
          const { rows } = await pg.database.query(
            'SELECT * FROM action_ledger ORDER BY created_at DESC LIMIT $1',
            [limit]
          );
          if (rows.length > 0) {
            events = rows;
            source = 'postgresql';
          }
        } catch {
          // fall back to in-memory
        }
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, source, events, integrity: ledger.verify() }));
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
      let body: Record<string, unknown>;
      try {
        body = await readJson(req);
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'invalid_body';
        const status = msg === 'request_body_too_large' ? 413 : 400;
        res.writeHead(status, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
        return;
      }
      const validation = validateBody(body, ['skillId', 'task']);
      if (!validation.valid) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'missing_required_field', field: validation.missing }));
        return;
      }
      const skillId = String(body.skillId ?? '');
      const task = String(body.task ?? '');
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
      const skillTrace = tracer.startTrace(`skill.${skillId}`, {
        'tool.name': skillId,
        'agent.session_id': session.sessionId,
        'tool.tier': 'read',
        'policy.result': 'allow',
      });
      const claw = makeClawContext(policy);
      let result: Awaited<ReturnType<typeof claw.runSkill>>;
      try {
        result = await claw.runSkill({
          skillId,
          task,
          llmProviderId: typeof body.llmProviderId === 'string' ? body.llmProviderId : undefined,
          maxSteps: typeof body.maxSteps === 'number' ? body.maxSteps : undefined,
          readOnlyTools: body.readOnlyTools !== false,
        });
        tracer.endSpan(skillTrace.spanId, result.ok ? 'OK' : 'ERROR');
      } catch (e) {
        tracer.endSpan(skillTrace.spanId, 'ERROR', e instanceof Error ? e.message : 'skill_failed');
        throw e;
      }
      metricsCollector.incCounter('grc_agent_invocations_total');
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
      let body: Record<string, unknown>;
      try {
        body = await readJson(req);
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'invalid_body';
        const status = msg === 'request_body_too_large' ? 413 : 400;
        res.writeHead(status, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
        return;
      }
      const validation = validateBody(body, ['source']);
      if (!validation.valid) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'missing_required_field', field: validation.missing }));
        return;
      }
      const source = String(body.source ?? '') as IngestSource;
      const tenantId = Number(body.tenantId ?? 1);
      const payload = body.payload;
      const ingestSpan = tracer.startTrace(`ingest.normalize.${source}`, {
        'tool.name': `ingest.${source}`,
        'agent.tenant_id': String(tenantId),
        'policy.result': 'allow',
      });
      const event = normalizeBySource(source, payload, tenantId);
      if (!event) {
        tracer.endSpan(ingestSpan.spanId, 'ERROR', 'normalize_failed');
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'normalize_failed', source }));
        return;
      }
      tracer.setAttributes(ingestSpan.spanId, { 'evidence.type': event.eventType });
      // Broadcast normalized event to all subscribed SOC WebSocket clients
      broadcastSocEvent(event);
      const impact = await a2z.mapSecurityEventToControls({
        eventUuid: event.eventUuid,
        eventType: event.eventType,
        severity: event.severity,
        sourceSystem: event.sourceSystem,
        tenantId: event.tenantId,
        eventData: event.eventData,
      });
      tracer.endSpan(ingestSpan.spanId, 'OK');
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
      let body: Record<string, unknown>;
      try {
        body = await readJson(req);
      } catch (e) {
        const msg = e instanceof Error ? e.message : 'invalid_body';
        const status = msg === 'request_body_too_large' ? 413 : 400;
        res.writeHead(status, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: msg }));
        return;
      }
      const validation = validateBody(body, ['tool']);
      if (!validation.valid) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'missing_required_field', field: validation.missing }));
        return;
      }
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
        const decisionEvent = ledger.recordDecision(intent, decision);
        const updatedAssurance = assurance.observeDecision(intent, false, decision.reason);
        const assuranceReceipt = await persistAssuranceEnvelope(intent, decisionEvent, undefined, updatedAssurance);
        res.writeHead(403, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ decision, assurance: updatedAssurance, assuranceReceipt, action: { id: intent.actionId, executionState: 'approval_required' }, audit: session.getAuditLog() }));
        return;
      }
      const decision = await session.invoke({
        tool,
        args,
        approvalToken: body.approvalToken as string | undefined,
        idempotencyKey: idem || undefined,
      });
      const decisionEvent = ledger.recordDecision(intent, decision);
      const updatedAssurance = assurance.observeDecision(intent, decision.allowed, decision.reason);
      if (!decision.allowed) {
        const assuranceReceipt = await persistAssuranceEnvelope(intent, decisionEvent, undefined, updatedAssurance);
        res.writeHead(403, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ decision, assurance: updatedAssurance, assuranceReceipt, action: { id: intent.actionId, executionState: decision.requiresApproval ? 'approval_required' : 'denied' }, audit: session.getAuditLog() }));
        return;
      }
      let output: Record<string, unknown> | undefined;
      const traceSpan = tracer.startTrace(`agent.tool.${tool}`, {
        'agent.did': typeof body.agentId === 'string' ? body.agentId : 'system',
        'agent.session_id': sessionId,
        'tool.name': tool,
        'tool.tier': toolTierFor(tool),
        'policy.result': decision.allowed ? 'allow' : 'deny',
      });
      try {
        const claw = makeClawContext(policy);
        output = await dispatchAgentTool(tool, args, {
          registry: connectors,
          evidence,
          a2z,
          claw,
          persistence: pg,
          agentBuilder,
          chatGrc: chatGRC,
        });
        tracer.endSpan(traceSpan.spanId, 'OK');
        metricsCollector.incCounter('grc_agent_invocations_total');
      } catch (e) {
        tracer.endSpan(traceSpan.spanId, 'ERROR', e instanceof Error ? e.message : 'dispatch_failed');
        const resultEvent = ledger.recordResult(intent, { executionState: 'failed' });
        const assuranceReceipt = await persistAssuranceEnvelope(intent, decisionEvent, resultEvent, assurance.get(intent.actionId));
        res.writeHead(502, { 'Content-Type': 'application/json' });
        res.end(
          JSON.stringify({
            decision,
            error: e instanceof Error ? e.message : 'agent_dispatch_failed',
            assurance: assurance.get(intent.actionId),
            assuranceReceipt,
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
      const assuranceReceipt = await persistAssuranceEnvelope(intent, decisionEvent, action, assurance.get(intent.actionId));
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: executionState !== 'failed' && executionState !== 'not_configured',
          decision,
          output,
          action: { id: action.actionId, executionState },
          assurance: assurance.get(intent.actionId),
          assuranceReceipt,
          audit: session.getAuditLog(),
        })
      );
      return;
    }

    // --- Risk Quantification Endpoints ---
    if (req.method === 'POST' && path === '/api/risk/monte-carlo') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const engine = new MonteCarloEngine(body.scenario as unknown as import('@grc-claw/risk-quantification').RiskScenario, { iterations: body.iterations as number, seed: body.seed as number });
        const result = engine.run();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/risk/fair') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const calc = new FAIRCalculator(body.scenario as unknown as import('@grc-claw/risk-quantification').RiskScenario, { iterations: body.iterations as number, seed: body.seed as number });
        const result = calc.calculate();
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/risk/register') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const entries = riskRegister.getAllEntries();
      const metrics = riskRegister.portfolioMetrics();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, entries, metrics }));
      return;
    }
    if (req.method === 'POST' && path === '/api/risk/scenarios') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const entry = riskRegister.addScenario(body as unknown as import('@grc-claw/risk-quantification').RiskScenario);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, entry }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/risk/heatmap') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const heatmap = riskRegister.generateHeatMap(5);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, ...heatmap }));
      return;
    }

    // --- Entity Management Endpoints ---
    if (req.method === 'POST' && path === '/api/entities') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const entity = entityManager.createEntity(body as Parameters<typeof entityManager.createEntity>[0]);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, entity }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && /^\/api\/entities\/?$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const entities = entityManager.listEntities();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, entities }));
      return;
    }
    if (req.method === 'GET' && /^\/api\/entities\/[^/]+$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const id = path.split('/').pop()!;
      const entity = entityManager.getEntity(id);
      if (!entity) { res.writeHead(404); res.end(JSON.stringify({ error: 'not_found' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, entity }));
      return;
    }
    if (req.method === 'POST' && /^\/api\/entities\/[^/]+\/relationships$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const entityId = path.split('/')[3];
        const body = await readJson(req);
        const rel = entityManager.addRelationship(entityId, body.childEntityId as string, body.relationshipType as 'ownership' | 'subsidiary' | 'division' | 'branch' | 'joint_venture' | 'franchise');
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, relationship: rel }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && /^\/api\/entities\/[^/]+\/compliance$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const entityId = path.split('/')[3];
      const statuses = entityManager.getComplianceStatuses(entityId);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, statuses }));
      return;
    }
    if (req.method === 'GET' && path === '/api/entities/consolidated-report') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const report = entityManager.getConsolidatedReport();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, report }));
      return;
    }

    if (tryServeConsoleStatic(req, res, path)) return;

    // --- ACCM Endpoints ---
    if (req.method === 'POST' && path === '/api/accm/detect-gaps') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const frameworkCode = String(body.frameworkCode ?? 'iso27001') as ACCMFrameworkCode;
        const gaps = await accmEngine.detectGaps(frameworkCode);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, frameworkCode, gapsDetected: gaps.length, gaps }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/accm/remediate') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const frameworkCode = String(body.frameworkCode ?? 'iso27001') as ACCMFrameworkCode;
        const gaps = await accmEngine.detectGaps(frameworkCode);
        const results = [];
        for (const gap of gaps) {
          const workflow = accmEngine.createRemediationPlan(gap);
          const result = await accmEngine.executeRemediation(workflow);
          results.push({ gapId: gap.id, controlCode: gap.controlCode, workflowId: workflow.id, result });
        }
        // Broadcast compliance update after remediation
        const updatedPosture = computeCompliancePosture();
        const overallScore = Object.values(updatedPosture).reduce((sum, fw) => sum + (fw as { compliance_pct: number }).compliance_pct, 0) / Math.max(1, Object.keys(updatedPosture).length);
        broadcastComplianceUpdate({
          overall_score: Math.round(overallScore * 10) / 10,
          frameworks: updatedPosture,
          trigger: 'accm_remediate',
          frameworkCode,
          remediationsApplied: results.length,
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, frameworkCode, remediations: results }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/accm/verify') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const workflowId = String(body.workflowId ?? '');
        const workflow = accmEngine.getWorkflow(workflowId);
        if (!workflow) {
          res.writeHead(404); res.end(JSON.stringify({ error: 'workflow_not_found', workflowId }));
          return;
        }
        const verification = await accmEngine.verifyRemediation(workflow);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, verification }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && path === '/api/accm/full-cycle') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const frameworkCode = String(body.frameworkCode ?? 'iso27001') as ACCMFrameworkCode;
        const report = await accmEngine.fullCycle(frameworkCode);
        // Broadcast compliance update to all subscribed clients
        const updatedPosture = computeCompliancePosture();
        const overallScore = Object.values(updatedPosture).reduce((sum, fw) => sum + (fw as { compliance_pct: number }).compliance_pct, 0) / Math.max(1, Object.keys(updatedPosture).length);
        broadcastComplianceUpdate({
          overall_score: Math.round(overallScore * 10) / 10,
          frameworks: updatedPosture,
          trigger: 'accm_full_cycle',
          frameworkCode,
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, report }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    // --- Agent Builder Endpoints ---
    if (req.method === 'GET' && path === '/api/agents') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const agents = agentBuilder.listAgents();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, agents, count: agents.length }));
      return;
    }
    if (req.method === 'GET' && /^\/api\/agents\/[^/]+$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const agentId = decodeURIComponent(path.split('/').pop()!);
      const agent = agentBuilder.getAgent(agentId);
      if (!agent) { res.writeHead(404); res.end(JSON.stringify({ ok: false, error: 'agent_not_found', agentId })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, agent }));
      return;
    }
    if (req.method === 'POST' && path === '/api/agents') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const definition = body as unknown as AgentDefinition;
        const agent = agentBuilder.createAgent(definition);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, agent }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ ok: false, error: msg }));
      }
      return;
    }
    if (req.method === 'POST' && /^\/api\/agents\/[^/]+\/trigger$/.test(path)) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const agentId = decodeURIComponent(path.split('/')[3]!);
      try {
        let body: Record<string, unknown> = {};
        try { body = await readJson(req); } catch { /* empty context is fine */ }
        const run = await agentBuilder.triggerAgent(agentId, body);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, run }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ ok: false, error: msg }));
      }
      return;
    }

    // --- Framework Crosswalk Endpoints ---
    const crosswalkMatch = path.match(/^\/api\/crosswalk\/([^/]+)\/([^/]+)$/);
    if (req.method === 'GET' && crosswalkMatch) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const source = decodeURIComponent(crosswalkMatch[1]!);
      const target = decodeURIComponent(crosswalkMatch[2]!);
      const report = frameworkCrosswalk.generateCrosswalk(source, target);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, report }));
      return;
    }
    if (req.method === 'GET' && path === '/api/crosswalk/overlaps') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const pairs = frameworkCrosswalk.getSupportedPairs();
      const overlaps = pairs.map(([s, t]) => frameworkCrosswalk.findOverlaps(s, t));
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, overlaps }));
      return;
    }
    if (req.method === 'POST' && path === '/api/crosswalk/coverage') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const controlIds = (body.controlIds as string[]) ?? [];
        const frameworks = (body.frameworks as string[]) ?? [];
        const coverage = frameworkCrosswalk.calculateMultiFrameworkCoverage(controlIds, frameworks);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, coverage }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    // --- Chat GRC Endpoints ---
    if (req.method === 'POST' && path === '/api/chat') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const message = String(body.message ?? '');
        const context = (body.context as Record<string, unknown>) ?? {};
        const sessionId = typeof body.sessionId === 'string' ? body.sessionId : undefined;
        const chatContext = {
          frameworks: (context.frameworks as string[]) ?? [],
          controls: (context.controls as string[]) ?? [],
          evidence: (context.evidence as string[]) ?? [],
          risks: (context.risks as string[]) ?? [],
        };
        const response = await chatGRC.processMessage(message, chatContext, sessionId);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, response }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }
    if (req.method === 'GET' && path === '/api/chat/sessions') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const sessions = chatGRC.listSessions();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, sessions }));
      return;
    }
    if (req.method === 'POST' && path === '/api/chat/sessions') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const initialContext = (body.context as Record<string, unknown>) ?? {};
        const chatContext = {
          frameworks: (initialContext.frameworks as string[]) ?? [],
          controls: (initialContext.controls as string[]) ?? [],
          evidence: (initialContext.evidence as string[]) ?? [],
          risks: (initialContext.risks as string[]) ?? [],
        };
        const session = chatGRC.createSession(chatContext);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, session }));
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        res.writeHead(400); res.end(JSON.stringify({ error: msg }));
      }
      return;
    }

    // ─── Board Reporting (#8) ─────────────────────────────────────────────────
    if (req.method === 'GET' && path === '/api/reporting/board') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const reqUrl = new URL(req.url ?? '', 'http://local');
      const type = (reqUrl.searchParams.get('type') ?? 'board_summary') as Parameters<BoardReportGenerator['generateReport']>[0];
      const period = reqUrl.searchParams.get('period') ?? new Date().toISOString().substring(0, 7);
      const report = boardReporter.generateReport(type, period);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, report }));
      return;
    }
    if (req.method === 'GET' && path === '/api/reporting/dashboard') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, dashboard: boardReporter.getExecutiveDashboard() }));
      return;
    }

    // ─── Third-Party Risk (#9) ────────────────────────────────────────────────
    if (req.method === 'GET' && path === '/api/vendors') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, vendors: vendorRegistry.listVendors() }));
      return;
    }
    if (req.method === 'POST' && path === '/api/vendors') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const vendor = vendorRegistry.registerVendor(body as Parameters<VendorRegistry['registerVendor']>[0]);
        vendorRegistry.startMonitoring(vendor.id);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, vendor }));
      } catch (e: unknown) { res.writeHead(400); res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) })); }
      return;
    }
    if (req.method === 'GET' && path.startsWith('/api/vendors/') && path.endsWith('/risk-score')) {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const vendorId = path.split('/')[3];
      const score = vendorRegistry.calculateRiskScore(vendorId ?? '');
      if (!score) { res.writeHead(404); res.end(JSON.stringify({ error: 'vendor_not_found' })); return; }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, score }));
      return;
    }

    // ─── Questionnaire Automation (#4) ───────────────────────────────────────
    if (req.method === 'POST' && path === '/api/questionnaire/import') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const csvContent = String(body.csv ?? '');
        if (!csvContent) { res.writeHead(400); res.end(JSON.stringify({ error: 'csv field required' })); return; }
        const questionnaire = questionnaireAutomation.parseCSVQuestions(csvContent);
        res.writeHead(201, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, questionnaire }));
      } catch (e: unknown) { res.writeHead(400); res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) })); }
      return;
    }
    if (req.method === 'POST' && path === '/api/questionnaire/auto-answer') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req);
        const questionnaireId = String(body.questionnaireId ?? '');
        const response = questionnaireAutomation.autoAnswer(questionnaireId);
        if (!response) { res.writeHead(404); res.end(JSON.stringify({ error: 'questionnaire_not_found' })); return; }
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, response }));
      } catch (e: unknown) { res.writeHead(400); res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) })); }
      return;
    }

    // ─── Observability Trace Endpoints ─────────────────────────────────────────
    if (path === '/api/traces' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const url = new URL(req.url ?? '', 'http://local');
      const limit = Number(url.searchParams.get('limit') ?? 50);
      const stats = tracer.getStats();
      const otlp = tracer.exportOTLP();
      const allSpans = otlp.resourceSpans.flatMap((r) => r.scopeSpans.flatMap((s) => s.spans));
      const traceIds = [...new Set(allSpans.map((s) => s.traceId))];
      const recentTraces = traceIds.slice(-limit).map((traceId) => {
        const spans = tracer.getTrace(traceId);
        const first = spans[0];
        const last = spans[spans.length - 1];
        return {
          traceId,
          name: first?.name ?? 'unknown',
          spanCount: spans.length,
          startTime: first?.startTime,
          endTime: last?.endTime,
          status: last?.status ?? 'UNSET',
          durationMs: last?.durationMs,
        };
      });
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, traces: recentTraces, stats }));
      return;
    }
    if (path === '/api/traces/metrics' && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const stats = tracer.getStats();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        ok: true,
        metrics: {
          totalTraces: stats.totalTraces,
          totalSpans: stats.totalSpans,
          avgSpanDurationMs: stats.avgSpanDurationMs,
          errorRate: Math.round(stats.errorRate * 10000) / 100,
          totalMetricEvents: stats.totalMetrics,
        },
      }));
      return;
    }
    const traceDetailMatch = path.match(/^\/api\/traces\/([^/]+)$/);
    if (traceDetailMatch && req.method === 'GET') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      const traceId = decodeURIComponent(traceDetailMatch[1]!);
      const spans = tracer.getTrace(traceId);
      if (spans.length === 0) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: 'trace_not_found', traceId }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true, traceId, spans }));
      return;
    }

    // ─── ZK Proof Generation (#6) ─────────────────────────────────────────────
    if (req.method === 'POST' && path === '/api/zk/prove') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req) as { controlId: string; frameworkCode: string; controlStatus: string; evidenceHashes: string[] };
        const proof = await complianceProver.generateProof({
          controlId: body.controlId,
          frameworkCode: body.frameworkCode,
          controlStatus: body.controlStatus,
          evidenceHashes: body.evidenceHashes ?? [],
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, proof }));
      } catch (e: unknown) { res.writeHead(400); res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) })); }
      return;
    }
    if (req.method === 'POST' && path === '/api/zk/verify') {
      if (!authOk(req)) { res.writeHead(401); res.end(JSON.stringify({ error: 'unauthorized' })); return; }
      try {
        const body = await readJson(req) as unknown as Parameters<ComplianceProver['verifyProof']>[0];
        const result = await complianceProver.verifyProof(body);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, result }));
      } catch (e: unknown) { res.writeHead(400); res.end(JSON.stringify({ error: e instanceof Error ? e.message : String(e) })); }
      return;
    }

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
          channel?: string;
          token?: string;
          params?: { auth?: { token?: string }; role?: string };
        };
        if (!connected && frame.type === 'connect') {
          const token = frame.params?.auth?.token ?? '';
          const secretBuf = Buffer.from(config.token, 'utf8');
          const tokenBuf = Buffer.from(token, 'utf8');
          const tokenValid = secretBuf.length === tokenBuf.length && timingSafeEqual(secretBuf, tokenBuf);
          if (!tokenValid) {
            const wsIp = (socket as unknown as { _socket?: { remoteAddress?: string } })._socket?.remoteAddress ?? 'unknown';
            console.warn(
              `[SECURITY] auth_failure ip=${wsIp} reason=ws_token_mismatch endpoint=/ws timestamp=${new Date().toISOString()}`
            );
            socket.close(4001, 'unauthorized');
            return;
          }
          connected = true;
          socket.send(JSON.stringify({ type: 'hello-ok', role: frame.params?.role ?? 'operator' }));
          return;
        }
        if (frame.type === 'subscribe' && frame.channel === 'soc_events') {
          const token = frame.token ?? '';
          const secretBuf = Buffer.from(config.token, 'utf8');
          const tokenBuf = Buffer.from(token, 'utf8');
          const authed = secretBuf.length === tokenBuf.length && timingSafeEqual(secretBuf, tokenBuf);
          if (authed) {
            socClients.add(socket);
            socket.send(JSON.stringify({ type: 'subscribed', channel: 'soc_events', message: 'Streaming normalized SOC events' }));
          } else {
            socket.send(JSON.stringify({ type: 'error', message: 'unauthorized' }));
          }
          return;
        }
        if (frame.type === 'subscribe' && frame.channel === 'compliance_updates') {
          const token = frame.token ?? '';
          const secretBuf = Buffer.from(config.token, 'utf8');
          const tokenBuf = Buffer.from(token, 'utf8');
          const authed = secretBuf.length === tokenBuf.length && timingSafeEqual(secretBuf, tokenBuf);
          if (authed) {
            complianceClients.add(socket);
            // Send initial compliance posture immediately on subscription
            const initialPosture = computeCompliancePosture();
            const overallScore = Object.values(initialPosture).reduce((sum, fw) => sum + (fw as { compliance_pct: number }).compliance_pct, 0) / Math.max(1, Object.keys(initialPosture).length);
            socket.send(JSON.stringify({
              type: 'compliance_update',
              data: { overall_score: Math.round(overallScore * 10) / 10, frameworks: initialPosture, ts: new Date().toISOString() },
              ts: new Date().toISOString(),
            }));
            socket.send(JSON.stringify({ type: 'subscribed', channel: 'compliance_updates', message: 'Streaming real-time compliance updates' }));
          } else {
            socket.send(JSON.stringify({ type: 'error', message: 'unauthorized' }));
          }
          return;
        }
        if (!connected) {
          socket.close(4000, 'connect_required');
        }
      } catch {
        socket.close(4002, 'invalid_frame');
      }
    });
    socket.on('close', () => { socClients.delete(socket); complianceClients.delete(socket); });
    socket.on('error', () => { socClients.delete(socket); complianceClients.delete(socket); });
  });

  // ─── Periodic SOC heartbeat — broadcast real compliance posture to subscribers ───
  function computeCompliancePosture(): Record<string, { compliance_pct: number; drift_detected: boolean; last_scan: string }> {
    const packs = listFrameworkPacks();
    const frameworks: Record<string, { compliance_pct: number; drift_detected: boolean; last_scan: string }> = {};
    for (const pack of packs) {
      let total = 0;
      let withEvidence = 0;
      for (const ctrl of pack.controls) {
        total++;
        if (evidence.listByControl(ctrl.id).length > 0) withEvidence++;
      }
      frameworks[pack.code] = {
        compliance_pct: total > 0 ? Math.round((withEvidence / total) * 1000) / 10 : 0,
        drift_detected: false,
        last_scan: new Date().toISOString(),
      };
    }
    return frameworks;
  }

  const heartbeatInterval = setInterval(() => {
    if (socClients.size === 0) return;
    broadcastSocEvent({
      type: 'heartbeat',
      id: `heartbeat-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      status: 'alive',
      node_id: `gateway-${config.host}:${config.port}`,
    });
  }, 60_000);

  // ─── Compliance posture summary — broadcast every 5 minutes ─────────────────
  const postureInterval = setInterval(() => {
    if (socClients.size === 0 && complianceClients.size === 0) return;
    const posture = computeCompliancePosture();
    const overallScore = Object.values(posture).reduce((sum, fw) => sum + (fw as { compliance_pct: number }).compliance_pct, 0) / Math.max(1, Object.keys(posture).length);
    const complianceUpdate = {
      type: 'posture_update',
      id: `posture-${Date.now().toString(36)}`,
      timestamp: new Date().toISOString(),
      frameworks: posture,
      node_id: `gateway-${config.host}:${config.port}`,
    };
    broadcastSocEvent(complianceUpdate);
    broadcastComplianceUpdate({
      overall_score: Math.round(overallScore * 10) / 10,
      frameworks: posture,
      trigger: 'periodic_heartbeat',
    });
  }, 300_000);

  return {
    listen: () =>
      new Promise<void>((resolve) => {
        httpServer.listen(config.port, config.host, () => resolve());
      }),
    close: async () => {
      clearInterval(heartbeatInterval);
      clearInterval(postureInterval);
      await closePersistence();
      return new Promise<void>((resolve, reject) => {
        wss.close(() => httpServer.close((e) => (e ? reject(e) : resolve())));
      });
    },
    evidence,
    a2z,
    refreshExecPolicy,
    persistence: pg,
  };
}

function toolTierFor(tool: string): ToolTier {
  return BUILTIN_AGENT_TOOLS.find((definition) => definition.name === tool)?.tier
    ?? (tool.includes('delete') || tool.includes('destroy') ? 'destructive' : 'read');
}

function readJson(req: IncomingMessage): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    let totalBytes = 0;
    req.on('data', (c: Buffer) => {
      totalBytes += c.length;
      if (totalBytes > MAX_BODY_BYTES) {
        req.destroy();
        reject(new Error('request_body_too_large'));
        return;
      }
      chunks.push(c);
    });
    req.on('end', () => {
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));
      } catch (e) {
        reject(e);
      }
    });
    req.on('error', reject);
  });
}

function validateBody(
  body: Record<string, unknown>,
  requiredFields: string[]
): { valid: boolean; missing?: string } {
  for (const field of requiredFields) {
    if (!(field in body)) {
      return { valid: false, missing: field };
    }
  }
  return { valid: true };
}
