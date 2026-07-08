import { describe, it, expect, beforeEach } from 'vitest';
import { Cjadc2Engine } from './cjadc2-engine';
import {
  Cjadc2Domain,
  Cjadc2Component,
  Cjadc2Operation,
  ComponentType,
  ComponentStatus,
  SecurityClassification,
  InteroperabilityStandard,
  SecurityControl,
  SecurityLevel,
  OperationStatus
} from './types';

describe('Cjadc2Engine', () => {
  let engine: Cjadc2Engine;

  beforeEach(() => {
    engine = new Cjadc2Engine();
  });

  const createTestComponent = (overrides: Partial<Cjadc2Component> = {}): Cjadc2Component => ({
    id: 'test-001',
    name: 'Test Sensor',
    type: ComponentType.SENSOR,
    domain: [Cjadc2Domain.SENSE],
    classification: SecurityClassification.SECRET,
    status: ComponentStatus.OPERATIONAL,
    capabilities: ['radar', 'real_time_processing'],
    interoperability: [
      {
        protocol: 'TCP/IP',
        standard: InteroperabilityStandard.LINK_16,
        version: '1.0',
        required: true
      }
    ],
    security: [
      {
        control: SecurityControl.ENCRYPTION,
        level: SecurityLevel.HIGH,
        status: 'met'
      },
      {
        control: SecurityControl.AUTHENTICATION,
        level: SecurityLevel.HIGH,
        status: 'met'
      }
    ],
    ...overrides
  });

  describe('assessDomain', () => {
    it('should assess SENSE domain', () => {
      const components = [
        createTestComponent({ id: 'sensor-1', type: ComponentType.SENSOR, capabilities: ['radar', 'real_time_processing', 'threat_detection'] }),
        createTestComponent({ id: 'sensor-2', type: ComponentType.SENSOR, capabilities: ['fusion', 'data_correlation'] }),
        createTestComponent({ id: 'dl-1', type: ComponentType.DATA_LINK, capabilities: ['data_sharing', 'multi_link'] })
      ];

      const assessment = engine.assessDomain(Cjadc2Domain.SENSE, components);

      expect(assessment).toBeDefined();
      expect(assessment.domain).toBe(Cjadc2Domain.SENSE);
      expect(assessment.score).toBeGreaterThanOrEqual(0);
      expect(assessment.score).toBeLessThanOrEqual(100);
      expect(assessment.maxScore).toBe(100);
      expect(['compliant', 'partial', 'non_compliant']).toContain(assessment.status);
    });

    it('should assess DECIDE domain', () => {
      const components = [
        createTestComponent({ id: 'cmd-1', type: ComponentType.COMMAND, capabilities: ['command_structure', 'situational_awareness'] }),
        createTestComponent({ id: 'ai-1', type: ComponentType.AI_SYSTEM, capabilities: ['explainability', 'bias_monitoring', 'override'] }),
        createTestComponent({ id: 'da-1', type: ComponentType.DECISION_AID, capabilities: ['human_approval', 'abort'] })
      ];

      const assessment = engine.assessDomain(Cjadc2Domain.DECIDE, components);

      expect(assessment).toBeDefined();
      expect(assessment.domain).toBe(Cjadc2Domain.DECIDE);
      expect(assessment.score).toBeGreaterThanOrEqual(0);
      expect(assessment.score).toBeLessThanOrEqual(100);
    });

    it('should assess ACT domain', () => {
      const components = [
        createTestComponent({ id: 'weapon-1', type: ComponentType.WEAPON, capabilities: ['engagement_authorization', 'positive_identification'] }),
        createTestComponent({ id: 'ai-1', type: ComponentType.AI_SYSTEM, capabilities: ['human_control', 'abort'] })
      ];

      const assessment = engine.assessDomain(Cjadc2Domain.ACT, components);

      expect(assessment).toBeDefined();
      expect(assessment.domain).toBe(Cjadc2Domain.ACT);
      expect(assessment.score).toBeGreaterThanOrEqual(0);
      expect(assessment.score).toBeLessThanOrEqual(100);
    });

    it('should assess COMMUNICATE domain', () => {
      const components = [
        createTestComponent({ id: 'net-1', type: ComponentType.NETWORK, capabilities: ['cross_domain', 'multi_link', 'aes256'] }),
        createTestComponent({ id: 'dl-1', type: ComponentType.DATA_LINK, capabilities: ['stanag_format', 'key_management'] })
      ];

      const assessment = engine.assessDomain(Cjadc2Domain.COMMUNICATE, components);

      expect(assessment).toBeDefined();
      expect(assessment.domain).toBe(Cjadc2Domain.COMMUNICATE);
      expect(assessment.score).toBeGreaterThanOrEqual(0);
      expect(assessment.score).toBeLessThanOrEqual(100);
    });

    it('should return empty assessment for unknown domain', () => {
      const assessment = engine.assessDomain(Cjadc2Domain.MOVE, []);

      expect(assessment.score).toBe(0);
      expect(assessment.status).toBe('non_compliant');
      expect(assessment.componentsAssessed).toBe(0);
    });
  });

  describe('assessInteroperability', () => {
    it('should assess interoperability with compliant components', () => {
      const components = [
        createTestComponent({
          id: 'net-1',
          type: ComponentType.NETWORK,
          interoperability: [
            { protocol: 'TCP/IP', standard: InteroperabilityStandard.LINK_16, version: '1.0', required: true },
            { protocol: 'UDP', standard: InteroperabilityStandard.LINK_22, version: '2.0', required: true }
          ]
        }),
        createTestComponent({
          id: 'net-2',
          type: ComponentType.NETWORK,
          interoperability: [
            { protocol: 'TCP/IP', standard: InteroperabilityStandard.LINK_16, version: '1.0', required: true }
          ]
        })
      ];

      const assessment = engine.assessInteroperability(components);

      expect(assessment).toBeDefined();
      expect(assessment.score).toBeGreaterThanOrEqual(0);
      expect(assessment.score).toBeLessThanOrEqual(100);
      expect(assessment.compliance).toBeDefined();
      expect(Array.isArray(assessment.compliance)).toBe(true);
    });

    it('should detect offline component issues', () => {
      const components = [
        createTestComponent({
          id: 'net-1',
          type: ComponentType.NETWORK,
          status: ComponentStatus.OFFLINE,
          interoperability: [
            { protocol: 'TCP/IP', standard: InteroperabilityStandard.LINK_16, version: '1.0', required: true }
          ]
        })
      ];

      const assessment = engine.assessInteroperability(components);

      expect(assessment.protocolIssues.length).toBeGreaterThan(0);
      expect(assessment.protocolIssues[0].severity).toBe('high');
    });
  });

  describe('assessSecurity', () => {
    it('should assess security with compliant components', () => {
      const components = [
        createTestComponent({
          security: [
            { control: SecurityControl.ENCRYPTION, level: SecurityLevel.HIGH, status: 'met' },
            { control: SecurityControl.AUTHENTICATION, level: SecurityLevel.HIGH, status: 'met' },
            { control: SecurityControl.ACCESS_CONTROL, level: SecurityLevel.MEDIUM, status: 'met' }
          ]
        })
      ];

      const assessment = engine.assessSecurity(components);

      expect(assessment).toBeDefined();
      expect(assessment.score).toBeGreaterThanOrEqual(0);
      expect(assessment.score).toBeLessThanOrEqual(100);
      expect(assessment.controlStatus).toBeDefined();
      expect(Array.isArray(assessment.controlStatus)).toBe(true);
    });

    it('should detect security vulnerabilities', () => {
      const components = [
        createTestComponent({
          security: [
            { control: SecurityControl.ENCRYPTION, level: SecurityLevel.CRITICAL, status: 'not_met' },
            { control: SecurityControl.AUTHENTICATION, level: SecurityLevel.HIGH, status: 'met' }
          ]
        })
      ];

      const assessment = engine.assessSecurity(components);

      expect(assessment.vulnerabilities.length).toBeGreaterThan(0);
      expect(assessment.vulnerabilities[0].severity).toBe('critical');
    });
  });

  describe('generateOperationReport', () => {
    it('should generate operation report', () => {
      const operation: Cjadc2Operation = {
        id: 'op-001',
        name: 'Test Operation',
        type: 'reconnaissance',
        domain: [Cjadc2Domain.SENSE, Cjadc2Domain.COMMUNICATE],
        components: ['sensor-1', 'net-1'],
        status: OperationStatus.ACTIVE,
        classification: SecurityClassification.SECRET,
        objectives: ['Gather intelligence', 'Share data']
      };

      const components = [
        createTestComponent({ id: 'sensor-1', type: ComponentType.SENSOR, capabilities: ['radar'] }),
        createTestComponent({ id: 'net-1', type: ComponentType.NETWORK, capabilities: ['cross_domain'] })
      ];

      const report = engine.generateOperationReport(operation, components);

      expect(report).toBeDefined();
      expect(report.operation).toBe(operation);
      expect(report.overallScore).toBeGreaterThanOrEqual(0);
      expect(report.overallScore).toBeLessThanOrEqual(100);
      expect(report.domainScores).toBeDefined();
      expect(Array.isArray(report.domainScores)).toBe(true);
      expect(report.interoperability).toBeDefined();
      expect(report.security).toBeDefined();
      expect(['critical', 'high', 'medium', 'low']).toContain(report.riskLevel);
      expect(['ready', 'conditionally_ready', 'not_ready']).toContain(report.readinessStatus);
      expect(report.summary).toBeDefined();
      expect(typeof report.summary).toBe('string');
    });
  });

  describe('mapToGr00t', () => {
    it('should map components to GR00T capabilities', () => {
      const components = [
        createTestComponent({ id: 'sensor-1', type: ComponentType.SENSOR, capabilities: ['radar'] }),
        createTestComponent({ id: 'ai-1', type: ComponentType.AI_SYSTEM, capabilities: ['explainability'] }),
        createTestComponent({ id: 'net-1', type: ComponentType.NETWORK, capabilities: ['cross_domain'] }),
        createTestComponent({ id: 'cmd-1', type: ComponentType.COMMAND, capabilities: ['command_structure'] })
      ];

      const assessment = engine.mapToGr00t(components);

      expect(assessment).toBeDefined();
      expect(assessment.mappings).toBeDefined();
      expect(Array.isArray(assessment.mappings)).toBe(true);
      expect(assessment.overallCoverage).toBeGreaterThanOrEqual(0);
      expect(assessment.overallCoverage).toBeLessThanOrEqual(100);
      expect(Array.isArray(assessment.capabilityGaps)).toBe(true);
      expect(Array.isArray(assessment.recommendations)).toBe(true);
    });

    it('should detect capability gaps', () => {
      const components = [
        createTestComponent({ id: 'sensor-1', type: ComponentType.SENSOR, capabilities: ['radar'] })
      ];

      const assessment = engine.mapToGr00t(components);

      expect(assessment.capabilityGaps.length).toBeGreaterThan(0);
      expect(assessment.recommendations.length).toBeGreaterThan(0);
    });
  });
});
