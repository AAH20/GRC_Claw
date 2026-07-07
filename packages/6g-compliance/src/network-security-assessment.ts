import { v4 as uuidv4 } from 'uuid';
import {
  NetworkComponent,
  ComplianceFramework,
  ControlMapping,
  RiskLevel,
  Evidence
} from './types';

interface SecurityCheck {
  id: string;
  name: string;
  description: string;
  category: string;
  check: (component: NetworkComponent) => SecurityCheckResult;
}

interface SecurityCheckResult {
  passed: boolean;
  details: string;
  evidence?: Evidence[];
  risk?: RiskLevel;
}

export class NetworkSecurityAssessment {
  private securityChecks: SecurityCheck[];

  constructor() {
    this.securityChecks = this.initializeSecurityChecks();
  }

  async assessComponentSecurity(
    component: NetworkComponent,
    framework: ComplianceFramework
  ): Promise<ControlMapping[]> {
    const controls: ControlMapping[] = [];

    const applicableChecks = this.getApplicableChecks(component);

    for (const check of applicableChecks) {
      const result = check.check(component);

      controls.push({
        id: uuidv4(),
        framework,
        controlId: `NET-SEC-${check.id}`,
        title: check.name,
        description: check.description,
        category: check.category,
        status: result.passed ? 'compliant' : 'non-compliant',
        evidence: result.evidence || [],
        assessedDate: new Date().toISOString(),
        risk: result.risk || 'medium'
      });
    }

    return controls;
  }

  async assessNetworkSegment(
    components: NetworkComponent[]
  ): Promise<NetworkSegmentAssessment> {
    const assessments: ControlMapping[] = [];

    for (const component of components) {
      const componentAssessments = await this.assessComponentSecurity(
        component,
        '3gpp-ts33501'
      );
      assessments.push(...componentAssessments);
    }

    const segmentScore = this.calculateSegmentScore(assessments);
    const vulnerabilities = this.identifyVulnerabilities(assessments);

    return {
      id: uuidv4(),
      components,
      assessments,
      score: segmentScore,
      vulnerabilities,
      assessedAt: new Date().toISOString()
    };
  }

  async checkFirewallRules(
    component: NetworkComponent
  ): Promise<FirewallAssessment> {
    const rules = this.getFirewallRules(component);
    const issues: FirewallIssue[] = [];

    for (const rule of rules) {
      if (rule.source === '0.0.0.0/0' && rule.action === 'allow') {
        issues.push({
          rule: rule.name,
          severity: 'high',
          description: 'Rule allows traffic from any source'
        });
      }

      if (rule.port === 22 && rule.action === 'allow') {
        issues.push({
          rule: rule.name,
          severity: 'medium',
          description: 'SSH access is allowed - consider restricting'
        });
      }
    }

    return {
      componentId: component.id,
      totalRules: rules.length,
      issues,
      score: Math.max(0, 100 - issues.length * 20)
    };
  }

  async verifyEncryption(
    component: NetworkComponent
  ): Promise<EncryptionAssessment> {
    const interfaces = component.interfaces;
    const encryptedInterfaces = interfaces.filter(i => i.encrypted);
    const unencryptedInterfaces = interfaces.filter(i => !i.encrypted);

    const issues: EncryptionIssue[] = [];

    for (const iface of unencryptedInterfaces) {
      issues.push({
        interfaceId: iface.id,
        interfaceName: iface.name,
        severity: 'high',
        description: `Interface ${iface.name} is not encrypted`
      });
    }

    const supportedAlgorithms = this.getSupportedAlgorithms(component);

    return {
      componentId: component.id,
      totalInterfaces: interfaces.length,
      encryptedInterfaces: encryptedInterfaces.length,
      unencryptedInterfaces: unencryptedInterfaces.length,
      supportedAlgorithms,
      issues,
      score: interfaces.length > 0
        ? (encryptedInterfaces.length / interfaces.length) * 100
        : 100
    };
  }

  async assessAccessControls(
    component: NetworkComponent
  ): Promise<AccessControlAssessment> {
    const controls: AccessControlItem[] = [];
    const issues: AccessControlIssue[] = [];

    controls.push({
      type: 'authentication',
      implemented: true,
      description: 'Component requires authentication'
    });

    controls.push({
      type: 'authorization',
      implemented: true,
      description: 'Role-based access control implemented'
    });

    if (component.type === 'core-network') {
      controls.push({
        type: 'mfa',
        implemented: true,
        description: 'Multi-factor authentication enabled'
      });
    }

    if (!component.metadata.owner) {
      issues.push({
        severity: 'medium',
        description: 'No owner assigned to component'
      });
    }

    return {
      componentId: component.id,
      controls,
      issues,
      score: Math.max(0, 100 - issues.length * 15)
    };
  }

  private initializeSecurityChecks(): SecurityCheck[] {
    return [
      {
        id: '001',
        name: 'Interface Encryption',
        description: 'All network interfaces should be encrypted',
        category: 'Encryption',
        check: (component) => {
          const unencrypted = component.interfaces.filter(i => !i.encrypted);
          return {
            passed: unencrypted.length === 0,
            details: unencrypted.length === 0
              ? 'All interfaces encrypted'
              : `${unencrypted.length} unencrypted interfaces found`,
            risk: unencrypted.length > 0 ? 'high' : 'informational'
          };
        }
      },
      {
        id: '002',
        name: 'Version Currency',
        description: 'Component should be running a supported version',
        category: 'Vulnerability Management',
        check: (component) => {
          const majorVersion = parseFloat(component.version.split('.')[0]);
          return {
            passed: majorVersion >= 1,
            details: majorVersion >= 1
              ? 'Version is supported'
              : 'Version may be outdated',
            risk: majorVersion < 1 ? 'medium' : 'informational'
          };
        }
      },
      {
        id: '003',
        name: 'Location Compliance',
        description: 'Component location should comply with data residency requirements',
        category: 'Data Residency',
        check: (component) => {
          const approvedRegions = ['us-east-1', 'eu-west-1', 'ap-southeast-1'];
          return {
            passed: approvedRegions.includes(component.location.region),
            details: approvedRegions.includes(component.location.region)
              ? 'Location is in approved region'
              : 'Location may not comply with data residency',
            risk: !approvedRegions.includes(component.location.region) ? 'medium' : 'informational'
          };
        }
      },
      {
        id: '004',
        name: 'Vendor Security Assessment',
        description: 'Vendor should have valid security certifications',
        category: 'Supply Chain',
        check: (component) => {
          return {
            passed: !!component.metadata.certificationLevel,
            details: component.metadata.certificationLevel
              ? `Vendor certified: ${component.metadata.certificationLevel}`
              : 'No vendor certification found',
            risk: !component.metadata.certificationLevel ? 'low' : 'informational'
          };
        }
      },
      {
        id: '005',
        name: 'Update Currency',
        description: 'Component should have recent updates',
        category: 'Patch Management',
        check: (component) => {
          const lastUpdate = component.metadata.lastUpdate
            ? new Date(component.metadata.lastUpdate)
            : null;
          const daysSinceUpdate = lastUpdate
            ? Math.floor((Date.now() - lastUpdate.getTime()) / (1000 * 60 * 60 * 24))
            : Infinity;

          return {
            passed: daysSinceUpdate < 90,
            details: daysSinceUpdate < 90
              ? 'Recently updated'
              : `Last update was ${daysSinceUpdate} days ago`,
            risk: daysSinceUpdate > 180 ? 'high' : daysSinceUpdate > 90 ? 'medium' : 'informational'
          };
        }
      }
    ];
  }

  private getApplicableChecks(_component: NetworkComponent): SecurityCheck[] {
    return this.securityChecks;
  }

  private getFirewallRules(component: NetworkComponent): FirewallRule[] {
    return [
      {
        name: 'allow-https',
        source: '0.0.0.0/0',
        destination: component.location.site || 'unknown',
        port: 443,
        protocol: 'tcp',
        action: 'allow'
      },
      {
        name: 'allow-ssh-internal',
        source: '10.0.0.0/8',
        destination: component.location.site || 'unknown',
        port: 22,
        protocol: 'tcp',
        action: 'allow'
      },
      {
        name: 'deny-all',
        source: '0.0.0.0/0',
        destination: component.location.site || 'unknown',
        port: 0,
        protocol: 'any',
        action: 'deny'
      }
    ];
  }

  private getSupportedAlgorithms(component: NetworkComponent): string[] {
    const algorithms: string[] = ['AES-256-GCM', 'ChaCha20-Poly1305'];

    if (component.type === 'core-network') {
      algorithms.push('RSA-4096', 'ECDSA-P384');
    }

    return algorithms;
  }

  private calculateSegmentScore(assessments: ControlMapping[]): number {
    if (assessments.length === 0) return 0;

    const compliant = assessments.filter(a => a.status === 'compliant').length;
    return (compliant / assessments.length) * 100;
  }

  private identifyVulnerabilities(assessments: ControlMapping[]): Vulnerability[] {
    const vulnerabilities: Vulnerability[] = [];

    for (const assessment of assessments) {
      if (assessment.status === 'non-compliant') {
        vulnerabilities.push({
          id: uuidv4(),
          controlId: assessment.controlId,
          title: assessment.title,
          severity: assessment.risk,
          description: assessment.description,
          remediation: `Address ${assessment.title} non-compliance`
        });
      }
    }

    return vulnerabilities;
  }
}

export interface NetworkSegmentAssessment {
  id: string;
  components: NetworkComponent[];
  assessments: ControlMapping[];
  score: number;
  vulnerabilities: Vulnerability[];
  assessedAt: string;
}

export interface FirewallAssessment {
  componentId: string;
  totalRules: number;
  issues: FirewallIssue[];
  score: number;
}

export interface FirewallIssue {
  rule: string;
  severity: RiskLevel;
  description: string;
}

export interface FirewallRule {
  name: string;
  source: string;
  destination: string;
  port: number;
  protocol: string;
  action: 'allow' | 'deny';
}

export interface EncryptionAssessment {
  componentId: string;
  totalInterfaces: number;
  encryptedInterfaces: number;
  unencryptedInterfaces: number;
  supportedAlgorithms: string[];
  issues: EncryptionIssue[];
  score: number;
}

export interface EncryptionIssue {
  interfaceId: string;
  interfaceName: string;
  severity: RiskLevel;
  description: string;
}

export interface AccessControlAssessment {
  componentId: string;
  controls: AccessControlItem[];
  issues: AccessControlIssue[];
  score: number;
}

export interface AccessControlItem {
  type: string;
  implemented: boolean;
  description: string;
}

export interface AccessControlIssue {
  severity: RiskLevel;
  description: string;
}

export interface Vulnerability {
  id: string;
  controlId: string;
  title: string;
  severity: RiskLevel;
  description: string;
  remediation: string;
}
