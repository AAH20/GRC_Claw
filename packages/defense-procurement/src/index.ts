import { createHash } from 'node:crypto';

export type ProcurementFramework =
  | 'cmmc_l1' | 'cmmc_l2' | 'cmmc_l3'
  | 'nist_800_171'
  | 'nist_800_53'
  | 'fedramp_low' | 'fedramp_moderate' | 'fedramp_high'
  | 'iso_27001' | 'iso_42001'
  | 'soc2'
  | 'nist_ai_rmf'
  | 'eu_ai_act'
  | 'hitrust'
  | 'itil4'
  | 'cobit2019'
  | 'csa_ccm'
  | 'iec_62443'
  | 'nerc_cip'
  | 'dora'
  | 'nis2'
  | 'gdpr'
  | 'hipaa'
  | 'pci_dss';

export type PacketMode =
  | 'prime_contractor'
  | 'government_buyer'
  | 'auditor'
  | 'insurer'
  | 'board'
  | 'pe_diligence'
  | 'msp_vciso'
  | 'acquirer'
  | 'regulator';

export type CuiBoundaryStatus = 'not_started' | 'in_progress' | 'mapped' | 'validated' | 'verified';

export type SprsScore = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10;

export interface CuiBoundaryAsset {
  assetId: string;
  name: string;
  type: 'data_store' | 'processing_system' | 'network_segment' | 'endpoint' | 'cloud_service' | 'saas_application';
  cuiCategories: string[];
  networkLocation: 'cui_spine' | 'cui_edge' | 'non_cui' | 'boundary';
  encryptionAtRest: boolean;
  encryptionInTransit: boolean;
  accessControl: string;
  lastValidated: string;
}

export interface SspControl {
  controlId: string;
  framework: ProcurementFramework;
  family: string;
  title: string;
  description: string;
  status: 'not_applicable' | 'not_implemented' | 'partially_implemented' | 'fully_implemented';
  implementationDescription: string;
  evidenceIds: string[];
  responsibleParty: string;
  lastAssessed: string;
  nextAssessment: string;
  poamId?: string;
}

export interface PoamItem {
  poamId: string;
  controlId: string;
  framework: ProcurementFramework;
  weakness: string;
  description: string;
  riskLevel: 'low' | 'moderate' | 'high' | 'critical';
  remediationPlan: string;
  milestoneDate: string;
  completionDate?: string;
  status: 'open' | 'in_progress' | 'remediated' | 'accepted' | 'expired';
  responsibleParty: string;
  evidenceIds: string[];
}

export interface SupplierRisk {
  supplierId: string;
  name: string;
  tier: 'critical' | 'high' | 'medium' | 'low';
  riskScore: number;
  certifications: string[];
  lastAssessment: string;
  openFindings: number;
  contractualControls: string[];
  incidentHistory: Array<{ date: string; severity: string; description: string }>;
}

export interface AiSystemInventory {
  systemId: string;
  name: string;
 用途: string;
  riskTier: 'minimal' | 'limited' | 'high' | 'unacceptable';
  framework: 'eu_ai_act' | 'nist_ai_rmf' | 'iso_42001';
  modelProvider: string;
  modelVersion: string;
  trainingDataSources: string[];
  lastAssessment: string;
  conformityAssessment?: string;
  nistAiRmfFunctions?: string[];
}

export interface SbomEntry {
  componentName: string;
  version: string;
  supplier: string;
  license: string;
  cveOpen: number;
  cveCritical: number;
  lastScanned: string;
}

export interface AiBomEntry {
  modelName: string;
  provider: string;
  version: string;
  trainingData: string[];
  inferenceEndpoint: string;
  lastScanned: string;
  vulnerabilities: number;
}

export interface ProcurementPacket {
  packetId: string;
  version: 'v1';
  createdAt: string;
  tenantId: number;
  orgSlug: string;
  packetMode: PacketMode;
  frameworks: ProcurementFramework[];
  cuiBoundary: CuiBoundaryAsset[];
  sspControls: SspControl[];
  poamItems: PoamItem[];
  supplierRisk: SupplierRisk[];
  aiInventory: AiSystemInventory[];
  sbom: SbomEntry[];
  aiBom: AiBomEntry[];
  sprsScore: SprsScore;
  fedrampInheritance?: {
    baseline: string;
    inheritedControls: number;
    inheritedControlIds: string[];
  };
  sovereignDeployment?: {
    region: string;
    mode: 'hosted' | 'self_hosted' | 'air_gapped';
    llmProvider: string;
    dataResidency: string;
  };
  agentReceipts: Array<{
    receiptId: string;
    tool: string;
    allowed: boolean;
    timestamp: string;
  }>;
  packetHash: string;
  exportFormats: Array<'json' | 'oscal_ssp' | 'oscal_poam' | 'pdf' | 'excel' | 'stix' | 'sarif'>;
}

function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, v]) => v !== undefined)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([k, v]) => [k, stable(v)]),
    );
  }
  return value;
}

function sha256(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(stable(value))).digest('hex');
}

export function generatePacketId(orgSlug: string, mode: PacketMode): string {
  return `procurement:${orgSlug}:${mode}:${sha256({ orgSlug, mode, ts: Date.now() }).slice(0, 12)}`;
}

export function buildProcurementPacket(input: Omit<ProcurementPacket, 'version' | 'packetHash'>): ProcurementPacket {
  const base: Omit<ProcurementPacket, 'packetHash'> = {
    ...input,
    version: 'v1',
  };
  return { ...base, packetHash: sha256(base) };
}

export function verifyProcurementPacket(packet: ProcurementPacket): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
  if (packet.version !== 'v1') errors.push('unsupported_version');
  if (!packet.packetId) errors.push('missing_packet_id');
  if (!packet.orgSlug) errors.push('missing_org_slug');
  if (!packet.packetMode) errors.push('missing_packet_mode');
  if (packet.packetHash !== sha256({ ...packet, packetHash: undefined })) {
    errors.push('packet_hash_mismatch');
  }
  return { ok: errors.length === 0, errors };
}

export function calculateSprsScore(packet: ProcurementPacket): SprsScore {
  let score = 0;
  const implemented = packet.sspControls.filter((c) => c.status === 'fully_implemented').length;
  const total = packet.sspControls.length;
  if (total > 0) {
    const pct = implemented / total;
    if (pct >= 0.95) score += 4;
    else if (pct >= 0.8) score += 3;
    else if (pct >= 0.6) score += 2;
    else if (pct >= 0.4) score += 1;
  }
  const openCritical = packet.poamItems.filter((p) => p.riskLevel === 'critical' && p.status === 'open').length;
  const openHigh = packet.poamItems.filter((p) => p.riskLevel === 'high' && p.status === 'open').length;
  if (openCritical === 0) score += 2;
  else if (openCritical <= 2) score += 1;
  if (openHigh === 0) score += 2;
  else if (openHigh <= 5) score += 1;
  const sbomClean = packet.sbom.filter((s) => s.cveCritical === 0).length;
  if (packet.sbom.length > 0 && sbomClean === packet.sbom.length) score += 2;
  return Math.min(10, Math.max(0, score)) as SprsScore;
}

export function getPacketModeExportFormats(mode: PacketMode): ProcurementPacket['exportFormats'] {
  const base: ProcurementPacket['exportFormats'] = ['json', 'pdf'];
  switch (mode) {
    case 'government_buyer':
      return [...base, 'oscal_ssp', 'oscal_poam', 'stix'];
    case 'prime_contractor':
      return [...base, 'oscal_ssp', 'oscal_poam', 'excel'];
    case 'auditor':
      return [...base, 'oscal_ssp', 'oscal_poam', 'sarif'];
    case 'insurer':
      return [...base, 'stix', 'excel'];
    case 'board':
      return [...base, 'excel'];
    case 'pe_diligence':
      return [...base, 'excel', 'stix'];
    case 'acquirer':
      return [...base, 'oscal_ssp', 'sarif', 'stix'];
    default:
      return base;
  }
}

export function formatPacketForEvidenceGraph(packet: ProcurementPacket): Record<string, unknown> {
  return {
    objectKind: 'node',
    objectType: 'procurement_packet',
    label: `Procurement: ${packet.packetMode} (${packet.orgSlug})`,
    source: 'defense-procurement',
    payload: {
      packet_id: packet.packetId,
      mode: packet.packetMode,
      frameworks: packet.frameworks,
      sprs_score: packet.sprsScore,
      controls_total: packet.sspControls.length,
      controls_implemented: packet.sspControls.filter((c) => c.status === 'fully_implemented').length,
      poam_open: packet.poamItems.filter((p) => p.status === 'open').length,
      suppliers_critical: packet.supplierRisk.filter((s) => s.tier === 'critical').length,
      ai_systems: packet.aiInventory.length,
      sbom_components: packet.sbom.length,
      ai_bom_models: packet.aiBom.length,
      packet_hash: packet.packetHash,
    },
  };
}

export const CMMC_LEVELS: Record<string, { name: string; controls: number; frameworks: ProcurementFramework[] }> = {
  cmmc_l1: { name: 'CMMC Level 1', controls: 17, frameworks: ['nist_800_171'] },
  cmmc_l2: { name: 'CMMC Level 2', controls: 110, frameworks: ['nist_800_171', 'nist_800_53'] },
  cmmc_l3: { name: 'CMMC Level 3', controls: 110, frameworks: ['nist_800_171', 'nist_800_53', 'fedramp_moderate'] },
};

export const FEDRAMP_BASELINES: Record<string, { name: string; controls: number }> = {
  fedramp_low: { name: 'FedRAMP Low', controls: 125 },
  fedramp_moderate: { name: 'FedRAMP Moderate', controls: 325 },
  fedramp_high: { name: 'FedRAMP High', controls: 421 },
};
