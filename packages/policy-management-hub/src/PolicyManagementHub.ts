import type {
  Policy,
  PolicyStatus,
  PolicyCategory,
  ApprovalStatus,
  PolicyChange,
  PolicyControlMapping,
  ApprovalStep,
  ApprovalWorkflow,
  Attestation,
  PolicyTemplate,
  PolicySearchFilter,
  PolicyHubStats,
  PolicyEvent,
  PolicyEventKind,
} from "./types.js";
import { newId, nowIso } from "./types.js";

// ─── Built-in Template Library (50+ templates) ────────────────────────

const BUILT_IN_TEMPLATES: PolicyTemplate[] = [
  { id: "tpl-001", name: "Information Security Policy", category: "security", framework: "ISO 27001", description: "Core information security policy covering confidentiality, integrity, and availability", content: "# Information Security Policy\n\n## 1. Purpose\nEstablish the framework for protecting organizational information assets.\n\n## 2. Scope\nAll employees, contractors, and third parties with access to organizational data.\n\n## 3. Policy Statements\n- All information assets shall be classified and protected accordingly.\n- Access controls shall follow least-privilege principle.\n- Security incidents must be reported within 24 hours.\n\n## 4. Responsibilities\n- CISO: Overall security governance\n- IT: Technical implementation\n- All staff: Compliance", sections: ["Purpose", "Scope", "Policy Statements", "Responsibilities", "Enforcement"], tags: ["security", "iso27001"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-002", name: "Access Control Policy", category: "security", framework: "SOC 2", description: "Defines access control mechanisms and user lifecycle management", content: "# Access Control Policy\n\n## 1. Purpose\nEnsure appropriate access to systems and data based on business needs.\n\n## 2. Policy Statements\n- Access granted on need-to-know and least-privilege basis.\n- Multi-factor authentication required for critical systems.\n- Quarterly access reviews mandatory.\n- Terminated access within 24 hours of employee departure.", sections: ["Purpose", "Policy Statements", "Access Provisioning", "Access Reviews", "Termination"], tags: ["security", "soc2", "access"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-003", name: "Data Classification Policy", category: "security", framework: "ISO 27001", description: "Framework for classifying and protecting data by sensitivity", content: "# Data Classification Policy\n\n## 1. Purpose\nClassify data to ensure appropriate protection levels.\n\n## 2. Classification Levels\n- **Public**: No restriction\n- **Internal**: Employee use only\n- **Confidential**: Limited access\n- **Restricted**: Highly sensitive, encrypted at rest and in transit", sections: ["Purpose", "Classification Levels", "Handling Requirements", "Labeling", "Disposal"], tags: ["security", "data", "classification"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-004", name: "Acceptable Use Policy", category: "operational", framework: "SOC 2", description: "Defines acceptable use of organizational IT resources", content: "# Acceptable Use Policy\n\n## 1. Purpose\nSet expectations for responsible use of IT resources.\n\n## 2. Policy Statements\n- Systems used primarily for business purposes.\n- No unauthorized software installation.\n- No sharing of credentials.\n- Personal use must not impact productivity or security.", sections: ["Purpose", "Scope", "Policy Statements", "Monitoring", "Enforcement"], tags: ["operational", "acceptable-use"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-005", name: "Incident Response Policy", category: "security", framework: "NIST CSF", description: "Defines incident detection, response, and recovery procedures", content: "# Incident Response Policy\n\n## 1. Purpose\nEnsure effective detection, response, and recovery from security incidents.\n\n## 2. Incident Classification\n- **Critical**: Active breach, data exfiltration\n- **High**: Confirmed intrusion attempt\n- **Medium**: Policy violation\n- **Low**: Suspicious activity\n\n## 3. Response Procedures\n1. Detection and Analysis\n2. Containment\n3. Eradication\n4. Recovery\n5. Lessons Learned", sections: ["Purpose", "Incident Classification", "Response Procedures", "Communication", "Post-Incident Review"], tags: ["security", "incident-response", "nist"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-006", name: "Business Continuity Policy", category: "operational", framework: "ISO 22301", description: "Ensures business operations continue during disruptions", content: "# Business Continuity Policy\n\n## 1. Purpose\nMaintain critical business operations during and after disruptions.\n\n## 2. BCP Requirements\n- RTO and RPO defined for all critical systems.\n- Annual BCP testing required.\n- Backup procedures documented and tested quarterly.", sections: ["Purpose", "Scope", "BCP Requirements", "Testing", "Roles"], tags: ["operational", "bcp", "resilience"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-007", name: "Data Retention Policy", category: "compliance", framework: "GDPR", description: "Defines data retention periods and disposal procedures", content: "# Data Retention Policy\n\n## 1. Purpose\nComply with legal and regulatory data retention requirements.\n\n## 2. Retention Schedule\n- Financial records: 7 years\n- Employee records: 7 years post-termination\n- Customer data: Duration of relationship + 3 years\n- Security logs: 1 year", sections: ["Purpose", "Retention Schedule", "Disposal Methods", "Legal Hold"], tags: ["compliance", "data-retention", "gdpr"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-008", name: "Privacy Policy", category: "privacy", framework: "GDPR", description: "Covers personal data processing and individual rights", content: "# Privacy Policy\n\n## 1. Purpose\nDefine how personal data is collected, processed, and protected.\n\n## 2. Data Subject Rights\n- Right of access\n- Right to rectification\n- Right to erasure\n- Right to data portability\n- Right to object\n\n## 3. Lawful Basis\n- Consent\n- Contract performance\n- Legal obligation\n- Legitimate interests", sections: ["Purpose", "Data Processing", "Data Subject Rights", "Lawful Basis", "Data Protection"], tags: ["privacy", "gdpr", "data-protection"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-009", name: "Employee Handbook Policy", category: "hr", framework: "General", description: "General employment policies and procedures", content: "# Employee Handbook Policy\n\n## 1. Purpose\nSet expectations for employee conduct and workplace policies.\n\n## 2. Key Areas\n- Code of Conduct\n- Anti-harassment\n- Remote Work\n- PTO and Leave\n- Performance Reviews", sections: ["Code of Conduct", "Workplace", "Benefits", "Performance", "Termination"], tags: ["hr", "employment"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-010", name: "Vendor Management Policy", category: "compliance", framework: "SOC 2", description: "Policies for managing third-party vendor risk", content: "# Vendor Management Policy\n\n## 1. Purpose\nMitigate risks associated with third-party vendors.\n\n## 2. Requirements\n- Due diligence before onboarding\n- Annual security assessments for critical vendors\n- Contractual security requirements\n- Continuous monitoring for high-risk vendors", sections: ["Purpose", "Vendor Assessment", "Contract Requirements", "Monitoring", "Offboarding"], tags: ["compliance", "vendor", "third-party"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-011", name: "Encryption Policy", category: "security", framework: "ISO 27001", description: "Standards for encrypting data at rest and in transit", content: "# Encryption Policy\n\n## 1. Purpose\nEnsure sensitive data is protected through encryption.\n\n## 2. Standards\n- AES-256 for data at rest\n- TLS 1.3 for data in transit\n- RSA-2048 minimum for key exchange\n- Hardware security modules for key storage", sections: ["Purpose", "Encryption Standards", "Key Management", "Implementation"], tags: ["security", "encryption"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-012", name: "Vulnerability Management Policy", category: "security", framework: "NIST CSF", description: "Process for identifying and remediating vulnerabilities", content: "# Vulnerability Management Policy\n\n## 1. Purpose\nSystematic approach to identifying and remediating vulnerabilities.\n\n## 2. Scanning Schedule\n- Critical assets: Weekly\n- All systems: Monthly\n- External-facing: Weekly\n- Code: Every CI/CD build", sections: ["Purpose", "Scanning", "Prioritization", "Remediation", "Verification"], tags: ["security", "vulnerability", "patching"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-013", name: "Change Management Policy", category: "it", framework: "ITIL", description: "Controls for managing changes to IT infrastructure", content: "# Change Management Policy\n\n## 1. Purpose\nControl changes to minimize disruption.\n\n## 2. Change Types\n- Standard: Pre-approved\n- Normal: Requires CAB review\n- Emergency: Expedited approval\n\n## 3. Process\n1. Request\n2. Assess\n3. Approve\n4. Implement\n5. Review", sections: ["Purpose", "Change Types", "Approval Process", "Implementation", "Review"], tags: ["it", "change-management"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-014", name: "Network Security Policy", category: "security", framework: "ISO 27001", description: "Controls for securing network infrastructure", content: "# Network Security Policy\n\n## 1. Purpose\nProtect network infrastructure from unauthorized access.\n\n## 2. Controls\n- Network segmentation\n- Firewall rules review quarterly\n- IDS/IPS monitoring\n- VPN required for remote access\n- Zero-trust architecture", sections: ["Purpose", "Network Architecture", "Firewall Management", "Monitoring", "Remote Access"], tags: ["security", "network"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-015", name: "Physical Security Policy", category: "security", framework: "ISO 27001", description: "Physical access controls and facility security", content: "# Physical Security Policy\n\n## 1. Purpose\nProtect physical assets and facilities.\n\n## 2. Controls\n- Badge access for all facilities\n- Visitor logging and escort\n- CCTV monitoring\n- Server room restricted access\n- Clean desk policy", sections: ["Purpose", "Access Control", "Visitor Management", "Monitoring", "Secure Areas"], tags: ["security", "physical"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-016", name: "Secure Development Policy", category: "it", framework: "SOC 2", description: "Security requirements for software development", content: "# Secure Development Policy\n\n## 1. Purpose\nIntegrate security into the software development lifecycle.\n\n## 2. Requirements\n- Threat modeling for new features\n- SAST/DAST in CI/CD pipeline\n- Dependency scanning\n- Code review for security-sensitive changes\n- Security training for developers", sections: ["Purpose", "SDLC Integration", "Code Review", "Testing", "Deployment"], tags: ["it", "secure-development", "devsecops"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-017", name: "Cloud Security Policy", category: "security", framework: "CSA CCM", description: "Security controls for cloud environments", content: "# Cloud Security Policy\n\n## 1. Purpose\nEnsure secure use of cloud services.\n\n## 2. Requirements\n- Cloud security architecture review\n- IAM best practices\n- Encryption of cloud data\n- Logging and monitoring\n- Cost governance", sections: ["Purpose", "Architecture", "IAM", "Data Protection", "Monitoring"], tags: ["security", "cloud"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-018", name: "Data Loss Prevention Policy", category: "security", framework: "PCI DSS", description: "Controls to prevent unauthorized data exfiltration", content: "# Data Loss Prevention Policy\n\n## 1. Purpose\nPrevent unauthorized transfer of sensitive data.\n\n## 2. Controls\n- DLP monitoring on email and web\n- USB blocking\n- Watermarking sensitive documents\n- Data egress monitoring\n- User behavior analytics", sections: ["Purpose", "Controls", "Monitoring", "Incident Response", "Enforcement"], tags: ["security", "dlp", "data-protection"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-019", name: "Identity and Access Management Policy", category: "security", framework: "NIST CSF", description: "Framework for managing digital identities and access", content: "# IAM Policy\n\n## 1. Purpose\nManage identities and access across the organization.\n\n## 2. Requirements\n- Centralized identity provider\n- MFA for all users\n- Privileged access management\n- Regular access certification\n- Just-in-time access for admin", sections: ["Purpose", "Identity Lifecycle", "Authentication", "Authorization", "Audit"], tags: ["security", "iam"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-020", name: "Monitoring and Logging Policy", category: "security", framework: "SOC 2", description: "Requirements for security monitoring and log management", content: "# Monitoring and Logging Policy\n\n## 1. Purpose\nEnsure comprehensive security monitoring.\n\n## 2. Requirements\n- Centralized log aggregation\n- 90-day log retention minimum\n- Real-time alerting on critical events\n- Log integrity protection\n- Regular review of access logs", sections: ["Purpose", "Log Collection", "Retention", "Alerting", "Review"], tags: ["security", "monitoring", "logging"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-021", name: "Asset Management Policy", category: "it", framework: "ISO 27001", description: "Inventory and lifecycle management for IT assets", content: "# Asset Management Policy\n\n## 1. Purpose\nTrack and manage all IT assets.\n\n## 2. Requirements\n- Complete asset inventory\n- Asset lifecycle tracking\n- Configuration management\n- Disposal procedures", sections: ["Purpose", "Inventory", "Lifecycle", "Configuration", "Disposal"], tags: ["it", "asset-management"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-022", name: "Backup and Recovery Policy", category: "it", framework: "ISO 22301", description: "Data backup and recovery procedures", content: "# Backup and Recovery Policy\n\n## 1. Purpose\nEnsure data can be recovered after loss.\n\n## 2. Requirements\n- Daily incremental backups\n- Weekly full backups\n- Offsite backup storage\n- Quarterly recovery testing\n- Immutable backup copies", sections: ["Purpose", "Backup Schedule", "Storage", "Testing", "Recovery"], tags: ["it", "backup", "recovery"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-023", name: "Anti-Corruption Policy", category: "compliance", framework: "FCPA", description: "Anti-bribery and anti-corruption controls", content: "# Anti-Corruption Policy\n\n## 1. Purpose\nPrevent bribery and corruption.\n\n## 2. Requirements\n- No facilitation payments\n- Gift limits documented\n- Due diligence on intermediaries\n- Training for all employees\n- Whistleblower protection", sections: ["Purpose", "Prohibited Conduct", "Gifts and Entertainment", "Third Parties", "Reporting"], tags: ["compliance", "anti-corruption", "fcpa"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-024", name: "Conflict of Interest Policy", category: "hr", framework: "General", description: "Managing conflicts of interest in business relationships", content: "# Conflict of Interest Policy\n\n## 1. Purpose\nIdentify and manage potential conflicts of interest.\n\n## 2. Requirements\n- Annual disclosure of interests\n- Recusal from related decisions\n- Board notification of material conflicts\n- External relationship review", sections: ["Purpose", "Disclosure", "Management", "Board Oversight", "Enforcement"], tags: ["hr", "governance"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-025", name: "Whistleblower Policy", category: "compliance", framework: "SOX", description: "Protections and procedures for reporting misconduct", content: "# Whistleblower Policy\n\n## 1. Purpose\nEncourage reporting of unethical behavior without fear of retaliation.\n\n## 2. Reporting Channels\n- Anonymous hotline\n- Email to compliance officer\n- Direct to board audit committee\n\n## 3. Protections\n- No retaliation\n- Confidential handling\n- Independent investigation", sections: ["Purpose", "Reporting Channels", "Investigation", "Protections", "Follow-up"], tags: ["compliance", "whistleblower"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-026", name: "Code of Ethics Policy", category: "hr", framework: "General", description: "Ethical standards for all employees", content: "# Code of Ethics\n\n## 1. Purpose\nEstablish ethical standards for business conduct.\n\n## 2. Standards\n- Integrity in all dealings\n- Respect for others\n- Fair competition\n- Confidentiality protection\n- Reporting obligations", sections: ["Purpose", "Standards", "Conflicts", "Compliance", "Consequences"], tags: ["hr", "ethics"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-027", name: "Travel Security Policy", category: "safety", framework: "General", description: "Security requirements for business travel", content: "# Travel Security Policy\n\n## 1. Purpose\nEnsure employee safety during business travel.\n\n## 2. Requirements\n- Travel registration\n- Security briefings for high-risk destinations\n- Emergency contact procedures\n- Data protection while traveling", sections: ["Purpose", "Pre-Travel", "In-Transit", "At Destination", "Post-Travel"], tags: ["safety", "travel"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-028", name: "BYOD Policy", category: "it", framework: "SOC 2", description: "Bring your own device security requirements", content: "# BYOD Policy\n\n## 1. Purpose\nAllow personal device use while maintaining security.\n\n## 2. Requirements\n- Device enrollment in MDM\n- Minimum OS version\n- Remote wipe capability\n- Separate work profile\n- No rooted/jailbroken devices", sections: ["Purpose", "Eligibility", "Security Requirements", "Support", "Termination"], tags: ["it", "byod", "mobile"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-029", name: "Third-Party Data Sharing Policy", category: "privacy", framework: "GDPR", description: "Controls for sharing data with third parties", content: "# Third-Party Data Sharing Policy\n\n## 1. Purpose\nEnsure compliant data sharing with external parties.\n\n## 2. Requirements\n- Data processing agreements required\n- Privacy impact assessments\n- Encryption in transit\n- Contractual obligations\n- Regular audits", sections: ["Purpose", "Assessment", "Agreements", "Safeguards", "Monitoring"], tags: ["privacy", "third-party", "data-sharing"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-030", name: "Cloud Data Residency Policy", category: "privacy", framework: "GDPR", description: "Requirements for data location and cross-border transfers", content: "# Data Residency Policy\n\n## 1. Purpose\nEnsure data is stored and processed in compliant locations.\n\n## 2. Requirements\n- Data residency mapping\n- Cross-border transfer assessments\n- Standard contractual clauses\n- Adequacy decisions verification", sections: ["Purpose", "Data Location", "Cross-Border Transfers", "Safeguards", "Monitoring"], tags: ["privacy", "data-residency"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-031", name: "SOC 2 Information Security Policy", category: "security", framework: "SOC 2", description: "Complete information security policy for SOC 2 compliance", content: "# SOC 2 Information Security Policy\n\n## 1. Purpose\nDemonstrate SOC 2 Trust Service Criteria compliance.\n\n## 2. Controls\n- Logical access controls\n- System operations\n- Change management\n- Risk mitigation\n- Incident response", sections: ["Purpose", "Trust Criteria", "Controls", "Monitoring", "Reporting"], tags: ["security", "soc2"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-032", name: "HIPAA Privacy Policy", category: "privacy", framework: "HIPAA", description: "PHI protection and privacy requirements", content: "# HIPAA Privacy Policy\n\n## 1. Purpose\nProtect patient health information.\n\n## 2. Requirements\n- Minimum necessary standard\n- Patient rights\n- Business associate agreements\n- Breach notification\n- Training requirements", sections: ["Purpose", "PHI Handling", "Patient Rights", "BAAs", "Breach Response"], tags: ["privacy", "hipaa", "healthcare"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-033", name: "HIPAA Security Policy", category: "security", framework: "HIPAA", description: "Technical safeguards for electronic PHI", content: "# HIPAA Security Policy\n\n## 1. Purpose\nProtect electronic PHI through technical safeguards.\n\n## 2. Safeguards\n- Access controls\n- Audit controls\n- Integrity controls\n- Transmission security\n- Workstation security", sections: ["Purpose", "Technical Safeguards", "Administrative Safeguards", "Physical Safeguards", "Compliance"], tags: ["security", "hipaa", "ephi"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-034", name: "PCI DSS Policy", category: "security", framework: "PCI DSS", description: "Payment card data protection requirements", content: "# PCI DSS Policy\n\n## 1. Purpose\nProtect cardholder data.\n\n## 2. Requirements\n- Network segmentation\n- Access control\n- Encryption of cardholder data\n- Regular testing\n- Vulnerability management", sections: ["Purpose", "Cardholder Data", "Network Security", "Access Control", "Testing"], tags: ["security", "pci", "payment"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-035", name: "Risk Assessment Policy", category: "compliance", framework: "ISO 27001", description: "Framework for organizational risk assessments", content: "# Risk Assessment Policy\n\n## 1. Purpose\nSystematic approach to identifying and managing risks.\n\n## 2. Process\n1. Risk identification\n2. Risk analysis\n3. Risk evaluation\n4. Risk treatment\n5. Monitoring and review", sections: ["Purpose", "Methodology", "Frequency", "Roles", "Reporting"], tags: ["compliance", "risk", "assessment"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-036", name: "Internal Audit Policy", category: "compliance", framework: "ISO 27001", description: "Internal audit program requirements", content: "# Internal Audit Policy\n\n## 1. Purpose\nIndependent verification of control effectiveness.\n\n## 2. Program\n- Annual audit plan\n- Risk-based audit scheduling\n- Qualified auditors\n- Findings tracking\n- Management reporting", sections: ["Purpose", "Audit Program", "Execution", "Reporting", "Follow-up"], tags: ["compliance", "audit"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-037", name: "Key Performance Indicators Policy", category: "operational", framework: "General", description: "Framework for defining and tracking KPIs", content: "# KPI Policy\n\n## 1. Purpose\nEstablish measurable indicators for organizational performance.\n\n## 2. Requirements\n- Aligned with business objectives\n- SMART criteria\n- Regular review cycles\n- Dashboard reporting", sections: ["Purpose", "Selection Criteria", "Review Process", "Reporting", "Improvement"], tags: ["operational", "kpi", "performance"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-038", name: "Configuration Management Policy", category: "it", framework: "ITIL", description: "Managing system configurations and baselines", content: "# Configuration Management Policy\n\n## 1. Purpose\nMaintain accurate records of IT configurations.\n\n## 2. Requirements\n- Configuration baseline\n- Change tracking\n- CMDB maintenance\n- Configuration audits\n- Automation where possible", sections: ["Purpose", "Baselines", "Tracking", "Auditing", "Tools"], tags: ["it", "configuration"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-039", name: "Capacity Management Policy", category: "it", framework: "ITIL", description: "Ensuring IT capacity meets business demand", content: "# Capacity Management Policy\n\n## 1. Purpose\nEnsure IT resources meet current and future demand.\n\n## 2. Requirements\n- Performance monitoring\n- Demand forecasting\n- Capacity planning\n- Cost optimization\n- Regular reviews", sections: ["Purpose", "Monitoring", "Planning", "Optimization", "Review"], tags: ["it", "capacity"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-040", name: "Incident Management Policy", category: "it", framework: "ITIL", description: "Managing IT service disruptions", content: "# Incident Management Policy\n\n## 1. Purpose\nRestore normal service operation quickly.\n\n## 2. Process\n1. Detection\n2. Categorization\n3. Prioritization\n4. Resolution\n5. Closure\n6. Review", sections: ["Purpose", "Process", "Escalation", "Communication", "Reporting"], tags: ["it", "incident"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-041", name: "Problem Management Policy", category: "it", framework: "ITIL", description: "Root cause analysis and prevention", content: "# Problem Management Policy\n\n## 1. Purpose\nIdentify and resolve root causes of incidents.\n\n## 2. Process\n1. Problem detection\n2. Root cause analysis\n3. Workaround identification\n4. Resolution\n5. Knowledge management", sections: ["Purpose", "Detection", "Analysis", "Resolution", "Prevention"], tags: ["it", "problem"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-042", name: "Release Management Policy", category: "it", framework: "ITIL", description: "Planning and controlling software releases", content: "# Release Management Policy\n\n## 1. Purpose\nPlan and manage software releases.\n\n## 2. Requirements\n- Release planning\n- Testing requirements\n- Rollback procedures\n- Post-release verification\n- Release calendar", sections: ["Purpose", "Planning", "Testing", "Deployment", "Review"], tags: ["it", "release"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-043", name: "Financial Controls Policy", category: "financial", framework: "SOX", description: "Internal financial controls and reporting", content: "# Financial Controls Policy\n\n## 1. Purpose\nEnsure accuracy of financial reporting.\n\n## 2. Controls\n- Segregation of duties\n- Authorization levels\n- Reconciliation procedures\n- Audit trail requirements\n- Financial review committees", sections: ["Purpose", "Controls", "Authorization", "Reporting", "Compliance"], tags: ["financial", "controls"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-044", name: "Procurement Policy", category: "financial", framework: "General", description: "Purchasing and procurement procedures", content: "# Procurement Policy\n\n## 1. Purpose\nStandardize procurement processes.\n\n## 2. Requirements\n- Approval thresholds\n- Vendor evaluation\n- Contract management\n- Budget verification\n- Value-for-money assessment", sections: ["Purpose", "Process", "Approval", "Vendor Selection", "Contract"], tags: ["financial", "procurement"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-045", name: "Expense Reimbursement Policy", category: "financial", framework: "General", description: "Employee expense reporting requirements", content: "# Expense Reimbursement Policy\n\n## 1. Purpose\nDefine acceptable expense practices.\n\n## 2. Requirements\n- Receipt required for all expenses\n- Approval workflow\n- Spending limits\n- Prohibited expenses\n- Timely submission", sections: ["Purpose", "Eligibility", "Process", "Limits", "Compliance"], tags: ["financial", "expense"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-046", name: "Workplace Safety Policy", category: "safety", framework: "OSHA", description: "Workplace health and safety requirements", content: "# Workplace Safety Policy\n\n## 1. Purpose\nEnsure a safe working environment.\n\n## 2. Requirements\n- Risk assessments\n- Emergency procedures\n- Safety training\n- Incident reporting\n- Equipment maintenance", sections: ["Purpose", "Hazards", "Procedures", "Training", "Reporting"], tags: ["safety", "workplace"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-047", name: "Remote Work Policy", category: "hr", framework: "General", description: "Security and productivity requirements for remote work", content: "# Remote Work Policy\n\n## 1. Purpose\nEnable secure remote work.\n\n## 2. Requirements\n- VPN usage\n- Secure home network\n- Dedicated workspace\n- Data protection\n- Availability expectations", sections: ["Purpose", "Eligibility", "Security", "Productivity", "Support"], tags: ["hr", "remote-work"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-048", name: "Training and Awareness Policy", category: "hr", framework: "SOC 2", description: "Security awareness training requirements", content: "# Training and Awareness Policy\n\n## 1. Purpose\nEnsure all staff understand security responsibilities.\n\n## 2. Requirements\n- Onboarding security training\n- Annual refresher\n- Role-specific training\n- Phishing awareness\n- Completion tracking", sections: ["Purpose", "Training Program", "Delivery", "Tracking", "Effectiveness"], tags: ["hr", "training", "awareness"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-049", name: "Termination Procedures Policy", category: "hr", framework: "SOC 2", description: "Offboarding and access revocation procedures", content: "# Termination Procedures Policy\n\n## 1. Purpose\nEnsure secure employee offboarding.\n\n## 2. Process\n1. HR notification\n2. Access revocation\n3. Asset return\n4. Knowledge transfer\n5. Exit interview", sections: ["Purpose", "Process", "Access Revocation", "Asset Recovery", "Knowledge Transfer"], tags: ["hr", "termination", "offboarding"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-050", name: "Records Management Policy", category: "compliance", framework: "ISO 27001", description: "Managing organizational records and documentation", content: "# Records Management Policy\n\n## 1. Purpose\nSystematic management of business records.\n\n## 2. Requirements\n- Records classification\n- Retention schedules\n- Storage and retrieval\n- Disposal procedures\n- Legal hold process", sections: ["Purpose", "Classification", "Retention", "Storage", "Disposal"], tags: ["compliance", "records"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-051", name: "Business Ethics Policy", category: "compliance", framework: "General", description: "Ethical business conduct requirements", content: "# Business Ethics Policy\n\n## 1. Purpose\nMaintain high ethical standards in business dealings.\n\n## 2. Standards\n- Fair competition\n- Honest representation\n- Conflict avoidance\n- Regulatory compliance\n- Reporting mechanisms", sections: ["Purpose", "Standards", "Competition", "Reporting", "Enforcement"], tags: ["compliance", "ethics"], isDefault: true, version: 1, createdAt: nowIso() },
  { id: "tpl-052", name: "Environmental Policy", category: "operational", framework: "ISO 14001", description: "Environmental responsibility requirements", content: "# Environmental Policy\n\n## 1. Purpose\nMinimize environmental impact.\n\n## 2. Commitments\n- Waste reduction\n- Energy efficiency\n- Sustainable procurement\n- Compliance monitoring\n- Continuous improvement", sections: ["Purpose", "Commitments", "Targets", "Monitoring", "Improvement"], tags: ["operational", "environmental"], isDefault: true, version: 1, createdAt: nowIso() },
];

// ─── PolicyManagementHub ──────────────────────────────────────────────

export class PolicyManagementHub {
  private policies: Map<string, Policy> = new Map();
  private workflows: Map<string, ApprovalWorkflow> = new Map();
  private templates: Map<string, PolicyTemplate> = new Map();
  private events: PolicyEvent[] = [];

  constructor() {
    for (const tpl of BUILT_IN_TEMPLATES) {
      this.templates.set(tpl.id, { ...tpl });
    }
  }

  // ─── Policy CRUD ──────────────────────────────────────────────────

  createPolicy(input: {
    title: string;
    category: PolicyCategory;
    content: string;
    summary: string;
    owner: string;
    department: string;
    framework: string;
    effectiveDate: string;
    reviewDate: string;
    tags?: string[];
    templateId?: string;
  }): Policy {
    const id = newId();
    const now = nowIso();
    const slug = input.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");

    let content = input.content;
    if (input.templateId) {
      const tpl = this.templates.get(input.templateId);
      if (tpl) content = tpl.content;
    }

    const policy: Policy = {
      id,
      title: input.title,
      slug,
      category: input.category,
      status: "draft",
      version: 1,
      content,
      summary: input.summary,
      owner: input.owner,
      department: input.department,
      framework: input.framework,
      effectiveDate: input.effectiveDate,
      reviewDate: input.reviewDate,
      nextReviewDate: input.reviewDate,
      approvalChain: [],
      changeHistory: [
        {
          id: newId(),
          version: 1,
          changedBy: input.owner,
          changedAt: now,
          summary: "Initial policy creation",
        },
      ],
      attestations: [],
      controlMappings: [],
      evidenceIds: [],
      tags: input.tags ?? [],
      createdAt: now,
      updatedAt: now,
    };

    this.policies.set(id, policy);
    this.emit("policy_created", id, input.owner, {});
    return policy;
  }

  getPolicy(id: string): Policy | undefined {
    return this.policies.get(id);
  }

  listPolicies(): Policy[] {
    return Array.from(this.policies.values());
  }

  updatePolicy(id: string, input: { title?: string; content?: string; summary?: string; category?: PolicyCategory; tags?: string[]; changedBy: string }): Policy {
    const policy = this.policies.get(id);
    if (!policy) throw new Error(`Policy ${id} not found`);

    const now = nowIso();
    const newVersion = policy.version + 1;

    if (input.title) policy.title = input.title;
    if (input.content) {
      policy.changeHistory.push({
        id: newId(),
        version: newVersion,
        changedBy: input.changedBy,
        changedAt: now,
        summary: "Content updated",
        previousContent: policy.content,
        diff: `v${policy.version} -> v${newVersion}`,
      });
      policy.content = input.content;
      policy.version = newVersion;
    }
    if (input.summary) policy.summary = input.summary;
    if (input.category) policy.category = input.category;
    if (input.tags) policy.tags = input.tags;
    policy.updatedAt = now;

    return policy;
  }

  deletePolicy(id: string): boolean {
    return this.policies.delete(id);
  }

  // ─── Approval Workflow ────────────────────────────────────────────

  initiateApproval(policyId: string, steps: Array<{ assigneeId: string; assigneeName: string; role: string; deadline?: string }>, initiatedBy: string): ApprovalWorkflow {
    const policy = this.policies.get(policyId);
    if (!policy) throw new Error(`Policy ${policyId} not found`);

    const workflowSteps: ApprovalStep[] = steps.map((s, i) => ({
      id: newId(),
      order: i + 1,
      assigneeId: s.assigneeId,
      assigneeName: s.assigneeName,
      role: s.role,
      status: "pending",
      deadline: s.deadline,
    }));

    const workflow: ApprovalWorkflow = {
      id: newId(),
      policyId,
      steps: workflowSteps,
      currentStep: 0,
      initiatedBy,
      initiatedAt: nowIso(),
      isComplete: false,
    };

    this.workflows.set(workflow.id, workflow);
    policy.approvalChain = workflowSteps;
    policy.status = "under_review";
    this.emit("policy_submitted_for_review", policyId, initiatedBy, { workflowId: workflow.id });

    return workflow;
  }

  approveStep(workflowId: string, stepId: string, assigneeId: string, comments?: string): ApprovalWorkflow {
    const workflow = this.workflows.get(workflowId);
    if (!workflow) throw new Error(`Workflow ${workflowId} not found`);

    const step = workflow.steps.find((s) => s.id === stepId);
    if (!step) throw new Error(`Step ${stepId} not found`);
    if (step.assigneeId !== assigneeId) throw new Error(`Only assigned user ${step.assigneeId} can approve this step`);

    step.status = "approved";
    step.comments = comments;
    step.decidedAt = nowIso();

    this.emit("approval_step_completed", workflow.policyId, assigneeId, { stepId, approved: true });

    const policy = this.policies.get(workflow.policyId);
    if (policy) {
      const idx = policy.approvalChain.findIndex((s) => s.id === stepId);
      if (idx >= 0) policy.approvalChain[idx] = { ...step };
    }

    workflow.currentStep++;
    if (workflow.currentStep >= workflow.steps.length) {
      workflow.isComplete = true;
      workflow.completedAt = nowIso();
      if (policy) {
        policy.status = "approved";
        policy.updatedAt = nowIso();
      }
      this.emit("policy_approved", workflow.policyId, assigneeId, { workflowId });
    }

    return workflow;
  }

  rejectStep(workflowId: string, stepId: string, assigneeId: string, comments: string): ApprovalWorkflow {
    const workflow = this.workflows.get(workflowId);
    if (!workflow) throw new Error(`Workflow ${workflowId} not found`);

    const step = workflow.steps.find((s) => s.id === stepId);
    if (!step) throw new Error(`Step ${stepId} not found`);
    if (step.assigneeId !== assigneeId) throw new Error(`Only assigned user can reject this step`);

    step.status = "rejected";
    step.comments = comments;
    step.decidedAt = nowIso();

    const policy = this.policies.get(workflow.policyId);
    if (policy) {
      policy.status = "revision_needed";
      policy.updatedAt = nowIso();
      const idx = policy.approvalChain.findIndex((s) => s.id === stepId);
      if (idx >= 0) policy.approvalChain[idx] = { ...step };
    }

    this.emit("policy_rejected", workflow.policyId, assigneeId, { stepId, comments });
    return workflow;
  }

  // ─── Publishing ───────────────────────────────────────────────────

  publishPolicy(policyId: string, publishedBy: string): Policy {
    const policy = this.policies.get(policyId);
    if (!policy) throw new Error(`Policy ${policyId} not found`);
    if (policy.status !== "approved") throw new Error(`Policy must be approved before publishing (current: ${policy.status})`);

    policy.status = "published";
    policy.publishedAt = nowIso();
    policy.updatedAt = nowIso();

    this.emit("policy_published", policyId, publishedBy, { version: policy.version });
    return policy;
  }

  // ─── Attestation ──────────────────────────────────────────────────

  assignAttestation(policyId: string, employees: Array<{ employeeId: string; employeeName: string; employeeEmail: string; department: string }>, dueDate: string): Attestation[] {
    const policy = this.policies.get(policyId);
    if (!policy) throw new Error(`Policy ${policyId} not found`);

    const now = nowIso();
    const attestations: Attestation[] = employees.map((emp) => {
      const attestation: Attestation = {
        id: newId(),
        policyId,
        policyVersion: policy.version,
        employeeId: emp.employeeId,
        employeeName: emp.employeeName,
        employeeEmail: emp.employeeEmail,
        department: emp.department,
        status: "pending",
        dueDate,
        reminderCount: 0,
        createdAt: now,
      };
      policy.attestations.push(attestation);
      this.emit("attestation_assigned", policyId, emp.employeeId, { dueDate });
      return attestation;
    });

    return attestations;
  }

  completeAttestation(policyId: string, employeeId: string): Attestation | undefined {
    const policy = this.policies.get(policyId);
    if (!policy) throw new Error(`Policy ${policyId} not found`);

    const attestation = policy.attestations.find(
      (a) => a.employeeId === employeeId && a.status === "pending"
    );
    if (!attestation) return undefined;

    attestation.status = "attested";
    attestation.attestedAt = nowIso();
    attestation.policyVersion = policy.version;

    this.emit("attestation_completed", policyId, employeeId, { attestationId: attestation.id });

    const pendingCount = policy.attestations.filter((a) => a.status === "pending").length;
    if (pendingCount === 0) {
      policy.status = "under_attestation";
      policy.updatedAt = nowIso();
    }

    return attestation;
  }

  // ─── Control Mapping ──────────────────────────────────────────────

  mapToControl(policyId: string, controlId: string, framework: string, controlTitle: string, mappedBy: string): void {
    const policy = this.policies.get(policyId);
    if (!policy) throw new Error(`Policy ${policyId} not found`);

    const exists = policy.controlMappings.some((m) => m.controlId === controlId && m.framework === framework);
    if (exists) return;

    policy.controlMappings.push({
      controlId,
      framework,
      controlTitle,
      mappedAt: nowIso(),
      mappedBy,
    });
  }

  // ─── Evidence Linkage ─────────────────────────────────────────────

  linkEvidence(policyId: string, evidenceId: string): void {
    const policy = this.policies.get(policyId);
    if (!policy) throw new Error(`Policy ${policyId} not found`);
    if (!policy.evidenceIds.includes(evidenceId)) {
      policy.evidenceIds.push(evidenceId);
    }
  }

  // ─── Templates ────────────────────────────────────────────────────

  getTemplates(): PolicyTemplate[] {
    return Array.from(this.templates.values());
  }

  getTemplateById(id: string): PolicyTemplate | undefined {
    return this.templates.get(id);
  }

  getTemplatesByCategory(category: PolicyCategory): PolicyTemplate[] {
    return Array.from(this.templates.values()).filter((t) => t.category === category);
  }

  getTemplatesByFramework(framework: string): PolicyTemplate[] {
    return Array.from(this.templates.values()).filter((t) => t.framework === framework);
  }

  // ─── Search & Filter ──────────────────────────────────────────────

  searchPolicies(filter: PolicySearchFilter): Policy[] {
    let results = Array.from(this.policies.values());

    if (filter.query) {
      const q = filter.query.toLowerCase();
      results = results.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.summary.toLowerCase().includes(q) ||
          p.content.toLowerCase().includes(q) ||
          p.tags.some((t) => t.toLowerCase().includes(q))
      );
    }
    if (filter.status && filter.status.length > 0) {
      results = results.filter((p) => filter.status!.includes(p.status));
    }
    if (filter.category && filter.category.length > 0) {
      results = results.filter((p) => filter.category!.includes(p.category));
    }
    if (filter.framework && filter.framework.length > 0) {
      results = results.filter((p) => filter.framework!.includes(p.framework));
    }
    if (filter.owner) {
      results = results.filter((p) => p.owner === filter.owner);
    }
    if (filter.department) {
      results = results.filter((p) => p.department === filter.department);
    }
    if (filter.tags && filter.tags.length > 0) {
      results = results.filter((p) => filter.tags!.some((t) => p.tags.includes(t)));
    }
    if (filter.effectiveBefore) {
      results = results.filter((p) => p.effectiveDate <= filter.effectiveBefore!);
    }
    if (filter.effectiveAfter) {
      results = results.filter((p) => p.effectiveDate >= filter.effectiveAfter!);
    }
    if (filter.reviewBefore) {
      results = results.filter((p) => p.reviewDate <= filter.reviewBefore!);
    }
    if (filter.reviewAfter) {
      results = results.filter((p) => p.reviewDate >= filter.reviewAfter!);
    }

    return results;
  }

  // ─── Statistics ───────────────────────────────────────────────────

  getStats(): PolicyHubStats {
    const policies = this.listPolicies();
    const now = new Date();

    const byStatus: Record<PolicyStatus, number> = {
      draft: 0,
      under_review: 0,
      approved: 0,
      published: 0,
      under_attestation: 0,
      revision_needed: 0,
    };
    const byCategory: Record<PolicyCategory, number> = {
      security: 0,
      privacy: 0,
      compliance: 0,
      operational: 0,
      hr: 0,
      financial: 0,
      it: 0,
      safety: 0,
    };

    let upcomingReviews = 0;
    let overdueReviews = 0;
    let pendingAttestations = 0;
    let overdueAttestations = 0;
    let pendingApprovals = 0;

    for (const p of policies) {
      byStatus[p.status]++;
      byCategory[p.category]++;

      const reviewDate = new Date(p.reviewDate);
      if (reviewDate > now && reviewDate.getTime() - now.getTime() < 30 * 24 * 60 * 60 * 1000) {
        upcomingReviews++;
      }
      if (reviewDate < now) {
        overdueReviews++;
      }

      const pendingAtts = p.attestations.filter((a) => a.status === "pending");
      pendingAttestations += pendingAtts.length;

      const overdueAtts = p.attestations.filter(
        (a) => a.status === "pending" && new Date(a.dueDate) < now
      );
      overdueAttestations += overdueAtts.length;

      const pendingSteps = p.approvalChain.filter((s) => s.status === "pending");
      pendingApprovals += pendingSteps.length;
    }

    return {
      totalPolicies: policies.length,
      byStatus,
      byCategory,
      upcomingReviews,
      overdueReviews,
      pendingAttestations,
      overdueAttestations,
      pendingApprovals,
      averageApprovalTimeHours: 0,
    };
  }

  // ─── Events ───────────────────────────────────────────────────────

  private emit(kind: PolicyEventKind, policyId: string, actor: string, metadata: Record<string, unknown>): void {
    this.events.push({
      id: newId(),
      kind,
      policyId,
      actor,
      timestamp: nowIso(),
      metadata,
    });
  }

  getEvents(policyId?: string): PolicyEvent[] {
    if (policyId) return this.events.filter((e) => e.policyId === policyId);
    return [...this.events];
  }
}
