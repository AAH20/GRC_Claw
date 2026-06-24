const STORAGE_KEY = 'grc-claw-console-settings';

export interface ConsoleSettings {
  baseUrl: string;
  token: string;
  tenantId: number;
  a2zSocUrl: string;
  a2zTrustTenantId: string;
  trustScore: number;
  trustTier: string;
  cursorAutoMode: boolean;
}

const defaults: ConsoleSettings = {
  baseUrl: '',
  token: '',
  tenantId: 1,
  a2zSocUrl: 'https://a2zsoc.com',
  a2zTrustTenantId: 'demo',
  trustScore: 87,
  trustTier: 'Gold',
  cursorAutoMode: true,
};

export function loadSettings(): ConsoleSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { ...defaults };
    return { ...defaults, ...JSON.parse(raw) };
  } catch {
    return { ...defaults };
  }
}

export function saveSettings(s: ConsoleSettings): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
}

export function settingsVersion(): number {
  const s = loadSettings();
  return s.token.length + s.baseUrl.length + (s.cursorAutoMode ? 1 : 0);
}
