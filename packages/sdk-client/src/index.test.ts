import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import { GrcClawClient, GrcClawError, GrcClawTimeoutError } from './index.js';

// ── Helpers ────────────────────────────────────────────────

function mockFetch(handler: (req: Request) => Response | Promise<Response>): () => void {
  const prev = globalThis.fetch;
  globalThis.fetch = async (input: string | URL | Request, init?: RequestInit) => {
    const req = input instanceof Request ? input : new Request(String(input), init);
    return handler(req);
  };
  return () => { globalThis.fetch = prev; };
}

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function bodyOf(req: Request): Promise<Record<string, unknown>> {
  return req.json() as Promise<Record<string, unknown>>;
}

const BASE = 'https://gateway.example.com';
const TOKEN = 'test-token-123';

function makeClient(overrides?: Partial<ConstructorParameters<typeof GrcClawClient>[0]>): GrcClawClient {
  return new GrcClawClient({ baseUrl: BASE, token: TOKEN, retries: 0, ...overrides });
}

// ── Tests ──────────────────────────────────────────────────

describe('GrcClawClient', () => {
  let restore: () => void;

  afterEach(() => restore?.());

  describe('constructor', () => {
    it('strips trailing slashes from baseUrl', () => {
      const client = new GrcClawClient({ baseUrl: 'https://example.com///', token: 'x' });
      const url = (client as unknown as { baseUrl: string }).baseUrl;
      assert.equal(url, 'https://example.com');
    });
  });

  describe('health()', () => {
    it('returns health payload', async () => {
      restore = mockFetch(() => jsonResponse({ ok: true, service: 'grc-claw-gateway' }));
      const client = makeClient();
      const res = await client.health();
      assert.equal(res.ok, true);
      assert.equal(res.service, 'grc-claw-gateway');
    });
  });

  describe('listFrameworks()', () => {
    it('returns packs array', async () => {
      restore = mockFetch(() => jsonResponse({ packs: [{ id: 'iso27001' }] }));
      const client = makeClient();
      const res = await client.listFrameworks();
      assert.equal(res.packs.length, 1);
    });
  });

  describe('normalizeEvent()', () => {
    it('POSTs source + payload', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ ok: true, event: { eventUuid: 'e1' } });
      });
      const client = makeClient();
      const res = await client.normalizeEvent('crowdstrike', { alert: 'malware' }, 7);
      assert.equal(res.ok, true);
      assert.equal(captured.source, 'crowdstrike');
      assert.equal(captured.tenantId, 7);
    });
  });

  describe('invokeAgent()', () => {
    it('sends tool + args + idempotencyKey', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ ok: true, output: {} });
      });
      const client = makeClient();
      await client.invokeAgent('claw.collect_evidence', { framework: 'soc2' }, {
        sessionId: 's1',
        idempotencyKey: 'idem-1',
      });
      assert.equal(captured.tool, 'claw.collect_evidence');
      assert.equal((captured.args as Record<string, unknown>).framework, 'soc2');
      assert.equal(captured.idempotencyKey, 'idem-1');
    });
  });

  describe('listConnectors()', () => {
    it('returns connector list', async () => {
      restore = mockFetch(() => jsonResponse({ ok: true, connectors: [] }));
      const client = makeClient();
      const res = await client.listConnectors();
      assert.equal(res.ok, true);
    });
  });

  describe('createActionLedgerEvent()', () => {
    it('POSTs event body', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ ok: true });
      });
      const client = makeClient();
      await client.createActionLedgerEvent({ actionId: 'a1', type: 'intent' });
      assert.equal(captured.actionId, 'a1');
    });
  });

  describe('getAssuranceEnvelope()', () => {
    it('fetches by id', async () => {
      restore = mockFetch(() => jsonResponse({ ok: true, envelopeId: 'env-1' }));
      const client = makeClient();
      const res = await client.getAssuranceEnvelope('env-1');
      assert.equal(res.ok, true);
      assert.equal(res.envelopeId, 'env-1');
    });
  });

  describe('listSkills()', () => {
    it('returns skills list', async () => {
      restore = mockFetch(() => jsonResponse({ ok: true, skills: [{ id: 's1' }] }));
      const client = makeClient();
      const res = await client.listSkills();
      assert.equal(res.ok, true);
      assert.equal(res.skills.length, 1);
    });
  });

  describe('runSkill()', () => {
    it('POSTs skillId + task', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ ok: true, result: {} });
      });
      const client = makeClient();
      await client.runSkill('soc2-check', 'collect evidence for controls', {
        llmProviderId: 'gemini',
        maxSteps: 5,
      });
      assert.equal(captured.skillId, 'soc2-check');
      assert.equal(captured.task, 'collect evidence for controls');
      assert.equal(captured.llmProviderId, 'gemini');
    });
  });

  describe('getMetrics()', () => {
    it('returns raw metrics text', async () => {
      restore = mockFetch(() => new Response('grc_compliance_score 0.87\n', { status: 200 }));
      const client = makeClient();
      const res = await client.getMetrics();
      assert.ok(res.includes('0.87'));
    });
  });

  describe('TPRM', () => {
    it('createVendor POSTs data', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ id: 'v1', name: 'AWS' });
      });
      const client = makeClient();
      const res = await client.createVendor({ name: 'AWS', riskScore: 0.1, status: 'approved', services: ['compute'] });
      assert.equal(captured.name, 'AWS');
      assert.equal(res.id, 'v1');
    });

    it('listVendors sends pagination', async () => {
      let url = '';
      restore = mockFetch(async (req) => {
        url = req.url;
        return jsonResponse({ vendors: [], total: 0 });
      });
      const client = makeClient();
      await client.listVendors({ page: 2, limit: 10 });
      assert.ok(url.includes('page=2'));
      assert.ok(url.includes('limit=10'));
    });

    it('getVendorRiskScore fetches by id', async () => {
      restore = mockFetch(() => jsonResponse({ vendor: { id: 'v1' }, riskScore: 0.42, gaps: [] }));
      const client = makeClient();
      const res = await client.getVendorRiskScore('v1');
      assert.equal(res.riskScore, 0.42);
    });
  });

  describe('Trust Center', () => {
    it('createTrustPage POSTs slug + company', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ id: 'tp1', slug: 'acme-security', company: 'Acme Corp', published: false, createdAt: '2026-01-01' });
      });
      const client = makeClient();
      const res = await client.createTrustPage('acme-security', 'Acme Corp');
      assert.equal(captured.slug, 'acme-security');
      assert.equal(captured.company, 'Acme Corp');
      assert.equal(res.id, 'tp1');
    });

    it('publishTrustPage POSTs to publish endpoint', async () => {
      let path = '';
      restore = mockFetch(async (req) => {
        path = new URL(req.url).pathname;
        return jsonResponse({ id: 'tp1', slug: 'x', company: 'y', published: true, publishedAt: '2026-01-01', createdAt: '2026-01-01' });
      });
      const client = makeClient();
      await client.publishTrustPage('tp1');
      assert.equal(path, '/api/trust/pages/tp1/publish');
    });
  });

  describe('Audit', () => {
    it('createAudit POSTs data', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ id: 'a1', framework: 'iso27001', status: 'draft', findings: [], createdAt: '', updatedAt: '' });
      });
      const client = makeClient();
      await client.createAudit({ framework: 'iso27001', status: 'draft' });
      assert.equal(captured.framework, 'iso27001');
    });

    it('listFindings sends pagination', async () => {
      let url = '';
      restore = mockFetch(async (req) => {
        url = req.url;
        return jsonResponse([]);
      });
      const client = makeClient();
      await client.listFindings('a1', { limit: 5 });
      assert.ok(url.includes('/api/audits/a1/findings'));
      assert.ok(url.includes('limit=5'));
    });
  });

  describe('Policy', () => {
    it('createPolicy POSTs data', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ id: 'p1', name: 'Access Control', type: 'security', status: 'active', createdAt: '', updatedAt: '' });
      });
      const client = makeClient();
      await client.createPolicy({ name: 'Access Control', type: 'security', status: 'active' });
      assert.equal(captured.name, 'Access Control');
    });

    it('listPolicies sends pagination', async () => {
      let url = '';
      restore = mockFetch(async (req) => {
        url = req.url;
        return jsonResponse([]);
      });
      const client = makeClient();
      await client.listPolicies({ page: 3 });
      assert.ok(url.includes('page=3'));
    });
  });

  describe('Incidents', () => {
    it('reportIncident POSTs data', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ id: 'i1', title: 'Phishing attempt', severity: 'high', status: 'open', reportedAt: '', updatedAt: '' });
      });
      const client = makeClient();
      const res = await client.reportIncident({ title: 'Phishing attempt', severity: 'high', status: 'open' });
      assert.equal(captured.title, 'Phishing attempt');
      assert.equal(res.id, 'i1');
    });

    it('listIncidents sends pagination', async () => {
      let url = '';
      restore = mockFetch(async (req) => {
        url = req.url;
        return jsonResponse([]);
      });
      const client = makeClient();
      await client.listIncidents({ limit: 20 });
      assert.ok(url.includes('limit=20'));
    });
  });

  describe('Board Reporting', () => {
    it('generateReport POSTs type + period', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ ok: true, report: {} });
      });
      const client = makeClient();
      await client.generateReport('compliance', 'Q1-2026');
      assert.equal(captured.type, 'compliance');
      assert.equal(captured.period, 'Q1-2026');
    });

    it('getExecutiveDashboard GETs', async () => {
      restore = mockFetch(() => jsonResponse({ ok: true, score: 0.92 }));
      const client = makeClient();
      const res = await client.getExecutiveDashboard();
      assert.equal(res.ok, true);
      assert.equal(res.score, 0.92);
    });
  });

  describe('Auto Evidence', () => {
    it('connectProvider POSTs provider + accountId', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ connectionId: 'c1', status: 'connected' });
      });
      const client = makeClient();
      const res = await client.connectProvider('aws', 'acct-123');
      assert.equal(captured.provider, 'aws');
      assert.equal(captured.accountId, 'acct-123');
      assert.equal(res.connectionId, 'c1');
    });

    it('deployCollectors POSTs provider', async () => {
      let captured: Record<string, unknown> = {};
      restore = mockFetch(async (req) => {
        captured = await bodyOf(req);
        return jsonResponse({ deployed: 3, collectorIds: ['c1', 'c2', 'c3'] });
      });
      const client = makeClient();
      const res = await client.deployCollectors('aws');
      assert.equal(captured.provider, 'aws');
      assert.equal(res.deployed, 3);
    });
  });

  describe('error handling', () => {
    it('throws GrcClawError on 4xx', async () => {
      restore = mockFetch(() => jsonResponse({ error: 'unauthorized', code: 'auth_failed' }, 401));
      const client = makeClient();
      try {
        await client.health();
        assert.fail('should throw');
      } catch (e) {
        assert.ok(e instanceof GrcClawError);
        assert.equal(e.statusCode, 401);
        assert.equal(e.code, 'auth_failed');
      }
    });

    it('does not retry 4xx errors', async () => {
      let calls = 0;
      restore = mockFetch(() => { calls++; return jsonResponse({ error: 'bad' }, 400); });
      const client = makeClient({ retries: 3, retryDelay: 10 });
      try {
        await client.health();
      } catch {
        // expected
      }
      assert.equal(calls, 1);
    });

    it('retries on 5xx', async () => {
      let calls = 0;
      restore = mockFetch(() => { calls++; return jsonResponse({ error: 'server_error' }, 500); });
      const client = makeClient({ retries: 2, retryDelay: 1 });
      try {
        await client.health();
      } catch {
        // expected
      }
      assert.equal(calls, 3); // 1 initial + 2 retries
    });
  });

  describe('auth header', () => {
    it('sends Bearer token', async () => {
      let authHeader = '';
      restore = mockFetch(async (req) => {
        authHeader = req.headers.get('Authorization') ?? '';
        return jsonResponse({ ok: true });
      });
      const client = makeClient();
      await client.health();
      assert.equal(authHeader, `Bearer ${TOKEN}`);
    });
  });
});
