import type { SecurityEventCanonical } from '@grc-claw/core';
import { wazuhLevelToSeverity } from '../severity.js';
import { stableEventUuid } from '../uuid.js';

export interface WazuhAlert {
  rule?: { id?: string | number; level?: number; description?: string };
  data?: { srcip?: string; dstip?: string; srcport?: string; dstport?: string };
  timestamp?: string;
  id?: string;
}

export function normalizeWazuh(raw: WazuhAlert, tenantId: number): SecurityEventCanonical {
  const level = Number(raw.rule?.level ?? 5);
  const ruleId = String(raw.rule?.id ?? '0');
  const src = raw.data?.srcip;
  const dst = raw.data?.dstip;
  const ts = raw.timestamp ?? new Date().toISOString();
  const eventType = level >= 10 ? 'auth.failure' : 'host.anomaly';

  return {
    eventUuid: stableEventUuid(['wazuh', ruleId, src, dst, ts, raw.id]),
    eventType,
    severity: wazuhLevelToSeverity(level),
    sourceSystem: 'wazuh',
    tenantId,
    eventData: {
      '@timestamp': ts,
      message: raw.rule?.description ?? 'Wazuh alert',
      host: {},
      source: src ? { ip: src, port: Number(raw.data?.srcport) || undefined } : undefined,
      destination: dst ? { ip: dst, port: Number(raw.data?.dstport) || undefined } : undefined,
      rule: { id: ruleId, name: raw.rule?.description, category: 'wazuh' },
      raw: raw as Record<string, unknown>,
    },
  };
}
