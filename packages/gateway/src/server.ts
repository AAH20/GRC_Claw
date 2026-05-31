import { createServer, type IncomingMessage, type ServerResponse } from 'node:http';
import { WebSocketServer, type WebSocket } from 'ws';
import { A2ZSocConnector, loadA2ZConfigFromEnv } from '@grc-claw/a2z-connector';
import { AgentSession, ExecPolicy } from '@grc-claw/agent-runtime';
import { EvidenceStore } from '@grc-claw/evidence';
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
import { IdempotencyCache } from './idempotency.js';

export interface GatewayConfig {
  host: string;
  port: number;
  token: string;
}

export function createGateway(config: GatewayConfig) {
  const dedupe = new IdempotencyCache();
  const evidence = new EvidenceStore();
  const a2z = new A2ZSocConnector(loadA2ZConfigFromEnv());
  const execPolicy = new ExecPolicy();

  function authOk(req: IncomingMessage): boolean {
    const header = req.headers['x-grc-claw-token'] ?? req.headers.authorization;
    const token =
      typeof header === 'string' && header.startsWith('Bearer ')
        ? header.slice(7)
        : String(header ?? '');
    return token === config.token;
  }

  const httpServer = createServer(async (req, res) => {
    const path = req.url?.split('?')[0] ?? '/';

    if (path === '/health') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(
        JSON.stringify({
          ok: true,
          service: 'grc-claw-gateway',
          a2z_soc_mode: process.env.A2Z_SOC_MODE ?? 'demo',
          agentic_ai_security: true,
          cloud_security_integration: true,
          iso_42001_aims: true,
          cloud_sources: CLOUD_INGEST_SOURCES,
          marketing: 'OpenClaw for GRC — pairs with a2z-soc.com',
        })
      );
      return;
    }

    if (path === '/api/frameworks' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ packs: listFrameworkPacks() }));
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
      const session = new AgentSession(String(body.sessionId ?? 'default'), execPolicy);
      const decision = await session.invoke({
        tool: String(body.tool ?? ''),
        args: (body.args as Record<string, unknown>) ?? {},
        approvalToken: body.approvalToken as string | undefined,
        idempotencyKey: idem || undefined,
      });
      res.writeHead(decision.allowed ? 200 : 403, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ decision, audit: session.getAuditLog() }));
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
  };
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
