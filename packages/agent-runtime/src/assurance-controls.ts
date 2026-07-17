/**
 * Assurance-plane control IDs for Agent Trust Passport (not a Stakpak DevOps clone).
 * Map secret-blind handling and destructive deny into GRC language.
 */
export const AGENT_TRUST_ASSURANCE_CONTROLS = [
  {
    id: 'atp-execpolicy-allowlist',
    title: 'ExecPolicy tool allowlist',
    description: 'Agents may only invoke tools present in the ExecPolicy allowlist.',
    frameworks: ['iso42001', 'soc2', 'nist-ai-rmf'],
  },
  {
    id: 'atp-destructive-human-gate',
    title: 'Destructive action human gate',
    description: 'Destructive-tier tools require explicit approval before execution.',
    frameworks: ['iso42001', 'soc2', 'eu-ai-act'],
  },
  {
    id: 'atp-secret-blind-args',
    title: 'Secret-blind argument redaction',
    description: 'Audit and trust exports redact secret material from tool arguments.',
    frameworks: ['iso27001', 'soc2', 'gdpr'],
  },
  {
    id: 'atp-decision-ledger',
    title: 'Decision ledger sync',
    description: 'ExecPolicy decisions sync to a2zsoc agent_trust_events for buyer verify.',
    frameworks: ['iso42001', 'soc2'],
  },
  {
    id: 'atp-passport-freshness',
    title: 'Passport freshness window',
    description: 'Buyer verify bands require living decisions within 30 days.',
    frameworks: ['iso42001', 'nist-ai-rmf'],
  },
] as const;

export type AgentTrustAssuranceControlId = (typeof AGENT_TRUST_ASSURANCE_CONTROLS)[number]['id'];
