import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { NemotronComplianceEngine } from './nemotron-compliance.js';
import { assessRiskTier, assessEuAiAct, getEuAiActGaps } from './eu-ai-act.js';
import { assessNistRmf, getNistGaps } from './nist-ai-rmf.js';
import { assessIso42001 } from './iso-42001.js';
import { generateAiBom, validateBomIntegrity, getBomSummary } from './ai-bom.js';
import type { NemotronModel, NemotronDeploymentConfig } from './types.js';

const NEMOTRON_8B: NemotronModel = {
  id: 'nemotron-mini-8b',
  name: 'Nemotron Mini',
  version: '1.0.0',
  parameters: 8_000_000_000,
  capabilities: ['text-generation', 'multilingual'],
  license: 'NVIDIA Open Model License',
  trainingDataSources: ['common-crawl', 'wikipedia', 'arxiv', 'books'],
  architecture: 'Transformer Decoder',
  contextWindow: 4096,
  modality: 'text',
};

const NEMOTRON_70B: NemotronModel = {
  id: 'nemotron-70b',
  name: 'Nemotron 70B',
  version: '2.0.0',
  parameters: 70_000_000_000,
  capabilities: [
    'text-generation',
    'chatbot',
    'code-generation',
    'content-generation',
    'multilingual',
  ],
  license: 'NVIDIA Open Model License',
  trainingDataSources: ['common-crawl', 'wikipedia', 'arxiv', 'books', 'code', 'stackoverflow'],
  architecture: 'Transformer Decoder',
  contextWindow: 16384,
  modality: 'text',
};

const UNACCEPTABLE_MODEL: NemotronModel = {
  ...NEMOTRON_8B,
  id: 'bad-model',
  name: 'Bad Model',
  capabilities: ['social-scoring', 'real-time-biometric-identification'],
};

const DEPLOYMENT_CONFIG: NemotronDeploymentConfig = {
  model: NEMOTRON_8B,
  hardware: {
    gpus: 4,
    gpuMemory: 80,
    precision: 'fp16',
    quantization: false,
    tensorParallelism: 2,
  },
  network: {
    exposed: true,
    tlsVersion: '1.3',
    rateLimiting: true,
    maxRequestsPerMinute: 60,
    allowedOrigins: ['https://app.example.com'],
  },
  security: {
    authRequired: true,
    authMethod: 'oauth2',
    inputValidation: true,
    outputFiltering: true,
    loggingEnabled: true,
    auditTrail: true,
    dataEncryption: 'both',
    accessControl: 'rbac',
  },
  environment: 'production',
};

describe('Risk Tier Assessment', () => {
  it('classifies minimal risk for standard text models', () => {
    assert.equal(assessRiskTier(NEMOTRON_8B), 'minimal');
  });

  it('classifies unacceptable risk for social scoring models', () => {
    assert.equal(assessRiskTier(UNACCEPTABLE_MODEL), 'unacceptable');
  });

  it('classifies limited risk for chatbot models', () => {
    const model: NemotronModel = { ...NEMOTRON_8B, capabilities: ['chatbot'] };
    assert.equal(assessRiskTier(model), 'limited');
  });

  it('classifies high risk for employment decision models', () => {
    const model: NemotronModel = {
      ...NEMOTRON_8B,
      capabilities: ['employment-decision-making', 'text-generation'],
    };
    assert.equal(assessRiskTier(model), 'high');
  });
});

describe('EU AI Act Assessment', () => {
  it('generates valid EU AI Act assessment', () => {
    const assessment = assessEuAiAct(NEMOTRON_8B);
    assert.ok(assessment.riskTier);
    assert.ok(Array.isArray(assessment.articles));
    assert.ok(assessment.articles.length > 0);
    assert.ok(assessment.conformityAssessment);
    assert.ok(Array.isArray(assessment.transparencyObligations));
  });

  it('identifies gaps for models without limitations documented', () => {
    const assessment = assessEuAiAct(NEMOTRON_8B);
    const gaps = getEuAiActGaps(assessment);
    assert.ok(Array.isArray(gaps));
  });

  it('checks transparency for multimodal models', () => {
    const multimodal: NemotronModel = {
      ...NEMOTRON_8B,
      modality: 'multimodal',
    };
    const assessment = assessEuAiAct(multimodal);
    const deepfakeObligation = assessment.transparencyObligations.find((t) =>
      t.obligation.toLowerCase().includes('deepfake')
    );
    assert.ok(deepfakeObligation);
    assert.equal(deepfakeObligation.met, false);
  });
});

describe('NIST AI RMF Assessment', () => {
  it('assesses all four NIST functions', () => {
    const assessment = assessNistRmf(NEMOTRON_8B);
    assert.equal(assessment.functions.length, 4);
    const functionNames = assessment.functions.map((f) => f.function);
    assert.deepEqual(functionNames, ['GOVERN', 'MAP', 'MEASURE', 'MANAGE']);
  });

  it('produces overall score between 0 and 100', () => {
    const assessment = assessNistRmf(NEMOTRON_8B);
    assert.ok(assessment.overallScore >= 0);
    assert.ok(assessment.overallScore <= 100);
  });

  it('identifies gaps', () => {
    const assessment = assessNistRmf(NEMOTRON_8B);
    const gaps = getNistGaps(assessment);
    assert.ok(Array.isArray(gaps));
  });

  it('includes accountability checks', () => {
    const assessment = assessNistRmf(NEMOTRON_8B);
    assert.ok(assessment.accountabilityChecks.length > 0);
  });
});

describe('ISO 42001 Assessment', () => {
  it('generates Annex A controls', () => {
    const assessment = assessIso42001(NEMOTRON_8B);
    assert.ok(assessment.controls.length > 0);
    assert.ok(assessment.controls[0].id.startsWith('A.'));
  });

  it('scores correctly based on model properties', () => {
    const assessment = assessIso42001(NEMOTRON_8B);
    assert.ok(assessment.overallScore >= 0);
    assert.ok(assessment.overallScore <= 100);
  });

  it('generates gaps for partial controls', () => {
    const assessment = assessIso42001(NEMOTRON_8B);
    assert.ok(Array.isArray(assessment.gaps));
    assert.ok(Array.isArray(assessment.recommendations));
  });
});

describe('AI BOM Generation', () => {
  it('generates a valid AI BOM', () => {
    const bom = generateAiBom(NEMOTRON_8B);
    assert.equal(bom.modelId, NEMOTRON_8B.id);
    assert.equal(bom.modelName, NEMOTRON_8B.name);
    assert.equal(bom.version, NEMOTRON_8B.version);
    assert.ok(bom.trainingData.length > 0);
    assert.ok(bom.vulnerabilities.length > 0);
    assert.ok(bom.sbomHash);
    assert.ok(bom.generatedAt);
  });

  it('validates BOM integrity', () => {
    const bom = generateAiBom(NEMOTRON_8B);
    assert.ok(validateBomIntegrity(bom));
  });

  it('provides correct BOM summary', () => {
    const bom = generateAiBom(NEMOTRON_8B);
    const summary = getBomSummary(bom);
    assert.ok(summary.totalVulnerabilities > 0);
    assert.equal(typeof summary.criticalVulns, 'number');
    assert.equal(typeof summary.piiSources, 'number');
  });

  it('tracks PII in training data', () => {
    const socialModel: NemotronModel = {
      ...NEMOTRON_8B,
      trainingDataSources: ['social-media'],
    };
    const bom = generateAiBom(socialModel);
    const summary = getBomSummary(bom);
    assert.ok(summary.piiSources > 0);
  });

  it('adds vulnerability for code-capable models', () => {
    const bom = generateAiBom(NEMOTRON_70B);
    const codeVuln = bom.vulnerabilities.find((v) => v.id === 'NEM-VULN-007');
    assert.ok(codeVuln);
  });

  it('adds vulnerability for very large models', () => {
    const bom = generateAiBom(NEMOTRON_70B);
    const largeVuln = bom.vulnerabilities.find((v) => v.id === 'NEM-VULN-006');
    assert.ok(largeVuln);
  });
});

describe('NemotronComplianceEngine', () => {
  it('assesses compliance across multiple frameworks', () => {
    const engine = new NemotronComplianceEngine();
    const assessments = engine.assessModelCompliance(NEMOTRON_8B, [
      'EU_AI_ACT',
      'NIST_AI_RMF',
      'ISO_42001',
    ]);
    assert.equal(assessments.length, 3);
    const frameworks = assessments.map((a) => a.framework);
    assert.deepEqual(frameworks, ['EU_AI_ACT', 'NIST_AI_RMF', 'ISO_42001']);
  });

  it('validates deployment configuration', () => {
    const engine = new NemotronComplianceEngine();
    const result = engine.assessDeployment(DEPLOYMENT_CONFIG);
    assert.equal(typeof result.compliant, 'boolean');
    assert.ok(typeof result.score === 'number');
    assert.ok(Array.isArray(result.issues));
    assert.ok(Array.isArray(result.recommendations));
  });

  it('flags missing authentication', () => {
    const engine = new NemotronComplianceEngine();
    const config: NemotronDeploymentConfig = {
      ...DEPLOYMENT_CONFIG,
      security: { ...DEPLOYMENT_CONFIG.security, authRequired: false },
    };
    const result = engine.assessDeployment(config);
    assert.equal(result.compliant, false);
    assert.ok(result.issues.some((i) => i.includes('Authentication')));
  });

  it('generates full compliance report', () => {
    const engine = new NemotronComplianceEngine();
    const report = engine.generateComplianceReport(NEMOTRON_8B, DEPLOYMENT_CONFIG);
    assert.ok(report.reportId);
    assert.equal(report.model.id, NEMOTRON_8B.id);
    assert.equal(report.assessments.length, 3);
    assert.ok(report.aiBom);
    assert.ok(typeof report.riskScore === 'number');
    assert.ok(report.riskTier);
    assert.ok(report.recommendations.length > 0);
    assert.ok(report.generatedAt);
  });

  it('maps model to EU AI Act controls', () => {
    const engine = new NemotronComplianceEngine();
    const controls = engine.mapToControls(NEMOTRON_8B, 'EU_AI_ACT');
    assert.ok(controls.length > 0);
    assert.ok(controls[0].controlId.startsWith('Art.'));
  });

  it('maps model to NIST controls', () => {
    const engine = new NemotronComplianceEngine();
    const controls = engine.mapToControls(NEMOTRON_8B, 'NIST_AI_RMF');
    assert.ok(controls.length > 0);
    assert.ok(controls[0].controlId.startsWith('GOVERN') || controls[0].controlId.startsWith('MAP'));
  });

  it('maps model to ISO controls', () => {
    const engine = new NemotronComplianceEngine();
    const controls = engine.mapToControls(NEMOTRON_8B, 'ISO_42001');
    assert.ok(controls.length > 0);
    assert.ok(controls[0].controlId.startsWith('A.'));
  });

  it('generates lower risk score for 70B model with minimal security', () => {
    const engine = new NemotronComplianceEngine();
    const insecureConfig: NemotronDeploymentConfig = {
      ...DEPLOYMENT_CONFIG,
      security: {
        authRequired: false,
        authMethod: 'api_key',
        inputValidation: false,
        outputFiltering: false,
        loggingEnabled: false,
        auditTrail: false,
        dataEncryption: 'at-rest',
        accessControl: 'acl',
      },
    };
    const report = engine.generateComplianceReport(NEMOTRON_70B, insecureConfig);
    assert.ok(report.riskScore < 80);
  });

  it('identifies critical risk for unacceptable models', () => {
    const engine = new NemotronComplianceEngine();
    const report = engine.generateComplianceReport(UNACCEPTABLE_MODEL, DEPLOYMENT_CONFIG);
    assert.equal(report.riskTier, 'unacceptable');
    assert.ok(report.riskScore < 50);
  });
});
