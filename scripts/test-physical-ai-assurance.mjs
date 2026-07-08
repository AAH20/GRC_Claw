import assert from 'node:assert/strict';

const { assessPhysicalAiSystem, createSamplePhysicalAiAssuranceEnvelope } = await import('../packages/physical-ai-assurance/dist/index.js');

const sample = createSamplePhysicalAiAssuranceEnvelope();
assert.equal(sample.schema, 'grc_claw.physical_ai_assurance.v1');
assert.equal(sample.assuranceType, 'physical_ai_humanoid_vla');
assert.equal(sample.deploymentReadiness, 'ready');
assert.ok(sample.controlMappings.some((mapping) => mapping.framework === 'iso_42001'));
assert.equal(sample.a2zSocPayload.recommendedRoute, '/physical-ai-humanoid-assurance');
assert.ok(sample.safetyBoundary.some((boundary) => boundary.includes('Assurance-only')));
assert.ok(sample.safetyBoundary.some((boundary) => boundary.includes('no robot motion plans')));
assert.ok(sample.embodiment.robotClass === 'humanoid');

const blocked = assessPhysicalAiSystem({
  systemId: 'unsafe-incomplete-robotics-upload',
  title: 'Incomplete humanoid robotics upload',
  source: 'operator_upload',
  scope: 'No evidence, approval, action boundary, network boundary, limitations, or emergency stop attached.',
  embodiment: {
    robotClass: 'humanoid',
    autonomyMode: 'bounded_autonomy',
    operatingDomain: 'critical_infrastructure',
  },
});

assert.equal(blocked.deploymentReadiness, 'blocked');
assert.ok(blocked.requiredActions.length >= 5);
assert.ok(blocked.riskScore >= 70);
assert.ok(!blocked.safetyBoundary.join(' ').includes('target coordinates'));

console.log('test:physical-ai-assurance OK');
