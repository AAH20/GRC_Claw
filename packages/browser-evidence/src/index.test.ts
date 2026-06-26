import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import {
  BrowserEvidenceCollector,
  type BrowserAdapter,
  type PortalConfig,
  type CollectorConfig,
  AWS_CONSOLE,
  CLOUDFLARE_DASHBOARD,
} from './index.js';

function createMockAdapter(overrides: Partial<BrowserAdapter> = {}): BrowserAdapter {
  let currentUrl = '';
  return {
    launch: async () => {},
    navigate: async (url: string) => { currentUrl = url; },
    screenshot: async () => Buffer.from('mock-screenshot-data'),
    getContent: async () => '<html><body>mock-dom</body></html>',
    close: async () => {},
    elementExists: async (_selector: string) => false,
    fillInput: async (_selector: string, _text: string) => {},
    click: async (_selector: string) => {},
    getText: async (_selector: string) => null,
    ...overrides,
  };
}

function createTestPortal(overrides: Partial<PortalConfig> = {}): PortalConfig {
  return {
    name: 'TestPortal',
    url: 'https://test.example.com',
    authType: 'sso',
    credentials: { username: 'user@test.com', password: 'pass' },
    selectors: {
      login: '#login',
      security: '#security',
    },
    screenshotPaths: ['/', '/security'],
    ...overrides,
  };
}

describe('BrowserEvidenceCollector', () => {
  let mockAdapter: BrowserAdapter;
  let collector: BrowserEvidenceCollector;

  const defaultConfig: Partial<CollectorConfig> = {
    headless: true,
    timeout: 10000,
    retryCount: 2,
    stealthMode: true,
  };

  beforeEach(() => {
    mockAdapter = createMockAdapter();
    collector = new BrowserEvidenceCollector(defaultConfig, mockAdapter);
  });

  it('should collect evidence from a single portal', async () => {
    const portal = createTestPortal();
    const artifact = await collector.collectFromPortal(portal);

    assert.ok(artifact.id, 'should have an id');
    assert.equal(artifact.portalId, 'TestPortal');
    assert.ok(Buffer.isBuffer(artifact.screenshot), 'screenshot should be Buffer');
    assert.equal(typeof artifact.domSnapshot, 'string');
    assert.equal(typeof artifact.hash, 'string');
    assert.equal(typeof artifact.timestamp, 'string');
    assert.ok(artifact.hash.length > 0, 'hash should not be empty');
  });

  it('should collect evidence from multiple portals', async () => {
    const portals = [
      createTestPortal({ name: 'Portal1' }),
      createTestPortal({ name: 'Portal2' }),
    ];
    const artifacts = await collector.collectFromMultiplePortals(portals);

    assert.equal(artifacts.length, 2);
    assert.equal(artifacts[0].portalId, 'Portal1');
    assert.equal(artifacts[1].portalId, 'Portal2');
  });

  it('should skip failed portals and continue collecting', async () => {
    let callCount = 0;
    const failingAdapter = createMockAdapter({
      launch: async () => {
        callCount++;
        if (callCount === 1) {
          throw new Error('Browser launch failed');
        }
      },
    });

    const failingCollector = new BrowserEvidenceCollector(
      { retryCount: 0 },
      failingAdapter
    );

    const portals = [
      createTestPortal({ name: 'FailPortal' }),
      createTestPortal({ name: 'SuccessPortal' }),
    ];

    const artifacts = await failingCollector.collectFromMultiplePortals(portals);
    assert.equal(artifacts.length, 1);
    assert.equal(artifacts[0].portalId, 'SuccessPortal');
  });

  it('should compare identical artifacts as unchanged', async () => {
    const portal = createTestPortal();
    const artifact1 = await collector.collectFromPortal(portal);
    const artifact2 = await collector.collectFromPortal(portal);

    const result = collector.compareArtifacts(artifact1, artifact2);
    assert.equal(result.changed, false);
    assert.equal(result.differences.length, 0);
  });

  it('should detect differences between different artifacts', async () => {
    const portal = createTestPortal();
    const artifact1 = await collector.collectFromPortal(portal);

    const diffAdapter = createMockAdapter({
      screenshot: async () => Buffer.from('different-screenshot-data'),
    });
    const diffCollector = new BrowserEvidenceCollector(defaultConfig, diffAdapter);
    const artifact2 = await diffCollector.collectFromPortal(portal);

    const result = collector.compareArtifacts(artifact1, artifact2);
    assert.equal(result.changed, true);
    assert.ok(result.differences.length > 0);
  });

  it('should retry on failure with exponential backoff', async () => {
    let attempts = 0;
    const retryAdapter = createMockAdapter({
      launch: async () => {
        attempts++;
        if (attempts <= 2) {
          throw new Error(`Attempt ${attempts} failed`);
        }
      },
    });

    const retryCollector = new BrowserEvidenceCollector(
      { retryCount: 3 },
      retryAdapter
    );

    const portal = createTestPortal();
    const artifact = await retryCollector.collectFromPortal(portal);

    assert.equal(attempts, 3);
    assert.ok(artifact.id);
  });

  it('should throw after exhausting retries', async () => {
    const alwaysFailAdapter = createMockAdapter({
      launch: async () => {
        throw new Error('Always fails');
      },
    });

    const failCollector = new BrowserEvidenceCollector(
      { retryCount: 1 },
      alwaysFailAdapter
    );

    const portal = createTestPortal();
    await assert.rejects(
      () => failCollector.collectFromPortal(portal),
      /Failed after 2 attempts/
    );
  });

  it('should track sessions', async () => {
    const portal = createTestPortal();
    await collector.collectFromPortal(portal);

    const sessions = collector.getSessions();
    assert.equal(sessions.length, 1);
    assert.equal(sessions[0].status, 'completed');
    assert.equal(sessions[0].portalId, 'TestPortal');
  });

  it('should work with template portals', async () => {
    const artifact = await collector.collectFromPortal(AWS_CONSOLE);
    assert.equal(artifact.portalId, 'AWS Console');

    const cfArtifact = await collector.collectFromPortal(CLOUDFLARE_DASHBOARD);
    assert.equal(cfArtifact.portalId, 'Cloudflare Dashboard');
  });

  it('should handle authentication failure gracefully', async () => {
    const noLoginAdapter = createMockAdapter();
    const noLoginCollector = new BrowserEvidenceCollector({ retryCount: 0 }, noLoginAdapter);

    const portal = createTestPortal({
      selectors: {},
    });

    await assert.rejects(
      () => noLoginCollector.collectFromPortal(portal),
      /Authentication failed: No login selector defined/
    );
  });

  it('should generate consistent hashes for same data', async () => {
    const adapter1 = createMockAdapter();
    const adapter2 = createMockAdapter();
    const collector1 = new BrowserEvidenceCollector(defaultConfig, adapter1);
    const collector2 = new BrowserEvidenceCollector(defaultConfig, adapter2);

    const portal = createTestPortal();
    const artifact1 = await collector1.collectFromPortal(portal);
    const artifact2 = await collector2.collectFromPortal(portal);

    assert.equal(artifact1.hash, artifact2.hash);
  });
});
