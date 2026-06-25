import type { FrameworkCode } from "./types.js";
import type {
  FederatedOrganization,
  ComplianceSharingAgreement,
  FederatedComplianceState,
  MeshSyncEvent,
  RegulatoryReport,
  Jurisdiction,
  ComplianceAggregate,
  CrossJurisdictionMapping,
} from "./types.js";
import { ComplianceMeshNetwork } from "./mesh/ComplianceMeshNetwork.js";
import { RegulatoryReportGenerator } from "./reporting/RegulatoryReportGenerator.js";

export interface FederatedMeshConfig {
  topology: "star" | "ring" | "mesh" | "hierarchical";
  defaultJurisdiction: Jurisdiction;
  syncIntervalMs: number;
  maxTrustDecay: number;
}

const DEFAULT_MESH_CONFIG: FederatedMeshConfig = {
  topology: "mesh",
  defaultJurisdiction: "global",
  syncIntervalMs: 300_000,
  maxTrustDecay: 0.1,
};

export class FederatedComplianceMesh {
  private meshNetwork: ComplianceMeshNetwork;
  private reportGenerator: RegulatoryReportGenerator;
  private config: FederatedMeshConfig;

  constructor(config: Partial<FederatedMeshConfig> = {}) {
    this.config = { ...DEFAULT_MESH_CONFIG, ...config };
    this.meshNetwork = new ComplianceMeshNetwork(this.config.topology);
    this.reportGenerator = new RegulatoryReportGenerator();
  }

  registerOrganization(org: FederatedOrganization): void {
    this.meshNetwork.registerOrganization(org);
  }

  deregisterOrganization(orgId: string): boolean {
    return this.meshNetwork.deregisterOrganization(orgId);
  }

  createSharingAgreement(agreement: ComplianceSharingAgreement): void {
    this.meshNetwork.createSharingAgreement(agreement);
  }

  updateComplianceState(
    orgId: string,
    frameworkCode: FrameworkCode,
    state: FederatedComplianceState
  ): MeshSyncEvent[] {
    return this.meshNetwork.propagateComplianceUpdate(orgId, frameworkCode, state);
  }

  getAggregateCompliance(
    orgIds: string[],
    frameworkCode: FrameworkCode
  ): ComplianceAggregate {
    const result = this.meshNetwork.getAggregateCompliance(orgIds, frameworkCode);
    return {
      orgIds,
      frameworkCode,
      aggregateScore: result.aggregateScore,
      orgScores: result.orgScores,
      calculatedAt: new Date().toISOString(),
      minimumScore: result.minimumScore,
      maximumScore: result.maximumScore,
    };
  }

  generateRegulatoryReport(
    orgId: string,
    jurisdiction: Jurisdiction,
    frameworkCode: FrameworkCode,
    controlScores: Map<string, number>
  ): RegulatoryReport {
    return this.reportGenerator.generateComplianceReport(orgId, jurisdiction, frameworkCode, controlScores);
  }

  generateGapAnalysis(
    orgId: string,
    jurisdiction: Jurisdiction,
    frameworkCode: FrameworkCode,
    currentScores: Map<string, number>,
    targetScore: number = 80
  ): RegulatoryReport {
    return this.reportGenerator.generateGapAnalysis(orgId, jurisdiction, frameworkCode, currentScores, targetScore);
  }

  findCrossJurisdictionMappings(
    sourceFramework: FrameworkCode,
    targetJurisdiction: Jurisdiction
  ): CrossJurisdictionMapping[] {
    return this.reportGenerator.findCrossJurisdictionMappings(sourceFramework, targetJurisdiction);
  }

  getApplicableFrameworks(jurisdiction: Jurisdiction): FrameworkCode[] {
    return this.reportGenerator.getApplicableFrameworks(jurisdiction);
  }

  findPath(fromOrgId: string, toOrgId: string): string[] | null {
    return this.meshNetwork.findPath(fromOrgId, toOrgId);
  }

  getMeshStats(): {
    totalOrgs: number;
    activeOrgs: number;
    totalConnections: number;
    sharingAgreements: number;
    syncEvents: number;
  } {
    return this.meshNetwork.getMeshStats();
  }

  getOrganizations(): FederatedOrganization[] {
    return this.meshNetwork.getOrganizations();
  }

  getSyncEvents(orgId?: string): MeshSyncEvent[] {
    return this.meshNetwork.getSyncEvents(orgId);
  }

  getReports(orgId?: string): RegulatoryReport[] {
    return this.reportGenerator.getReports(orgId);
  }

  getMeshNetwork(): ComplianceMeshNetwork {
    return this.meshNetwork;
  }

  getReportGenerator(): RegulatoryReportGenerator {
    return this.reportGenerator;
  }
}

export { ComplianceMeshNetwork } from "./mesh/ComplianceMeshNetwork.js";
export { RegulatoryReportGenerator } from "./reporting/RegulatoryReportGenerator.js";
export type * from "./types.js";
