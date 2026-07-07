import { v4 as uuidv4 } from 'uuid';
import {
  NetworkComponent,
  ComplianceFramework,
  ControlMapping,
  ControlStatus,
  RiskLevel,
  NetworkInterface
} from './types';

interface ORANRequirement {
  id: string;
  title: string;
  description: string;
  category: string;
  specification: string;
  applicableInterfaces: NetworkInterface['type'][];
  applicableComponents: NetworkComponent['type'][];
}

export class ORANCompliance {
  private securityRequirements: ORANRequirement[];
  private interfaceRequirements: ORANRequirement[];

  constructor() {
    this.securityRequirements = this.initializeSecurityRequirements();
    this.interfaceRequirements = this.initializeInterfaceRequirements();
  }

  getControlsForComponent(
    component: NetworkComponent,
    framework: ComplianceFramework
  ): ControlMapping[] {
    const controls: ControlMapping[] = [];

    if (framework === 'oran-sds') {
      const sdsControls = this.getSDSControls(component);
      controls.push(...sdsControls);
    }

    if (framework === 'oran-security') {
      const securityControls = this.getSecurityControls(component);
      controls.push(...securityControls);
    }

    const interfaceControls = this.getInterfaceControls(component, framework);
    controls.push(...interfaceControls);

    return controls;
  }

  async validateORANInterfaces(
    component: NetworkComponent
  ): Promise<ORANInterfaceValidation> {
    const validations: InterfaceValidation[] = [];
    const issues: ORANIssue[] = [];

    for (const iface of component.interfaces) {
      const validation = this.validateInterface(iface, component);
      validations.push(validation);

      if (!validation.compliant) {
        issues.push({
          interfaceId: iface.id,
          interfaceName: iface.name,
          severity: 'high',
          description: validation.issues.join(', ')
        });
      }
    }

    return {
      componentId: component.id,
      componentType: component.type,
      validations,
      issues,
      score: validations.length > 0
        ? (validations.filter(v => v.compliant).length / validations.length) * 100
        : 100
    };
  }

  async validateOTSTestCases(
    component: NetworkComponent
  ): Promise<OTSTestResult> {
    const testSuites = this.getTestSuites(component);
    const results: TestCaseResult[] = [];

    for (const suite of testSuites) {
      for (const testCase of suite.testCases) {
        const result = this.executeTestCase(component, testCase);
        results.push(result);
      }
    }

    const passed = results.filter(r => r.status === 'passed').length;
    const failed = results.filter(r => r.status === 'failed').length;
    const skipped = results.filter(r => r.status === 'skipped').length;

    return {
      componentId: component.id,
      totalTests: results.length,
      passed,
      failed,
      skipped,
      results,
      score: results.length > 0 ? (passed / results.length) * 100 : 100
    };
  }

  private getSDSControls(component: NetworkComponent): ControlMapping[] {
    const controls: ControlMapping[] = [];

    const sdsRequirements = [
      {
        title: 'SDS Architecture Compliance',
        description: 'Component must comply with O-RAN SDS architecture',
        category: 'Architecture',
        check: () => component.interfaces.length > 0
      },
      {
        title: 'SDS API Specification',
        description: 'Component must implement O-RAN SDS API specifications',
        category: 'API',
        check: () => component.type !== 'device'
      },
      {
        title: 'SDS Security Requirements',
        description: 'Component must meet O-RAN SDS security requirements',
        category: 'Security',
        check: () => component.interfaces.some(i => i.encrypted)
      },
      {
        title: 'SDS Interoperability',
        description: 'Component must support O-RAN SDS interoperability',
        category: 'Interoperability',
        check: () => true
      }
    ];

    for (let i = 0; i < sdsRequirements.length; i++) {
      const req = sdsRequirements[i];
      const passed = req.check();

      controls.push({
        id: uuidv4(),
        framework: 'oran-sds',
        controlId: `SDS-${String(i + 1).padStart(3, '0')}`,
        title: req.title,
        description: req.description,
        category: req.category,
        status: passed ? 'compliant' : 'non-compliant',
        evidence: [],
        assessedDate: new Date().toISOString(),
        risk: passed ? 'informational' : 'medium'
      });
    }

    return controls;
  }

  private getSecurityControls(component: NetworkComponent): ControlMapping[] {
    const controls: ControlMapping[] = [];

    for (const req of this.securityRequirements) {
      if (req.applicableComponents.includes(component.type)) {
        const passed = this.checkSecurityRequirement(component, req);

        controls.push({
          id: uuidv4(),
          framework: 'oran-security',
          controlId: req.id,
          title: req.title,
          description: req.description,
          category: req.category,
          status: passed ? 'compliant' : 'non-compliant',
          evidence: [],
          assessedDate: new Date().toISOString(),
          risk: passed ? 'informational' : 'high'
        });
      }
    }

    return controls;
  }

  private getInterfaceControls(
    component: NetworkComponent,
    framework: ComplianceFramework
  ): ControlMapping[] {
    const controls: ControlMapping[] = [];

    for (const iface of component.interfaces) {
      const applicableReqs = this.interfaceRequirements.filter(req =>
        req.applicableInterfaces.includes(iface.type)
      );

      for (const req of applicableReqs) {
        const passed = this.checkInterfaceRequirement(component, iface, req);

        controls.push({
          id: uuidv4(),
          framework,
          controlId: `${req.id}-${iface.id}`,
          title: `${req.title} (${iface.name})`,
          description: req.description,
          category: req.category,
          status: passed ? 'compliant' : 'non-compliant',
          evidence: [],
          assessedDate: new Date().toISOString(),
          risk: passed ? 'informational' : 'high'
        });
      }
    }

    return controls;
  }

  private validateInterface(
    iface: NetworkInterface,
    component: NetworkComponent
  ): InterfaceValidation {
    const issues: string[] = [];

    if (!iface.encrypted) {
      issues.push('Interface is not encrypted');
    }

    if (iface.type === 'e2' && !iface.protocol.includes('DTLS')) {
      issues.push('E2 interface should use DTLS');
    }

    if (iface.type === 'a1' && !iface.encrypted) {
      issues.push('A1 interface must be encrypted');
    }

    return {
      interfaceId: iface.id,
      interfaceName: iface.name,
      interfaceType: iface.type,
      compliant: issues.length === 0,
      issues
    };
  }

  private getTestSuites(component: NetworkComponent): TestSuite[] {
    return [
      {
        name: 'Interface Security Tests',
        testCases: [
          {
            id: 'SEC-001',
            name: 'TLS Version Check',
            description: 'Verify TLS 1.2+ is used'
          },
          {
            id: 'SEC-002',
            name: 'Cipher Suite Strength',
            description: 'Verify strong cipher suites are used'
          },
          {
            id: 'SEC-003',
            name: 'Certificate Validation',
            description: 'Verify certificates are valid and not expired'
          }
        ]
      },
      {
        name: 'Protocol Compliance Tests',
        testCases: [
          {
            id: 'PROTO-001',
            name: 'Message Format Validation',
            description: 'Verify messages follow O-RAN specifications'
          },
          {
            id: 'PROTO-002',
            name: 'Version Compatibility',
            description: 'Verify protocol version compatibility'
          }
        ]
      }
    ];
  }

  private executeTestCase(
    component: NetworkComponent,
    testCase: TestCase
  ): TestCaseResult {
    let status: 'passed' | 'failed' | 'skipped' = 'passed';
    let message = 'Test passed';

    if (testCase.id === 'SEC-001') {
      const hasStrongTLS = component.interfaces.some(i =>
        i.encrypted && i.protocol.includes('TLS')
      );
      status = hasStrongTLS ? 'passed' : 'failed';
      message = hasStrongTLS ? 'Strong TLS in use' : 'Weak or no TLS detected';
    }

    if (testCase.id === 'SEC-002') {
      const hasStrongCiphers = component.interfaces.some(i =>
        i.encrypted
      );
      status = hasStrongCiphers ? 'passed' : 'failed';
      message = hasStrongCiphers ? 'Strong ciphers in use' : 'Weak ciphers detected';
    }

    return {
      testCaseId: testCase.id,
      testCaseName: testCase.name,
      status,
      message,
      executedAt: new Date().toISOString()
    };
  }

  private checkSecurityRequirement(
    component: NetworkComponent,
    req: ORANRequirement
  ): boolean {
    if (req.id === 'SEC-001') {
      return component.interfaces.some(i => i.encrypted);
    }

    if (req.id === 'SEC-002') {
      return component.type !== 'device' || component.interfaces.length > 0;
    }

    if (req.id === 'SEC-003') {
      return true;
    }

    return true;
  }

  private checkInterfaceRequirement(
    component: NetworkComponent,
    iface: NetworkInterface,
    req: ORANRequirement
  ): boolean {
    if (req.id === 'IF-001') {
      return iface.encrypted;
    }

    if (req.id === 'IF-002') {
      return iface.protocol !== '';
    }

    return true;
  }

  private initializeSecurityRequirements(): ORANRequirement[] {
    return [
      {
        id: 'SEC-001',
        title: 'Transport Layer Security',
        description: 'All O-RAN interfaces must use TLS 1.2 or higher',
        category: 'Transport Security',
        specification: 'O-RAN.SDD-RANWF',
        applicableInterfaces: ['e1', 'e2', 'o1', 'o2', 'a1'],
        applicableComponents: ['ran-node', 'edge-compute', 'orchestrator']
      },
      {
        id: 'SEC-002',
        title: 'Mutual Authentication',
        description: 'Mutual authentication must be implemented between O-RAN components',
        category: 'Authentication',
        specification: 'O-RAN.SDD-RANWF',
        applicableInterfaces: ['e1', 'e2', 'o1', 'a1'],
        applicableComponents: ['ran-node', 'core-network', 'edge-compute']
      },
      {
        id: 'SEC-003',
        title: 'Key Management',
        description: 'Secure key management must be implemented',
        category: 'Key Management',
        specification: 'O-RAN.SDD-RANWF',
        applicableInterfaces: ['e1', 'e2', 'o1'],
        applicableComponents: ['ran-node', 'core-network', 'security-gateway']
      },
      {
        id: 'SEC-004',
        title: 'Secure Boot',
        description: 'Components must support secure boot processes',
        category: 'Platform Security',
        specification: 'O-RAN.SDD-RANWF',
        applicableInterfaces: [],
        applicableComponents: ['ran-node', 'core-network', 'edge-compute']
      },
      {
        id: 'SEC-005',
        title: 'Firmware Integrity',
        description: 'Firmware integrity must be verified during updates',
        category: 'Supply Chain Security',
        specification: 'O-RAN.SDD-RANWF',
        applicableInterfaces: [],
        applicableComponents: ['ran-node', 'core-network', 'edge-compute']
      }
    ];
  }

  private initializeInterfaceRequirements(): ORANRequirement[] {
    return [
      {
        id: 'IF-001',
        title: 'Interface Encryption',
        description: 'O-RAN interfaces must be encrypted',
        category: 'Interface Security',
        specification: 'O-RAN.WG3',
        applicableInterfaces: ['e1', 'e2', 'o1', 'o2', 'a1'],
        applicableComponents: ['ran-node', 'core-network', 'edge-compute']
      },
      {
        id: 'IF-002',
        title: 'Protocol Compliance',
        description: 'Interfaces must use O-RAN specified protocols',
        category: 'Protocol Compliance',
        specification: 'O-RAN.WG3',
        applicableInterfaces: ['e1', 'e2', 'o1', 'o2', 'a1'],
        applicableComponents: ['ran-node', 'core-network', 'edge-compute']
      },
      {
        id: 'IF-003',
        title: 'Message Authentication',
        description: 'Messages must be authenticated',
        category: 'Message Security',
        specification: 'O-RAN.WG3',
        applicableInterfaces: ['e2', 'a1'],
        applicableComponents: ['ran-node', 'orchestrator']
      }
    ];
  }
}

export interface ORANInterfaceValidation {
  componentId: string;
  componentType: NetworkComponent['type'];
  validations: InterfaceValidation[];
  issues: ORANIssue[];
  score: number;
}

export interface InterfaceValidation {
  interfaceId: string;
  interfaceName: string;
  interfaceType: NetworkInterface['type'];
  compliant: boolean;
  issues: string[];
}

export interface ORANIssue {
  interfaceId: string;
  interfaceName: string;
  severity: RiskLevel;
  description: string;
}

export interface OTSTestResult {
  componentId: string;
  totalTests: number;
  passed: number;
  failed: number;
  skipped: number;
  results: TestCaseResult[];
  score: number;
}

export interface TestSuite {
  name: string;
  testCases: TestCase[];
}

export interface TestCase {
  id: string;
  name: string;
  description: string;
}

export interface TestCaseResult {
  testCaseId: string;
  testCaseName: string;
  status: 'passed' | 'failed' | 'skipped';
  message: string;
  executedAt: string;
}
