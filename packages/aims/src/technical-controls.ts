export interface AimsTechnicalControl {
  id: string;
  objective: string;
  clause: string;
  grcClawComponent: string;
  evidenceCommand?: string;
}

export const AIMS_TECHNICAL_CONTROLS: AimsTechnicalControl[] = [
  {
    id: 'TC-01',
    objective: 'Human oversight of agent actions',
    clause: '8 / A.14',
    grcClawComponent: '@grc-claw/agent-runtime',
    evidenceCommand: 'POST /api/agent/invoke (destructive without approval → 403)',
  },
  {
    id: 'TC-02',
    objective: 'Traceability of agent decisions',
    clause: '9 / A.10',
    grcClawComponent: 'AgentSession.getAuditLog()',
  },
  {
    id: 'TC-03',
    objective: 'Access control to control plane',
    clause: '8 / A.12',
    grcClawComponent: '@grc-claw/gateway',
    evidenceCommand: 'WS connect + X-GRC-Claw-Token',
  },
  {
    id: 'TC-04',
    objective: 'Integrity of compliance evidence',
    clause: '7 / A.6',
    grcClawComponent: '@grc-claw/evidence',
  },
  {
    id: 'TC-05',
    objective: 'Monitoring AI-related security events',
    clause: '9 / A.10',
    grcClawComponent: '@grc-claw/ingest + a2zsoc.com',
    evidenceCommand: 'POST /api/ingest/normalize',
  },
  {
    id: 'TC-06',
    objective: 'Supplier API key hygiene',
    clause: '8 / A.9',
    grcClawComponent: 'npm run doctor',
  },
];

export function listTechnicalControls(): AimsTechnicalControl[] {
  return [...AIMS_TECHNICAL_CONTROLS];
}
