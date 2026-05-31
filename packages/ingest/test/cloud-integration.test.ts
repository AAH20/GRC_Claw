/**
 * grc-claw-cloud-security-integration skill tests
 */
import assert from 'node:assert/strict';
import { describe, it } from 'node:test';
import { ExecPolicy } from '@grc-claw/agent-runtime';
import { A2ZSocConnector } from '@grc-claw/a2z-connector';
import {
  CLOUD_INGEST_SOURCES,
  guardDutyScore,
  normalizeAwsGuardDuty,
  normalizeAzureSentinel,
  normalizeBySource,
  normalizeCloud,
  normalizeGcpChronicle,
} from '@grc-claw/ingest';

const TENANT = 1;

describe('grc-claw-cloud-security-integration: source_system registry', () => {
  it('exposes all 10 cloud sources from skill', () => {
    assert.equal(CLOUD_INGEST_SOURCES.length, 10);
    assert.ok(CLOUD_INGEST_SOURCES.includes('azure_sentinel'));
    assert.ok(CLOUD_INGEST_SOURCES.includes('gcp_chronicle'));
    assert.ok(CLOUD_INGEST_SOURCES.includes('aws_cloudwatch'));
  });
});

describe('AWS normalizers', () => {
  it('GuardDuty EventBridge detail → aws_guardduty critical', () => {
    const ev = normalizeAwsGuardDuty(
      {
        detail: {
          id: 'gd-1',
          severity: 7.5,
          type: 'UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration',
        },
      },
      TENANT
    );
    assert.equal(ev.sourceSystem, 'aws_guardduty');
    assert.equal(ev.severity, 'critical');
    assert.equal(ev.eventType, 'identity.compromise');
  });

  it('GuardDuty score mapping', () => {
    assert.equal(guardDutyScore(7), 'critical');
    assert.equal(guardDutyScore(4), 'high');
  });
});

describe('Azure normalizers', () => {
  it('Sentinel incident → azure_sentinel', () => {
    const ev = normalizeAzureSentinel(
      {
        id: '/subscriptions/x/incidents/1',
        properties: { severity: 'High', title: 'Suspicious sign-in from TOR' },
      },
      TENANT
    );
    assert.equal(ev.sourceSystem, 'azure_sentinel');
    assert.equal(ev.severity, 'high');
    assert.equal(ev.eventType, 'auth.failure');
  });
});

describe('GCP normalizers', () => {
  it('Chronicle UDM → gcp_chronicle', () => {
    const ev = normalizeGcpChronicle(
      {
        security_result: [{ severity: 'HIGH', summary: 'Suspicious egress' }],
        principal: { ip: ['10.0.0.5'] },
      },
      TENANT
    );
    assert.equal(ev.sourceSystem, 'gcp_chronicle');
    assert.equal(ev.severity, 'high');
    assert.equal(ev.eventType, 'network.intrusion');
  });
});

describe('normalizeBySource cloud dispatch', () => {
  it('routes azure_sentinel and aws_guardduty', () => {
    const s = normalizeBySource(
      'azure_sentinel',
      { properties: { severity: 'Medium', title: 'Test' } },
      TENANT
    );
    assert.equal(s?.sourceSystem, 'azure_sentinel');
    const g = normalizeBySource(
      'aws_guardduty',
      { detail: { id: '1', severity: 5, type: 'T' } },
      TENANT
    );
    assert.equal(g?.sourceSystem, 'aws_guardduty');
  });

  it('all cloud sources normalize non-empty payload', () => {
    for (const src of CLOUD_INGEST_SOURCES) {
      const ev = normalizeCloud(src, { properties: { severity: 'Low', title: 't' }, detail: { id: '1', severity: 1, type: 'T' }, finding: { severity: 'LOW' }, security_result: [{ severity: 'LOW' }] }, TENANT);
      assert.ok(ev, `failed for ${src}`);
      assert.equal(ev!.sourceSystem, src);
    }
  });
});

describe('cloud → GRC → agentic AI SOAR', () => {
  it('Sentinel maps to controls via A2Z connector', async () => {
    const ev = normalizeAzureSentinel(
      { properties: { severity: 'High', title: 'Malware detected' } },
      TENANT
    );
    const c = new A2ZSocConnector({
      baseUrl: 'http://x',
      apiKey: 'k',
      tenantId: TENANT,
      mode: 'demo',
    });
    const impact = await c.mapSecurityEventToControls(ev);
    assert.ok(impact.controlIds.length > 0);
  });

  it('Sentinel playbook tool is destructive without approval', () => {
    const policy = new ExecPolicy();
    const d = policy.evaluate({ tool: 'sentinel.run_playbook', args: { playbookId: 'isolate' } });
    assert.equal(d.allowed, false);
    assert.equal(d.reason, 'destructive_requires_approval');
  });

  it('sentinel.get_incident is read-only', () => {
    const policy = new ExecPolicy();
    const d = policy.evaluate({ tool: 'sentinel.get_incident', args: { id: '1' } });
    assert.equal(d.allowed, true);
  });

  it('chronicle.soar.run_playbook is destructive', () => {
    const policy = new ExecPolicy();
    const d = policy.evaluate({ tool: 'chronicle.soar.run_playbook', args: {} });
    assert.equal(d.requiresApproval, true);
  });
});

describe('stable uuid dedupe (cloud)', () => {
  it('same GuardDuty id produces same event_uuid', () => {
    const p = { detail: { id: 'same-id', severity: 5, type: 'T' } };
    const a = normalizeAwsGuardDuty(p, TENANT);
    const b = normalizeAwsGuardDuty(p, TENANT);
    assert.equal(a.eventUuid, b.eventUuid);
  });
});
