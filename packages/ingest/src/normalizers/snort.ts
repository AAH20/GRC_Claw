import type { SecurityEventCanonical } from '@grc-claw/core';
import { snortPriorityToSeverity } from '../severity.js';
import { stableEventUuid } from '../uuid.js';

export interface SnortAlertJson {
  timestamp?: string;
  msg?: string;
  gid?: number;
  sid?: number;
  rev?: number;
  priority?: number;
  proto?: string;
  src_addr?: string;
  src_port?: number;
  dst_addr?: string;
  dst_port?: number;
}

export function normalizeSnort(raw: SnortAlertJson, tenantId: number): SecurityEventCanonical {
  const ruleId = `${raw.gid ?? 1}:${raw.sid ?? 0}:${raw.rev ?? 0}`;
  const priority = raw.priority ?? 3;
  const ts = raw.timestamp ?? new Date().toISOString();

  return {
    eventUuid: stableEventUuid(['snort', ruleId, raw.src_addr, raw.dst_addr, ts]),
    eventType: 'network.intrusion',
    severity: snortPriorityToSeverity(priority),
    sourceSystem: 'snort',
    tenantId,
    eventData: {
      '@timestamp': ts,
      message: raw.msg ?? 'Snort alert',
      source: raw.src_addr ? { ip: raw.src_addr, port: raw.src_port ?? 0 } : undefined,
      destination: raw.dst_addr ? { ip: raw.dst_addr, port: raw.dst_port ?? 0 } : undefined,
      rule: { id: ruleId, name: raw.msg, category: 'snort' },
      raw: raw as Record<string, unknown>,
    },
  };
}
