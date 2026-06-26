export interface ComplianceRule {
  id: string;
  name: string;
  category: string;
  checkFunction: string;
  frameworks: string[];
  severity: 'critical' | 'high' | 'medium' | 'low';
  controlId: Record<string, string>;
}

export const COMPLIANCE_RULES: ComplianceRule[] = [
  {
    id: 'mfa_enabled',
    name: 'Multi-Factor Authentication Enabled',
    category: 'Identity & Access Management',
    checkFunction: 'checkMFAStatus',
    frameworks: ['SOC2', 'ISO27001', 'HIPAA'],
    severity: 'critical',
    controlId: {
      SOC2: 'CC6.1',
      ISO27001: 'A.9.4.2',
      HIPAA: '164.312(d)',
    },
  },
  {
    id: 'disk_encryption',
    name: 'Full Disk Encryption',
    category: 'Data Protection',
    checkFunction: 'checkEncryptionStatus',
    frameworks: ['SOC2', 'ISO27001', 'HIPAA'],
    severity: 'critical',
    controlId: {
      SOC2: 'CC6.1',
      ISO27001: 'A.10.1.1',
      HIPAA: '164.312(a)(2)(iv)',
    },
  },
  {
    id: 'firewall_enabled',
    name: 'Host Firewall Enabled',
    category: 'Network Security',
    checkFunction: 'checkFirewallStatus',
    frameworks: ['SOC2', 'ISO27001', 'HIPAA'],
    severity: 'high',
    controlId: {
      SOC2: 'CC6.6',
      ISO27001: 'A.13.1.1',
      HIPAA: '164.312(e)(1)',
    },
  },
  {
    id: 'antivirus_running',
    name: 'Antivirus / Endpoint Protection Running',
    category: 'Endpoint Security',
    checkFunction: 'checkAntivirusStatus',
    frameworks: ['SOC2', 'ISO27001', 'HIPAA'],
    severity: 'high',
    controlId: {
      SOC2: 'CC7.1',
      ISO27001: 'A.12.2.1',
      HIPAA: '164.308(a)(5)(ii)(B)',
    },
  },
  {
    id: 'os_up_to_date',
    name: 'Operating System Up to Date',
    category: 'Vulnerability Management',
    checkFunction: 'checkOSVersion',
    frameworks: ['SOC2', 'ISO27001', 'HIPAA'],
    severity: 'high',
    controlId: {
      SOC2: 'CC7.1',
      ISO27001: 'A.12.6.1',
      HIPAA: '164.308(a)(1)(ii)(B)',
    },
  },
  {
    id: 'password_manager',
    name: 'Password Manager Installed',
    category: 'Identity & Access Management',
    checkFunction: 'checkPasswordManager',
    frameworks: ['SOC2', 'ISO27001'],
    severity: 'medium',
    controlId: {
      SOC2: 'CC6.1',
      ISO27001: 'A.9.4.3',
    },
  },
  {
    id: 'screen_lock',
    name: 'Screen Lock Configured',
    category: 'Physical Security',
    checkFunction: 'checkScreenLock',
    frameworks: ['SOC2', 'ISO27001', 'HIPAA'],
    severity: 'medium',
    controlId: {
      SOC2: 'CC6.4',
      ISO27001: 'A.11.2.9',
      HIPAA: '164.310(a)(2)(iii)',
    },
  },
  {
    id: 'auto_lock',
    name: 'Auto-Lock Timeout Active',
    category: 'Physical Security',
    checkFunction: 'checkAutoLock',
    frameworks: ['SOC2', 'ISO27001', 'HIPAA'],
    severity: 'medium',
    controlId: {
      SOC2: 'CC6.4',
      ISO27001: 'A.11.2.9',
      HIPAA: '164.310(a)(2)(iii)',
    },
  },
  {
    id: 'usb_control',
    name: 'USB Device Control',
    category: 'Data Protection',
    checkFunction: 'checkUSBControl',
    frameworks: ['SOC2', 'ISO27001'],
    severity: 'medium',
    controlId: {
      SOC2: 'CC6.1',
      ISO27001: 'A.11.2.5',
    },
  },
  {
    id: 'browser_extensions',
    name: 'Browser Extension Audit',
    category: 'Endpoint Security',
    checkFunction: 'checkBrowserExtensions',
    frameworks: ['SOC2', 'ISO27001'],
    severity: 'low',
    controlId: {
      SOC2: 'CC6.1',
      ISO27001: 'A.12.2.1',
    },
  },
];

export function getRulesByFramework(framework: string): ComplianceRule[] {
  return COMPLIANCE_RULES.filter((r) => r.frameworks.includes(framework));
}

export function getRuleById(id: string): ComplianceRule | undefined {
  return COMPLIANCE_RULES.find((r) => r.id === id);
}

export function getRulesByCategory(category: string): ComplianceRule[] {
  return COMPLIANCE_RULES.filter((r) => r.category === category);
}
