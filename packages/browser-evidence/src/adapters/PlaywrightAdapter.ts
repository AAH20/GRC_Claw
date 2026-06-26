import type { Browser, BrowserContext, Page } from 'playwright';
import type { BrowserAdapter } from '../types.js';

export interface PlaywrightAdapterOptions {
  headless?: boolean;
  timeout?: number;
  slowMo?: number;
  userAgent?: string;
  viewport?: { width: number; height: number };
  args?: string[];
  chromiumArgs?: string[];
  firefoxArgs?: string[];
  webkitArgs?: string[];
}

const DEFAULT_OPTIONS: Required<PlaywrightAdapterOptions> = {
  headless: true,
  timeout: 30_000,
  slowMo: 0,
  userAgent: '',
  viewport: { width: 1920, height: 1080 },
  args: [],
  chromiumArgs: [],
  firefoxArgs: [],
  webkitArgs: [],
};

export class PlaywrightAdapter implements BrowserAdapter {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;
  private options: Required<PlaywrightAdapterOptions>;
  private playwright: typeof import('playwright') | null = null;

  constructor(options: PlaywrightAdapterOptions = {}) {
    this.options = { ...DEFAULT_OPTIONS, ...options };
  }

  async launch(): Promise<void> {
    if (this.page) {
      return;
    }

    try {
      this.playwright = await import('playwright');
    } catch {
      throw new Error(
        'Playwright is not installed. Run: npm install playwright'
      );
    }

    const launchOptions: Record<string, unknown> = {
      headless: this.options.headless,
      slowMo: this.options.slowMo || undefined,
    };

    const allArgs = [
      ...this.options.args,
      ...this.options.chromiumArgs,
    ].filter(Boolean);
    if (allArgs.length > 0) {
      launchOptions.args = allArgs;
    }

    this.browser = await this.playwright.chromium.launch(launchOptions);

    const contextOptions: Record<string, unknown> = {};
    if (this.options.userAgent) {
      contextOptions.userAgent = this.options.userAgent;
    }
    if (this.options.viewport) {
      contextOptions.viewport = this.options.viewport;
    }

    this.context = await this.browser.newContext(contextOptions);
    this.page = await this.context.newPage();
    this.page.setDefaultTimeout(this.options.timeout);
  }

  async navigate(url: string): Promise<void> {
    const page = this.getPage();
    await page.goto(url, { waitUntil: 'domcontentloaded' });
  }

  async screenshot(): Promise<Buffer> {
    const page = this.getPage();
    const buffer = await page.screenshot({ type: 'png', fullPage: false });
    return Buffer.from(buffer);
  }

  async getContent(): Promise<string> {
    const page = this.getPage();
    return page.content();
  }

  async close(): Promise<void> {
    try {
      if (this.page && !this.page.isClosed()) {
        await this.page.close();
      }
    } catch {
      // ignore close errors
    }

    try {
      if (this.context) {
        await this.context.close();
      }
    } catch {
      // ignore close errors
    }

    try {
      if (this.browser && this.browser.isConnected()) {
        await this.browser.close();
      }
    } catch {
      // ignore close errors
    }

    this.page = null;
    this.context = null;
    this.browser = null;
  }

  async fillInput(selector: string, value: string): Promise<void> {
    const page = this.getPage();
    const locator = page.locator(selector);
    await locator.fill(value);
  }

  async click(selector: string): Promise<void> {
    const page = this.getPage();
    const locator = page.locator(selector);
    await locator.click();
  }

  async getText(selector: string): Promise<string | null> {
    const page = this.getPage();
    const locator = page.locator(selector);

    const visible = await locator.isVisible().catch(() => false);
    if (!visible) {
      return null;
    }

    const text = await locator.textContent();
    return text?.trim() ?? null;
  }

  async elementExists(selector: string): Promise<boolean> {
    const page = this.getPage();
    const locator = page.locator(selector);
    const count = await locator.count();
    return count > 0;
  }

  private getPage(): Page {
    if (!this.page || this.page.isClosed()) {
      throw new Error(
        'Browser page is not available. Call launch() first or ensure the page has not been closed.'
      );
    }
    return this.page;
  }
}
