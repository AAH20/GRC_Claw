import type {
  ComplianceImpact,
  ComplianceScore,
  GRCEngineFacade,
  SecurityEventCanonical,
  Severity,
} from '@grc-claw/core';

export interface A2ZSocConfig {
  baseUrl: string;
  apiKey: string;
  tenantId: number;
  mode: 'private' | 'demo';
}

export interface A2ZSecurityEventRow {
  event_uuid: string;
  event_type: string;
  severity: Severity;
  source_system: string;
  tenant_id: number;
  correlation_id?: string;
  compliance_impact?: ComplianceImpact & { controlIds?: string[] };
  event_data: Record<string, unknown>;
}

/**
 * Bridge between GRC_Claw (OSS) and Private A2Z SOC.
 * Uses documented REST shapes from A2Z SOC Sprint 6 plan.
 */
export class A2ZSocConnector implements GRCEngineFacade {
  constructor(private readonly cfg: A2ZSocConfig) {}

  private headers(idempotencyKey?: string): Record<string, string> {
    const h: Record<string, string> = {
      Authorization: `Bearer ${this.cfg.apiKey}`,
      'Content-Type': 'application/json',
      'X-A2Z-Tenant-Id': String(this.cfg.tenantId),
      'X-GRC-Claw-Bridge': '1',
    };
    if (idempotencyKey) h['Idempotency-Key'] = idempotencyKey;
    return h;
  }

  private url(path: string): string {
    return `${this.cfg.baseUrl.replace(/\/$/, '')}${path}`;
  }

  async pullSecurityEvents(sinceIso: string, limit = 100): Promise<SecurityEventCanonical[]> {
    if (this.cfg.mode === 'demo') {
      return demoEvents(this.cfg.tenantId);
    }
    const q = new URLSearchParams({ since: sinceIso, limit: String(limit) });
    const res = await fetch(`${this.url('/api/events')}?${q}`, {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error(`A2Z SOC events: ${res.status}`);
    const body = (await res.json()) as { events?: A2ZSecurityEventRow[] };
    return (body.events ?? []).map(rowToCanonical);
  }

  async pushComplianceAlert(payload: {
    controlId: string;
    message: string;
    severity: Severity;
    idempotencyKey: string;
  }): Promise<void> {
    if (this.cfg.mode === 'demo') return;
    const res = await fetch(this.url('/api/compliance/alerts'), {
      method: 'POST',
      headers: this.headers(payload.idempotencyKey),
      body: JSON.stringify({
        tenant_id: this.cfg.tenantId,
        control_id: payload.controlId,
        message: payload.message,
        severity: payload.severity,
      }),
    });
    if (!res.ok) throw new Error(`A2Z SOC alert push: ${res.status}`);
  }

  async getComplianceScore(tenantId: number, frameworkCode: string): Promise<ComplianceScore> {
    if (this.cfg.mode === 'demo') {
      return { tenantId, frameworkCode, scorePercent: 72, failingControls: 3, totalControls: 12 };
    }
    const res = await fetch(
      this.url(`/api/grc/score?tenant_id=${tenantId}&framework=${encodeURIComponent(frameworkCode)}`),
      { headers: this.headers() }
    );
    if (!res.ok) throw new Error(`A2Z SOC score: ${res.status}`);
    return res.json() as Promise<ComplianceScore>;
  }

  async listControls(tenantId: number, frameworkCode?: string) {
    if (this.cfg.mode === 'demo') {
      void tenantId;
      return [
        {
          id: 'iso-a.8.16',
          controlCode: 'A.8.16',
          title: 'Monitoring activities',
          frameworkCode: 'iso27001',
          orgStatus: 'in_progress' as const,
        },
      ].filter((c) => !frameworkCode || c.frameworkCode === frameworkCode);
    }
    const q = frameworkCode ? `?framework=${encodeURIComponent(frameworkCode)}` : '';
    const res = await fetch(this.url(`/api/grc/controls${q}`), {
      headers: this.headers(),
    });
    if (!res.ok) throw new Error(`A2Z SOC controls: ${res.status}`);
    const body = (await res.json()) as { controls: GRCEngineFacade extends never ? never : Awaited<ReturnType<GRCEngineFacade['listControls']>> };
    return body.controls ?? [];
  }

  async attachEvidence(
    tenantId: number,
    controlId: string,
    payload: { hash: string; uri: string; collectedAt: string },
    idempotencyKey: string
  ) {
    if (this.cfg.mode === 'demo') {
      return { evidenceId: `demo-ev-${payload.hash.slice(0, 8)}` };
    }
    const res = await fetch(this.url('/api/grc/evidence'), {
      method: 'POST',
      headers: this.headers(idempotencyKey),
      body: JSON.stringify({ tenant_id: tenantId, control_id: controlId, ...payload }),
    });
    if (!res.ok) throw new Error(`A2Z SOC evidence: ${res.status}`);
    return res.json() as Promise<{ evidenceId: string }>;
  }

  async mapSecurityEventToControls(event: SecurityEventCanonical): Promise<ComplianceImpact> {
    if (event.complianceImpact) return event.complianceImpact;
    const mapping: Record<string, string[]> = {
      'auth.failure': ['iso-a.8.15', 'soc2-cc6.1'],
      'network.intrusion': ['iso-a.8.16', 'nist-de.ae'],
      'firewall.block': ['iso-a.8.16'],
      'identity.compromise': ['iso-a.5.16', 'soc2-cc6.1', 'nist-rs.ma'],
      'cloud.api': ['iso-a.8.15', 'soc2-cc7.2'],
      'cloud.misconfig': ['iso-a.8.9', 'soc2-cc7.2'],
      'host.anomaly': ['iso-a.8.16', 'nist-de.ae'],
    };
    const controlIds = mapping[event.eventType] ?? ['nist-rs.ma'];
    return {
      controlIds,
      rationale: `Mapped ${event.eventType} from ${event.sourceSystem} for A2Z SOC correlation`,
      suggestedSeverity: event.severity,
    };
  }

  /** Sync loop: pull SOC events → compute control impact */
  async syncInbound(sinceIso: string): Promise<{ processed: number; impacts: ComplianceImpact[] }> {
    const events = await this.pullSecurityEvents(sinceIso);
    const impacts: ComplianceImpact[] = [];
    for (const ev of events) {
      impacts.push(await this.mapSecurityEventToControls(ev));
    }
    return { processed: events.length, impacts };
  }
}

function rowToCanonical(row: A2ZSecurityEventRow): SecurityEventCanonical {
  return {
    eventUuid: row.event_uuid,
    eventType: row.event_type,
    severity: row.severity,
    sourceSystem: row.source_system,
    tenantId: row.tenant_id,
    correlationId: row.correlation_id,
    complianceImpact: row.compliance_impact
      ? {
          controlIds: row.compliance_impact.controlIds ?? [],
          rationale: row.compliance_impact.rationale ?? '',
          suggestedSeverity: row.compliance_impact.suggestedSeverity,
        }
      : undefined,
    eventData: row.event_data,
  };
}

function demoEvents(tenantId: number): SecurityEventCanonical[] {
  return [
    {
      eventUuid: 'demo-001',
      eventType: 'network.intrusion',
      severity: 'high',
      sourceSystem: 'suricata',
      tenantId,
      eventData: { message: 'Demo IDS alert — pair with Private A2Z SOC' },
    },
    {
      eventUuid: 'demo-002',
      eventType: 'auth.failure',
      severity: 'medium',
      sourceSystem: 'wazuh',
      tenantId,
      eventData: { message: 'Demo auth failure — A2Z SOC marketing bridge' },
    },
  ];
}

export function loadA2ZConfigFromEnv(): A2ZSocConfig {
  return {
    baseUrl: process.env.A2Z_SOC_BASE_URL ?? 'http://127.0.0.1:3000',
    apiKey: process.env.A2Z_SOC_API_KEY ?? 'demo-key',
    tenantId: Number(process.env.A2Z_SOC_TENANT_ID ?? '1'),
    mode: (process.env.A2Z_SOC_MODE as 'private' | 'demo') ?? 'demo',
  };
}
