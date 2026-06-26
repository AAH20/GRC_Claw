import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { AgentAuditTrail } from './AgentAuditTrail.js';

describe('AgentAuditTrail', () => {
  it('should record an audit entry with correct hash chain', () => {
    const trail = new AgentAuditTrail();
    const record = trail.record('did:grc:agent-1', 'evidence.collect', { controlId: 'ctrl-1' }, { ok: true });

    assert.equal(record.agentDid, 'did:grc:agent-1');
    assert.equal(record.tool, 'evidence.collect');
    assert.ok(record.hash);
    assert.ok(record.timestamp);
    assert.equal(trail.count(), 1);
  });

  it('should chain hashes correctly across multiple records', () => {
    const trail = new AgentAuditTrail();
    const r1 = trail.record('did:grc:agent-1', 'tool.a', {}, {});
    const r2 = trail.record('did:grc:agent-1', 'tool.b', {}, {});
    const r3 = trail.record('did:grc:agent-2', 'tool.a', {}, {});

    assert.equal(r1.previousHash, '0'.repeat(64));
    assert.equal(r2.previousHash, r1.hash);
    assert.equal(r3.previousHash, r2.hash);
  });

  it('should verify a valid audit trail', () => {
    const trail = new AgentAuditTrail();
    trail.record('agent-1', 'tool.a', { a: 1 }, { ok: true });
    trail.record('agent-1', 'tool.b', { b: 2 }, { ok: true });
    trail.record('agent-2', 'tool.a', { c: 3 }, { ok: false });

    const result = trail.verify();
    assert.equal(result.valid, true);
    assert.equal(result.totalRecords, 3);
    assert.equal(result.brokenAt, null);
  });

  it('should detect tampered record hash', () => {
    const trail = new AgentAuditTrail();
    trail.record('agent-1', 'tool.a', {}, {});
    trail.record('agent-1', 'tool.b', {}, {});

    // Tamper with the second record's hash
    const records = trail.list();
    (records[1] as any).hash = 'tampered-hash-value';

    const result = trail.verify();
    assert.equal(result.valid, false);
    assert.equal(result.brokenAt, 1);
    assert.ok(result.error?.includes('tampered'));
  });

  it('should detect broken chain when previousHash is wrong', () => {
    const trail = new AgentAuditTrail();
    trail.record('agent-1', 'tool.a', {}, {});
    trail.record('agent-1', 'tool.b', {}, {});

    const records = trail.list();
    (records[1] as any).previousHash = 'broken-link';

    const result = trail.verify();
    assert.equal(result.valid, false);
    assert.equal(result.brokenAt, 1);
    assert.ok(result.error?.includes('Chain broken'));
  });

  it('should query by agentDid', () => {
    const trail = new AgentAuditTrail();
    trail.record('agent-1', 'tool.a', {}, {});
    trail.record('agent-2', 'tool.a', {}, {});
    trail.record('agent-1', 'tool.b', {}, {});

    const results = trail.query({ agentDid: 'agent-1' });
    assert.equal(results.length, 2);
    assert.ok(results.every(r => r.agentDid === 'agent-1'));
  });

  it('should query by tool', () => {
    const trail = new AgentAuditTrail();
    trail.record('agent-1', 'tool.a', {}, {});
    trail.record('agent-1', 'tool.b', {}, {});
    trail.record('agent-2', 'tool.a', {}, {});

    const results = trail.query({ tool: 'tool.a' });
    assert.equal(results.length, 2);
    assert.ok(results.every(r => r.tool === 'tool.a'));
  });

  it('should query by time range', () => {
    const trail = new AgentAuditTrail();
    const r1 = trail.record('agent-1', 'tool.a', {}, {});
    const r2 = trail.record('agent-1', 'tool.b', {}, {});
    const r3 = trail.record('agent-1', 'tool.c', {}, {});

    // All 3 share same ms, so querying by exact timestamp of first record returns all 3
    const all = trail.query({ from: r1.timestamp, to: r3.timestamp });
    assert.equal(all.length, 3);

    // Query for records before any future time returns all
    const future = new Date(Date.now() + 100000).toISOString();
    const past = '2000-01-01T00:00:00.000Z';
    const allViaRange = trail.query({ from: past, to: future });
    assert.equal(allViaRange.length, 3);

    // Query with a very narrow range that excludes all
    const narrow = trail.query({ from: future, to: future });
    assert.equal(narrow.length, 0);
  });

  it('should export as JSON', () => {
    const trail = new AgentAuditTrail();
    trail.record('agent-1', 'tool.a', {}, {});
    trail.record('agent-2', 'tool.b', {}, {});

    const json = trail.export({ format: 'json' });
    const parsed = JSON.parse(json);
    assert.equal(parsed.length, 2);
  });

  it('should export as CSV', () => {
    const trail = new AgentAuditTrail();
    trail.record('agent-1', 'tool.a', {}, {});

    const csv = trail.export({ format: 'csv' });
    const lines = csv.split('\n');
    assert.equal(lines[0], 'id,timestamp,agentDid,tool,previousHash,hash');
    assert.equal(lines.length, 2);
  });

  it('should export filtered by agentDid', () => {
    const trail = new AgentAuditTrail();
    trail.record('agent-1', 'tool.a', {}, {});
    trail.record('agent-2', 'tool.b', {}, {});

    const json = trail.export({ format: 'json', agentDid: 'agent-1' });
    const parsed = JSON.parse(json);
    assert.equal(parsed.length, 1);
    assert.equal(parsed[0].agentDid, 'agent-1');
  });

  it('should handle empty trail verification', () => {
    const trail = new AgentAuditTrail();
    const result = trail.verify();
    assert.equal(result.valid, true);
    assert.equal(result.totalRecords, 0);
  });

  it('should limit query results', () => {
    const trail = new AgentAuditTrail();
    for (let i = 0; i < 10; i++) {
      trail.record('agent-1', 'tool.a', {}, {});
    }

    const results = trail.query({ limit: 3 });
    assert.equal(results.length, 3);
  });

  it('should paginate query results with offset', () => {
    const trail = new AgentAuditTrail();
    for (let i = 0; i < 10; i++) {
      trail.record('agent-1', `tool.${i}`, {}, {});
    }

    const page1 = trail.query({ limit: 3, offset: 0 });
    const page2 = trail.query({ limit: 3, offset: 3 });
    assert.equal(page1.length, 3);
    assert.equal(page2.length, 3);
    assert.notEqual(page1[0].id, page2[0].id);
  });
});
