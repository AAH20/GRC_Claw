/**
 * GRC_Claw TypeScript SDK - Composed/Aggregated APIs
 * ================================================
 * Dashboard, agent 360, compliance report, and executive summary.
 */

import { GRCClawClient } from '@grc-claw/sdk';

const client = new GRCClawClient({
  apiKey: 'grc_live_abc123...',
  tenantId: 'org-acme',
  environment: 'production',
});

async function composedExamples() {
  // --- Dashboard Overview ---
  const dashboard = await client.system.request('GET', '/v1.0/composed/dashboard');
  console.log(`Compliance: ${dashboard.compliance_summary.overall_score}%`);
  console.log(`Active agents: ${dashboard.active_agents.total}`);
  console.log(`Open findings: ${dashboard.open_findings.total}`);
  console.log(`Risk alerts: ${dashboard.risk_alerts.active}`);

  // --- Agent 360 ---
  const agent360 = await client.system.request('GET', '/v1.0/composed/agents/agent-1/360');
  console.log(`Agent: ${agent360.agent.name}`);
  console.log(`  Policies: ${agent360.policies.length}`);
  console.log(`  Enforcements: ${agent360.enforcements.total_24h}`);
  console.log(`  Evidence: ${agent360.evidence.total_submitted}`);

  // --- Compliance Report ---
  const report = await client.system.request('GET', '/v1.0/composed/compliance-report');
  for (const fw of report.frameworks) {
    console.log(`  ${fw.name}: ${fw.score}% (${fw.status})`);
  }

  // --- Executive Summary ---
  const summary = await client.system.request('GET', '/v1.0/composed/executive-summary');
  console.log(`Overall: ${summary.overall_compliance_score}`);
  console.log(`Risk: ${JSON.stringify(summary.risk_posture)}`);
  console.log(`Agents: ${JSON.stringify(summary.agent_governance)}`);
}

composedExamples().catch(console.error);
