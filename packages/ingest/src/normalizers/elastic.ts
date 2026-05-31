import type { SecurityEventCanonical, Severity } from '@grc-claw/core';
import { stableEventUuid } from '../uuid.js';

export interface ElasticAlertDoc {
  '@timestamp'?: string;
  'kibana.alert.rule.name'?: string;
  'kibana.alert.severity'?: string;
  'kibana.alert.uuid'?: string;
  'source.ip'?: string;
  'destination.ip'?: string;
  'event.category'?: string[];
}

function elasticSeverity(s?: string): Severity {
  const v = (s ?? 'low').toLowerCase();
  if (v === 'critical') return 'critical';
  if (v === 'high') return 'high';
  if (v === 'medium') return 'medium';
  return 'low';
}

export function normalizeElastic(raw: ElasticAlertDoc, tenantId: number): SecurityEventCanonical {
  const ts = raw['@timestamp'] ?? new Date().toISOString();
  const ruleName = raw['kibana.alert.rule.name'] ?? 'Elastic alert';
  const src = raw['source.ip'];
  const dst = raw['destination.ip'];
  const categories = raw['event.category'] ?? [];
  const eventType = categories.includes('intrusion_detection')
    ? 'network.intrusion'
    : categories.includes('authentication')
      ? 'auth.failure'
      : 'host.anomaly';

  return {
    eventUuid: stableEventUuid(['elastic', ruleName, src, dst, ts, raw['kibana.alert.uuid']]),
    eventType,
    severity: elasticSeverity(raw['kibana.alert.severity']),
    sourceSystem: 'elastic',
    tenantId,
    eventData: {
      '@timestamp': ts,
      message: ruleName,
      source: src ? { ip: src } : undefined,
      destination: dst ? { ip: dst } : undefined,
      rule: { id: raw['kibana.alert.uuid'], name: ruleName, category: 'elastic' },
      raw: raw as Record<string, unknown>,
    },
  };
}
