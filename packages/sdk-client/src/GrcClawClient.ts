import type {
  GrcClientConfig,
  SecurityEvent,
  AuditReport,
  Finding,
  Vendor,
  TrustPage,
  Incident,
  Policy,
  PaginationParams,
} from './types.js';

export class GrcClawError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly code: string,
    public readonly body?: unknown,
  ) {
    super(message);
    this.name = 'GrcClawError';
  }
}

export class GrcClawTimeoutError extends Error {
  constructor(message: string, public readonly request: string) {
    super(message);
    this.name = 'GrcClawTimeoutError';
  }
}

interface RetryOptions {
  retries: number;
  retryDelay: number;
  backoffMultiplier: number;
}

const DEFAULT_RETRY: RetryOptions = {
  retries: 3,
  retryDelay: 200,
  backoffMultiplier: 2,
};

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class GrcClawClient {
  private readonly baseUrl: string;
  private readonly token: string;
  private readonly timeout: number;
  private readonly retry: RetryOptions;

  constructor(config: GrcClientConfig) {
    this.baseUrl = config.baseUrl.replace(/\/+$/, '');
    this.token = config.token;
    this.timeout = config.timeout ?? 30_000;
    this.retry = {
      retries: config.retries ?? DEFAULT_RETRY.retries,
      retryDelay: config.retryDelay ?? DEFAULT_RETRY.retryDelay,
      backoffMultiplier: DEFAULT_RETRY.backoffMultiplier,
    };
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    params?: Record<string, string>,
  ): Promise<T> {
    const url = new URL(`${this.baseUrl}${path}`);
    if (params) {
      for (const [k, v] of Object.entries(params)) {
        if (v !== undefined && v !== null) url.searchParams.set(k, v);
      }
    }

    const headers: Record<string, string> = {
      Authorization: `Bearer ${this.token}`,
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };

    const init: RequestInit = {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(this.timeout),
    };

    let lastError: unknown;
    const maxAttempts = this.retry.retries + 1;

    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const res = await fetch(url.toString(), init);
        const text = await res.text();
        let json: unknown;
        try {
          json = JSON.parse(text);
        } catch {
          json = { raw: text };
        }

        if (!res.ok) {
          const errBody = json as Record<string, unknown>;
          const code = (errBody.code as string) ?? `http_${res.status}`;
          const msg = (errBody.error as string) ?? (errBody.message as string) ?? `HTTP ${res.status}`;

          if (res.status >= 500 && attempt < maxAttempts) {
            const delay = this.retry.retryDelay * Math.pow(this.retry.backoffMultiplier, attempt - 1);
            await sleep(delay);
            continue;
          }

          throw new GrcClawError(msg, res.status, code, json);
        }

        return json as T;
      } catch (err) {
        if (err instanceof GrcClawError) throw err;

        if (err instanceof DOMException && err.name === 'TimeoutError') {
          if (attempt < maxAttempts) {
            const delay = this.retry.retryDelay * Math.pow(this.retry.backoffMultiplier, attempt - 1);
            await sleep(delay);
            continue;
          }
          throw new GrcClawTimeoutError(`Request to ${path} timed out after ${this.timeout}ms`, path);
        }

        lastError = err;
        if (attempt < maxAttempts) {
          const delay = this.retry.retryDelay * Math.pow(this.retry.backoffMultiplier, attempt - 1);
          await sleep(delay);
        }
      }
    }

    throw lastError instanceof Error ? lastError : new Error('request_failed');
  }

  private qs(params?: PaginationParams): Record<string, string> {
    if (!params) return {};
    const q: Record<string, string> = {};
    if (params.page !== undefined) q.page = String(params.page);
    if (params.limit !== undefined) q.limit = String(params.limit);
    if (params.sortBy) q.sortBy = params.sortBy;
    if (params.sortOrder) q.sortOrder = params.sortOrder;
    return q;
  }

  // ── Gateway ──────────────────────────────────────────────

  async health(): Promise<{ ok: boolean; service: string; [k: string]: unknown }> {
    return this.request('GET', '/health');
  }

  async listFrameworks(): Promise<{ packs: unknown[] }> {
    return this.request('GET', '/api/frameworks');
  }

  async normalizeEvent(
    source: string,
    payload: unknown,
    tenantId: number = 1,
  ): Promise<{ ok: boolean; event: SecurityEvent; complianceImpact: unknown }> {
    return this.request('POST', '/api/ingest/normalize', { source, payload, tenantId });
  }

  async invokeAgent(
    tool: string,
    args: Record<string, unknown> = {},
    opts?: { sessionId?: string; idempotencyKey?: string; approvalToken?: string },
  ): Promise<{ ok: boolean; decision: unknown; output: unknown; action: unknown }> {
    return this.request('POST', '/api/agent/invoke', {
      tool,
      args,
      sessionId: opts?.sessionId,
      idempotencyKey: opts?.idempotencyKey,
      approvalToken: opts?.approvalToken,
    });
  }

  async listConnectors(): Promise<{ ok: boolean; [k: string]: unknown }> {
    return this.request('GET', '/api/connectors');
  }

  async createActionLedgerEvent(
    event: Record<string, unknown>,
  ): Promise<{ ok: boolean; [k: string]: unknown }> {
    return this.request('POST', '/api/action-ledger', event);
  }

  async getAssuranceEnvelope(
    id: string,
  ): Promise<{ ok: boolean; [k: string]: unknown }> {
    return this.request('GET', `/api/assurance/${id}`);
  }

  async listSkills(): Promise<{ ok: boolean; skills: unknown[] }> {
    return this.request('GET', '/api/skills');
  }

  async runSkill(
    skillId: string,
    task: string,
    opts?: { sessionId?: string; llmProviderId?: string; maxSteps?: number },
  ): Promise<{ ok: boolean; decision: unknown; result: unknown; audit: unknown }> {
    return this.request('POST', '/api/skills/run', {
      skillId,
      task,
      sessionId: opts?.sessionId,
      llmProviderId: opts?.llmProviderId,
      maxSteps: opts?.maxSteps,
    });
  }

  async getMetrics(): Promise<string> {
    const url = `${this.baseUrl}/metrics`;
    const res = await fetch(url, {
      headers: { Authorization: `Bearer ${this.token}` },
      signal: AbortSignal.timeout(this.timeout),
    });
    if (!res.ok) throw new GrcClawError(`HTTP ${res.status}`, res.status, `http_${res.status}`);
    return res.text();
  }

  // ── TPRM ─────────────────────────────────────────────────

  async createVendor(data: Omit<Vendor, 'id' | 'createdAt'>): Promise<Vendor> {
    return this.request('POST', '/api/tprm/vendors', data);
  }

  async listVendors(
    params?: PaginationParams,
  ): Promise<{ vendors: Vendor[]; total: number }> {
    return this.request('GET', '/api/tprm/vendors', undefined, this.qs(params));
  }

  async getVendorRiskScore(
    id: string,
  ): Promise<{ vendor: Vendor; riskScore: number; gaps: unknown[] }> {
    return this.request('GET', `/api/tprm/vendors/${id}/risk`);
  }

  // ── Trust Center ─────────────────────────────────────────

  async createTrustPage(
    slug: string,
    company: string,
  ): Promise<TrustPage> {
    return this.request('POST', '/api/trust/pages', { slug, company });
  }

  async publishTrustPage(
    id: string,
  ): Promise<TrustPage> {
    return this.request('POST', `/api/trust/pages/${id}/publish`);
  }

  // ── Audit ────────────────────────────────────────────────

  async createAudit(
    data: Omit<AuditReport, 'id' | 'findings' | 'createdAt' | 'updatedAt'>,
  ): Promise<AuditReport> {
    return this.request('POST', '/api/audits', data);
  }

  async listFindings(
    auditId: string,
    params?: PaginationParams,
  ): Promise<Finding[]> {
    return this.request('GET', `/api/audits/${auditId}/findings`, undefined, this.qs(params));
  }

  // ── Policy ───────────────────────────────────────────────

  async createPolicy(
    data: Omit<Policy, 'id' | 'createdAt' | 'updatedAt'>,
  ): Promise<Policy> {
    return this.request('POST', '/api/policies', data);
  }

  async listPolicies(
    params?: PaginationParams,
  ): Promise<Policy[]> {
    return this.request('GET', '/api/policies', undefined, this.qs(params));
  }

  // ── Incidents ────────────────────────────────────────────

  async reportIncident(
    data: Omit<Incident, 'id' | 'reportedAt' | 'updatedAt'>,
  ): Promise<Incident> {
    return this.request('POST', '/api/incidents', data);
  }

  async listIncidents(
    params?: PaginationParams,
  ): Promise<Incident[]> {
    return this.request('GET', '/api/incidents', undefined, this.qs(params));
  }

  // ── Board Reporting ──────────────────────────────────────

  async generateReport(
    type: string,
    period: string,
  ): Promise<{ ok: boolean; report: unknown }> {
    return this.request('POST', '/api/board-reports/generate', { type, period });
  }

  async getExecutiveDashboard(): Promise<{ ok: boolean; [k: string]: unknown }> {
    return this.request('GET', '/api/board-reports/dashboard');
  }

  // ── Auto Evidence ────────────────────────────────────────

  async connectProvider(
    provider: string,
    accountId: string,
  ): Promise<{ connectionId: string; status: string }> {
    return this.request('POST', '/api/auto-evidence/connect', { provider, accountId });
  }

  async deployCollectors(
    provider: string,
  ): Promise<{ deployed: number; collectorIds: string[] }> {
    return this.request('POST', '/api/auto-evidence/collectors/deploy', { provider });
  }
}
