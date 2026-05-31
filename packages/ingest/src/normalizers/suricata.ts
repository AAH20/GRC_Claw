import type { SecurityEventCanonical } from '@grc-claw/core';
import { suricataSeverityToSeverity } from '../severity.js';
import { stableEventUuid } from '../uuid.js';

export interface SuricataEveAlert {
  timestamp?: string;
  event_type?: string;
  src_ip?: string;
  src_port?: number;
  dest_ip?: string;
  dest_port?: number;
  proto?: string;
  alert?: {
    signature_id?: number;
    signature?: string;
    severity?: number;
    category?: string;
  };
  flow_id?: number;
}

export function normalizeSuricata(raw: SuricataEveAlert, tenantId: number): SecurityEventCanonical {
  const sev = raw.alert?.severity ?? 3;
  const sigId = String(raw.alert?.signature_id ?? 0);
  const ts = raw.timestamp ?? new Date().toISOString();

  return {
    eventUuid: stableEventUuid(['suricata', sigId, raw.src_ip, raw.dest_ip, ts, raw.flow_id]),
    eventType: 'network.intrusion',
    severity: suricataSeverityToSeverity(sev),
    sourceSystem: 'suricata',
    tenantId,
    eventData: {
      '@timestamp': ts,
      message: raw.alert?.signature ?? 'Suricata alert',
      source: raw.src_ip ? { ip: raw.src_ip, port: raw.src_port ?? 0 } : undefined,
      destination: raw.dest_ip ? { ip: raw.dest_ip, port: raw.dest_port ?? 0 } : undefined,
      rule: {
        id: sigId,
        name: raw.alert?.signature,
        category: raw.alert?.category,
      },
      raw: raw as Record<string, unknown>,
    },
  };
}
