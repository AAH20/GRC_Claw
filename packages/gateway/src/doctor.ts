#!/usr/bin/env node
const checks: { name: string; ok: boolean; hint?: string }[] = [];

const token = process.env.GRC_CLAW_GATEWAY_TOKEN;
checks.push({
  name: 'GRC_CLAW_GATEWAY_TOKEN set',
  ok: Boolean(token && token !== 'dev-change-me'),
  hint: 'Set a strong token before production',
});

checks.push({
  name: 'A2Z_SOC_MODE',
  ok: ['demo', 'private'].includes(process.env.A2Z_SOC_MODE ?? 'demo'),
});

if (process.env.A2Z_SOC_MODE === 'private') {
  checks.push({
    name: 'A2Z_SOC_BASE_URL',
    ok: Boolean(process.env.A2Z_SOC_BASE_URL),
    hint: 'Private A2Z SOC URL required',
  });
  checks.push({
    name: 'A2Z_SOC_API_KEY',
    ok: Boolean(process.env.A2Z_SOC_API_KEY),
  });
}

const host = process.env.GRC_CLAW_HOST ?? '127.0.0.1';
const port = process.env.GRC_CLAW_PORT ?? '18791';
checks.push({
  name: 'Loopback bind recommended',
  ok: host === '127.0.0.1' || host === 'localhost',
  hint: 'Expose via reverse proxy + TLS for remote access',
});

console.log('GRC_Claw doctor — Agentic AI Security + A2Z SOC bridge\n');
for (const c of checks) {
  console.log(`${c.ok ? '✓' : '✗'} ${c.name}${c.hint ? ` (${c.hint})` : ''}`);
}

const failed = checks.filter((c) => !c.ok).length;
console.log(`\nGateway health probe: http://${host}:${port}/health`);
process.exit(failed > 0 && process.env.A2Z_SOC_MODE === 'private' ? 1 : 0);
