// Compliance-as-Code: .grc-policy.yaml parser and validator

export interface GrcPolicy {
  version: '1';
  service: string;
  frameworks: string[];
  controls: PolicyControl[];
  data_classification?: 'public' | 'internal' | 'confidential' | 'restricted';
  owner?: string;
}

export interface PolicyControl {
  id: string;
  framework: string;
  required: boolean;
  satisfied_by: EvidenceSource[];
}

export interface EvidenceSource {
  type: string;
  connector?: string;
  max_age_days?: number;
}

export interface PolicyValidationResult {
  service: string;
  status: 'compliant' | 'drifted';
  controls: ControlResult[];
  drift_count: number;
  generated_at: string;
}

export interface ControlResult {
  control_id: string;
  framework: string;
  required: boolean;
  status: 'satisfied' | 'missing' | 'stale';
  evidence_age_days?: number;
  message: string;
}

export function parsePolicy(yamlContent: string): GrcPolicy {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const yaml = require('js-yaml');
  const raw = yaml.load(yamlContent) as any;
  if (!raw?.version || !raw?.service || !Array.isArray(raw?.controls)) {
    throw new Error('Invalid .grc-policy.yaml: missing version, service, or controls');
  }
  return raw as GrcPolicy;
}

export function validatePolicy(
  policy: GrcPolicy,
  evidenceRecords: Array<{ control_id: string; framework: string; collected_at: string; evidence_type: string }>
): PolicyValidationResult {
  const now = new Date();
  const results: ControlResult[] = [];

  for (const ctrl of policy.controls) {
    let satisfied = false;
    let stale = false;
    let evidenceAgeDays: number | undefined;

    for (const source of (ctrl.satisfied_by || [])) {
      const match = evidenceRecords.find(e =>
        e.control_id === ctrl.id &&
        e.framework === ctrl.framework &&
        e.evidence_type === source.type
      );
      if (match) {
        const age = Math.floor((now.getTime() - new Date(match.collected_at).getTime()) / 86400000);
        evidenceAgeDays = age;
        if (age <= (source.max_age_days ?? 90)) { satisfied = true; break; }
        else stale = true;
      }
    }

    results.push({
      control_id: ctrl.id,
      framework: ctrl.framework,
      required: ctrl.required,
      status: satisfied ? 'satisfied' : stale ? 'stale' : 'missing',
      evidence_age_days: evidenceAgeDays,
      message: satisfied
        ? `${ctrl.id} satisfied`
        : stale
          ? `Evidence for ${ctrl.id} is stale (${evidenceAgeDays}d old)`
          : `No evidence found for ${ctrl.id}`
    });
  }

  const drift = results.filter(r => r.status !== 'satisfied' && r.required);
  return {
    service: policy.service,
    status: drift.length === 0 ? 'compliant' : 'drifted',
    controls: results,
    drift_count: drift.length,
    generated_at: now.toISOString()
  };
}

export function generatePolicyTemplate(serviceName: string): string {
  return `# .grc-policy.yaml
version: '1'
service: ${serviceName}
frameworks: ['SOC2']
data_classification: internal

controls:
  - id: CC6.1
    framework: SOC2
    required: true
    satisfied_by:
      - type: mfa_enabled
        max_age_days: 7
  - id: CC8.1
    framework: SOC2
    required: true
    satisfied_by:
      - type: github_branch_protection
        max_age_days: 30
`;
}
