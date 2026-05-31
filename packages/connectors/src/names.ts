/** Stable agent tool name: mcp.<serverId>.<toolName> */
export function mcpGatedToolName(serverId: string, toolName: string): string {
  const s = sanitizeSegment(serverId);
  const t = sanitizeSegment(toolName);
  return `mcp.${s}.${t}`;
}

export function parseMcpGatedToolName(
  gatedName: string
): { serverId: string; toolName: string } | null {
  if (!gatedName.startsWith('mcp.')) return null;
  const rest = gatedName.slice(4);
  const dot = rest.indexOf('.');
  if (dot < 1) return null;
  return { serverId: rest.slice(0, dot), toolName: rest.slice(dot + 1) };
}

export function llmGatedToolName(providerId: string): string {
  return `llm.${sanitizeSegment(providerId)}.complete`;
}

export function parseLlmGatedToolName(gatedName: string): string | null {
  if (!gatedName.startsWith('llm.')) return null;
  const rest = gatedName.slice(4);
  if (!rest.endsWith('.complete')) return null;
  const providerId = rest.slice(0, -'.complete'.length);
  const dot = providerId.lastIndexOf('.');
  if (dot >= 0) return null;
  return providerId || null;
}

function sanitizeSegment(value: string): string {
  return value.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 64);
}
