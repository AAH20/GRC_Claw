import type { PolicyTemplate } from './types.js';

export const POLICY_TEMPLATES: PolicyTemplate[] = [
  {
    id: 'tpl-infosec',
    name: 'Information Security Policy',
    category: 'security',
    framework: 'ISO 27001',
    frameworkMappings: ['ISO 27001:A.5', 'NIST CSF:PR.IP', 'SOC 2:CC6.1', 'ISO 42001:A.7'],
    requiredSections: ['Purpose', 'Scope', 'Policy', 'Roles and Responsibilities', 'Enforcement', 'Review Cycle'],
    isDefault: true,
    content: `# Information Security Policy

## Purpose
Establish and maintain an information security management system (ISMS) to protect the confidentiality, integrity, and availability of organizational information assets.

## Scope
This policy applies to all employees, contractors, third-party users, and systems that access, process, or store organizational information assets.

## Policy
1. Classify all data according to the Data Classification Policy
2. Implement security controls proportionate to data sensitivity
3. Conduct risk assessments annually and after significant changes
4. Maintain a documented risk treatment plan
5. Perform internal ISMS audits on a semi-annual basis
6. Ensure management review of security objectives quarterly

## Roles and Responsibilities
- **CISO**: Owns the ISMS, reports to the board on security posture
- **IT Security Team**: Implements and monitors technical controls
- **Department Heads**: Ensure team compliance within their domain
- **All Employees**: Follow security policies and report incidents

## Enforcement
Violations may result in disciplinary action up to and including termination, civil penalties, or criminal prosecution.

## Review Cycle
This policy is reviewed annually or after significant organizational/technology changes.`,
  },
  {
    id: 'tpl-aup',
    name: 'Acceptable Use Policy',
    category: 'operational',
    framework: 'SOC 2',
    frameworkMappings: ['SOC 2:CC6.1', 'ISO 27001:A.6.2', 'NIST CSF:PR.AC'],
    requiredSections: ['Purpose', 'Scope', 'Acceptable Use', 'Prohibited Activities', 'Monitoring', 'Enforcement'],
    isDefault: true,
    content: `# Acceptable Use Policy

## Purpose
Define acceptable and prohibited use of company information systems, networks, and data to protect organizational assets and reduce risk.

## Scope
All company-owned and company-provided computing resources, networks, software, data, and cloud services.

## Acceptable Use
1. Use computing resources primarily for authorized business purposes
2. Maintain strong passwords and enable multi-factor authentication
3. Keep software and operating systems updated with security patches
4. Report suspected security incidents within 1 hour of discovery
5. Use encryption for sensitive data in transit and at rest
6. Back up work data according to department guidelines

## Prohibited Activities
1. Unauthorized installation of software or hardware
2. Accessing, downloading, or distributing inappropriate or illegal content
3. Sharing credentials with others or using shared accounts
4. Connecting unauthorized devices to the corporate network
5. Bypassing security controls or using unauthorized VPNs
6. Using company resources for personal commercial activities

## Monitoring
The company reserves the right to monitor all use of its systems and data. Users should have no expectation of privacy on company-owned systems.

## Enforcement
Violations result in immediate access revocation and disciplinary action. Willful violations may be referred to law enforcement.`,
  },
  {
    id: 'tpl-data-class',
    name: 'Data Classification Policy',
    category: 'security',
    framework: 'ISO 27001',
    frameworkMappings: ['ISO 27001:A.8.2', 'NIST CSF:PR.DS', 'SOC 2:CC6.5', 'GDPR:Art.5'],
    requiredSections: ['Purpose', 'Scope', 'Classification Levels', 'Handling Requirements', 'Labeling', 'De-classification'],
    isDefault: true,
    content: `# Data Classification Policy

## Purpose
Establish a framework for classifying organizational data based on sensitivity and criticality, ensuring appropriate protection controls are applied.

## Scope
All data created, collected, processed, stored, or transmitted by the organization, regardless of format or location.

## Classification Levels
1. **Public**: Information approved for public disclosure with no impact if disclosed
2. **Internal**: General business information not intended for public disclosure
3. **Confidential**: Sensitive business information that could cause harm if disclosed
4. **Restricted**: Highly sensitive data (PII, PHI, financial, trade secrets) subject to regulatory requirements

## Handling Requirements
- **Public**: No special handling required
- **Internal**: Access limited to authorized personnel; basic access logging
- **Confidential**: Encryption at rest and in transit; access logging; DLP monitoring
- **Restricted**: Strong encryption; strict need-to-know access; full audit trail; annual access review

## Labeling
All documents and data stores must be labeled with their classification level. Automated classification tools should be used where available.

## De-classification
Data may be de-classified upon approval from the Data Owner and after a risk assessment confirms that de-classification would not expose the organization to unacceptable risk.`,
  },
  {
    id: 'tpl-access-control',
    name: 'Access Control Policy',
    category: 'security',
    framework: 'ISO 27001',
    frameworkMappings: ['ISO 27001:A.9', 'NIST CSF:PR.AC', 'SOC 2:CC6.1', 'ISO 42001:A.8'],
    requiredSections: ['Purpose', 'Scope', 'Access Principles', 'Provisioning', 'Review', 'Termination', 'Privileged Access'],
    isDefault: true,
    content: `# Access Control Policy

## Purpose
Ensure that access to organizational systems, applications, and data is granted on a need-to-know basis and managed throughout the user lifecycle.

## Scope
All information systems, applications, databases, cloud services, and physical facilities owned or operated by the organization.

## Access Principles
1. **Least Privilege**: Users receive only the minimum access needed to perform their role
2. **Need-to-Know**: Access is restricted to information required for job function
3. **Separation of Duties**: Critical functions are divided among different individuals
4. **Zero Trust**: All access requests are verified regardless of source

## Provisioning
1. Access requests require approval from the data owner and the user's manager
2. New accounts are provisioned within 24 hours of approved request
3. Default accounts and passwords are changed before production use
4. Multi-factor authentication is required for all remote and privileged access

## Review
1. Access rights are reviewed quarterly by data owners
2. Privileged access is reviewed monthly
3. Dormant accounts (90+ days inactive) are automatically disabled
4. Access certifications are documented and retained for audit

## Termination
Access is revoked within 4 hours of termination notification and within 24 hours for role changes. All credentials are rotated after access removal.

## Privileged Access
1. Privileged accounts require separate identification
2. Privileged sessions are recorded and monitored
3. Emergency access (break-glass) procedures are documented and tested quarterly`,
  },
  {
    id: 'tpl-incident-response',
    name: 'Incident Response Policy',
    category: 'security',
    framework: 'NIST CSF',
    frameworkMappings: ['NIST CSF:RS.RP', 'ISO 27001:A.16', 'SOC 2:CC7.3', 'ISO 42001:A.6'],
    requiredSections: ['Purpose', 'Scope', 'Incident Classification', 'Response Procedures', 'Communication', 'Post-Incident'],
    isDefault: true,
    content: `# Incident Response Policy

## Purpose
Establish a structured approach to detecting, responding to, and recovering from security incidents to minimize impact and preserve evidence.

## Scope
All security events, incidents, and near-misses affecting organizational systems, data, or operations.

## Incident Classification
1. **P1 - Critical**: Active breach, data exfiltration, ransomware, or system-wide compromise
2. **P2 - High**: Confirmed compromise of a single system or account, malware outbreak
3. **P3 - Medium**: Suspicious activity requiring investigation, policy violations
4. **P4 - Low**: Failed attacks, minor misconfigurations, informational alerts

## Response Procedures
1. **Detection & Analysis**: Identify, validate, and assess the scope of the incident
2. **Containment**: Isolate affected systems to prevent spread (short-term and long-term)
3. **Eradication**: Remove the threat and affected artifacts
4. **Recovery**: Restore systems to normal operation from clean backups
5. **Post-Incident**: Conduct root cause analysis and implement preventive measures

## Communication
- P1/P2 incidents: Notify CISO within 15 minutes, executive team within 1 hour
- P3/P4 incidents: Report through standard ticketing within 4 hours
- External notification per regulatory requirements (e.g., 72-hour GDPR breach notification)

## Post-Incident
All P1/P2 incidents require a formal post-incident review within 5 business days, including root cause analysis, lessons learned, and action items tracked to completion.`,
  },
  {
    id: 'tpl-business-continuity',
    name: 'Business Continuity Policy',
    category: 'operational',
    framework: 'ISO 22301',
    frameworkMappings: ['ISO 22301', 'ISO 27001:A.17', 'SOC 2:CC9.1', 'NIST CSF:RC.RP'],
    requiredSections: ['Purpose', 'Scope', 'Business Impact Analysis', 'Recovery Strategies', 'Plan Maintenance', 'Testing'],
    isDefault: true,
    content: `# Business Continuity Policy

## Purpose
Ensure the organization can continue critical operations during and after a disruption, minimizing financial and reputational impact.

## Scope
All critical business processes, supporting infrastructure, and personnel required to maintain essential services.

## Business Impact Analysis
1. Identify critical business processes and their dependencies
2. Define Recovery Time Objectives (RTO) and Recovery Point Objectives (RPO) for each process
3. Assess financial and operational impact of disruptions
4. Update BIA annually and after significant organizational changes

## Recovery Strategies
1. **Hot Standby**: Real-time failover for mission-critical systems (RTO < 15 minutes)
2. **Warm Standby**: Delayed recovery for important systems (RTO < 4 hours)
3. **Cold Standby**: Manual recovery for non-critical systems (RTO < 24 hours)
4. **Remote Work**: Enable workforce continuity through remote operations

## Plan Maintenance
1. Business continuity plans are reviewed quarterly
2. Contact lists and resource inventories are updated monthly
3. Plan ownership is assigned to specific roles (not individuals)
4. Plans are stored in multiple accessible locations including offline

## Testing
1. Tabletop exercises are conducted quarterly
2. Functional tests are conducted semi-annually
3. Full recovery tests are conducted annually
4. Test results and improvement actions are documented and tracked`,
  },
  {
    id: 'tpl-vendor-management',
    name: 'Vendor Management Policy',
    category: 'compliance',
    framework: 'SOC 2',
    frameworkMappings: ['SOC 2:CC9.2', 'ISO 27001:A.15', 'NIST CSF:ID.SC', 'ISO 42001:A.5'],
    requiredSections: ['Purpose', 'Scope', 'Vendor Risk Assessment', 'Contractual Requirements', 'Monitoring', 'Offboarding'],
    isDefault: true,
    content: `# Vendor Management Policy

## Purpose
Manage risks associated with third-party vendors, suppliers, and service providers to ensure they meet organizational security and compliance requirements.

## Scope
All third-party entities that access, process, store, or transmit organizational data or provide critical services.

## Vendor Risk Assessment
1. Classify vendors by criticality tier (Critical, High, Medium, Low)
2. Complete security questionnaires for all Critical and High vendors
3. Require SOC 2 Type II or ISO 27001 certification for Critical vendors
4. Conduct on-site assessments for Critical vendors annually
5. Perform continuous monitoring of vendor security posture

## Contractual Requirements
All vendor contracts must include:
1. Data protection and confidentiality obligations
2. Right-to-audit clauses
3. Incident notification requirements (within 24 hours)
4. Business continuity and disaster recovery obligations
5. Data return and destruction upon termination
6. Subcontractor approval requirements

## Monitoring
1. Critical vendors: Monthly security posture review
2. High vendors: Quarterly security posture review
3. Medium/Low vendors: Annual risk reassessment
4. All vendors: Continuous monitoring through security ratings platforms

## Offboarding
Upon contract termination, verify: data return/destruction, access revocation, certificate of destruction, and removal from all production systems within 30 days.`,
  },
  {
    id: 'tpl-remote-work',
    name: 'Remote Work Security Policy',
    category: 'operational',
    framework: 'NIST CSF',
    frameworkMappings: ['NIST CSF:PR.AC', 'ISO 27001:A.6.2', 'SOC 2:CC6.6', 'ISO 42001:A.7'],
    requiredSections: ['Purpose', 'Scope', 'Device Requirements', 'Network Security', 'Data Protection', 'Physical Security'],
    isDefault: true,
    content: `# Remote Work Security Policy

## Purpose
Define security requirements for employees and contractors working remotely to protect organizational data and systems.

## Scope
All personnel who access organizational systems, data, or networks from locations outside of company premises.

## Device Requirements
1. Company-managed devices with full-disk encryption and MDM enrollment
2. Personal devices may only access email via approved mobile apps (no data storage)
3. All devices must run current, supported operating systems with automatic updates
4. Endpoint detection and response (EDR) agent required on all company devices

## Network Security
1. VPN required for all access to internal systems
2. Multi-factor authentication required for VPN and all SaaS applications
3. DNS filtering and web proxy enforced on company devices
4. Split tunneling is prohibited for corporate VPN connections

## Data Protection
1. No local storage of Restricted or Confidential data on personal devices
2. Cloud storage must use approved services with encryption enabled
3. Printing of Confidential data at remote locations is prohibited
4. Screen privacy filters required in public spaces

## Physical Security
1. Devices must not be left unattended in public areas
2. Work areas must prevent visual surveillance of screens (shoulder surfing)
3. Secure storage for company devices when not in use
4. Immediate reporting if a device is lost, stolen, or potentially compromised`,
  },
  {
    id: 'tpl-data-retention',
    name: 'Data Retention Policy',
    category: 'compliance',
    framework: 'GDPR',
    frameworkMappings: ['GDPR:Art.5', 'ISO 27001:A.8.3', 'SOC 2:CC6.5', 'HIPAA:164.530'],
    requiredSections: ['Purpose', 'Scope', 'Retention Schedule', 'Disposal Methods', 'Legal Hold', 'Compliance'],
    isDefault: true,
    content: `# Data Retention Policy

## Purpose
Establish requirements for the retention, archival, and secure disposal of organizational data to meet legal, regulatory, and business obligations.

## Scope
All data created, received, maintained, or transmitted by the organization in any format.

## Retention Schedule
1. **Financial Records**: 7 years from fiscal year end
2. **Employee Records**: 7 years after termination
3. **Customer Data**: Duration of relationship + 3 years
4. **Security Logs**: 1 year active, 6 years archived
5. **Email Communications**: 3 years (longer if contract-related)
6. **Incident Records**: 7 years from resolution
7. **Audit Reports**: 7 years from completion
8. **Contract Documents**: 10 years after expiration

## Disposal Methods
1. **Electronic Data**: NIST SP 800-88 compliant sanitization (Clear, Purge, or Destroy)
2. **Paper Documents**: Cross-cut shredding or certified destruction service
3. **Cloud Data**: Vendor-certified deletion with confirmation
4. **Backup Media**: Physical destruction or cryptographic erasure

## Legal Hold
When litigation or regulatory investigation is reasonably anticipated, all potentially relevant data must be preserved regardless of standard retention schedules. The Legal department coordinates holds.

## Compliance
Data custodians are responsible for ensuring their data is retained and disposed of per this schedule. Quarterly audits verify compliance with retention requirements.`,
  },
  {
    id: 'tpl-encryption',
    name: 'Encryption Policy',
    category: 'security',
    framework: 'ISO 27001',
    frameworkMappings: ['ISO 27001:A.10.1', 'NIST CSF:PR.DS', 'SOC 2:CC6.7', 'ISO 42001:A.8'],
    requiredSections: ['Purpose', 'Scope', 'Encryption Standards', 'Key Management', 'Data at Rest', 'Data in Transit'],
    isDefault: true,
    content: `# Encryption Policy

## Purpose
Define encryption standards and requirements to protect the confidentiality and integrity of organizational data at rest, in transit, and in use.

## Scope
All organizational data classified as Confidential or Restricted, all network communications, and all system-to-system communications.

## Encryption Standards
1. **Symmetric Encryption**: AES-256-GCM or ChaCha20-Poly1305
2. **Asymmetric Encryption**: RSA-2048 minimum (RSA-4096 preferred) or ECC P-256+
3. **Hashing**: SHA-256 minimum; SHA-384 or SHA-512 for high-sensitivity data
4. **TLS**: TLS 1.3 minimum; TLS 1.2 permitted only with approved cipher suites
5. **Database Encryption**: TDE with AES-256; column-level for PII/PHI fields

## Key Management
1. Keys are generated using FIPS 140-2 validated cryptographic modules
2. Key storage uses hardware security modules (HSM) or cloud KMS
3. Key rotation: symmetric keys annually, asymmetric keys every 2 years
4. Separation of duties: key custodians cannot also be key administrators
5. Key destruction verified with confirmation logging

## Data at Rest
1. Full-disk encryption on all endpoints and mobile devices
2. Database encryption for all systems storing Confidential/Restricted data
3. Backup encryption with independent key management
4. Cloud storage server-side encryption with customer-managed keys

## Data in Transit
1. TLS required for all external communications
2. mTLS required for service-to-service communication
3. IPsec or WireGuard for site-to-site VPN connections
4. Email encryption (S/MIME or PGP) for Confidential/Restricted content`,
  },
  {
    id: 'tpl-change-management',
    name: 'Change Management Policy',
    category: 'operational',
    framework: 'SOC 2',
    frameworkMappings: ['SOC 2:CC8.1', 'ISO 27001:A.12.1', 'NIST CSF:PR.IP'],
    requiredSections: ['Purpose', 'Scope', 'Change Classification', 'Approval Process', 'Testing', 'Rollback'],
    isDefault: true,
    content: `# Change Management Policy

## Purpose
Control changes to information systems and infrastructure to prevent unauthorized or untested modifications that could impact security, availability, or integrity.

## Scope
All changes to production systems, applications, databases, network infrastructure, and security controls.

## Change Classification
1. **Standard**: Pre-approved, low-risk changes following documented procedures
2. **Normal**: Changes requiring CAB review and approval
3. **Emergency**: Urgent changes to restore service; requires expedited approval

## Approval Process
1. All changes documented in a change request with business justification and risk assessment
2. Standard changes: Auto-approved if following documented procedure
3. Normal changes: CAB review, risk assessment, and approval required before implementation
4. Emergency changes: Post-implementation review within 48 hours

## Testing
1. All changes tested in a non-production environment before deployment
2. Test results documented and attached to the change request
3. User acceptance testing required for application changes
4. Security testing required for infrastructure and access-related changes

## Rollback
1. Documented rollback plan required for all Normal and Emergency changes
2. Rollback tested and validated before implementation
3. Rollback execution within defined time window if validation fails
4. Change marked as failed and root cause analysis initiated`,
  },
  {
    id: 'tpl-ai-governance',
    name: 'AI Governance Policy',
    category: 'compliance',
    framework: 'ISO 42001',
    frameworkMappings: ['ISO 42001', 'NIST AI RMF', 'EU AI Act', 'SOC 2:CC1.5'],
    requiredSections: ['Purpose', 'Scope', 'AI Risk Classification', 'Development Requirements', 'Deployment Controls', 'Monitoring', 'Transparency'],
    isDefault: true,
    content: `# AI Governance Policy

## Purpose
Establish governance frameworks for the responsible development, deployment, and monitoring of artificial intelligence systems in compliance with ISO 42001, NIST AI RMF, and emerging regulations.

## Scope
All AI/ML models, agents, automated decision systems, and generative AI tools used in organizational operations.

## AI Risk Classification
1. **Unacceptable Risk**: AI systems that manipulate behavior or enable mass surveillance (prohibited)
2. **High Risk**: AI used in critical infrastructure, employment decisions, law enforcement (strict controls)
3. **Limited Risk**: AI chatbots, emotion recognition (transparency requirements)
4. **Minimal Risk**: Spam filters, AI in games (voluntary guidelines)

## Development Requirements
1. Bias testing and fairness assessments before training completion
2. Model cards documenting training data, limitations, and intended use
3. Human oversight mechanisms for high-risk applications
4. Red-teaming and adversarial testing before deployment
5. Data provenance tracking for training datasets

## Deployment Controls
1. Model versioning and approval gates before production deployment
2. Output monitoring for hallucinations, bias, and policy violations
3. Kill switch capability for immediate model suspension
4. Rate limiting and abuse detection for generative AI endpoints

## Monitoring
1. Continuous performance monitoring against fairness metrics
2. Drift detection and automated alerting
3. Quarterly model re-validation for high-risk systems
4. Incident tracking specific to AI failures

## Transparency
1. Users are informed when interacting with AI systems
2. Model capabilities and limitations are documented
3. Decision logic is explainable for high-risk applications
4. Annual AI governance audit and board reporting`,
  },
];

/** Get a template by ID */
export function getTemplateById(id: string): PolicyTemplate | undefined {
  return POLICY_TEMPLATES.find((t) => t.id === id);
}

/** Get templates filtered by category */
export function getTemplatesByCategory(category: string): PolicyTemplate[] {
  return POLICY_TEMPLATES.filter((t) => t.category === category);
}

/** Get templates filtered by framework mapping */
export function getTemplatesByFramework(framework: string): PolicyTemplate[] {
  return POLICY_TEMPLATES.filter((t) =>
    t.frameworkMappings?.some((fm) => fm.toUpperCase().includes(framework.toUpperCase())),
  );
}
