/**
 * @grc-claw/observability
 * OpenTelemetry-native Agent Tracing and Compliance Observability
 *
 * Every agent step emits structured spans: tool invocations, LLM calls,
 * policy checks, evidence generation. Supports distributed tracing across
 * multi-agent swarms with custom compliance metrics.
 *
 * Export to any OTLP-compatible backend (Datadog, Grafana, Jaeger).
 */
import * as crypto from 'crypto';

// ─── Core Observability Types ────────────────────────────────────────

export type SpanKind = 'INTERNAL' | 'CLIENT' | 'SERVER' | 'PRODUCER' | 'CONSUMER';
export type SpanStatus = 'OK' | 'ERROR' | 'UNSET';

export interface SpanAttributes {
  'agent.did'?: string;
  'agent.session_id'?: string;
  'agent.tenant_id'?: string;
  'tool.name'?: string;
  'tool.tier'?: string;
  'tool.namespace'?: string;
  'policy.result'?: string;
  'policy.reason'?: string;
  'compliance.framework'?: string;
  'compliance.control_id'?: string;
  'compliance.score'?: number;
  'llm.provider'?: string;
  'llm.model'?: string;
  'llm.tokens_in'?: number;
  'llm.tokens_out'?: number;
  'llm.cost_usd'?: number;
  'llm.latency_ms'?: number;
  'evidence.hash'?: string;
  'evidence.type'?: string;
  'soar.playbook_id'?: string;
  'soar.execution_id'?: string;
  'soar.step_id'?: string;
  'risk.score'?: number;
  'risk.factors'?: string;
  'error.type'?: string;
  'error.message'?: string;
  [key: string]: string | number | boolean | undefined;
}

export interface SpanEvent {
  name: string;
  timestamp: string;
  attributes: Record<string, string | number | boolean>;
}

export interface Span {
  traceId: string;
  spanId: string;
  parentSpanId?: string;
  name: string;
  kind: SpanKind;
  status: SpanStatus;
  startTime: string;
  endTime?: string;
  durationMs?: number;
  attributes: SpanAttributes;
  events: SpanEvent[];
  resource: {
    'service.name': string;
    'service.version': string;
    'deployment.environment': string;
  };
}

export interface Metric {
  name: string;
  type: 'counter' | 'gauge' | 'histogram';
  value: number;
  unit: string;
  labels: Record<string, string>;
  timestamp: string;
}

export interface TraceContext {
  traceId: string;
  spanId: string;
  traceFlags: number;
}

// ─── Agent Tracer ────────────────────────────────────────────────────

export class AgentTracer {
  private spans: Map<string, Span> = new Map();
  private metrics: Metric[] = [];
  private activeTraces: Map<string, string[]> = new Map();  // traceId -> spanIds
  private serviceName: string;
  private serviceVersion: string;
  private environment: string;

  constructor(opts?: { serviceName?: string; version?: string; environment?: string }) {
    this.serviceName = opts?.serviceName ?? '@grc-claw/agent-runtime';
    this.serviceVersion = opts?.version ?? '0.1.0';
    this.environment = opts?.environment ?? 'development';
  }

  /** Start a new trace (root span) */
  startTrace(name: string, attributes?: SpanAttributes): Span {
    const traceId = crypto.randomUUID().replace(/-/g, '');
    return this.startSpan(name, { traceId, attributes });
  }

  /** Start a new span within a trace */
  startSpan(name: string, opts?: {
    traceId?: string;
    parentSpanId?: string;
    kind?: SpanKind;
    attributes?: SpanAttributes;
  }): Span {
    const traceId = opts?.traceId ?? crypto.randomUUID().replace(/-/g, '');
    const spanId = crypto.randomUUID().replace(/-/g, '').substring(0, 16);

    const span: Span = {
      traceId,
      spanId,
      parentSpanId: opts?.parentSpanId,
      name,
      kind: opts?.kind ?? 'INTERNAL',
      status: 'UNSET',
      startTime: new Date().toISOString(),
      attributes: opts?.attributes ?? {},
      events: [],
      resource: {
        'service.name': this.serviceName,
        'service.version': this.serviceVersion,
        'deployment.environment': this.environment,
      },
    };

    this.spans.set(spanId, span);

    // Track in active traces
    const traceSpans = this.activeTraces.get(traceId) ?? [];
    traceSpans.push(spanId);
    this.activeTraces.set(traceId, traceSpans);

    return span;
  }

  /** End a span */
  endSpan(spanId: string, status?: SpanStatus, error?: string): void {
    const span = this.spans.get(spanId);
    if (!span) return;

    span.endTime = new Date().toISOString();
    span.status = status ?? 'OK';
    span.durationMs = new Date(span.endTime).getTime() - new Date(span.startTime).getTime();

    if (error) {
      span.status = 'ERROR';
      span.attributes['error.message'] = error;
      span.events.push({
        name: 'exception',
        timestamp: new Date().toISOString(),
        attributes: { 'exception.message': error },
      });
    }
  }

  /** Add an event to a span */
  addSpanEvent(spanId: string, name: string, attributes?: Record<string, string | number | boolean>): void {
    const span = this.spans.get(spanId);
    if (!span) return;
    span.events.push({
      name,
      timestamp: new Date().toISOString(),
      attributes: attributes ?? {},
    });
  }

  /** Set span attributes */
  setAttributes(spanId: string, attributes: Partial<SpanAttributes>): void {
    const span = this.spans.get(spanId);
    if (!span) return;
    Object.assign(span.attributes, attributes);
  }

  // ─── Convenience Methods for Agent Operations ──

  /** Trace a tool invocation */
  traceToolInvocation(opts: {
    traceId: string;
    parentSpanId?: string;
    agentDid: string;
    sessionId: string;
    toolName: string;
    toolTier: string;
    policyResult: string;
    policyReason?: string;
  }): Span {
    const span = this.startSpan(`agent.tool.${opts.toolName}`, {
      traceId: opts.traceId,
      parentSpanId: opts.parentSpanId,
      kind: 'CLIENT',
      attributes: {
        'agent.did': opts.agentDid,
        'agent.session_id': opts.sessionId,
        'tool.name': opts.toolName,
        'tool.tier': opts.toolTier,
        'policy.result': opts.policyResult,
        'policy.reason': opts.policyReason,
      },
    });
    this.recordMetric('agent.tool.invocations', 'counter', 1, 'invocations', {
      tool: opts.toolName,
      tier: opts.toolTier,
      result: opts.policyResult,
    });
    return span;
  }

  /** Trace an LLM call */
  traceLLMCall(opts: {
    traceId: string;
    parentSpanId?: string;
    agentDid: string;
    provider: string;
    model: string;
    tokensIn: number;
    tokensOut: number;
    costUsd: number;
    latencyMs: number;
  }): Span {
    const span = this.startSpan(`agent.llm.${opts.provider}`, {
      traceId: opts.traceId,
      parentSpanId: opts.parentSpanId,
      kind: 'CLIENT',
      attributes: {
        'agent.did': opts.agentDid,
        'llm.provider': opts.provider,
        'llm.model': opts.model,
        'llm.tokens_in': opts.tokensIn,
        'llm.tokens_out': opts.tokensOut,
        'llm.cost_usd': opts.costUsd,
        'llm.latency_ms': opts.latencyMs,
      },
    });
    this.recordMetric('agent.llm.tokens', 'counter', opts.tokensIn + opts.tokensOut, 'tokens', {
      provider: opts.provider,
      model: opts.model,
    });
    this.recordMetric('agent.llm.cost', 'counter', opts.costUsd, 'usd', {
      provider: opts.provider,
      model: opts.model,
    });
    this.recordMetric('agent.llm.latency', 'histogram', opts.latencyMs, 'ms', {
      provider: opts.provider,
      model: opts.model,
    });
    return span;
  }

  /** Trace a compliance check */
  traceComplianceCheck(opts: {
    traceId: string;
    parentSpanId?: string;
    agentDid: string;
    framework: string;
    controlId: string;
    score: number;
    result: 'pass' | 'fail' | 'partial';
  }): Span {
    const span = this.startSpan(`agent.compliance.${opts.framework}`, {
      traceId: opts.traceId,
      parentSpanId: opts.parentSpanId,
      kind: 'INTERNAL',
      attributes: {
        'agent.did': opts.agentDid,
        'compliance.framework': opts.framework,
        'compliance.control_id': opts.controlId,
        'compliance.score': opts.score,
        'policy.result': opts.result,
      },
    });
    this.recordMetric('agent.compliance.checks', 'counter', 1, 'checks', {
      framework: opts.framework,
      result: opts.result,
    });
    this.recordMetric('agent.compliance.score', 'gauge', opts.score, 'score', {
      framework: opts.framework,
      control: opts.controlId,
    });
    return span;
  }

  /** Trace a SOAR playbook execution */
  traceSOARExecution(opts: {
    traceId: string;
    parentSpanId?: string;
    playbookId: string;
    executionId: string;
    trigger: string;
    severity: string;
  }): Span {
    return this.startSpan(`soar.playbook.${opts.playbookId}`, {
      traceId: opts.traceId,
      parentSpanId: opts.parentSpanId,
      kind: 'INTERNAL',
      attributes: {
        'soar.playbook_id': opts.playbookId,
        'soar.execution_id': opts.executionId,
        'policy.result': opts.trigger,
        'risk.factors': opts.severity,
      },
    });
  }

  // ─── Metrics ──

  /** Record a metric */
  recordMetric(name: string, type: Metric['type'], value: number, unit: string, labels: Record<string, string>): void {
    this.metrics.push({
      name,
      type,
      value,
      unit,
      labels,
      timestamp: new Date().toISOString(),
    });
  }

  /** Get all metrics (Prometheus format) */
  getPrometheusMetrics(): string {
    const grouped: Map<string, Metric[]> = new Map();
    for (const m of this.metrics) {
      const key = m.name;
      const group = grouped.get(key) ?? [];
      group.push(m);
      grouped.set(key, group);
    }

    const lines: string[] = [];
    for (const [name, metrics] of grouped) {
      const type = metrics[0]?.type ?? 'counter';
      lines.push(`# HELP ${name} Agent observability metric`);
      lines.push(`# TYPE ${name} ${type}`);
      for (const m of metrics) {
        const labels = Object.entries(m.labels).map(([k, v]) => `${k}="${v}"`).join(',');
        lines.push(`${name}{${labels}} ${m.value}`);
      }
    }
    return lines.join('\n');
  }

  // ─── Export ──

  /** Get all spans for a trace */
  getTrace(traceId: string): Span[] {
    const spanIds = this.activeTraces.get(traceId) ?? [];
    return spanIds.map((id) => this.spans.get(id)).filter(Boolean) as Span[];
  }

  /** Export spans as OTLP JSON (for Datadog, Grafana, Jaeger, etc.) */
  exportOTLP(): {
    resourceSpans: {
      resource: Span['resource'];
      scopeSpans: { scope: { name: string; version: string }; spans: Span[] }[];
    }[];
  } {
    const allSpans = Array.from(this.spans.values());
    return {
      resourceSpans: [
        {
          resource: {
            'service.name': this.serviceName,
            'service.version': this.serviceVersion,
            'deployment.environment': this.environment,
          },
          scopeSpans: [
            {
              scope: { name: this.serviceName, version: this.serviceVersion },
              spans: allSpans,
            },
          ],
        },
      ],
    };
  }

  /** Get observability statistics */
  getStats(): {
    totalSpans: number;
    totalTraces: number;
    totalMetrics: number;
    errorRate: number;
    avgSpanDurationMs: number;
  } {
    const allSpans = Array.from(this.spans.values());
    const completedSpans = allSpans.filter((s) => s.durationMs !== undefined);
    const errorSpans = allSpans.filter((s) => s.status === 'ERROR');
    const avgDuration = completedSpans.length > 0
      ? completedSpans.reduce((sum, s) => sum + (s.durationMs ?? 0), 0) / completedSpans.length
      : 0;

    return {
      totalSpans: allSpans.length,
      totalTraces: this.activeTraces.size,
      totalMetrics: this.metrics.length,
      errorRate: allSpans.length > 0 ? errorSpans.length / allSpans.length : 0,
      avgSpanDurationMs: Math.round(avgDuration * 100) / 100,
    };
  }
}

// ─── AI Bill of Materials Generator ──────────────────────────────────

export interface AIBOMEntry {
  component: string;
  type: 'model' | 'tool' | 'data_source' | 'policy' | 'framework';
  version?: string;
  provider?: string;
  license?: string;
  riskLevel: 'low' | 'medium' | 'high' | 'critical';
  properties: Record<string, unknown>;
}

export interface AIBOM {
  specVersion: '1.0';
  serialNumber: string;
  version: number;
  metadata: {
    timestamp: string;
    component: { type: 'application'; name: string; version: string };
    authors: { name: string }[];
  };
  components: AIBOMEntry[];
  dependencies: { ref: string; dependsOn: string[] }[];
  vulnerabilities: { id: string; source: string; description: string; severity: string }[];
}

// ─── SPDX 2.3 AI-BOM ────────────────────────────────────────────────

export interface SPDXDocument {
  spdxVersion: 'SPDX-2.3';
  dataLicense: 'CC0-1.0';
  SPDXID: 'SPDXRef-DOCUMENT';
  name: string;
  documentNamespace: string;
  creationInfo: { created: string; creators: string[] };
  packages: Array<{
    SPDXID: string;
    name: string;
    versionInfo: string;
    supplier: string;
    downloadLocation: string;
    filesAnalyzed: boolean;
    licenseConcluded: string;
    licenseDeclared: string;
    externalRefs: Array<{ referenceCategory: string; referenceType: string; referenceLocator: string }>;
    comment?: string;
  }>;
  relationships: Array<{ spdxElementId: string; relationshipType: string; relatedSpdxElement: string }>;
}

// ─── CycloneDX 1.5 AI-BOM ───────────────────────────────────────────

export interface CycloneDXDocument {
  bomFormat: 'CycloneDX';
  specVersion: '1.5';
  serialNumber: string;
  version: number;
  metadata: {
    timestamp: string;
    tools: Array<{ vendor: string; name: string; version: string }>;
    component: { type: string; name: string; version: string };
  };
  components: Array<{
    type: string;
    'bom-ref': string;
    name: string;
    version?: string;
    supplier?: { name: string };
    licenses?: Array<{ license: { id: string } }>;
    properties: Array<{ name: string; value: string }>;
    externalReferences?: Array<{ type: string; url: string }>;
  }>;
  dependencies: Array<{ ref: string; dependsOn: string[] }>;
}

export class AIBOMGenerator {
  /** Generate an AI-BOM in SPDX 2.3 format (EU AI Act Art.11 compliant) */
  generateSPDX(traces: Span[], agentName: string): SPDXDocument {
    const packages: SPDXDocument['packages'] = [];
    const relationships: SPDXDocument['relationships'] = [];
    const seen = new Set<string>();

    for (const span of traces) {
      if (span.attributes['llm.provider'] && span.attributes['llm.model']) {
        const model = String(span.attributes['llm.model']);
        const provider = String(span.attributes['llm.provider']);
        const spdxId = `SPDXRef-model-${model.replace(/[^a-zA-Z0-9]/g, '-')}`;
        if (!seen.has(spdxId)) {
          seen.add(spdxId);
          packages.push({
            SPDXID: spdxId,
            name: model,
            versionInfo: model,
            supplier: `Organization: ${provider}`,
            downloadLocation: `https://api.${provider.toLowerCase()}.com`,
            filesAnalyzed: false,
            licenseConcluded: 'LicenseRef-Commercial',
            licenseDeclared: 'NOASSERTION',
            externalRefs: [
              { referenceCategory: 'OTHER', referenceType: 'eu-ai-act-gpai-class', referenceLocator: 'GPAI' },
              { referenceCategory: 'SECURITY', referenceType: 'advisory', referenceLocator: `https://a2zsoc.com/api/platform/ai-bom-registry/${encodeURIComponent(provider.toLowerCase())}%2F${encodeURIComponent(model)}` },
            ],
            comment: `LLM invoked via GRC_Claw gateway. Tokens in: ${span.attributes['llm.tokens_in'] ?? 0}, out: ${span.attributes['llm.tokens_out'] ?? 0}`,
          });
          relationships.push({ spdxElementId: 'SPDXRef-DOCUMENT', relationshipType: 'DESCRIBES', relatedSpdxElement: spdxId });
        }
      }
      if (span.attributes['tool.name']) {
        const tool = String(span.attributes['tool.name']);
        const spdxId = `SPDXRef-tool-${tool.replace(/[^a-zA-Z0-9]/g, '-')}`;
        if (!seen.has(spdxId)) {
          seen.add(spdxId);
          packages.push({
            SPDXID: spdxId,
            name: tool,
            versionInfo: 'NOASSERTION',
            supplier: 'Organization: GRC_Claw',
            downloadLocation: 'https://github.com/AAH20/GRC_Claw',
            filesAnalyzed: false,
            licenseConcluded: 'MIT',
            licenseDeclared: 'MIT',
            externalRefs: [
              { referenceCategory: 'OTHER', referenceType: 'tool-tier', referenceLocator: String(span.attributes['tool.tier'] ?? 'read') },
            ],
          });
          relationships.push({ spdxElementId: 'SPDXRef-DOCUMENT', relationshipType: 'CONTAINS', relatedSpdxElement: spdxId });
        }
      }
    }

    return {
      spdxVersion: 'SPDX-2.3',
      dataLicense: 'CC0-1.0',
      SPDXID: 'SPDXRef-DOCUMENT',
      name: `AI-BOM for ${agentName}`,
      documentNamespace: `https://a2zsoc.com/ai-bom/${agentName}-${Date.now()}`,
      creationInfo: {
        created: new Date().toISOString(),
        creators: ['Tool: GRC_Claw AI-BOM Generator', 'Organization: A2Z SOC'],
      },
      packages,
      relationships,
    };
  }

  /** Generate an AI-BOM in CycloneDX 1.5 format */
  generateCycloneDX(traces: Span[], agentName: string): CycloneDXDocument {
    const components: CycloneDXDocument['components'] = [];
    const seen = new Set<string>();

    for (const span of traces) {
      if (span.attributes['llm.provider'] && span.attributes['llm.model']) {
        const model = String(span.attributes['llm.model']);
        const provider = String(span.attributes['llm.provider']);
        const ref = `model-${model.replace(/[^a-zA-Z0-9]/g, '-')}`;
        if (!seen.has(ref)) {
          seen.add(ref);
          components.push({
            type: 'machine-learning-model',
            'bom-ref': ref,
            name: model,
            version: model,
            supplier: { name: provider },
            licenses: [{ license: { id: 'LicenseRef-Commercial' } }],
            properties: [
              { name: 'grc:eu-ai-act-class', value: 'GPAI' },
              { name: 'grc:provider', value: provider },
              { name: 'grc:tokens-consumed', value: String((span.attributes['llm.tokens_in'] ?? 0) as number + (span.attributes['llm.tokens_out'] as number ?? 0)) },
              { name: 'grc:cost-usd', value: String(span.attributes['llm.cost_usd'] ?? 0) },
            ],
            externalReferences: [
              { type: 'website', url: `https://a2zsoc.com/api/platform/ai-bom-registry/${encodeURIComponent(provider.toLowerCase())}%2F${encodeURIComponent(model)}` },
            ],
          });
        }
      }
      if (span.attributes['tool.name']) {
        const tool = String(span.attributes['tool.name']);
        const ref = `tool-${tool.replace(/[^a-zA-Z0-9]/g, '-')}`;
        if (!seen.has(ref)) {
          seen.add(ref);
          components.push({
            type: 'library',
            'bom-ref': ref,
            name: tool,
            properties: [
              { name: 'grc:tool-tier', value: String(span.attributes['tool.tier'] ?? 'read') },
              { name: 'grc:policy-result', value: String(span.attributes['policy.result'] ?? 'unknown') },
            ],
          });
        }
      }
    }

    return {
      bomFormat: 'CycloneDX',
      specVersion: '1.5',
      serialNumber: `urn:uuid:${crypto.randomUUID()}`,
      version: 1,
      metadata: {
        timestamp: new Date().toISOString(),
        tools: [{ vendor: 'A2Z SOC', name: 'GRC_Claw AI-BOM Generator', version: '1.0.0' }],
        component: { type: 'application', name: agentName, version: '1.0.0' },
      },
      components,
      dependencies: [{ ref: agentName, dependsOn: components.map(c => c['bom-ref']) }],
    };
  }

  /** Generate an AI Bill of Materials from trace data */
  generateFromTraces(traces: Span[], agentName: string): AIBOM {
    const components: AIBOMEntry[] = [];
    const seenComponents = new Set<string>();

    for (const span of traces) {
      // Extract models
      if (span.attributes['llm.provider'] && span.attributes['llm.model']) {
        const key = `model:${span.attributes['llm.provider']}:${span.attributes['llm.model']}`;
        if (!seenComponents.has(key)) {
          seenComponents.add(key);
          components.push({
            component: String(span.attributes['llm.model']),
            type: 'model',
            provider: String(span.attributes['llm.provider']),
            riskLevel: 'medium',
            properties: {
              totalTokens: span.attributes['llm.tokens_in'] ?? 0 + (span.attributes['llm.tokens_out'] as number ?? 0),
              costUsd: span.attributes['llm.cost_usd'],
            },
          });
        }
      }

      // Extract tools
      if (span.attributes['tool.name']) {
        const key = `tool:${span.attributes['tool.name']}`;
        if (!seenComponents.has(key)) {
          seenComponents.add(key);
          const tier = String(span.attributes['tool.tier'] ?? 'read');
          components.push({
            component: String(span.attributes['tool.name']),
            type: 'tool',
            riskLevel: tier === 'destructive' ? 'high' : tier === 'write' ? 'medium' : 'low',
            properties: { tier },
          });
        }
      }

      // Extract frameworks
      if (span.attributes['compliance.framework']) {
        const key = `framework:${span.attributes['compliance.framework']}`;
        if (!seenComponents.has(key)) {
          seenComponents.add(key);
          components.push({
            component: String(span.attributes['compliance.framework']),
            type: 'framework',
            riskLevel: 'low',
            properties: { controlId: span.attributes['compliance.control_id'] },
          });
        }
      }
    }

    return {
      specVersion: '1.0',
      serialNumber: `urn:uuid:${crypto.randomUUID()}`,
      version: 1,
      metadata: {
        timestamp: new Date().toISOString(),
        component: { type: 'application', name: agentName, version: '0.1.0' },
        authors: [{ name: 'GRC_Claw AI-BOM Generator' }],
      },
      components,
      dependencies: [],
      vulnerabilities: [],
    };
  }
}
