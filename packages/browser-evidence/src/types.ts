import { randomUUID } from 'node:crypto';
import { createHash } from 'node:crypto';

export interface PortalConfig {
  name: string;
  url: string;
  authType: 'basic' | 'oauth' | 'sso' | 'api_key';
  credentials: Record<string, string>;
  selectors: Record<string, string>;
  screenshotPaths: string[];
}

export interface EvidenceArtifact {
  id: string;
  portalId: string;
  screenshot: Buffer;
  domSnapshot: string;
  structuredData: Record<string, unknown>;
  hash: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

export interface BrowserSession {
  id: string;
  portalId: string;
  status: 'active' | 'completed' | 'failed';
  startTime: string;
  evidenceCollected: number;
}

export interface CollectorConfig {
  headless: boolean;
  timeout: number;
  retryCount: number;
  stealthMode: boolean;
}

export interface BrowserAdapter {
  launch(): Promise<void>;
  navigate(url: string): Promise<void>;
  screenshot(): Promise<Buffer>;
  getContent(): Promise<string>;
  close(): Promise<void>;
}

export interface AuthResult {
  success: boolean;
  error?: string;
}

export function generateId(): string {
  return randomUUID();
}

export function hashData(data: string): string {
  return createHash('sha256').update(data).digest('hex');
}
