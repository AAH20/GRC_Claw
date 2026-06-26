import type { PortalConfig } from '../types.js';

export const AWS_CONSOLE: PortalConfig = {
  name: 'AWS Console',
  url: 'https://console.aws.amazon.com',
  authType: 'sso',
  credentials: { username: '', password: '' },
  selectors: {
    login: '#username, #signInButton, [data-testid="sign-in"]',
    iam: '#nav-iam, a[href*="iam"]',
    securityhub: 'a[href*="securityhub"], [data-testid="security-hub"]',
  },
  screenshotPaths: ['/', '/iam/home', '/securityhub/home'],
};

export const AZURE_PORTAL: PortalConfig = {
  name: 'Azure Portal',
  url: 'https://portal.azure.com',
  authType: 'sso',
  credentials: { username: '', password: '' },
  selectors: {
    login: '#i0116, #sign-in, [data-testid="login-form"]',
    defender: 'a[href*="Defender"], [data-testid="defender"]',
    sentinel: 'a[href*="Sentinel"], [data-testid="sentinel"]',
  },
  screenshotPaths: ['/', '/@Microsoft_Azure_Security_Center', '/@Microsoft_Azure_Sentinel'],
};

export const GCP_CONSOLE: PortalConfig = {
  name: 'GCP Console',
  url: 'https://console.cloud.google.com',
  authType: 'sso',
  credentials: { username: '', password: '' },
  selectors: {
    login: '#identifierId, [data-testid="login-form"]',
    scc: 'a[href*="security-command-center"], [data-testid="scc"]',
    chronicle: 'a[href*="chronicle"], [data-testid="chronicle"]',
  },
  screenshotPaths: ['/', '/security/command-center', '/chronicle/overview'],
};

export const OKTA_ADMIN: PortalConfig = {
  name: 'Okta Admin',
  url: 'https://admin.okta.com',
  authType: 'sso',
  credentials: { username: '', password: '' },
  selectors: {
    login: '#username, #okta-sign-in, [data-testid="okta-login"]',
    users: 'a[href*="/admin/users"], [data-testid="users"]',
    factors: 'a[href*="/admin/factors"], [data-testid="factors"]',
  },
  screenshotPaths: ['/', '/admin/users', '/admin/factors'],
};

export const GITHUB_SETTINGS: PortalConfig = {
  name: 'GitHub Settings',
  url: 'https://github.com',
  authType: 'sso',
  credentials: { username: '', password: '' },
  selectors: {
    login: '#login, #password, [data-testid="github-login"]',
    security: 'a[href*="/settings/security"], [data-testid="security"]',
    actions: 'a[href*="/settings/actions"], [data-testid="actions"]',
  },
  screenshotPaths: ['/', '/settings/security', '/settings/actions'],
};

export const CLOUDFLARE_DASHBOARD: PortalConfig = {
  name: 'Cloudflare Dashboard',
  url: 'https://dash.cloudflare.com',
  authType: 'sso',
  credentials: { email: '', password: '' },
  selectors: {
    login: '#email, #password, [data-testid="cf-login"]',
    security: 'a[href*="/security"], [data-testid="security"]',
    waf: 'a[href*="/waf"], [data-testid="waf"]',
  },
  screenshotPaths: ['/', '/security/overview', '/waf'],
};

export const PORTAL_TEMPLATES: Record<string, PortalConfig> = {
  AWS_CONSOLE,
  AZURE_PORTAL,
  GCP_CONSOLE,
  OKTA_ADMIN,
  GITHUB_SETTINGS,
  CLOUDFLARE_DASHBOARD,
};
