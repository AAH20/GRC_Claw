import { describe, it, expect } from 'vitest';
import {
  assessInfraAgentSystem,
  createSampleInfraAgentAssuranceEnvelope,
  INFRA_AGENT_DEFAULT_CONTROLS,
  INFRA_AGENT_CONTROL_MAPPINGS,
  type InfraAgentSystemInput,
} from './index';

describe('assessInfraAgentSystem', () => {
  const minimalInput: InfraAgentSystemInput = {
    systemId: 'test-001',
    title: 'Test infra agent',
    source: 'devops_autopilot',
    scope: 'unit test',
  };

  it('flags a minimal, undocumented agent as blocked with required actions', () => {
    const envelope = assessInfraAgentSystem(minimalInput);
    expect(envelope.deploymentReadiness).toBe('blocked');
    expect(envelope.requiredActions.length).toBeGreaterThan(0);
    expect(envelope.riskScore).toBeGreaterThan(30);
  });

  it('flags plaintext credential handling as a required action and higher risk than secret substitution', () => {
    const baseline: Partial<InfraAgentSystemInput> = {
      model: { provider: 'open_weight', modelId: 'test-model', endpointMode: 'self_hosted', toolAllowlist: ['infra.apply_change'] },
      runtime: { humanApprovalGate: { present: true, mechanism: 'human-in-the-loop' } },
      evidenceHashes: ['sha256:abc123'],
      humanApproval: { required: true, approverRole: 'Infra owner' },
      limitations: ['test only'],
    };
    const plaintext = assessInfraAgentSystem({
      ...minimalInput,
      ...baseline,
      actionScope: { credentialHandling: 'plaintext_env', targetEnvironment: 'production', networkGuardrails: ['x'] },
    });
    const substituted = assessInfraAgentSystem({
      ...minimalInput,
      ...baseline,
      actionScope: { credentialHandling: 'secret_substitution', targetEnvironment: 'production', networkGuardrails: ['x'] },
    });
    expect(plaintext.riskScore).toBeGreaterThan(substituted.riskScore);
    expect(
      plaintext.requiredActions.some((a) => a.toLowerCase().includes('credential handling')),
    ).toBe(true);
  });

  it('produces a ready or low-risk envelope when full evidence and controls are documented', () => {
    const envelope = assessInfraAgentSystem({
      systemId: 'test-002',
      title: 'Fully documented infra agent',
      source: 'devops_autopilot',
      scope: 'unit test',
      model: {
        provider: 'open_weight',
        modelId: 'test-model',
        endpointMode: 'self_hosted',
        toolAllowlist: ['infra.apply_change'],
      },
      actionScope: {
        actionTiers: ['read', 'write'],
        targetEnvironment: 'staging',
        credentialHandling: 'secret_substitution',
        networkGuardrails: ['destructive-action-network-block'],
        destructiveActionsBlocked: true,
      },
      runtime: {
        humanApprovalGate: { present: true, mechanism: 'human-in-the-loop' },
      },
      evidenceHashes: ['sha256:abc123'],
      humanApproval: { required: true, approverRole: 'Infra owner' },
      limitations: ['test only'],
    });
    expect(envelope.requiredActions).toHaveLength(0);
    expect(envelope.deploymentReadiness).not.toBe('blocked');
  });

  it('maps every default control framework to a mapping entry', () => {
    for (const framework of INFRA_AGENT_DEFAULT_CONTROLS) {
      expect(INFRA_AGENT_CONTROL_MAPPINGS[framework]).toBeDefined();
      expect(INFRA_AGENT_CONTROL_MAPPINGS[framework].framework).toBe(framework);
    }
  });

  it('deduplicates evidence hashes', () => {
    const envelope = assessInfraAgentSystem({
      ...minimalInput,
      evidenceHashes: ['sha256:a', 'sha256:a', 'sha256:b'],
    });
    expect(envelope.evidenceHashes).toEqual(['sha256:a', 'sha256:b']);
  });

  it('the sample envelope is deterministic in shape and schema-tagged', () => {
    const sample = createSampleInfraAgentAssuranceEnvelope();
    expect(sample.schema).toBe('grc_claw.infra_agent_assurance.v1');
    expect(sample.assuranceType).toBe('infra_agent_devops_autonomy');
    expect(sample.a2zSocPayload.recommendedRoute).toBe('/infra-agent-assurance');
  });
});
