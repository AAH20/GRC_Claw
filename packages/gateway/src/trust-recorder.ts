/**
 * Create a fire-and-forget TrustDecisionRecorder bound to A2Z SOC when configured.
 */
import type { TrustDecisionRecorder } from '@grc-claw/agent-runtime';
import { A2ZSocConnector, loadA2ZConfigFromEnv } from '@grc-claw/a2z-connector';

export function createA2ZTrustRecorder(): TrustDecisionRecorder | undefined {
  const cfg = loadA2ZConfigFromEnv();
  if (cfg.mode === 'demo' || !process.env.A2Z_SOC_API_KEY || process.env.A2Z_SOC_API_KEY === 'demo-key') {
    return undefined;
  }
  const connector = new A2ZSocConnector(cfg);
  return (payload) => {
    void connector
      .recordAgentTrustDecision({
        agentId: payload.agentId,
        decision: payload.decision,
        tool: payload.tool,
        tier: payload.tier,
        reason: payload.reason,
      })
      .catch(() => undefined);
  };
}
