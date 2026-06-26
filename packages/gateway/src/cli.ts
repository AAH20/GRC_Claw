#!/usr/bin/env node
import { createGateway } from './server.js';
import { initPersistence } from './persistence-init.js';

const host = process.env.GRC_CLAW_HOST ?? '127.0.0.1';
const port = Number(process.env.GRC_CLAW_PORT ?? '18791');
const token = process.env.GRC_CLAW_GATEWAY_TOKEN ?? 'dev-change-me';

async function main() {
  const persistence = await initPersistence();
  const gw = createGateway({ host, port, token }, persistence);

  await gw.listen();
  console.log(`GRC_Claw gateway listening on http://${host}:${port}`);
  console.log(`Persistence: ${persistence ? 'PostgreSQL' : 'demo (in-memory)'}`);
  console.log('Agentic AI security: ENABLED (exec policy + audit)');
  console.log(`A2Z SOC bridge: ${process.env.A2Z_SOC_MODE ?? 'demo'} → ${process.env.A2Z_SOC_BASE_URL ?? 'n/a'}`);
  console.log('Market: Open-source GRC + Private A2Z SOC');

  process.on('SIGINT', async () => {
    await gw.close();
    process.exit(0);
  });
}

main().catch((err) => {
  console.error('Gateway startup failed:', err);
  process.exit(1);
});
