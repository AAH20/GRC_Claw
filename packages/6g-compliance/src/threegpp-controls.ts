import { v4 as uuidv4 } from 'uuid';
import {
  NetworkComponent,
  ComplianceFramework,
  ControlMapping,
  ControlStatus,
  RiskLevel
} from './types';

interface ThreeGPPControl {
  id: string;
  title: string;
  description: string;
  category: string;
  version: string;
  applicableComponents: NetworkComponent['type'][];
}

export class ThreeGPPControls {
  private ts33501Controls: ThreeGPPControl[];
  private ts33210Controls: ThreeGPPControl[];
  private ts33511Controls: ThreeGPPControl[];
  private ts33512Controls: ThreeGPPControl[];

  constructor() {
    this.ts33501Controls = this.initializeTS33501Controls();
    this.ts33210Controls = this.initializeTS33210Controls();
    this.ts33511Controls = this.initializeTS33511Controls();
    this.ts33512Controls = this.initializeTS33512Controls();
  }

  getControlsForComponent(
    component: NetworkComponent,
    framework: ComplianceFramework
  ): ControlMapping[] {
    let controls: ThreeGPPControl[];

    switch (framework) {
      case '3gpp-ts33501':
        controls = this.ts33501Controls.filter(c =>
          c.applicableComponents.includes(component.type)
        );
        break;
      case '3gpp-ts33210':
        controls = this.ts33210Controls.filter(c =>
          c.applicableComponents.includes(component.type)
        );
        break;
      case '3gpp-ts33511':
        controls = this.ts33511Controls.filter(c =>
          c.applicableComponents.includes(component.type)
        );
        break;
      case '3gpp-ts33512':
        controls = this.ts33512Controls.filter(c =>
          c.applicableComponents.includes(component.type)
        );
        break;
      default:
        return [];
    }

    return controls.map(control => ({
      id: uuidv4(),
      framework,
      controlId: control.id,
      title: control.title,
      description: control.description,
      category: control.category,
      status: this.assessControl(component, control),
      evidence: [],
      assessedDate: new Date().toISOString(),
      risk: this.determineRisk(component, control)
    }));
  }

  private assessControl(
    component: NetworkComponent,
    control: ThreeGPPControl
  ): ControlStatus {
    if (this.isControlApplicable(component, control)) {
      if (this.isControlImplemented(component, control)) {
        return 'compliant';
      }
      return 'partially-compliant';
    }
    return 'not-applicable';
  }

  private isControlApplicable(
    component: NetworkComponent,
    control: ThreeGPPControl
  ): boolean {
    return control.applicableComponents.includes(component.type);
  }

  private isControlImplemented(
    component: NetworkComponent,
    control: ThreeGPPControl
  ): boolean {
    if (control.id.includes('auth')) {
      return component.interfaces.some(i => i.encrypted);
    }
    if (control.id.includes('cipher')) {
      return component.interfaces.some(i => i.encrypted);
    }
    return true;
  }

  private determineRisk(
    component: NetworkComponent,
    control: ThreeGPPControl
  ): RiskLevel {
    if (control.id.includes('auth') || control.id.includes('integrity')) {
      return 'high';
    }
    if (control.id.includes('cipher') || control.id.includes('key')) {
      return 'medium';
    }
    return 'low';
  }

  private initializeTS33501Controls(): ThreeGPPControl[] {
    return [
      {
        id: '33.501-5.1.1',
        title: 'Authentication and Key Agreement (AKA)',
        description: '5G AKA shall be used for mutual authentication between UE and network',
        category: 'Authentication',
        version: '17.0.0',
        applicableComponents: ['core-network', 'ran-node', 'device']
      },
      {
        id: '33.501-5.1.2',
        title: 'EAP-AKA Authentication',
        description: 'EAP-AKA shall be supported as an alternative authentication method',
        category: 'Authentication',
        version: '17.0.0',
        applicableComponents: ['core-network']
      },
      {
        id: '33.501-5.2.1',
        title: 'NAS Ciphering',
        description: 'NAS signaling shall be ciphered between UE and AMF',
        category: 'Confidentiality',
        version: '17.0.0',
        applicableComponents: ['core-network', 'ran-node']
      },
      {
        id: '33.501-5.2.2',
        title: 'NAS Integrity Protection',
        description: 'NAS signaling shall be integrity protected',
        category: 'Integrity',
        version: '17.0.0',
        applicableComponents: ['core-network', 'ran-node']
      },
      {
        id: '33.501-5.3.1',
        title: 'User Plane Ciphering',
        description: 'User plane data shall be ciphered between UE and gNB',
        category: 'Confidentiality',
        version: '17.0.0',
        applicableComponents: ['ran-node', 'device']
      },
      {
        id: '33.501-5.3.2',
        title: 'User Plane Integrity Protection',
        description: 'User plane integrity protection shall be supported',
        category: 'Integrity',
        version: '17.0.0',
        applicableComponents: ['ran-node', 'device']
      },
      {
        id: '33.501-5.4.1',
        title: 'Security Context Storage',
        description: 'Security context shall be stored securely in the network',
        category: 'Key Management',
        version: '17.0.0',
        applicableComponents: ['core-network']
      },
      {
        id: '33.501-5.4.2',
        title: 'Key Hierarchy',
        description: '5G key hierarchy shall be implemented as specified',
        category: 'Key Management',
        version: '17.0.0',
        applicableComponents: ['core-network', 'ran-node']
      },
      {
        id: '33.501-6.1.1',
        title: 'SUPI/SUCI Privacy',
        description: 'Permanent identifier (SUPI) shall be concealed using SUCI',
        category: 'Privacy',
        version: '17.0.0',
        applicableComponents: ['core-network', 'device']
      },
      {
        id: '33.501-6.2.1',
        title: 'Network Slice Security',
        description: 'Network slicing shall be securely implemented',
        category: 'Network Slicing',
        version: '17.0.0',
        applicableComponents: ['core-network', 'slice-controller']
      },
      {
        id: '33.501-6.3.1',
        title: 'Edge Computing Security',
        description: 'Edge computing security requirements shall be met',
        category: 'Edge Computing',
        version: '17.0.0',
        applicableComponents: ['edge-compute', 'core-network']
      },
      {
        id: '33.501-6.4.1',
        title: 'Service Based Architecture Security',
        description: 'SBA security shall be implemented between network functions',
        category: 'SBA Security',
        version: '17.0.0',
        applicableComponents: ['core-network']
      },
      {
        id: '33.501-6.5.1',
        title: 'Network Exposure Security',
        description: 'NEF security requirements shall be implemented',
        category: 'API Security',
        version: '17.0.0',
        applicableComponents: ['core-network']
      },
      {
        id: '33.501-6.6.1',
        title: 'Inter-operator Security',
        description: 'Security for inter-operator network connections',
        category: 'Roaming Security',
        version: '17.0.0',
        applicableComponents: ['core-network', 'transport']
      }
    ];
  }

  private initializeTS33210Controls(): ThreeGPPControl[] {
    return [
      {
        id: '33.210-5.1',
        title: 'Network Domain Security',
        description: 'Security between network elements within the same domain',
        category: 'Domain Security',
        version: '17.0.0',
        applicableComponents: ['core-network', 'ran-node', 'transport']
      },
      {
        id: '33.210-5.2',
        title: 'Network Domain Security for IP',
        description: 'IP-based network domain security using IPsec',
        category: 'Domain Security',
        version: '17.0.0',
        applicableComponents: ['transport', 'core-network']
      },
      {
        id: '33.210-5.3',
        title: 'Network Domain Security for GTP',
        description: 'GTP-based network domain security',
        category: 'Domain Security',
        version: '17.0.0',
        applicableComponents: ['core-network']
      },
      {
        id: '33.210-6.1',
        title: 'Service Layer Security',
        description: 'Security mechanisms at the service layer',
        category: 'Service Security',
        version: '17.0.0',
        applicableComponents: ['core-network']
      },
      {
        id: '33.210-6.2',
        title: 'Application Layer Security',
        description: 'TLS/SSL for application layer communications',
        category: 'Service Security',
        version: '17.0.0',
        applicableComponents: ['core-network', 'edge-compute']
      }
    ];
  }

  private initializeTS33511Controls(): ThreeGPPControl[] {
    return [
      {
        id: '33.511-5.1',
        title: 'Security Assurance Methodology',
        description: 'Structured security assurance evaluation methodology',
        category: 'Assurance',
        version: '17.0.0',
        applicableComponents: ['core-network', 'ran-node', 'edge-compute', 'device']
      },
      {
        id: '33.511-5.2',
        title: 'Security Test Specifications',
        description: 'Test cases for verifying security requirements',
        category: 'Testing',
        version: '17.0.0',
        applicableComponents: ['core-network', 'ran-node', 'edge-compute', 'device']
      },
      {
        id: '33.511-5.3',
        title: 'Vulnerability Assessment',
        description: 'Systematic vulnerability assessment procedures',
        category: 'Assessment',
        version: '17.0.0',
        applicableComponents: ['core-network', 'ran-node', 'edge-compute', 'device']
      },
      {
        id: '33.511-5.4',
        title: 'Penetration Testing',
        description: 'Penetration testing requirements and methodologies',
        category: 'Testing',
        version: '17.0.0',
        applicableComponents: ['core-network', 'ran-node', 'edge-compute']
      },
      {
        id: '33.511-6.1',
        title: 'NR Security Assurance',
        description: 'New Radio security assurance specifications',
        category: 'NR Assurance',
        version: '17.0.0',
        applicableComponents: ['ran-node', 'device']
      },
      {
        id: '33.511-6.2',
        title: 'NGC Security Assurance',
        description: 'Next Generation Core security assurance specifications',
        category: 'NGC Assurance',
        version: '17.0.0',
        applicableComponents: ['core-network']
      }
    ];
  }

  private initializeTS33512Controls(): ThreeGPPControl[] {
    return [
      {
        id: '33.512-5.1',
        title: 'Security Assurance for NF',
        description: 'Security assurance requirements for Network Functions',
        category: 'NF Security',
        version: '17.0.0',
        applicableComponents: ['core-network']
      },
      {
        id: '33.512-5.2',
        title: 'NF Isolation Requirements',
        description: 'Isolation requirements between network functions',
        category: 'Isolation',
        version: '17.0.0',
        applicableComponents: ['core-network', 'edge-compute']
      },
      {
        id: '33.512-5.3',
        title: 'NF Hardening',
        description: 'Security hardening requirements for network functions',
        category: 'Hardening',
        version: '17.0.0',
        applicableComponents: ['core-network', 'ran-node', 'edge-compute']
      },
      {
        id: '33.512-5.4',
        title: 'Container Security',
        description: 'Security requirements for containerized NFs',
        category: 'Container Security',
        version: '17.0.0',
        applicableComponents: ['core-network', 'edge-compute']
      },
      {
        id: '33.512-6.1',
        title: 'SBA Security Requirements',
        description: 'Service Based Architecture security requirements',
        category: 'SBA Security',
        version: '17.0.0',
        applicableComponents: ['core-network']
      },
      {
        id: '33.512-6.2',
        title: 'OAuth 2.0 Implementation',
        description: 'OAuth 2.0 for API authorization in SBA',
        category: 'API Security',
        version: '17.0.0',
        applicableComponents: ['core-network']
      },
      {
        id: '33.512-6.3',
        title: 'Mutual TLS',
        description: 'Mutual TLS for service-to-service communication',
        category: 'Transport Security',
        version: '17.0.0',
        applicableComponents: ['core-network', 'edge-compute']
      }
    ];
  }

  mapToGRCControl(threeGPPControlId: string): string {
    const mappings: Record<string, string> = {
      '33.501-5.1.1': 'GRC-AUTH-001',
      '33.501-5.2.1': 'GRC-CRYPTO-001',
      '33.501-5.3.1': 'GRC-CRYPTO-002',
      '33.501-6.1.1': 'GRC-PRIVACY-001',
      '33.501-6.2.1': 'GRC-NETWORK-001',
      '33.210-5.1': 'GRC-NET-SEC-001',
      '33.511-5.3': 'GRC-ASSESS-001',
      '33.512-5.3': 'GRC-HARDEN-001'
    };

    return mappings[threeGPPControlId] || 'GRC-UNKNOWN';
  }

  getGRCMapping(): Record<string, string[]> {
    return {
      'GRC-AUTH-001': ['33.501-5.1.1', '33.501-5.1.2'],
      'GRC-CRYPTO-001': ['33.501-5.2.1', '33.501-5.2.2'],
      'GRC-CRYPTO-002': ['33.501-5.3.1', '33.501-5.3.2'],
      'GRC-PRIVACY-001': ['33.501-6.1.1'],
      'GRC-NETWORK-001': ['33.501-6.2.1'],
      'GRC-NET-SEC-001': ['33.210-5.1', '33.210-5.2', '33.210-5.3'],
      'GRC-ASSESS-001': ['33.511-5.3'],
      'GRC-HARDEN-001': ['33.512-5.3', '33.512-5.4']
    };
  }
}
