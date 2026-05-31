#!/usr/bin/env node
import { createGateway } from './server.js';

const host = process.env.GRC_CLAW_HOST ?? '127.0.0.1';
const port = Number(process.env.GRC_CLAW_PORT ?? '18791');
const token = process.env.GRC_CLAW_GATEWAY_TOKEN ?? 'dev-change-me';

const gw = createGateway({ host, port, token });

gw.listen().then(() => {
  console.log(`GRC_Claw gateway listening on http://${host}:${port}`);
  console.log('Agentic AI security: ENABLED (exec policy + audit)');
  console.log(`A2Z SOC bridge: ${process.env.A2Z_SOC_MODE ?? 'demo'} → ${process.env.A2Z_SOC_BASE_URL ?? 'n/a'}`);
  console.log('Market: Open-source GRC + Private A2Z SOC');
});

process.on('SIGINT', () => {
  gw.close().then(() => process.exit(0));
});
