import { createHash } from 'node:crypto';
import type {
  FrameworkCode,
  RegulationAST,
  ASTControlNode,
  PolicyAST,
  PolicyAtom,
  CrosswalkEntry,
  RegulationMetadata,
  EvidenceRequirement,
} from '../types.js';

interface RawControl {
  id: string;
  code: string;
  title: string;
  description: string;
  family: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  dependencies?: string[];
  evidence?: EvidenceRequirement[];
  testLogic?: string;
  remediation?: string;
}

interface FrameworkDefinition {
  code: FrameworkCode;
  version: string;
  title: string;
  issuer: string;
  publishedAt: string;
  effectiveAt: string;
  controls: RawControl[];
}

const BUILTIN_FRAMEWORKS: Record<FrameworkCode, FrameworkDefinition> = {
  iso27001: {
    code: 'iso27001',
    version: '2022',
    title: 'ISO/IEC 27001:2022 Information Security Management',
    issuer: 'ISO/IEC',
    publishedAt: '2022-10-25',
    effectiveAt: '2025-10-31',
    controls: [
      { id: 'iso-a.5.1', code: 'A.5.1', title: 'Policies for Information Security', description: 'Information security policy and topic-specific policies shall be defined, approved by management, published, and communicated.', family: 'Organizational', severity: 'HIGH', evidence: [{ type: 'policy', source: 'document_system', freshness: '90d' }] },
      { id: 'iso-a.5.2', code: 'A.5.2', title: 'Information Security Roles', description: 'Information security roles and responsibilities shall be defined and allocated.', family: 'Organizational', severity: 'MEDIUM', evidence: [{ type: 'policy', source: 'rbac_config', freshness: '90d' }] },
      { id: 'iso-a.5.3', code: 'A.5.3', title: 'Segregation of Duties', description: 'Conflicting duties and conflicting areas of responsibility shall be segregated.', family: 'Organizational', severity: 'HIGH', evidence: [{ type: 'config', source: 'iam_policies', freshness: '30d' }] },
      { id: 'iso-a.5.4', code: 'A.5.4', title: 'Management Responsibilities', description: 'Management shall require all personnel to apply information security in accordance with the established policies.', family: 'Organizational', severity: 'MEDIUM', evidence: [{ type: 'attestation', source: 'training_records', freshness: '365d' }] },
      { id: 'iso-a.6.1', code: 'A.6.1', title: 'Screening', description: 'Background verification checks on all candidates for employment shall be carried out.', family: 'People', severity: 'MEDIUM', evidence: [{ type: 'certificate', source: 'hr_system', freshness: '365d' }] },
      { id: 'iso-a.6.2', code: 'A.6.2', title: 'Terms and Conditions of Employment', description: 'Employment contractual agreements shall state personnel and organization responsibilities.', family: 'People', severity: 'LOW', evidence: [{ type: 'document', source: 'contract_system', freshness: '365d' }] },
      { id: 'iso-a.6.3', code: 'A.6.3', title: 'Information Security Awareness, Education and Training', description: 'Personnel of the organization and relevant interested parties shall receive appropriate information security awareness, education and training.', family: 'People', severity: 'HIGH', evidence: [{ type: 'certificate', source: 'lms_platform', freshness: '365d' }] },
      { id: 'iso-a.7.1', code: 'A.7.1', title: 'Physical Security Perimeters', description: 'Security perimeters shall be defined and used to protect areas containing information and associated assets.', family: 'Physical', severity: 'HIGH', evidence: [{ type: 'screenshot', source: 'physical_security_log', freshness: '30d' }] },
      { id: 'iso-a.8.1', code: 'A.8.1', title: 'User Endpoint Devices', description: 'Information stored on, processed by or accessible via user endpoint devices shall be protected.', family: 'Technological', severity: 'HIGH', evidence: [{ type: 'config', source: 'mdm_system', freshness: '7d' }] },
      { id: 'iso-a.8.2', code: 'A.8.2', title: 'Privileged Access Rights', description: 'The allocation and use of privileged access rights shall be restricted and managed.', family: 'Technological', severity: 'CRITICAL', evidence: [{ type: 'config', source: 'iam_policies', freshness: '7d' }] },
      { id: 'iso-a.8.3', code: 'A.8.3', title: 'Information Access Restriction', description: 'Access to information and other information processing assets shall be restricted in accordance with the access control policy.', family: 'Technological', severity: 'HIGH', evidence: [{ type: 'config', source: 'rbac_config', freshness: '7d' }] },
      { id: 'iso-a.8.5', code: 'A.8.5', title: 'Secure Authentication', description: 'Secure authentication technologies and procedures shall be established and implemented.', family: 'Technological', severity: 'HIGH', evidence: [{ type: 'config', source: 'auth_config', freshness: '7d' }] },
      { id: 'iso-a.8.9', code: 'A.8.9', title: 'Configuration Management', description: 'Configurations, including security configurations, of hardware, software, services and networks shall be established, documented, implemented, monitored and reviewed.', family: 'Technological', severity: 'HIGH', evidence: [{ type: 'config', source: 'config_management', freshness: '7d' }] },
      { id: 'iso-a.8.16', code: 'A.8.16', title: 'Monitoring Activities', description: 'Networks, systems and applications shall be monitored for anomalous behaviour and appropriate actions taken.', family: 'Technological', severity: 'HIGH', evidence: [{ type: 'log', source: 'siem_system', freshness: '24h' }] },
    ],
  },
  'nist-csf': {
    code: 'nist-csf',
    version: '2.0',
    title: 'NIST Cybersecurity Framework 2.0',
    issuer: 'NIST',
    publishedAt: '2024-02-26',
    effectiveAt: '2024-02-26',
    controls: [
      { id: 'nist-gv-oc', code: 'GV.OC', title: 'Organizational Context', description: 'The organization\'s context, risk management strategy, and stakeholders are understood.', family: 'Govern', severity: 'HIGH', evidence: [{ type: 'policy', source: 'risk_register', freshness: '90d' }] },
      { id: 'nist-gv-rr', code: 'GV.RR', title: 'Roles, Responsibilities, and Authorities', description: 'Roles, responsibilities, and authorities for cybersecurity risk management are established.', family: 'Govern', severity: 'MEDIUM', evidence: [{ type: 'policy', source: 'org_chart', freshness: '90d' }] },
      { id: 'nist-id-am', code: 'ID.AM', title: 'Asset Management', description: 'Assets are identified, and cybersecurity risks to assets are understood.', family: 'Identify', severity: 'HIGH', evidence: [{ type: 'config', source: 'asset_inventory', freshness: '30d' }] },
      { id: 'nist-id-ra', code: 'ID.RA', title: 'Risk Assessment', description: 'Cybersecurity risks to the organization are understood and prioritized.', family: 'Identify', severity: 'HIGH', evidence: [{ type: 'config', source: 'risk_assessment', freshness: '90d' }] },
      { id: 'nist-pr-ac', code: 'PR.AC', title: 'Identity Management, Authentication and Access Control', description: 'Access to assets is limited to authorized users, processes, and devices.', family: 'Protect', severity: 'CRITICAL', evidence: [{ type: 'config', source: 'iam_system', freshness: '7d' }] },
      { id: 'nist-pr-ds', code: 'PR.DS', title: 'Data Security', description: 'Data is managed consistent with the organization\'s risk strategy.', family: 'Protect', severity: 'HIGH', evidence: [{ type: 'config', source: 'encryption_config', freshness: '30d' }] },
      { id: 'nist-pr-pt', code: 'PR.PT', title: 'Protective Technology', description: 'Technical security solutions are managed to protect assets.', family: 'Protect', severity: 'HIGH', evidence: [{ type: 'config', source: 'security_tools', freshness: '7d' }] },
      { id: 'nist-de-cm', code: 'DE.CM', title: 'Continuous Monitoring', description: 'The information system and assets are monitored for cybersecurity events.', family: 'Detect', severity: 'HIGH', evidence: [{ type: 'log', source: 'siem', freshness: '24h' }] },
      { id: 'nist-rc-rp', code: 'RC.RP', title: 'Recovery Planning', description: 'Recovery processes and plans are executed during recovery operations.', family: 'Recover', severity: 'HIGH', evidence: [{ type: 'config', source: 'disaster_recovery', freshness: '90d' }] },
    ],
  },
  soc2: {
    code: 'soc2',
    version: '2017',
    title: 'SOC 2 Trust Services Criteria',
    issuer: 'AICPA',
    publishedAt: '2017-01-01',
    effectiveAt: '2017-01-01',
    controls: [
      { id: 'soc2-cc6.1', code: 'CC6.1', title: 'Logical Access Security', description: 'The entity implements logical access security software, infrastructure, and architectures over protected information assets.', family: 'Common Criteria', severity: 'CRITICAL', evidence: [{ type: 'config', source: 'access_controls', freshness: '7d' }] },
      { id: 'soc2-cc6.2', code: 'CC6.2', title: 'User Authentication', description: 'Prior to issuing system credentials and granting system access, the entity registers and authorizes new internal and external users.', family: 'Common Criteria', severity: 'HIGH', evidence: [{ type: 'config', source: 'user_provisioning', freshness: '7d' }] },
      { id: 'soc2-cc6.3', code: 'CC6.3', title: 'Role-Based Access', description: 'The entity authorizes, modifies, or removes access to data, software, functions, and other system assets based on roles.', family: 'Common Criteria', severity: 'HIGH', evidence: [{ type: 'config', source: 'rbac_config', freshness: '30d' }] },
      { id: 'soc2-cc7.1', code: 'CC7.1', title: 'Vulnerability Management', description: 'To meet its objectives, the entity uses detection and monitoring procedures to identify changes to configurations.', family: 'Common Criteria', severity: 'HIGH', evidence: [{ type: 'scan', source: 'vulnerability_scanner', freshness: '7d' }] },
      { id: 'soc2-cc7.2', code: 'CC7.2', title: 'Security Event Monitoring', description: 'The entity monitors system components and the operation of those components for anomalies.', family: 'Common Criteria', severity: 'HIGH', evidence: [{ type: 'log', source: 'siem', freshness: '24h' }] },
      { id: 'soc2-a1.2', code: 'A1.2', title: 'Environmental Protections', description: 'The entity authorizes, designs, develops or configures, implements, operates, approves, maintains, and monitors environmental protections.', family: 'Availability', severity: 'MEDIUM', evidence: [{ type: 'config', source: 'datacenter', freshness: '30d' }] },
    ],
  },
  'iso42001': {
    code: 'iso42001',
    version: '2023',
    title: 'ISO/IEC 42001 AI Management System',
    issuer: 'ISO/IEC',
    publishedAt: '2023-12-01',
    effectiveAt: '2025-06-30',
    controls: [
      { id: 'iso4-aimso.1', code: 'AIMSO.1', title: 'AIMS Scope', description: 'The organization shall determine the boundaries and applicability of the AIMS.', family: 'AIMS Foundation', severity: 'HIGH', evidence: [{ type: 'document', source: 'aims_charter', freshness: '90d' }] },
      { id: 'iso4-a.6.1', code: 'A.6.1', title: 'AI Risk Assessment', description: 'The organization shall establish, implement and maintain an AI risk assessment process.', family: 'AI Risk', severity: 'HIGH', evidence: [{ type: 'config', source: 'risk_register', freshness: '30d' }] },
      { id: 'iso4-a.6.2', code: 'A.6.2', title: 'AI Risk Treatment', description: 'The organization shall implement an AI risk treatment process.', family: 'AI Risk', severity: 'HIGH', evidence: [{ type: 'policy', source: 'risk_treatment', freshness: '90d' }] },
      { id: 'iso4-a.7.1', code: 'A.7.1', title: 'AI System Impact Assessment', description: 'The organization shall perform AI system impact assessments.', family: 'AI Operations', severity: 'CRITICAL', evidence: [{ type: 'attestation', source: 'impact_assessment', freshness: '90d' }] },
      { id: 'iso4-a.7.2', code: 'A.7.2', title: 'AI System Planning', description: 'The organization shall establish criteria for AI system development.', family: 'AI Operations', severity: 'HIGH', evidence: [{ type: 'policy', source: 'development_plan', freshness: '90d' }] },
      { id: 'iso4-a.8.1', code: 'A.8.1', title: 'AI Model Development', description: 'The organization shall establish processes for AI model development and evaluation.', family: 'AI Operations', severity: 'HIGH', evidence: [{ type: 'config', source: 'model_registry', freshness: '30d' }] },
      { id: 'iso4-a.8.2', code: 'A.8.2', title: 'AI Data Quality', description: 'The organization shall establish processes for AI data management and quality assurance.', family: 'AI Operations', severity: 'HIGH', evidence: [{ type: 'config', source: 'data_quality', freshness: '7d' }] },
      { id: 'iso4-a.8.3', code: 'A.8.3', title: 'AI System Verification', description: 'The organization shall verify AI system performance and accuracy.', family: 'AI Operations', severity: 'HIGH', evidence: [{ type: 'scan', source: 'model_validation', freshness: '30d' }] },
    ],
  },
  'eu-ai-act': {
    code: 'eu-ai-act',
    version: '2024',
    title: 'EU Artificial Intelligence Act',
    issuer: 'European Union',
    publishedAt: '2024-08-01',
    effectiveAt: '2025-02-02',
    controls: [
      { id: 'euai-risk-prohibited', code: 'Art.5', title: 'Prohibited AI Practices', description: 'AI practices that manipulate behavior, exploit vulnerabilities, or conduct social scoring are prohibited.', family: 'Prohibited', severity: 'CRITICAL', evidence: [{ type: 'policy', source: 'ai_policy', freshness: '90d' }] },
      { id: 'euai-risk-high', code: 'Art.6', title: 'High-Risk AI Classification', description: 'AI systems are classified as high-risk based on intended use and domain.', family: 'Classification', severity: 'HIGH', evidence: [{ type: 'config', source: 'ai_inventory', freshness: '30d' }] },
      { id: 'euai-governance', code: 'Art.9', title: 'Risk Management System', description: 'Providers shall establish and implement a risk management system for high-risk AI.', family: 'Governance', severity: 'HIGH', evidence: [{ type: 'policy', source: 'risk_management', freshness: '90d' }] },
      { id: 'euai-data', code: 'Art.10', title: 'Data Governance', description: 'Training data shall be relevant, sufficiently representative, and free of errors.', family: 'Data', severity: 'HIGH', evidence: [{ type: 'config', source: 'data_governance', freshness: '30d' }] },
      { id: 'euai-logging', code: 'Art.12', title: 'Record-Keeping', description: 'High-risk AI systems shall enable automatic recording of events (logs).', family: 'Transparency', severity: 'HIGH', evidence: [{ type: 'log', source: 'ai_logging', freshness: '24h' }] },
      { id: 'euai-transparency', code: 'Art.13', title: 'Transparency', description: 'Providers shall ensure high-risk AI systems are sufficiently transparent.', family: 'Transparency', severity: 'HIGH', evidence: [{ type: 'document', source: 'ai_documentation', freshness: '90d' }] },
      { id: 'euai-human', code: 'Art.14', title: 'Human Oversight', description: 'High-risk AI systems shall be designed to allow effective human oversight.', family: 'Oversight', severity: 'CRITICAL', evidence: [{ type: 'config', source: 'human_oversight', freshness: '30d' }] },
      { id: 'euai-accuracy', code: 'Art.15', title: 'Accuracy and Robustness', description: 'High-risk AI systems shall be designed to achieve appropriate levels of accuracy.', family: 'Performance', severity: 'HIGH', evidence: [{ type: 'scan', source: 'model_testing', freshness: '30d' }] },
    ],
  },
  dora: {
    code: 'dora',
    version: '2025',
    title: 'Digital Operational Resilience Act',
    issuer: 'European Union',
    publishedAt: '2022-12-14',
    effectiveAt: '2025-01-17',
    controls: [
      { id: 'dora-ict-5', code: 'ICT-5', title: 'ICT Asset Management', description: 'Financial entities shall maintain inventories of all ICT assets.', family: 'ICT Risk Management', severity: 'HIGH', evidence: [{ type: 'config', source: 'asset_inventory', freshness: '7d' }] },
      { id: 'dora-ict-6', code: 'ICT-6', title: 'Configuration Management', description: 'Financial entities shall establish and implement configuration management processes.', family: 'ICT Risk Management', severity: 'HIGH', evidence: [{ type: 'config', source: 'config_management', freshness: '7d' }] },
      { id: 'dora-ict-7', code: 'ICT-7', title: 'Vulnerability Management', description: 'Financial entities shall have in place a vulnerability management and threat monitoring process.', family: 'ICT Risk Management', severity: 'CRITICAL', evidence: [{ type: 'scan', source: 'vulnerability_scanner', freshness: '7d' }] },
      { id: 'dora-ict-9', code: 'ICT-9', title: 'Monitoring and Logging', description: 'Financial entities shall continuously monitor the operation of ICT systems.', family: 'ICT Risk Management', severity: 'HIGH', evidence: [{ type: 'log', source: 'siem', freshness: '24h' }] },
      { id: 'dora-ict-10', code: 'ICT-10', title: 'Backup and Recovery', description: 'Financial entities shall establish and implement backup, restoration, and recovery procedures.', family: 'ICT Risk Management', severity: 'HIGH', evidence: [{ type: 'config', source: 'backup_system', freshness: '7d' }] },
      { id: 'dora-ict-17', code: 'ICT-17', title: 'ICT Third-Party Risk', description: 'Financial entities shall manage ICT third-party risk.', family: 'Third-Party', severity: 'HIGH', evidence: [{ type: 'policy', source: 'vendor_assessments', freshness: '90d' }] },
    ],
  },
  nis2: {
    code: 'nis2',
    version: '2024',
    title: 'NIS2 Directive',
    issuer: 'European Union',
    publishedAt: '2023-01-16',
    effectiveAt: '2024-10-17',
    controls: [
      { id: 'nis2-art21', code: 'Art.21', title: 'Cybersecurity Risk Management', description: 'Essential and important entities shall implement appropriate technical and organizational measures.', family: 'Risk Management', severity: 'HIGH', evidence: [{ type: 'policy', source: 'risk_management', freshness: '90d' }] },
      { id: 'nis2-art21-2', code: 'Art.21(2)', title: 'Incident Handling', description: 'Establish and exercise incident handling capabilities.', family: 'Incident Response', severity: 'HIGH', evidence: [{ type: 'config', source: 'incident_response', freshness: '90d' }] },
      { id: 'nis2-art21-3', code: 'Art.21(3)', title: 'Business Continuity', description: 'Implement policies on business continuity and crisis management.', family: 'Resilience', severity: 'HIGH', evidence: [{ type: 'config', source: 'bcp_plan', freshness: '90d' }] },
      { id: 'nis2-art21-5', code: 'Art.21(5)', title: 'Security of Procurement', description: 'Implement cybersecurity hygiene policies and ICT training.', family: 'Supply Chain', severity: 'MEDIUM', evidence: [{ type: 'certificate', source: 'training_system', freshness: '365d' }] },
      { id: 'nis2-art21-6', code: 'Art.21(6)', title: 'Third-Party Security', description: 'Ensure ICT service provider security measures.', family: 'Supply Chain', severity: 'HIGH', evidence: [{ type: 'policy', source: 'vendor_assessments', freshness: '90d' }] },
    ],
  },
  hipaa: { code: 'hipaa', version: '2013', title: 'HIPAA Security Rule', issuer: 'HHS', publishedAt: '2013-01-01', effectiveAt: '2013-01-01', controls: [] },
  'pci-dss': { code: 'pci-dss', version: '4.0', title: 'PCI DSS v4.0', issuer: 'PCI SSC', publishedAt: '2022-03-31', effectiveAt: '2024-03-31', controls: [] },
  fedramp: { code: 'fedramp', version: '2024', title: 'FedRAMP Baseline', issuer: 'FedRAMP', publishedAt: '2024-01-01', effectiveAt: '2024-01-01', controls: [] },
  cmmc: { code: 'cmmc', version: '2.0', title: 'Cybersecurity Maturity Model Certification 2.0', issuer: 'DoD', publishedAt: '2024-01-01', effectiveAt: '2024-01-01', controls: [] },
  gdpr: { code: 'gdpr', version: '2016', title: 'General Data Protection Regulation', issuer: 'European Union', publishedAt: '2016-04-27', effectiveAt: '2018-05-25', controls: [] },
  lgpd: { code: 'lgpd', version: '2020', title: 'Lei Geral de Protecao de Dados', issuer: 'Brazil', publishedAt: '2020-09-18', effectiveAt: '2020-09-18', controls: [] },
  pipl: { code: 'pipl', version: '2021', title: 'Personal Information Protection Law', issuer: 'China', publishedAt: '2021-08-20', effectiveAt: '2021-11-01', controls: [] },
  tisax: { code: 'tisax', version: '2023', title: 'Trusted Information Security Assessment Exchange', issuer: 'ENX', publishedAt: '2023-01-01', effectiveAt: '2023-01-01', controls: [] },
  popia: { code: 'popia', version: '2021', title: 'Protection of Personal Information Act', issuer: 'South Africa', publishedAt: '2021-07-01', effectiveAt: '2021-07-01', controls: [] },
};

const DEFAULT_CROSSWALKS: CrosswalkEntry[] = [
  { sourceFramework: 'iso27001', sourceControl: 'A.8.2', targetFramework: 'soc2', targetControl: 'CC6.1', relationship: 'equivalent', confidence: 0.95 },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.3', targetFramework: 'soc2', targetControl: 'CC6.3', relationship: 'equivalent', confidence: 0.9 },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.16', targetFramework: 'soc2', targetControl: 'CC7.2', relationship: 'equivalent', confidence: 0.92 },
  { sourceFramework: 'iso27001', sourceControl: 'A.8.5', targetFramework: 'nist-csf', targetControl: 'PR.AC', relationship: 'equivalent', confidence: 0.88 },
  { sourceFramework: 'iso42001', sourceControl: 'A.6.1', targetFramework: 'nist-csf', targetControl: 'ID.RA', relationship: 'equivalent', confidence: 0.85 },
  { sourceFramework: 'iso42001', sourceControl: 'A.8.2', targetFramework: 'iso27001', targetControl: 'A.5.1', relationship: 'superset', confidence: 0.82 },
  { sourceFramework: 'soc2', sourceControl: 'CC7.2', targetFramework: 'dora', targetControl: 'ICT-9', relationship: 'equivalent', confidence: 0.9 },
  { sourceFramework: 'nist-csf', sourceControl: 'ID.AM', targetFramework: 'dora', targetControl: 'ICT-5', relationship: 'equivalent', confidence: 0.87 },
  { sourceFramework: 'eu-ai-act', sourceControl: 'Art.14', targetFramework: 'iso42001', targetControl: 'A.7.1', relationship: 'stronger', confidence: 0.78 },
  { sourceFramework: 'iso27001', sourceControl: 'A.5.3', targetFramework: 'soc2', targetControl: 'CC6.1', relationship: 'subset', confidence: 0.8 },
  { sourceFramework: 'dora', sourceControl: 'ICT-17', targetFramework: 'iso27001', targetControl: 'A.5.2', relationship: 'stronger', confidence: 0.75 },
];

function parseSeverity(sev?: string): 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL' {
  if (!sev) return 'MEDIUM';
  const s = sev.toUpperCase();
  if (s === 'CRITICAL') return 'CRITICAL';
  if (s === 'HIGH') return 'HIGH';
  if (s === 'LOW') return 'LOW';
  return 'MEDIUM';
}

function buildPolicyAST(control: RawControl): PolicyAST {
  const deps = control.dependencies ?? [];
  const evidence = control.evidence ?? [];

  if (deps.length === 0 && evidence.length === 0) {
    return {
      type: 'atom',
      atom: { subject: control.id, predicate: 'satisfied_by', object: 'auto_evidence', constraints: {} },
    };
  }

  const atoms: PolicyAST[] = evidence.map((e) => ({
    type: 'atom',
    atom: { subject: control.id, predicate: 'has_evidence', object: e.type, constraints: { source: e.source, freshness: e.freshness } },
  }));

  deps.forEach((dep) => {
    atoms.push({
      type: 'atom',
      atom: { subject: control.id, predicate: 'depends_on', object: dep, constraints: {} },
    });
  });

  return { type: 'conjunction', children: atoms };
}

function hashAST(ast: RegulationAST): string {
  const content = JSON.stringify({ controls: ast.controls.map((c) => ({ id: c.id, code: c.code, ast: c.ast })) });
  return createHash('sha256').update(content).digest('hex');
}

export class RegulationASTCompiler {
  private asts: Map<FrameworkCode, RegulationAST> = new Map();
  private crosswalks: CrosswalkEntry[];

  constructor(crosswalks?: CrosswalkEntry[]) {
    this.crosswalks = crosswalks ?? DEFAULT_CROSSWALKS;
    for (const [code, def] of Object.entries(BUILTIN_FRAMEWORKS)) {
      this.compileFramework(def);
    }
  }

  private compileFramework(def: FrameworkDefinition): RegulationAST {
    const controls: ASTControlNode[] = def.controls.map((ctrl) => ({
      id: ctrl.id,
      code: ctrl.code,
      title: ctrl.title,
      ast: buildPolicyAST(ctrl),
      crossRefs: this.crosswalks
        .filter((cw) => cw.sourceFramework === def.code && cw.sourceControl === ctrl.code)
        .map((cw) => `${cw.targetFramework}:${cw.targetControl}`),
      evidenceChain: {
        required: ctrl.evidence ?? [],
        collected: [],
        validUntil: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString(),
      },
    }));

    const metadata: RegulationMetadata = {
      title: def.title,
      issuer: def.issuer,
      publishedAt: def.publishedAt,
      effectiveAt: def.effectiveAt,
      totalControls: controls.length,
      families: [...new Set(def.controls.map((c) => c.family))],
    };

    const ast: RegulationAST = {
      id: `${def.code}:${def.version}`,
      framework: def.code,
      version: def.version,
      compiledAt: new Date().toISOString(),
      controls,
      crosswalks: this.crosswalks.filter((cw) => cw.sourceFramework === def.code || cw.targetFramework === def.code),
      metadata,
    };

    this.asts.set(def.code, ast);
    return ast;
  }

  getAST(framework: FrameworkCode): RegulationAST | undefined {
    return this.asts.get(framework);
  }

  getAllASTs(): RegulationAST[] {
    return Array.from(this.asts.values());
  }

  compileNaturalLanguage(framework: FrameworkCode, text: string): ASTControlNode {
    const existing = this.asts.get(framework);
    if (!existing) throw new Error(`Framework ${framework} not compiled`);

    const hash = createHash('sha256').update(text).digest('hex').slice(0, 8);
    const newControl: ASTControlNode = {
      id: `${framework}-gen-${hash}`,
      code: `GEN-${hash.toUpperCase()}`,
      title: text.slice(0, 100),
      ast: {
        type: 'implication',
        children: [
          { type: 'atom', atom: { subject: 'generated', predicate: 'input', object: text, constraints: {} } },
          { type: 'atom', atom: { subject: 'generated', predicate: 'enforced_by', object: framework, constraints: {} } },
        ],
      },
      crossRefs: [],
      evidenceChain: { required: [{ type: 'automated', source: 'generated', freshness: '24h' }], collected: [], validUntil: '' },
    };

    existing.controls.push(newControl);
    return newControl;
  }

  findEquivalent(framework: FrameworkCode, controlCode: string): CrosswalkEntry[] {
    return this.crosswalks.filter(
      (cw) => cw.sourceFramework === framework && cw.sourceControl === controlCode && cw.relationship === 'equivalent'
    );
  }

  findStronger(framework: FrameworkCode, controlCode: string): CrosswalkEntry[] {
    return this.crosswalks.filter(
      (cw) => cw.targetFramework === framework && cw.targetControl === controlCode && cw.relationship === 'stronger'
    );
  }

  deduplicateEvidence(orgId: string, framework: FrameworkCode, evidenceMap: Map<string, string[]>): Map<string, string[]> {
    const ast = this.asts.get(framework);
    if (!ast) return evidenceMap;

    const deduplicated = new Map<string, string[]>();
    const evidenceOwnership = new Map<string, string>();

    for (const control of ast.controls) {
      const existingEvidence = evidenceMap.get(control.id) ?? [];
      const canonicalEvidence = existingEvidence[0];

      if (!canonicalEvidence || evidenceOwnership.has(canonicalEvidence)) continue;
      evidenceOwnership.set(canonicalEvidence, control.id);
      deduplicated.set(control.id, existingEvidence);
    }

    return deduplicated;
  }

  getHash(framework: FrameworkCode): string | undefined {
    const ast = this.asts.get(framework);
    return ast ? hashAST(ast) : undefined;
  }
}
