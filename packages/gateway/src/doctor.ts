#!/usr/bin/env node
import { getConnectorRegistry } from '@grc-claw/connectors';

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

try {
  const reg = getConnectorRegistry();
  for (const llm of reg.listLlm()) {
    checks.push({
      name: `LLM ${llm.id} api key (${llm.apiKeyEnv})`,
      ok: Boolean(reg.resolveApiKey(llm.apiKeyEnv)),
      hint: llm.apiKeyEnv,
    });
  }
  for (const mcp of reg.listMcp()) {
    checks.push({
      name: `MCP ${mcp.id} configured`,
      ok: Boolean(mcp.url),
      hint: mcp.url,
    });
    if (mcp.apiKeyEnv) {
      checks.push({
        name: `MCP ${mcp.id} api key (${mcp.apiKeyEnv})`,
        ok: Boolean(reg.resolveApiKey(mcp.apiKeyEnv)),
      });
    }
  }
  if (reg.listLlm().length === 0 && reg.listMcp().length === 0) {
    checks.push({
      name: 'BYOC connectors (optional)',
      ok: true,
      hint: 'Set GRC_CLAW_CONNECTORS_CONFIG for LLM/MCP',
    });
  }
} catch (e) {
  checks.push({
    name: 'BYOC connectors config',
    ok: false,
    hint: e instanceof Error ? e.message : 'invalid config',
  });
}

console.log('GRC_Claw doctor — Agentic AI Security + A2Z SOC bridge + BYOC\n');
for (const c of checks) {
  console.log(`${c.ok ? '✓' : '✗'} ${c.name}${c.hint ? ` (${c.hint})` : ''}`);
}

const failed = checks.filter((c) => !c.ok).length;
console.log(`\nGateway health probe: http://${host}:${port}/health`);
process.exit(failed > 0 && process.env.A2Z_SOC_MODE === 'private' ? 1 : 0);
