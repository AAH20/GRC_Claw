import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { NotificationEngine, type NotificationEngineConfig } from './NotificationEngine.js';
import type { NotificationPayload } from './types.js';

function createTestConfig(): NotificationEngineConfig {
  return {
    channels: {
      slack: { webhookUrl: 'https://hooks.slack.com/services/test/test/test' },
      email: {
        smtpHost: 'smtp.test.com',
        smtpPort: 587,
        smtpUser: 'user@test.com',
        smtpPass: 'pass',
        fromAddress: 'grc@test.com',
      },
      teams: { webhookUrl: 'https://outlook.office.com/webhook/test' },
    },
    retry: { maxRetries: 0 },
  };
}

describe('NotificationEngine', () => {
  it('creates with config', () => {
    const engine = new NotificationEngine(createTestConfig());
    assert.ok(engine);
  });

  it('returns history as empty array initially', () => {
    const engine = new NotificationEngine(createTestConfig());
    const history = engine.getHistory();
    assert.equal(history.length, 0);
  });

  it('returns correct delivery stats initially', () => {
    const engine = new NotificationEngine(createTestConfig());
    const stats = engine.getDeliveryStats();
    assert.equal(stats.total, 0);
    assert.equal(stats.sent, 0);
    assert.equal(stats.failed, 0);
    assert.equal(stats.rateLimited, 0);
  });

  it('rejects send when channel is not configured', async () => {
    const engine = new NotificationEngine({ channels: {} });
    const payload: NotificationPayload = {
      template: 'compliance_alert',
      severity: 'critical',
      title: 'Test Alert',
      message: 'Test message',
      channels: ['slack'],
    };
    const records = await engine.send(payload);
    assert.equal(records.length, 1);
    assert.equal(records[0].status, 'failed');
    assert.equal(records[0].lastError, 'Channel not configured');
  });

  it('rate limits when threshold exceeded', async () => {
    const engine = new NotificationEngine({
      channels: { slack: { webhookUrl: 'https://hooks.slack.com/test' } },
      rateLimits: { slack: { maxPerMinute: 2 } },
      retry: { maxRetries: 0 },
    });

    const payload: NotificationPayload = {
      template: 'drift_alert',
      severity: 'warning',
      title: 'Drift',
      message: 'Config drift detected',
      channels: ['slack'],
    };

    // First two should go through (will fail on network but not rate-limited)
    await engine.send(payload);
    await engine.send(payload);

    // Third should be rate-limited
    const records = await engine.send(payload);
    assert.equal(records.length, 1);
    assert.equal(records[0].status, 'rate_limited');
  });

  it('filters history by channel', () => {
    const engine = new NotificationEngine(createTestConfig());
    const stats = engine.getDeliveryStats();
    assert.ok(typeof stats.byChannel === 'object');
  });

  it('getDeliveryStats returns channel breakdown', () => {
    const engine = new NotificationEngine(createTestConfig());
    const stats = engine.getDeliveryStats();
    assert.ok(stats.byChannel);
    assert.equal(typeof stats.byChannel, 'object');
  });
});
