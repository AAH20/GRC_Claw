import type { FrameworkCode } from "../types.js";
import type {
  FederatedOrganization,
  CrossOrgComplianceRequest,
  ComplianceSharingAgreement,
  FederatedComplianceState,
  MeshSyncEvent,
  MeshTopology,
  Jurisdiction,
  OrgRelationship,
} from "../types.js";

export interface MeshNode {
  orgId: string;
  connections: string[];
  trustLevel: number;
  lastSeen: string;
}

export class ComplianceMeshNetwork {
  private organizations: Map<string, FederatedOrganization> = new Map();
  private nodes: Map<string, MeshNode> = new Map();
  private syncEvents: MeshSyncEvent[] = [];
  private sharingAgreements: Map<string, ComplianceSharingAgreement> = new Map();
  private complianceStates: Map<string, FederatedComplianceState> = new Map();
  private topology: MeshTopology;

  constructor(topology: MeshTopology = "mesh") {
    this.topology = topology;
  }

  registerOrganization(org: FederatedOrganization): void {
    this.organizations.set(org.id, org);
    this.nodes.set(org.id, {
      orgId: org.id,
      connections: org.parentId ? [org.parentId] : [],
      trustLevel: org.trustLevel,
      lastSeen: new Date().toISOString(),
    });

    if (org.parentId) {
      const parentNode = this.nodes.get(org.parentId);
      if (parentNode && !parentNode.connections.includes(org.id)) {
        parentNode.connections.push(org.id);
      }
    }
  }

  deregisterOrganization(orgId: string): boolean {
    const org = this.organizations.get(orgId);
    if (!org) return false;

    for (const nodeId of this.nodes.keys()) {
      const node = this.nodes.get(nodeId)!;
      node.connections = node.connections.filter((c) => c !== orgId);
    }

    this.organizations.delete(orgId);
    this.nodes.delete(orgId);
    return true;
  }

  createSharingAgreement(agreement: ComplianceSharingAgreement): void {
    this.sharingAgreements.set(agreement.id, agreement);
  }

  requestComplianceData(request: CrossOrgComplianceRequest): boolean {
    const fromOrg = this.organizations.get(request.fromOrgId);
    const toOrg = this.organizations.get(request.toOrgId);

    if (!fromOrg || !toOrg) return false;
    if (toOrg.status !== "active") return false;

    const hasAgreement = Array.from(this.sharingAgreements.values()).some(
      (a) =>
        a.orgIds.includes(request.fromOrgId) &&
        a.orgIds.includes(request.toOrgId) &&
        a.frameworkCode === request.frameworkCode
    );

    if (!hasAgreement) return false;

    request.status = "approved";
    return true;
  }

  propagateComplianceUpdate(orgId: string, frameworkCode: FrameworkCode, state: FederatedComplianceState): MeshSyncEvent[] {
    const node = this.nodes.get(orgId);
    if (!node) return [];

    const propagatedTo: string[] = [];
    const events: MeshSyncEvent[] = [];

    for (const connectedOrgId of node.connections) {
      const connectedOrg = this.organizations.get(connectedOrgId);
      if (connectedOrg && connectedOrg.status === "active") {
        propagatedTo.push(connectedOrgId);
        const stateKey = `${connectedOrgId}:${frameworkCode}`;
        this.complianceStates.set(stateKey, {
          ...state,
          orgId: connectedOrgId,
          lastUpdated: new Date().toISOString(),
        });
      }
    }

    const event: MeshSyncEvent = {
      id: `sync-${Date.now()}`,
      type: "compliance_update",
      orgId,
      timestamp: new Date().toISOString(),
      payload: { frameworkCode, overallScore: state.overallScore },
      propagatedTo,
    };

    this.syncEvents.push(event);
    return [event];
  }

  getAggregateCompliance(orgIds: string[], frameworkCode: FrameworkCode): {
    aggregateScore: number;
    orgScores: Map<string, number>;
    minimumScore: number;
    maximumScore: number;
  } {
    const orgScores = new Map<string, number>();

    for (const orgId of orgIds) {
      const stateKey = `${orgId}:${frameworkCode}`;
      const state = this.complianceStates.get(stateKey);
      if (state) {
        orgScores.set(orgId, state.overallScore);
      }
    }

    const scores = Array.from(orgScores.values());
    const aggregateScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;

    return {
      aggregateScore,
      orgScores,
      minimumScore: scores.length > 0 ? Math.min(...scores) : 0,
      maximumScore: scores.length > 0 ? Math.max(...scores) : 0,
    };
  }

  findPath(fromOrgId: string, toOrgId: string): string[] | null {
    const visited = new Set<string>();
    const queue: string[][] = [[fromOrgId]];

    while (queue.length > 0) {
      const path = queue.shift()!;
      const current = path[path.length - 1];

      if (current === toOrgId) return path;
      if (visited.has(current)) continue;
      visited.add(current);

      const node = this.nodes.get(current);
      if (node) {
        for (const neighbor of node.connections) {
          if (!visited.has(neighbor)) {
            queue.push([...path, neighbor]);
          }
        }
      }
    }

    return null;
  }

  getOrganizations(): FederatedOrganization[] {
    return Array.from(this.organizations.values());
  }

  getSyncEvents(orgId?: string): MeshSyncEvent[] {
    if (orgId) return this.syncEvents.filter((e) => e.orgId === orgId);
    return this.syncEvents;
  }

  getMeshStats(): {
    totalOrgs: number;
    activeOrgs: number;
    totalConnections: number;
    sharingAgreements: number;
    syncEvents: number;
  } {
    const orgs = Array.from(this.organizations.values());
    const totalConnections = Array.from(this.nodes.values()).reduce((sum, n) => sum + n.connections.length, 0);

    return {
      totalOrgs: orgs.length,
      activeOrgs: orgs.filter((o) => o.status === "active").length,
      totalConnections,
      sharingAgreements: this.sharingAgreements.size,
      syncEvents: this.syncEvents.length,
    };
  }
}
