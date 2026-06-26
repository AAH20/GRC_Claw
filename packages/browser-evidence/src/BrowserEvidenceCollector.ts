import {
  type PortalConfig,
  type EvidenceArtifact,
  type BrowserSession,
  type CollectorConfig,
  type BrowserAdapter,
  type AuthResult,
  generateId,
  hashData,
} from './types.js';

const DEFAULT_CONFIG: CollectorConfig = {
  headless: true,
  timeout: 30000,
  retryCount: 3,
  stealthMode: true,
};

export class BrowserEvidenceCollector {
  private config: CollectorConfig;
  private adapter: BrowserAdapter;
  private sessions: Map<string, BrowserSession> = new Map();

  constructor(config: Partial<CollectorConfig> = {}, browserAdapter: BrowserAdapter) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.adapter = browserAdapter;
  }

  async collectFromPortal(portal: PortalConfig): Promise<EvidenceArtifact> {
    const session = this.createSession(portal.name);
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.config.retryCount; attempt++) {
      try {
        if (attempt > 0) {
          const delay = Math.min(1000 * Math.pow(2, attempt - 1), 10000);
          await this.sleep(delay);
        }

        await this.adapter.launch();
        session.status = 'active';

        const authResult = await this.authenticate(portal);
        if (!authResult.success) {
          throw new Error(`Authentication failed: ${authResult.error}`);
        }

        const artifact = await this.captureEvidence(portal);
        session.status = 'completed';
        session.evidenceCollected = 1;
        return artifact;
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
        session.status = 'failed';
      } finally {
        await this.safeClose();
      }
    }

    throw new Error(`Failed after ${this.config.retryCount + 1} attempts: ${lastError?.message}`);
  }

  async collectFromMultiplePortals(portals: PortalConfig[]): Promise<EvidenceArtifact[]> {
    const results: EvidenceArtifact[] = [];

    for (const portal of portals) {
      try {
        const artifact = await this.collectFromPortal(portal);
        results.push(artifact);
      } catch {
        // continue collecting from remaining portals
      }
    }

    return results;
  }

  compareArtifacts(
    previous: EvidenceArtifact,
    current: EvidenceArtifact
  ): { changed: boolean; differences: string[] } {
    const differences: string[] = [];

    if (previous.hash !== current.hash) {
      differences.push('overall_hash_changed');
    }

    if (!previous.screenshot.equals(current.screenshot)) {
      differences.push('screenshot_changed');
    }

    if (previous.domSnapshot !== current.domSnapshot) {
      differences.push('dom_changed');
    }

    const prevKeys = Object.keys(previous.structuredData);
    const currKeys = Object.keys(current.structuredData);

    const addedKeys = currKeys.filter((k) => !prevKeys.includes(k));
    const removedKeys = prevKeys.filter((k) => !currKeys.includes(k));

    if (addedKeys.length > 0) {
      differences.push(`data_added: ${addedKeys.join(', ')}`);
    }
    if (removedKeys.length > 0) {
      differences.push(`data_removed: ${removedKeys.join(', ')}`);
    }

    for (const key of prevKeys) {
      if (currKeys.includes(key)) {
        const prevVal = JSON.stringify(previous.structuredData[key]);
        const currVal = JSON.stringify(current.structuredData[key]);
        if (prevVal !== currVal) {
          differences.push(`data_changed: ${key}`);
        }
      }
    }

    return { changed: differences.length > 0, differences };
  }

  getSessions(): BrowserSession[] {
    return Array.from(this.sessions.values());
  }

  private createSession(portalId: string): BrowserSession {
    const session: BrowserSession = {
      id: generateId(),
      portalId,
      status: 'active',
      startTime: new Date().toISOString(),
      evidenceCollected: 0,
    };
    this.sessions.set(session.id, session);
    return session;
  }

  private async authenticate(portal: PortalConfig): Promise<AuthResult> {
    try {
      await this.adapter.navigate(portal.url);

      const loginSelector = portal.selectors.login;
      if (!loginSelector) {
        return { success: false, error: 'No login selector defined' };
      }

      const hasLogin = await this.elementExists(loginSelector);
      if (!hasLogin) {
        return { success: true };
      }

      await this.typeIntoSelector(loginSelector, portal.credentials.username || '');

      const passwordField = 'input[type="password"]';
      const hasPassword = await this.elementExists(passwordField);
      if (hasPassword) {
        await this.typeIntoSelector(passwordField, portal.credentials.password || '');
      }

      const submitButton = 'button[type="submit"], input[type="submit"], #signInButton';
      const hasSubmit = await this.elementExists(submitButton);
      if (hasSubmit) {
        await this.clickElement(submitButton);
      }

      await this.sleep(2000);

      const currentUrl = portal.url;
      const loginStillVisible = await this.elementExists(loginSelector);
      if (loginStillVisible) {
        return { success: false, error: 'Still on login page after submission' };
      }

      return { success: true };
    } catch (err) {
      return { success: false, error: err instanceof Error ? err.message : String(err) };
    }
  }

  private async captureEvidence(portal: PortalConfig): Promise<EvidenceArtifact> {
    const allScreenshots: Buffer[] = [];
    const allDomSnapshots: string[] = [];
    const structuredData: Record<string, unknown> = {};

    for (const path of portal.screenshotPaths) {
      const fullUrl = new URL(path, portal.url).toString();
      await this.adapter.navigate(fullUrl);

      await this.sleep(1000);

      const screenshot = await this.adapter.screenshot();
      allScreenshots.push(screenshot);

      const content = await this.adapter.getContent();
      allDomSnapshots.push(content);

      for (const [key, selector] of Object.entries(portal.selectors)) {
        if (key === 'login') continue;
        if (selector) {
          const text = await this.extractTextBySelector(selector);
          if (text) {
            structuredData[key] = text;
          }
        }
      }
    }

    const combinedScreenshot = Buffer.concat(allScreenshots);
    const combinedDom = allDomSnapshots.join('\n---PAGE_BREAK---\n');

    const hashPayload = JSON.stringify({
      portal: portal.name,
      screenshots: combinedScreenshot.toString('base64'),
      dom: combinedDom,
      data: structuredData,
    });

    return {
      id: generateId(),
      portalId: portal.name,
      screenshot: combinedScreenshot,
      domSnapshot: combinedDom,
      structuredData,
      hash: hashData(hashPayload),
      timestamp: new Date().toISOString(),
      metadata: {
        pathsCaptured: portal.screenshotPaths.length,
        authType: portal.authType,
      },
    };
  }

  private async elementExists(selector: string): Promise<boolean> {
    return this.adapter.elementExists(selector);
  }

  private async typeIntoSelector(selector: string, text: string): Promise<void> {
    await this.adapter.fillInput(selector, text);
  }

  private async clickElement(selector: string): Promise<void> {
    await this.adapter.click(selector);
  }

  private async extractTextBySelector(selector: string): Promise<string | null> {
    return this.adapter.getText(selector);
  }

  private async safeClose(): Promise<void> {
    try {
      await this.adapter.close();
    } catch {
      // ignore close errors
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
