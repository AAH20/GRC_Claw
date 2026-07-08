import { describe, it, expect, beforeEach } from 'vitest';
import { Gr00tComplianceEngine } from './gr00t-compliance-engine';
import { checkItarCompliance, generateItarComplianceReport, classifyItarCategory } from './itar-compliance';
import { assessDodCompliance, mapGr00tToDodControls, getCmmcLevels } from './dod-compliance';
import { assessCjadc2Compliance, getCjadc2Requirements } from './cjadc2-framework';
import { assessAutonomousWeaponsCompliance, getAutonomyLevels, getLethalRestrictions } from './autonomous-weapons-policy';
import type { Gr00tModel, DeploymentConfig, MilitaryOperation, Cjadc2Component } from './types';

const createTestModel = (overrides: Partial<Gr00tModel> = {}): Gr00tModel => ({
  id: 'gr00t-n1',
  name: 'NVIDIA Isaac GR00T N1',
  version: '1.0.0',
  parameters: 7_000_000_000,
  embodimentTag: 'HUMANOID',
  capabilities: ['navigation', 'manipulation', 'human-in-the-loop'],
  exportClassification: 'UNCLASSIFIED',
  trainingDataOrigin: 'US',
  weights: {
    precision: 'FP32',
    sizeBytes: 28_000_000_000,
    sha256: 'abc123def456',
  },
  ...overrides,
});

const createTestConfig = (model: Gr00tModel): DeploymentConfig => ({
  model,
  robot: {
    id: 'robot-001',
    name: 'Test Robot',
    type: 'HUMANOID',
    embodiment: 'HUMANOID',
    location: 'US',
    network: {
      isolated: true,
      vpnRequired: true,
      encryptionStandard: 'AES-256',
      classification: 'UNCLASSIFIED',
    },
    operators: ['operator-1'],
    authorizedCountries: ['US', 'CA', 'GB'],
  },
  network: {
    type: 'isolated',
    classification: 'UNCLASSIFIED',
    encryption: 'AES-256',
    monitoring: true,
    intrusionDetection: true,
  },
  security: {
    accessControl: 'RBAC',
    auditLogging: true,
    keyManagement: 'FIPS-140-2',
    patchManagement: 'automated',
    incidentResponse: true,
  },
  classification: 'UNCLASSIFIED',
});

const createTestOperation = (): MilitaryOperation => ({
  id: 'op-001',
  name: 'Training Exercise',
  type: 'training',
  domain: 'LAND',
  classification: 'UNCLASSIFIED',
  permittedEmbodiments: ['HUMANOID'],
  humanOversightRequired: true,
  engagementAuthority: 'Defensive',
  rulesOfEngagement: 'Standard ROE',
});

describe('Gr00tComplianceEngine', () => {
  let engine: Gr00tComplianceEngine;

  beforeEach(() => {
    engine = new Gr00tComplianceEngine();
  });

  describe('assessModelCompliance', () => {
    it('should assess ITAR compliance for US-deployed model', () => {
      const model = createTestModel({ exportClassification: 'UNCLASSIFIED' });
      const config = createTestConfig(model);

      const results = engine.assessModelCompliance(model, ['ITAR'], config);

      expect(results).toHaveLength(1);
      expect(results[0].framework).toBe('ITAR');
      expect(results[0].assessment.overallScore).toBe(100);
      expect(results[0].assessment.status).toBe('PASS');
    });

    it('should fail ITAR compliance for restricted country deployment', () => {
      const model = createTestModel({ exportClassification: 'UNCLASSIFIED' });
      const config = createTestConfig(model);
      config.robot.authorizedCountries = ['US', 'CN'];

      const results = engine.assessModelCompliance(model, ['ITAR'], config);

      expect(results).toHaveLength(1);
      expect(results[0].framework).toBe('ITAR');
      expect(results[0].assessment.status).toBe('FAIL');
    });

    it('should assess DoD compliance', () => {
      const model = createTestModel();
      const config = createTestConfig(model);

      const results = engine.assessModelCompliance(model, ['DOD_5200_21'], config);

      expect(results).toHaveLength(1);
      expect(results[0].framework).toBe('DOD_5200_21');
      expect(results[0].assessment.overallScore).toBeGreaterThan(0);
    });

    it('should assess multiple frameworks', () => {
      const model = createTestModel();
      const config = createTestConfig(model);

      const results = engine.assessModelCompliance(model, ['ITAR', 'DOD_5200_21', 'NIST_800_171'], config);

      expect(results).toHaveLength(3);
      const frameworks = results.map(r => r.framework);
      expect(frameworks).toContain('ITAR');
      expect(frameworks).toContain('DOD_5200_21');
      expect(frameworks).toContain('NIST_800_171');
    });
  });

  describe('assessRobotDeployment', () => {
    it('should assess full deployment compliance', () => {
      const model = createTestModel();
      const config = createTestConfig(model);

      const result = engine.assessRobotDeployment(config);

      expect(result.compliance).toBeDefined();
      expect(result.overallStatus).toBeDefined();
      expect(result.overallScore).toBeGreaterThanOrEqual(0);
      expect(result.overallScore).toBeLessThanOrEqual(100);
    });

    it('should include CJADC2 for SECRET classification', () => {
      const model = createTestModel();
      const config = createTestConfig(model);
      config.classification = 'SECRET';

      const result = engine.assessRobotDeployment(config);

      expect(result.compliance.length).toBeGreaterThanOrEqual(4);
    });
  });

  describe('generateComplianceReport', () => {
    it('should generate a full compliance report', () => {
      const model = createTestModel();
      const config = createTestConfig(model);
      const operation = createTestOperation();

      const report = engine.generateComplianceReport(model, config, operation);

      expect(report.id).toBeDefined();
      expect(report.timestamp).toBeDefined();
      expect(report.modelId).toBe(model.id);
      expect(report.robotId).toBe(config.robot.id);
      expect(report.overallStatus).toBeDefined();
      expect(report.overallScore).toBeGreaterThanOrEqual(0);
      expect(report.frameworkResults).toBeDefined();
      expect(report.summary).toBeDefined();
      expect(report.exportControlStatus).toBeDefined();
      expect(report.deploymentRecommendation).toBeDefined();
    });

    it('should store generated reports', () => {
      const model = createTestModel();
      const config = createTestConfig(model);

      const report = engine.generateComplianceReport(model, config);
      const retrieved = engine.getReport(report.id);

      expect(retrieved).toBeDefined();
      expect(retrieved?.id).toBe(report.id);
    });
  });

  describe('mapToMilitaryControls', () => {
    it('should map to military controls', () => {
      const model = createTestModel();

      const result = engine.mapToMilitaryControls(model, 'DOD_5200_21');

      expect(result.dodControls).toBeDefined();
      expect(result.itarControls).toBeDefined();
      expect(result.cjadc2Controls).toBeDefined();
      expect(result.weaponPolicy).toBeDefined();
    });
  });
});

describe('ITAR Compliance', () => {
  it('should classify GR00T model ITAR category', () => {
    const model = createTestModel({ exportClassification: 'SECRET' });
    const category = classifyItarCategory(model);

    expect(category.category).toBeDefined();
    expect(category.licenseRequired).toBe(true);
  });

  it('should check ITAR compliance for US deployment', () => {
    const model = createTestModel({ exportClassification: 'UNCLASSIFIED', embodimentTag: 'INDUSTRIAL' });
    const result = checkItarCompliance(model, ['US']);

    expect(result.compliant).toBe(true);
    expect(result.findings).toHaveLength(0);
  });

  it('should fail ITAR for restricted countries', () => {
    const model = createTestModel();
    const result = checkItarCompliance(model, ['US', 'CN']);

    expect(result.compliant).toBe(false);
    expect(result.findings.length).toBeGreaterThan(0);
  });

  it('should generate ITAR compliance report with hash', () => {
    const model = createTestModel();
    const report = generateItarComplianceReport(model, ['US']);

    expect(report.result).toBeDefined();
    expect(report.gaps).toBeDefined();
    expect(report.recommendations).toBeDefined();
    expect(report.complianceHash).toBeDefined();
    expect(report.complianceHash).toHaveLength(64);
  });
});

describe('DoD Compliance', () => {
  it('should assess DoD compliance with full config', () => {
    const model = createTestModel();
    const config = createTestConfig(model);

    const result = assessDodCompliance(model, config);

    expect(result.framework).toBe('NIST 800-171 / DoD 5200.21');
    expect(result.controlsAssessed).toBeGreaterThan(0);
    expect(result.controlsPassed).toBeGreaterThanOrEqual(0);
    expect(result.cmmcLevel).toBeGreaterThanOrEqual(0);
    expect(result.cmmcLevel).toBeLessThanOrEqual(3);
  });

  it('should map GR00T controls to DoD requirements', () => {
    const model = createTestModel();
    const config = createTestConfig(model);

    const result = mapGr00tToDodControls(model, config);

    expect(result.gaps).toBeDefined();
    expect(result.recommendations).toBeDefined();
    expect(Array.isArray(result.gaps)).toBe(true);
  });

  it('should return CMMC levels', () => {
    const levels = getCmmcLevels();

    expect(levels[1]).toBeDefined();
    expect(levels[2]).toBeDefined();
    expect(levels[3]).toBeDefined();
    expect(levels[1].controls).toBe(17);
  });
});

describe('CJADC2 Framework', () => {
  it('should assess CJADC2 compliance with components', () => {
    const model = createTestModel();
    const components: Cjadc2Component[] = [
      {
        id: 'sensor-001',
        name: 'Multi-Sensor Array',
        type: 'sensor',
        domain: 'SENSE',
        securityLevel: 'CONFIDENTIAL',
        interoperabilityStandard: 'STANAG_4586',
        protocols: ['STANAG_4586', 'STANAG_4607'],
        dataFormats: ['NITF', 'GeoTIFF'],
      },
      {
        id: 'comms-001',
        name: 'Tactical Comms',
        type: 'communications',
        domain: 'COMMUNICATE',
        securityLevel: 'SECRET',
        interoperabilityStandard: 'STANAG_4406',
        protocols: ['STANAG_4406', 'Link-16'],
        dataFormats: ['VMF', 'J-Series'],
      },
    ];

    const result = assessCjadc2Compliance(model, components);

    expect(result.readiness).toBeDefined();
    expect(result.readiness.score).toBeGreaterThanOrEqual(0);
    expect(result.readiness.score).toBeLessThanOrEqual(100);
    expect(result.gaps).toBeDefined();
    expect(result.recommendations).toBeDefined();
  });

  it('should return CJADC2 requirements', () => {
    const requirements = getCjadc2Requirements();

    expect(requirements.length).toBeGreaterThan(0);
    expect(requirements[0].id).toBeDefined();
    expect(requirements[0].domain).toBeDefined();
  });
});

describe('Autonomous Weapons Policy', () => {
  it('should assess compliance for non-lethal operation', () => {
    const model = createTestModel();
    const operation = createTestOperation();

    const result = assessAutonomousWeaponsCompliance(model, operation);

    expect(result.compliant).toBeDefined();
    expect(result.hitlCompliance).toBeDefined();
    expect(result.lethalAutonomy).toBeDefined();
    expect(result.gaps).toBeDefined();
    expect(result.recommendations).toBeDefined();
  });

  it('should return autonomy levels', () => {
    const levels = getAutonomyLevels();

    expect(levels).toHaveLength(5);
    expect(levels[0].name).toBe('Manual Control');
    expect(levels[4].lethalAuthority).toBe(true);
  });

  it('should return lethal restrictions', () => {
    const restrictions = getLethalRestrictions();

    expect(restrictions.length).toBeGreaterThan(0);
    expect(restrictions.some(r => r.includes('autonomous'))).toBe(true);
  });

  it('should fail HITL for model without oversight capability', () => {
    const model = createTestModel({ capabilities: ['navigation'] });
    const operation = createTestOperation();

    const result = assessAutonomousWeaponsCompliance(model, operation);

    expect(result.hitlCompliance.compliant).toBe(false);
  });
});

describe('Type Definitions', () => {
  it('should accept valid Gr00tModel', () => {
    const model: Gr00tModel = {
      id: 'test',
      name: 'Test Model',
      version: '1.0.0',
      parameters: 1_000_000,
      embodimentTag: 'HUMANOID',
      capabilities: ['navigation'],
      exportClassification: 'UNCLASSIFIED',
      trainingDataOrigin: 'US',
      weights: {
        precision: 'FP32',
        sizeBytes: 4_000_000,
        sha256: 'abc123',
      },
    };

    expect(model.id).toBe('test');
  });
});
