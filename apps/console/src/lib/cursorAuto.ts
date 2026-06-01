import { loadSettings } from './settings';
import type { CursorAutoHint } from './pageMeta';

export function gatewayBase(): string {
  const s = loadSettings().baseUrl.trim();
  if (s) return s.replace(/\/$/, '');
  if (typeof window !== 'undefined') return window.location.origin;
  return 'http://127.0.0.1:18791';
}

export function buildCurl(hint: CursorAutoHint): string {
  const base = gatewayBase();
  const url = `${base}${hint.endpoint}`;
  const { token } = loadSettings();
  const headers = ["-H 'Content-Type: application/json'"];
  if (hint.auth && token) headers.push(`-H 'X-GRC-Claw-Token: ${token}'`);
  const body =
    hint.method !== 'GET' && hint.exampleBody
      ? ` \\\n  -d '${hint.exampleBody.replace(/'/g, "'\\''")}'`
      : '';
  return `curl -s -X ${hint.method} '${url}' \\\n  ${headers.join(' \\\n  ')}${body}`;
}

export const CURSOR_MCP_SNIPPET = `{
  "mcpServers": {
    "grc-claw-gateway": {
      "url": "http://127.0.0.1:18791",
      "headers": {
        "X-GRC-Claw-Token": "YOUR_GRC_CLAW_GATEWAY_TOKEN"
      },
      "description": "GRC_Claw HTTP gateway — use fetch/curl from Cursor Auto Mode"
    }
  }
}`;

export const CURSOR_AUTO_RULES = `# GRC_Claw — Cursor Auto Mode rules
- Gateway default: http://127.0.0.1:18791
- Auth header: X-GRC-Claw-Token (matches GRC_CLAW_GATEWAY_TOKEN)
- Read GET /health and GET /api/frameworks without auth
- Never invoke destructive agent tools without explicit user approval
- Prefer ingest → complianceImpact before suggesting control updates
- A2Z SOC bridge: POST /api/a2z/sync (auth required) when A2Z_SOC_MODE=private
- Full API map: http://localhost:5174/llms.txt
`;

// Re-exported from chatPrompts for backward compatibility
export { CURSOR_AUTO_SYSTEM_PROMPT } from './chatPrompts';
