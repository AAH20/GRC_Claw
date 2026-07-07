import assert from 'node:assert/strict';

const { assessAiRanExperiment, createSampleAiRanAssuranceEnvelope } = await import('../packages/ai-ran-assurance/dist/index.js');

const sample = createSampleAiRanAssuranceEnvelope();
assert.equal(sample.schema, 'grc_claw.ai_ran_assurance.v1');
assert.equal(sample.assuranceType, 'ai_ran_6g');
assert.equal(sample.deploymentReadiness, 'conditional');
assert.ok(sample.controlMappings.some((mapping) => mapping.framework === 'iso_42001'));
assert.ok(sample.a2zSocPayload.recommendedRoute === '/ai-ran-6g-assurance');
assert.ok(sample.safetyBoundary.some((boundary) => boundary.includes('Assurance-only')));

const blocked = assessAiRanExperiment({
  experimentId: 'unsafe-incomplete-upload',
  title: 'Incomplete operator upload',
  source: 'operator_upload',
  scope: 'No evidence or approval attached.',
});

assert.equal(blocked.deploymentReadiness, 'blocked');
assert.ok(blocked.requiredActions.length >= 4);
assert.ok(blocked.riskScore >= 70);

console.log('test:ai-ran-assurance OK');
