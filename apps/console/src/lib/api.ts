import { loadSettings } from './settings';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body: unknown
  ) {
    super(message);
  }
}

function resolveBase(): string {
  const s = loadSettings().baseUrl.trim();
  return s || '';
}

function authHeaders(extra?: Record<string, string>): Record<string, string> {
  const { token } = loadSettings();
  const h: Record<string, string> = { 'Content-Type': 'application/json', ...extra };
  if (token) h['X-GRC-Claw-Token'] = token;
  return h;
}

async function request<T>(
  path: string,
  init?: RequestInit & { auth?: boolean }
): Promise<T> {
  const url = `${resolveBase()}${path}`;
  const headers = init?.auth === false ? { 'Content-Type': 'application/json' } : authHeaders(init?.headers as Record<string, string>);
  const res = await fetch(url, { ...init, headers: { ...headers, ...(init?.headers as Record<string, string>) } });
  const text = await res.text();
  let body: unknown = text;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    /* plain text */
  }
  if (!res.ok) throw new ApiError(`HTTP ${res.status}`, res.status, body);
  return body as T;
}

export const api = {
  health: () => request<Record<string, unknown>>('/health', { auth: false }),

  frameworks: () => request<{ packs: unknown[] }>('/api/frameworks', { auth: false }),

  cursorSkills: () =>
    request<{ ok: boolean; note: string; skills: unknown[] }>('/api/cursor-skills', {
      auth: false,
    }),

  skills: () => request<{ ok: boolean; skills: unknown[] }>('/api/skills', { auth: false }),

  skillDetail: (skillId: string, includeBody = true) =>
    request<{ ok: boolean; skill: unknown }>(
      `/api/skills/${encodeURIComponent(skillId)}${includeBody ? '' : '?body=0'}`,
      { auth: false }
    ),

  skillRun: (body: unknown) =>
    request<Record<string, unknown>>('/api/skills/run', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  aimsVendorGaps: (vendor?: string) =>
    request<{ summary: unknown[]; gaps: unknown[] }>(
      vendor ? `/api/aims/vendor-gaps?vendor=${encodeURIComponent(vendor)}` : '/api/aims/vendor-gaps',
      { auth: false }
    ),

  aimsTechnicalControls: () =>
    request<{ scope: unknown; clauses: unknown[]; controls: unknown[] }>(
      '/api/aims/technical-controls',
      { auth: false }
    ),

  connectors: () => request<Record<string, unknown>>('/api/connectors', { auth: false }),

  connectorsReload: () =>
    request<{ ok: boolean }>('/api/connectors/reload', { method: 'POST' }),

  llmChat: (providerId: string, body: unknown) =>
    request<Record<string, unknown>>(`/api/connectors/llm/${encodeURIComponent(providerId)}/chat`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  mcpTools: (serverId: string) =>
    request<{ tools: unknown[] }>(`/api/connectors/mcp/${encodeURIComponent(serverId)}/tools`),

  mcpCall: (serverId: string, body: unknown) =>
    request<Record<string, unknown>>(`/api/connectors/mcp/${encodeURIComponent(serverId)}/call`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  ingestNormalize: (body: unknown) =>
    request<Record<string, unknown>>('/api/ingest/normalize', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  a2zSync: () =>
    request<Record<string, unknown>>('/api/a2z/sync', { method: 'POST' }),

  agentInvoke: (body: unknown) =>
    request<Record<string, unknown>>('/api/agent/invoke', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};
