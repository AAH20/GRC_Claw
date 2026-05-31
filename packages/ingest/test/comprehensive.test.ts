/**
 * Comprehensive suite: ingest-oss-siem-ids-logs + netsec-grc-architecture-engineering
 * + GRC_Claw agentic AI security
 */
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { AgentSession, ExecPolicy } from '@grc-claw/agent-runtime';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';
import { EvidenceStore } from '@grc-claw/evidence';
import { listFrameworkPacks } from '@grc-claw/frameworks';
import {
  normalizeBySource,
  normalizeElastic,
  normalizeSnort,
  normalizeSuricata,
  normalizeUfwLine,
  normalizeWazuh,
  stableEventUuid,
  suricataSeverityToSeverity,
  wazuhLevelToSeverity,
} from '@grc-claw/ingest';

const TENANT = 1;

describe('ingest-oss-siem-ids-logs: severity mapping', () => {
  it('Wazuh level ≥12 → critical', () => {
    assert.equal(wazuhLevelToSeverity(12), 'critical');
    assert.equal(wazuhLevelToSeverity(15), 'critical');
  });
  it('Wazuh 8–11 → high', () => assert.equal(wazuhLevelToSeverity(9), 'high'));
  it('Wazuh 5–7 → medium', () => assert.equal(wazuhLevelToSeverity(6), 'medium'));
  it('Suricata severity 1 → critical', () => assert.equal(suricataSeverityToSeverity(1), 'critical'));
  it('Suricata severity 2 → high', () => assert.equal(suricataSeverityToSeverity(2), 'high'));
});

describe('ingest-oss-siem-ids-logs: stable event_uuid dedupe', () => {
  it('same inputs produce same uuid', () => {
    const a = stableEventUuid(['wazuh', '5710', '1.2.3.4', '5.6.7.8', '2026-01-01T00:00:00Z']);
    const b = stableEventUuid(['wazuh', '5710', '1.2.3.4', '5.6.7.8', '2026-01-01T00:00:00Z']);
    assert.equal(a, b);
  });
  it('different src ip produces different uuid', () => {
    const a = stableEventUuid(['suricata', '1', '1.1.1.1', '2.2.2.2', 't']);
    const b = stableEventUuid(['suricata', '1', '9.9.9.9', '2.2.2.2', 't']);
    assert.notEqual(a, b);
  });
});

describe('ingest-oss-siem-ids-logs: per-source normalizers', () => {
  it('Wazuh → canonical', () => {
    const ev = normalizeWazuh(
      {
        rule: { id: 5710, level: 10, description: 'SSHD auth failed' },
        data: { srcip: '203.0.113.1', dstip: '192.168.1.1' },
        timestamp: '2026-05-31T10:00:00.000Z',
        id: 'w1',
      },
      TENANT
    );
    assert.equal(ev.sourceSystem, 'wazuh');
    assert.equal(ev.severity, 'high');
    assert.equal((ev.eventData as { source?: { ip?: string } }).source?.ip, '203.0.113.1');
    assert.match(ev.eventUuid, /^[0-9a-f-]{36}$/);
  });

  it('Suricata EVE → network.intrusion', () => {
    const ev = normalizeSuricata(
      {
        timestamp: '2026-05-31T10:00:00.000Z',
        event_type: 'alert',
        src_ip: '10.0.0.5',
        dest_ip: '10.0.0.10',
        dest_port: 443,
        alert: { signature_id: 2024897, signature: 'ET SCAN', severity: 1 },
        flow_id: 99,
      },
      TENANT
    );
    assert.equal(ev.sourceSystem, 'suricata');
    assert.equal(ev.eventType, 'network.intrusion');
    assert.equal(ev.severity, 'critical');
  });

  it('Snort alert_json → network.intrusion', () => {
    const ev = normalizeSnort(
      {
        gid: 1,
        sid: 1000001,
        rev: 1,
        priority: 1,
        msg: 'TEST RULE',
        src_addr: '1.2.3.4',
        dst_addr: '5.6.7.8',
        dst_port: 80,
      },
      TENANT
    );
    assert.equal(ev.sourceSystem, 'snort');
    assert.equal((ev.eventData as { rule?: { id?: string } }).rule?.id, '1:1000001:1');
    assert.equal(ev.severity, 'critical');
  });

  it('Elastic ECS alert', () => {
    const ev = normalizeElastic(
      {
        '@timestamp': '2026-05-31T10:00:00.000Z',
        'kibana.alert.rule.name': 'Brute Force',
        'kibana.alert.severity': 'high',
        'source.ip': '198.51.100.2',
        'destination.ip': '192.0.2.1',
        'event.category': ['intrusion_detection'],
      },
      TENANT
    );
    assert.equal(ev.sourceSystem, 'elastic');
    assert.equal(ev.eventType, 'network.intrusion');
    assert.equal(ev.severity, 'high');
  });

  it('UFW BLOCK line → firewall.block', () => {
    const line =
      '[UFW BLOCK] IN=eth0 OUT= MAC= SRC=203.0.113.10 DST=192.168.1.5 LEN=60 PROTO=TCP DPT=22';
    const ev = normalizeUfwLine(line, TENANT)!;
    assert.equal(ev.sourceSystem, 'ufw');
    assert.equal(ev.eventType, 'firewall.block');
    assert.equal((ev.eventData as { source?: { ip?: string } }).source?.ip, '203.0.113.10');
    assert.equal((ev.eventData as { destination?: { port?: number } }).destination?.port, 22);
  });

  it('normalizeBySource dispatches all OSS sources', () => {
    const sources = ['wazuh', 'suricata', 'snort', 'elastic'] as const;
    for (const s of sources) {
      const ev = normalizeBySource(s, {}, TENANT);
      assert.ok(ev, `missing normalizer for ${s}`);
      assert.equal(ev!.sourceSystem, s === 'elastic' ? 'elastic' : s);
    }
  });
});

describe('netsec-grc-architecture: GRC + evidence plane', () => {
  it('four framework packs (ISO 27001, NIST, SOC2, ISO 42001 AIMS)', () => {
    const packs = listFrameworkPacks();
    assert.equal(packs.length, 4);
    assert.deepEqual(
      packs.map((p) => p.code).sort(),
      ['iso27001', 'iso42001', 'nist_csf', 'soc2']
    );
  });

  it('evidence SHA-256 lineage', () => {
    const store = new EvidenceStore();
    const rec = store.attach({
      controlId: 'iso-a.8.16',
      tenantId: TENANT,
      uri: 's3://evidence/demo.pdf',
      collectedAt: new Date().toISOString(),
      lineage: { source: 'automated_test' },
      content: 'audit artifact bytes',
    });
    assert.equal(rec.sha256.length, 64);
    assert.equal(store.listByControl('iso-a.8.16').length, 1);
  });
});

describe('agentic AI security: exec policy', () => {
  const policy = new ExecPolicy();

  it('read tools auto-allowed', () => {
    const d = policy.evaluate({ tool: 'soc.query_events', args: {} });
    assert.equal(d.allowed, true);
    assert.equal(d.reason, 'read_allowed');
  });

  it('destructive requires approval', () => {
    const d = policy.evaluate({ tool: 'firewall.apply_rule', args: {} });
    assert.equal(d.allowed, false);
    assert.equal(d.requiresApproval, true);
  });

  it('write requires idempotency key', () => {
    const d = policy.evaluate({ tool: 'evidence.attach', args: {} });
    assert.equal(d.allowed, false);
    assert.equal(d.reason, 'write_requires_idempotency_key');
  });

  it('agent session enforces max calls and audit log', async () => {
    const session = new AgentSession('arch-test', new ExecPolicy(undefined, { maxCallsPerTurn: 2 }));
    await session.invoke({ tool: 'grc.list_controls', args: {} });
    await session.invoke({ tool: 'grc.get_compliance_score', args: {} });
    const blocked = await session.invoke({ tool: 'grc.list_controls', args: {} });
    assert.equal(blocked.allowed, false);
    assert.equal(blocked.reason, 'max_calls_exceeded');
    assert.equal(session.getAuditLog().length, 3);
  });
});

describe('end-to-end: ingest → GRC impact → agent read path', () => {
  it('Suricata critical maps to monitoring controls via A2Z connector', async () => {
    const raw = normalizeSuricata(
      {
        alert: { signature_id: 1, severity: 1, signature: 'Critical IDS' },
        src_ip: '10.0.0.1',
        dest_ip: '10.0.0.2',
      },
      TENANT
    );
    const connector = new A2ZSocConnector({
      baseUrl: 'http://localhost',
      apiKey: 'k',
      tenantId: TENANT,
      mode: 'demo',
    });
    const impact = await connector.mapSecurityEventToControls(raw);
    assert.ok(impact.controlIds.includes('iso-a.8.16'));
    assert.ok(impact.controlIds.includes('nist-de.ae'));

    const session = new AgentSession('e2e', new ExecPolicy());
    const decision = await session.invoke({
      tool: 'soc.query_events',
      args: { eventType: raw.eventType },
    });
    assert.equal(decision.allowed, true);
  });

  it('Wazuh auth failure maps to access controls', async () => {
    const raw = normalizeWazuh(
      { rule: { id: 5710, level: 10 }, data: { srcip: '1.2.3.4' } },
      TENANT
    );
    const connector = new A2ZSocConnector({
      baseUrl: 'http://localhost',
      apiKey: 'k',
      tenantId: TENANT,
      mode: 'demo',
    });
    const impact = await connector.mapSecurityEventToControls(raw);
    assert.ok(impact.controlIds.includes('iso-a.8.15'));
    assert.ok(impact.controlIds.includes('soc2-cc6.1'));
  });
});

describe('architecture: control vs data plane separation', () => {
  it('ingest normalizers do not mutate exec policy state', () => {
    const policy = new ExecPolicy();
    normalizeWazuh({ rule: { level: 15 } }, TENANT);
    const before = policy.evaluate({ tool: 'grc.list_controls', args: {} });
    assert.equal(before.allowed, true);
  });
});
