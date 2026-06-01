import { loadSettings } from './settings';

export interface SchedulableJob {
  id: string;
  name: string;
  type: 'long-running' | 'cron-friendly';
  endpoint: string;
  method: string;
  auth: boolean;
  description: string;
  suggestedSchedule?: string;
}

/** Jobs the GRC_Claw gateway exposes — schedulable via host cron or Cursor Automations (not OS daemons in-browser). */
export const GATEWAY_JOBS: SchedulableJob[] = [
  {
    id: 'gateway-daemon',
    name: 'GRC_Claw gateway (control plane)',
    type: 'long-running',
    endpoint: 'http://127.0.0.1:18791',
    method: 'LISTEN',
    auth: false,
    description:
      'Long-lived HTTP + WebSocket daemon. Run: GRC_CLAW_GATEWAY_TOKEN=… npm run gateway. Keep alive with systemd/pm2.',
    suggestedSchedule: 'Always on (systemd service)',
  },
  {
    id: 'health-ping',
    name: 'Health check',
    type: 'cron-friendly',
    endpoint: '/health',
    method: 'GET',
    auth: false,
    description: 'Liveness probe — confirms gateway, BYOC, A2Z mode flags.',
    suggestedSchedule: '*/5 * * * * (every 5 min)',
  },
  {
    id: 'a2z-sync',
    name: 'A2Z SOC bridge sync',
    type: 'cron-friendly',
    endpoint: '/api/a2z/sync',
    method: 'POST',
    auth: true,
    description: 'Pull last hour of security_events from Private A2Z SOC (needs A2Z_SOC_MODE=private).',
    suggestedSchedule: '0 * * * * (hourly)',
  },
  {
    id: 'connectors-reload',
    name: 'BYOC connectors reload',
    type: 'cron-friendly',
    endpoint: '/api/connectors/reload',
    method: 'POST',
    auth: true,
    description: 'Reload LLM/MCP registry from env after config changes.',
    suggestedSchedule: 'On deploy only',
  },
  {
    id: 'ingest-batch',
    name: 'SIEM / cloud ingest normalize',
    type: 'cron-friendly',
    endpoint: '/api/ingest/normalize',
    method: 'POST',
    auth: true,
    description: 'Normalize vendor JSON → canonical event + complianceImpact (per payload).',
    suggestedSchedule: 'Per alert webhook or batch ETL',
  },
  {
    id: 'agent-read-controls',
    name: 'Agent: list controls',
    type: 'cron-friendly',
    endpoint: '/api/agent/invoke',
    method: 'POST',
    auth: true,
    description: 'Read tier — tool grc.list_controls with tenantId.',
    suggestedSchedule: 'Daily compliance snapshot',
  },
  {
    id: 'agent-read-score',
    name: 'Agent: compliance score',
    type: 'cron-friendly',
    endpoint: '/api/agent/invoke',
    method: 'POST',
    auth: true,
    description: 'Read tier — tool grc.get_compliance_score.',
    suggestedSchedule: 'Daily',
  },
  {
    id: 'agent-read-events',
    name: 'Agent: query SOC events',
    type: 'cron-friendly',
    endpoint: '/api/agent/invoke',
    method: 'POST',
    auth: true,
    description: 'Read tier — tool soc.query_events.',
    suggestedSchedule: 'Hourly with sync',
  },
  {
    id: 'frameworks-export',
    name: 'Framework packs export',
    type: 'cron-friendly',
    endpoint: '/api/frameworks',
    method: 'GET',
    auth: false,
    description: 'ISO 27001, NIST CSF, SOC 2, ISO 42001 control packs.',
    suggestedSchedule: 'Weekly audit baseline',
  },
  {
    id: 'aims-vendor-gaps',
    name: 'ISO 42001 vendor gaps',
    type: 'cron-friendly',
    endpoint: '/api/aims/vendor-gaps',
    method: 'GET',
    auth: false,
    description: 'AI vendor gap matrix (Anthropic, OpenAI, Cursor, OpenClaw).',
    suggestedSchedule: 'Monthly supply-chain review',
  },
];

export function wantsJobCatalog(userText: string): boolean {
  return /\b(list|show|all|what|which)\b/i.test(userText) &&
    /\b(daemon|cron|job|schedule|automati|background|task)\b/i.test(userText);
}

export function formatSchedulableJobsCatalog(): string {
  const token = loadSettings().token || 'YOUR_GRC_CLAW_GATEWAY_TOKEN';
  const base = loadSettings().baseUrl.trim() || 'http://127.0.0.1:18791';

  const longRunning = GATEWAY_JOBS.filter((j) => j.type === 'long-running');
  const cronJobs = GATEWAY_JOBS.filter((j) => j.type === 'cron-friendly');

  let out =
    '## What I can run (GRC_Claw gateway)\n\n' +
    'This console **does not** start OS daemons or edit your crontab. Below is the full catalog of **gateway operations** you can run manually, via **host cron**, or **Cursor Automations** while the gateway daemon is up.\n\n';

  out += '### Long-running process (daemon)\n\n';
  for (const j of longRunning) {
    out += `| **${j.name}** | ${j.description} |\n`;
    out += `| Schedule | ${j.suggestedSchedule} |\n\n`;
  }

  out += '### Cron-friendly API jobs (curl / automation)\n\n';
  out += '| Job | Method | Endpoint | Auth | Suggested schedule |\n';
  out += '|-----|--------|----------|------|--------------------|\n';
  for (const j of cronJobs) {
    out += `| ${j.name} | ${j.method} | \`${j.endpoint}\` | ${j.auth ? 'Yes' : 'No'} | ${j.suggestedSchedule ?? '—'} |\n`;
  }

  out +=
    '\n### Example crontab (A2Z hourly sync)\n\n```bash\n' +
    `0 * * * * curl -s -X POST ${base}/api/a2z/sync -H "X-GRC-Claw-Token: ${token}"\n` +
    '```\n\n';

  out +=
    '### Example: daily control listing\n\n```bash\n' +
    `0 6 * * * curl -s -X POST ${base}/api/agent/invoke -H "X-GRC-Claw-Token: ${token}" -H "Content-Type: application/json" -d '{"sessionId":"cron","tool":"grc.list_controls","args":{"tenantId":1}}'\n` +
    '```\n\n';

  out +=
    '### Cursor IDE (not this browser)\n\n' +
    '- **Cursor Automations** (desktop): schedule agents with shell/MCP steps that call the URLs above.\n' +
    '- **Skills**: `GRC_Claw/.cursor/skills/` — used by Cursor agents, not executed by this web chat.\n\n' +
    'Ask me to **run** a job now (e.g. “sync A2Z” or “health check”) and I will call the gateway live.';

  return out;
}
