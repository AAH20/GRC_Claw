import type { SecurityEventCanonical } from '@grc-claw/core';
import { firewallActionToSeverity } from '../severity.js';
import { stableEventUuid } from '../uuid.js';

const UFW_RE =
  /\[UFW\s+(?<action>BLOCK|ALLOW|AUDIT)[^\]]*\].*SRC=(?<src>[\d.]+).*DST=(?<dst>[\d.]+).*PROTO=(?<proto>\w+)(?:.*DPT=(?<dpt>\d+))?/;

export function normalizeUfwLine(line: string, tenantId: number): SecurityEventCanonical | null {
  const m = line.match(UFW_RE);
  if (!m?.groups) return null;
  const { action, src, dst, proto, dpt } = m.groups;
  const ts = new Date().toISOString();

  return {
    eventUuid: stableEventUuid(['ufw', action, src, dst, proto, dpt, line.slice(0, 80)]),
    eventType: 'firewall.block',
    severity: firewallActionToSeverity(action),
    sourceSystem: 'ufw',
    tenantId,
    eventData: {
      '@timestamp': ts,
      message: line.trim(),
      source: { ip: src },
      destination: { ip: dst, port: dpt ? Number(dpt) : 0 },
      rule: { category: 'firewall', name: `UFW ${action}` },
      raw: { line },
    },
  };
}
