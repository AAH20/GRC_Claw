import { SixGComplianceEngine } from './sixg-compliance-engine';
import { ThreeGPPControls } from './threegpp-controls';
import { NetworkSecurityAssessment } from './network-security-assessment';
import { ORANCompliance } from './oran-compliance';
import {
  NetworkComponent,
  ComplianceFramework,
  ControlMapping
} from './types';

describe('6G Compliance Engine', () => {
  let engine: SixGComplianceEngine;

  beforeEach(() => {
    engine = new SixGComplianceEngine({
      enabled: true,
      intervalMinutes: 5,
      alertsEnabled: true,
      thresholdScore: 80,
      autoRemediate: false,
      notificationChannels: []
    });
  });

  describe('SixGComplianceEngine', () => {
    const mockComponent: NetworkComponent = {
      id: 'test-component-1',
      name: 'Test RAN Node',
      type: 'ran-node',
      vendor: 'TestVendor',
      version: '1.0.0',
      location: {
        region: 'us-east-1',
        zone: 'zone-a',
        site: 'site-1'
      },
      interfaces: [
        {
          id: 'iface-1',
          name: 'E2 Interface',
          type: 'e2',
          protocol: 'SCTP/TLS',
          encrypted: true
        },
        {
          id: 'iface-2',
          name: 'O1 Interface',
          type: 'o1',
          protocol: 'HTTPS',
          encrypted: true
        }
      ],
      metadata: {
        deploymentDate: '2024-01-01',
        lastUpdate: '2024-06-01',
        firmwareVersion: '2.1.0',
        certificationLevel: 'Level 3',
        owner: 'Network Operations',
        team: 'RAN Team'
      }
    };

    const mockCoreComponent: NetworkComponent = {
      id: 'test-component-2',
      name: 'Test Core Network',
      type: 'core-network',
      vendor: 'CoreVendor',
      version: '2.0.0',
      location: {
        region: 'us-east-1',
        zone: 'zone-b',
        site: 'core-site-1'
      },
      interfaces: [
        {
          id: 'iface-3',
          name: 'N2 Interface',
          type: 'n2',
          protocol: 'SCTP',
          encrypted: true
        },
        {
          id: 'iface-4',
          name: 'N3 Interface',
          type: 'n3',
          protocol: 'GTP-U',
          encrypted: false
        }
      ],
      metadata: {
        deploymentDate: '2024-01-15',
        lastUpdate: '2024-05-15',
        firmwareVersion: '3.0.0',
        certificationLevel: 'Level 4',
        owner: 'Core Network Team',
        team: 'Core Team'
      }
    };

    it('should create engine instance with default config', () => {
      const defaultEngine = new SixGComplianceEngine();
      expect(defaultEngine).toBeDefined();
    });

    it('should assess a single component', async () => {
      const assessment = await engine.assessComponent(
        mockComponent,
        ['3gpp-ts33501', 'nist-csf']
      );

      expect(assessment).toBeDefined();
      expect(assessment.component).toEqual(mockComponent);
      expect(assessment.score).toBeGreaterThanOrEqual(0);
      expect(assessment.score).toBeLessThanOrEqual(100);
      expect(assessment.controls).toBeInstanceOf(Array);
      expect(assessment.gaps).toBeInstanceOf(Array);
      expect(assessment.recommendations).toBeInstanceOf(Array);
    });

    it('should map component to 3GPP controls', async () => {
      const controls = await engine.mapToControls(
        mockComponent,
        '3gpp-ts33501'
      );

      expect(controls).toBeInstanceOf(Array);
      expect(controls.length).toBeGreaterThan(0);
      controls.forEach(control => {
        expect(control.framework).toBe('3gpp-ts33501');
        expect(control.controlId).toBeDefined();
        expect(control.status).toBeDefined();
      });
    });

    it('should map component to NIST controls', async () => {
      const controls = await engine.mapToControls(
        mockComponent,
        'nist-csf'
      );

      expect(controls).toBeInstanceOf(Array);
      expect(controls.length).toBeGreaterThan(0);
      controls.forEach(control => {
        expect(control.framework).toBe('nist-csf');
      });
    });

    it('should assess entire network', async () => {
      const report = await engine.assessNetwork(
        [mockComponent, mockCoreComponent],
        ['3gpp-ts33501', 'nist-csf']
      );

      expect(report).toBeDefined();
      expect(report.id).toBeDefined();
      expect(report.generatedAt).toBeDefined();
      expect(report.components).toHaveLength(2);
      expect(report.assessments).toHaveLength(2);
      expect(report.overallScore).toBeGreaterThanOrEqual(0);
      expect(report.overallScore).toBeLessThanOrEqual(100);
      expect(report.summary).toBeDefined();
    });

    it('should generate compliance report', async () => {
      const assessment1 = await engine.assessComponent(
        mockComponent,
        ['3gpp-ts33501']
      );
      const assessment2 = await engine.assessComponent(
        mockCoreComponent,
        ['3gpp-ts33501']
      );

      const report = await engine.generateReport([assessment1, assessment2]);

      expect(report).toBeDefined();
      expect(report.complianceByFramework).toBeDefined();
      expect(report.criticalGaps).toBeInstanceOf(Array);
      expect(report.recommendations).toBeInstanceOf(Array);
    });

    it('should perform continuous monitoring', async () => {
      const results = await engine.monitorContinuous([mockComponent]);

      expect(results).toBeInstanceOf(Array);
      expect(results.length).toBe(1);
      expect(results[0].componentId).toBe(mockComponent.id);
      expect(results[0].score).toBeGreaterThanOrEqual(0);
    });
  });

  describe('ThreeGPPControls', () => {
    let threeGPP: ThreeGPPControls;

    beforeEach(() => {
      threeGPP = new ThreeGPPControls();
    });

    const mockComponent: NetworkComponent = {
      id: 'test-3gpp',
      name: 'Test Component',
      type: 'core-network',
      vendor: 'Vendor',
      version: '1.0.0',
      location: { region: 'us-east-1', zone: 'zone-a' },
      interfaces: [
        {
          id: 'iface-1',
          name: 'N2',
          type: 'n2',
          protocol: 'SCTP',
          encrypted: true
        }
      ],
      metadata: { deploymentDate: '2024-01-01' }
    };

    it('should get 3GPP TS 33.501 controls', () => {
      const controls = threeGPP.getControlsForComponent(
        mockComponent,
        '3gpp-ts33501'
      );

      expect(controls).toBeInstanceOf(Array);
      expect(controls.length).toBeGreaterThan(0);
      controls.forEach(control => {
        expect(control.framework).toBe('3gpp-ts33501');
        expect(control.controlId).toMatch(/^33\.501/);
      });
    });

    it('should get 3GPP TS 33.210 controls', () => {
      const controls = threeGPP.getControlsForComponent(
        mockComponent,
        '3gpp-ts33210'
      );

      expect(controls).toBeInstanceOf(Array);
      controls.forEach(control => {
        expect(control.framework).toBe('3gpp-ts33210');
      });
    });

    it('should map 3GPP control to GRC control', () => {
      const grcId = threeGPP.mapToGRCControl('33.501-5.1.1');
      expect(grcId).toBe('GRC-AUTH-001');
    });

    it('should return GRC mapping', () => {
      const mapping = threeGPP.getGRCMapping();
      expect(mapping).toBeDefined();
      expect(mapping['GRC-AUTH-001']).toContain('33.501-5.1.1');
    });
  });

  describe('NetworkSecurityAssessment', () => {
    let assessment: NetworkSecurityAssessment;

    beforeEach(() => {
      assessment = new NetworkSecurityAssessment();
    });

    const mockComponent: NetworkComponent = {
      id: 'test-net-sec',
      name: 'Test Component',
      type: 'ran-node',
      vendor: 'Vendor',
      version: '1.0.0',
      location: { region: 'us-east-1', zone: 'zone-a' },
      interfaces: [
        {
          id: 'iface-1',
          name: 'E2',
          type: 'e2',
          protocol: 'SCTP/TLS',
          encrypted: true
        }
      ],
      metadata: {
        deploymentDate: '2024-01-01',
        lastUpdate: '2024-06-01'
      }
    };

    it('should assess component security', async () => {
      const controls = await assessment.assessComponentSecurity(
        mockComponent,
        '3gpp-ts33501'
      );

      expect(controls).toBeInstanceOf(Array);
      expect(controls.length).toBeGreaterThan(0);
    });

    it('should check firewall rules', async () => {
      const result = await assessment.checkFirewallRules(mockComponent);

      expect(result).toBeDefined();
      expect(result.componentId).toBe(mockComponent.id);
      expect(result.totalRules).toBeGreaterThan(0);
      expect(result.score).toBeGreaterThanOrEqual(0);
    });

    it('should verify encryption', async () => {
      const result = await assessment.verifyEncryption(mockComponent);

      expect(result).toBeDefined();
      expect(result.componentId).toBe(mockComponent.id);
      expect(result.totalInterfaces).toBeGreaterThan(0);
      expect(result.encryptedInterfaces).toBeGreaterThan(0);
    });

    it('should assess access controls', async () => {
      const result = await assessment.assessAccessControls(mockComponent);

      expect(result).toBeDefined();
      expect(result.componentId).toBe(mockComponent.id);
      expect(result.controls).toBeInstanceOf(Array);
      expect(result.controls.length).toBeGreaterThan(0);
    });

    it('should assess network segment', async () => {
      const result = await assessment.assessNetworkSegment([mockComponent]);

      expect(result).toBeDefined();
      expect(result.components).toHaveLength(1);
      expect(result.score).toBeGreaterThanOrEqual(0);
      expect(result.vulnerabilities).toBeInstanceOf(Array);
    });
  });

  describe('ORANCompliance', () => {
    let oran: ORANCompliance;

    beforeEach(() => {
      oran = new ORANCompliance();
    });

    const mockComponent: NetworkComponent = {
      id: 'test-oran',
      name: 'Test O-RAN Component',
      type: 'ran-node',
      vendor: 'ORANVendor',
      version: '1.0.0',
      location: { region: 'us-east-1', zone: 'zone-a' },
      interfaces: [
        {
          id: 'iface-1',
          name: 'E2',
          type: 'e2',
          protocol: 'SCTP/DTLS',
          encrypted: true
        },
        {
          id: 'iface-2',
          name: 'A1',
          type: 'a1',
          protocol: 'HTTPS',
          encrypted: true
        }
      ],
      metadata: { deploymentDate: '2024-01-01' }
    };

    it('should get O-RAN SDS controls', () => {
      const controls = oran.getControlsForComponent(
        mockComponent,
        'oran-sds'
      );

      expect(controls).toBeInstanceOf(Array);
      expect(controls.length).toBeGreaterThan(0);
      controls.forEach(control => {
        expect(control.framework).toBe('oran-sds');
      });
    });

    it('should get O-RAN security controls', () => {
      const controls = oran.getControlsForComponent(
        mockComponent,
        'oran-security'
      );

      expect(controls).toBeInstanceOf(Array);
      expect(controls.length).toBeGreaterThan(0);
      controls.forEach(control => {
        expect(control.framework).toBe('oran-security');
      });
    });

    it('should validate O-RAN interfaces', async () => {
      const result = await oran.validateORANInterfaces(mockComponent);

      expect(result).toBeDefined();
      expect(result.componentId).toBe(mockComponent.id);
      expect(result.validations).toBeInstanceOf(Array);
      expect(result.validations.length).toBeGreaterThan(0);
      expect(result.score).toBeGreaterThanOrEqual(0);
    });

    it('should validate OTS test cases', async () => {
      const result = await oran.validateOTSTestCases(mockComponent);

      expect(result).toBeDefined();
      expect(result.componentId).toBe(mockComponent.id);
      expect(result.totalTests).toBeGreaterThan(0);
      expect(result.passed).toBeGreaterThanOrEqual(0);
    });
  });

  describe('Integration Tests', () => {
    it('should perform full compliance workflow', async () => {
      const engine = new SixGComplianceEngine();

      const components: NetworkComponent[] = [
        {
          id: 'ran-1',
          name: 'RAN Node 1',
          type: 'ran-node',
          vendor: 'Vendor1',
          version: '2.0.0',
          location: { region: 'us-east-1', zone: 'zone-a' },
          interfaces: [
            {
              id: 'e2-1',
              name: 'E2',
              type: 'e2',
              protocol: 'SCTP/DTLS',
              encrypted: true
            }
          ],
          metadata: { deploymentDate: '2024-01-01' }
        },
        {
          id: 'core-1',
          name: 'Core Network 1',
          type: 'core-network',
          vendor: 'Vendor2',
          version: '3.0.0',
          location: { region: 'us-east-1', zone: 'zone-b' },
          interfaces: [
            {
              id: 'n2-1',
              name: 'N2',
              type: 'n2',
              protocol: 'SCTP',
              encrypted: true
            }
          ],
          metadata: { deploymentDate: '2024-01-15' }
        }
      ];

      const frameworks: ComplianceFramework[] = [
        '3gpp-ts33501',
        'oran-security',
        'nist-csf'
      ];

      const report = await engine.assessNetwork(components, frameworks);

      expect(report).toBeDefined();
      expect(report.components).toHaveLength(2);
      expect(report.overallScore).toBeGreaterThanOrEqual(0);
      expect(report.overallScore).toBeLessThanOrEqual(100);
      expect(report.complianceByFramework).toBeDefined();
      expect(report.summary.totalComponents).toBe(2);
    });

    it('should handle continuous monitoring workflow', async () => {
      const engine = new SixGComplianceEngine({
        enabled: true,
        intervalMinutes: 1,
        alertsEnabled: true,
        thresholdScore: 90,
        autoRemediate: false,
        notificationChannels: []
      });

      const components: NetworkComponent[] = [
        {
          id: 'monitor-1',
          name: 'Monitored Component',
          type: 'edge-compute',
          vendor: 'Vendor',
          version: '1.5.0',
          location: { region: 'us-east-1', zone: 'zone-c' },
          interfaces: [
            {
              id: 'o1-1',
              name: 'O1',
              type: 'o1',
              protocol: 'HTTPS',
              encrypted: true
            }
          ],
          metadata: { deploymentDate: '2024-02-01' }
        }
      ];

      const results = await engine.monitorContinuous(components);

      expect(results).toBeInstanceOf(Array);
      expect(results.length).toBe(1);
      expect(results[0].timestamp).toBeDefined();
    });
  });
});
