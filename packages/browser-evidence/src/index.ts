export type {
  PortalConfig,
  EvidenceArtifact,
  BrowserSession,
  CollectorConfig,
  BrowserAdapter,
  AuthResult,
} from './types.js';
export { generateId, hashData } from './types.js';
export { BrowserEvidenceCollector } from './BrowserEvidenceCollector.js';
export {
  AWS_CONSOLE,
  AZURE_PORTAL,
  GCP_CONSOLE,
  OKTA_ADMIN,
  GITHUB_SETTINGS,
  CLOUDFLARE_DASHBOARD,
  PORTAL_TEMPLATES,
} from './templates/index.js';
