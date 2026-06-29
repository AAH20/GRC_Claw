/**
 * @grc-claw/compliance-knowledge-graph
 * Living knowledge graph of global compliance requirements.
 *
 * Maps relationships between frameworks, controls, crosswalks, evidence,
 * organizations, threats, and technologies. Enables cross-framework
 * discovery, threat-to-control mapping, organizational rollup, pattern
 * detection, and real-time compliance posture queries.
 */

import * as crypto from 'node:crypto';

// ─── Core Graph Types ────────────────────────────────────────────────

/** Semantic types of compliance graph nodes. */
export type ComplianceNodeType =
  | 'framework'
  | 'control'
  | 'domain'
  | 'evidence'
  | 'organization'
  | 'threat'
  | 'technology'
  | 'requirement';

/** Typed edge relationships between compliance entities. */
export type ComplianceEdgeRelationship =
  | 'contains'            // framework → control, domain → control
  | 'mapped_to'           // control ↔ control (crosswalk)
  | 'satisfied_by'        // control → evidence
  | 'implemented_by'      // control → technology
  | 'mitigates'           // control → threat
  | 'scoped_to'           // organization → framework
  | 'implements'           // organization → control
  | 'depends_on'          // control → control
  | 'supersedes'          // control → control
  | 'parent_of'           // domain → domain
  | 'addresses'           // requirement → control;

/** Implementation status for a control within an organization. */
export type ControlStatus =
  | 'not_started'
  | 'in_progress'
  | 'partially_implemented'
  | 'implemented'
  | 'effective'
  | 'non_compliant'
  | 'not_applicable';

/** Severity for threat nodes. */
export type ThreatSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

/** Evidence maturity level. */
export type EvidenceMaturity = 'none' | 'ad_hoc' | 'documented' | 'automated' | 'continuous';

/** Node interface for all compliance graph entities. */
export interface ComplianceNode {
  readonly id: string;
  readonly type: ComplianceNodeType;
  name: string;
  description: string;
  properties: Record<string, unknown>;
  tags: string[];
  createdAt: string;
  updatedAt: string;
}

/** Typed edge connecting two compliance nodes. */
export interface ComplianceEdge {
  readonly id: string;
  readonly source: string;
  readonly target: string;
  readonly relationship: ComplianceEdgeRelationship;
  weight: number;                // 0–1, strength of relationship
  confidence: number;            // 0–1, mapping confidence
  metadata: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
}

/** Framework-specific metadata stored on framework nodes. */
export interface FrameworkProperties {
  version: string;
  issuer: string;
  effectiveDate: string;
  controlCount: number;
  domains: string[];
  jurisdiction?: string;
  industry?: string[];
}

/** Control-specific metadata stored on control nodes. */
export interface ControlProperties {
  frameworkId: string;
  controlId: string;             // e.g. "A.5.1.1", "CC6.1", "PR.AC-1"
  title: string;
  description: string;
  objective: string;
  domain?: string;
  family?: string;
  maturity?: string;
  isRequired: boolean;
}

/** Organization-specific metadata. */
export interface OrganizationProperties {
  name: string;
  industry: string;
  size: 'startup' | 'smb' | 'mid_market' | 'enterprise';
  frameworksInScope: string[];
  region?: string;
}

/** Threat-specific metadata. */
export interface ThreatProperties {
  name: string;
  description: string;
  mitreAttackId?: string;
  severity: ThreatSeverity;
  likelihood: number;            // 0–1
  impact: number;                // 0–1
  category: string;
}

/** Technology-specific metadata. */
export interface TechnologyProperties {
  name: string;
  vendor: string;
  category: string;              // e.g. "SIEM", "IAM", "DLP", "EDR"
  capabilities: string[];
  version?: string;
}

/** Evidence-specific metadata. */
export interface EvidenceProperties {
  name: string;
  type: 'policy' | 'procedure' | 'screenshot' | 'log' | 'certificate' | 'report' | 'scan' | 'configuration' | 'training_record' | 'audit_trail';
  url?: string;
  maturity: EvidenceMaturity;
  collectedAt?: string;
  expiresAt?: string;
  automatedCollection: boolean;
}

/** Filter criteria for graph queries. */
export interface NodeFilter {
  types?: ComplianceNodeType[];
  tags?: string[];
  frameworkId?: string;
  organizationId?: string;
  namePattern?: string | RegExp;
  minConfidence?: number;
  properties?: Record<string, unknown>;
}

/** Filter for edge traversal. */
export interface EdgeFilter {
  relationships?: ComplianceEdgeRelationship[];
  minWeight?: number;
  minConfidence?: number;
  sourceType?: ComplianceNodeType;
  targetType?: ComplianceNodeType;
}

/** Compliance posture snapshot for an organization. */
export interface CompliancePosture {
  organizationId: string;
  organizationName: string;
  overallScore: number;          // 0–100
  frameworks: FrameworkPosture[];
  calculatedAt: string;
}

/** Per-framework posture breakdown. */
export interface FrameworkPosture {
  frameworkId: string;
  frameworkName: string;
  score: number;                 // 0–100
  totalControls: number;
  implemented: number;
  partial: number;
  notStarted: number;
  notApplicable: number;
  gaps: ControlGap[];
}

/** A control gap identified during posture analysis. */
export interface ControlGap {
  controlId: string;
  controlName: string;
  frameworkId: string;
  status: ControlStatus;
  mitigatingControls: string[];
  riskScore: number;
  recommendation: string;
}

/** Crosswalk mapping between controls across frameworks. */
export interface CrosswalkMapping {
  sourceControlId: string;
  sourceFrameworkId: string;
  targetControlId: string;
  targetFrameworkId: string;
  relationship: 'equivalent' | 'subset' | 'superset' | 'related' | 'partial';
  confidence: number;
  notes?: string;
}

/** Coverage analysis results. */
export interface CoverageAnalysis {
  frameworkId: string;
  totalControls: number;
  coveredControls: number;
  uncoveredControls: string[];
  coveragePercent: number;
  byDomain: DomainCoverage[];
}

/** Per-domain coverage breakdown. */
export interface DomainCoverage {
  domain: string;
  total: number;
  covered: number;
  percent: number;
}

/** Gap analysis results across frameworks. */
export interface GapAnalysis {
  organizationId: string;
  frameworks: FrameworkGap[];
  commonGaps: string[];
  recommendations: string[];
  calculatedAt: string;
}

/** Gaps for a single framework. */
export interface FrameworkGap {
  frameworkId: string;
  totalControls: number;
  gaps: ControlGap[];
  riskScore: number;
}

/** Pattern detected in the compliance graph. */
export interface CompliancePattern {
  type: 'control_cluster' | 'evidence_gap' | 'framework_overlap' | 'threat_coverage' | 'technology_reuse';
  description: string;
  nodeIds: string[];
  confidence: number;
  severity: 'info' | 'low' | 'medium' | 'high';
  recommendation?: string;
}

/** Path between two nodes in the graph. */
export interface GraphPath {
  nodes: string[];
  edges: string[];
  length: number;
  totalWeight: number;
}

/** Analytics summary for the entire graph. */
export interface GraphSummary {
  totalNodes: number;
  totalEdges: number;
  nodesByType: Record<ComplianceNodeType, number>;
  edgesByRelationship: Record<ComplianceEdgeRelationship, number>;
  frameworks: string[];
  averageConfidence: number;
  density: number;
  connectedComponents: number;
}

// ─── Graph Query ─────────────────────────────────────────────────────

/** Query engine for traversing and filtering the compliance graph. */
export class GraphQuery {
  private kg: ComplianceKnowledgeGraph;

  constructor(kg: ComplianceKnowledgeGraph) {
    this.kg = kg;
  }

  /** Find all nodes matching a filter. */
  findNodes(filter: NodeFilter): ComplianceNode[] {
    let nodes = this.kg.getAllNodes();

    if (filter.types && filter.types.length > 0) {
      const typeSet = new Set(filter.types);
      nodes = nodes.filter((n) => typeSet.has(n.type));
    }

    if (filter.tags && filter.tags.length > 0) {
      const tagSet = new Set(filter.tags);
      nodes = nodes.filter((n) => n.tags.some((t) => tagSet.has(t)));
    }

    if (filter.frameworkId) {
      nodes = nodes.filter((n) => {
        if (n.type === 'control') {
          return (n.properties as unknown as ControlProperties).frameworkId === filter.frameworkId;
        }
        if (n.type === 'framework') {
          return n.id === filter.frameworkId;
        }
        return false;
      });
    }

    if (filter.organizationId) {
      const orgEdges = this.kg.getEdgesFrom(filter.organizationId);
      const scopedFrameworkIds = new Set(
        orgEdges
          .filter((e) => e.relationship === 'scoped_to' || e.relationship === 'implements')
          .map((e) => e.target),
      );
      nodes = nodes.filter((n) => scopedFrameworkIds.has(n.id));
    }

    if (filter.namePattern) {
      const pattern = filter.namePattern instanceof RegExp
        ? filter.namePattern
        : new RegExp(filter.namePattern, 'i');
      nodes = nodes.filter((n) => pattern.test(n.name));
    }

    if (filter.properties) {
      nodes = nodes.filter((n) =>
        Object.entries(filter.properties!).every(([key, value]) => n.properties[key] === value),
      );
    }

    return nodes;
  }

  /** Find all edges matching a filter. */
  findEdges(filter: EdgeFilter): ComplianceEdge[] {
    let edges = this.kg.getAllEdges();

    if (filter.relationships && filter.relationships.length > 0) {
      const relSet = new Set(filter.relationships);
      edges = edges.filter((e) => relSet.has(e.relationship));
    }

    if (filter.minWeight !== undefined) {
      edges = edges.filter((e) => e.weight >= filter.minWeight!);
    }

    if (filter.minConfidence !== undefined) {
      edges = edges.filter((e) => e.confidence >= filter.minConfidence!);
    }

    if (filter.sourceType || filter.targetType) {
      const nodeMap = this.kg.getNodeMap();
      edges = edges.filter((e) => {
        const sourceNode = nodeMap.get(e.source);
        const targetNode = nodeMap.get(e.target);
        if (!sourceNode || !targetNode) return false;
        if (filter.sourceType && sourceNode.type !== filter.sourceType) return false;
        if (filter.targetType && targetNode.type !== filter.targetType) return false;
        return true;
      });
    }

    return edges;
  }

  /** Get all controls mapped to a given control (crosswalk). */
  getCrosswalk(controlId: string, maxDepth: number = 2): CrosswalkMapping[] {
    const mappings: CrosswalkMapping[] = [];
    const visited = new Set<string>();
    const queue: Array<{ id: string; depth: number }> = [{ id: controlId, depth: 0 }];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (current.depth >= maxDepth) continue;
      if (visited.has(current.id)) continue;
      visited.add(current.id);

      const edges = this.kg.getEdgesFrom(current.id).filter(
        (e) => e.relationship === 'mapped_to',
      );

      for (const edge of edges) {
        const targetNode = this.kg.getNode(edge.target);
        if (!targetNode || targetNode.type !== 'control') continue;

        const targetProps = targetNode.properties as unknown as ControlProperties;
        const sourceNode = this.kg.getNode(current.id);
        if (!sourceNode) continue;

        const sourceProps = sourceNode.properties as unknown as ControlProperties;

        mappings.push({
          sourceControlId: current.id,
          sourceFrameworkId: sourceProps.frameworkId,
          targetControlId: edge.target,
          targetFrameworkId: targetProps.frameworkId,
          relationship: (edge.metadata.relationship as CrosswalkMapping['relationship']) ?? 'related',
          confidence: edge.confidence,
          notes: edge.metadata.notes as string | undefined,
        });

        if (current.depth + 1 < maxDepth) {
          queue.push({ id: edge.target, depth: current.depth + 1 });
        }
      }
    }

    return mappings;
  }

  /** Find all controls that mitigate a given threat. */
  findControlsForThreat(threatId: string): ComplianceNode[] {
    const edges = this.kg.getEdgesTo(threatId).filter(
      (e) => e.relationship === 'mitigates',
    );
    const nodeMap = this.kg.getNodeMap();
    return edges
      .map((e) => nodeMap.get(e.source))
      .filter((n): n is ComplianceNode => n !== undefined && n.type === 'control');
  }

  /** Find all threats mitigated by a given control. */
  findThreatsForControl(controlId: string): ComplianceNode[] {
    const edges = this.kg.getEdgesFrom(controlId).filter(
      (e) => e.relationship === 'mitigates',
    );
    const nodeMap = this.kg.getNodeMap();
    return edges
      .map((e) => nodeMap.get(e.target))
      .filter((n): n is ComplianceNode => n !== undefined && n.type === 'threat');
  }

  /** Find shortest path between two nodes using BFS. */
  findPath(sourceId: string, targetId: string, maxDepth: number = 10): GraphPath | null {
    if (sourceId === targetId) {
      return { nodes: [sourceId], edges: [], length: 0, totalWeight: 0 };
    }

    const adjacency = this.kg.getAdjacencyList();
    const visited = new Map<string, { parentId: string | null; edgeId: string | null }>();
    visited.set(sourceId, { parentId: null, edgeId: null });
    const queue: Array<{ id: string; depth: number }> = [{ id: sourceId, depth: 0 }];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (current.depth >= maxDepth) continue;

      const neighbors = adjacency.get(current.id) ?? [];
      for (const neighbor of neighbors) {
        if (visited.has(neighbor.nodeId)) continue;

        const edge = this.kg.getEdge(neighbor.edgeId);
        visited.set(neighbor.nodeId, {
          parentId: current.id,
          edgeId: neighbor.edgeId,
        });

        if (neighbor.nodeId === targetId) {
          return this.reconstructPath(visited, targetId, edge?.weight ?? 1);
        }

        queue.push({ id: neighbor.nodeId, depth: current.depth + 1 });
      }
    }

    return null;
  }

  private reconstructPath(
    visited: Map<string, { parentId: string | null; edgeId: string | null }>,
    targetId: string,
    lastWeight: number,
  ): GraphPath {
    const nodes: string[] = [targetId];
    const edges: string[] = [];
    let totalWeight = lastWeight;
    let current = targetId;

    while (true) {
      const entry = visited.get(current)!;
      if (entry.parentId === null) break;
      nodes.unshift(entry.parentId);
      if (entry.edgeId) {
        edges.unshift(entry.edgeId);
        const edge = this.kg.getEdge(entry.edgeId);
        if (edge && edges.length > 1) totalWeight += edge.weight;
      }
      current = entry.parentId;
    }

    return { nodes, edges, length: edges.length, totalWeight };
  }

  /** Get all nodes reachable from a starting node within a given depth. */
  traverse(startId: string, direction: 'outbound' | 'inbound' | 'both', maxDepth: number = 3): ComplianceNode[] {
    const nodeMap = this.kg.getNodeMap();
    const visited = new Set<string>();
    const result: ComplianceNode[] = [];
    const queue: Array<{ id: string; depth: number }> = [{ id: startId, depth: 0 }];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (current.depth >= maxDepth) continue;
      if (visited.has(current.id)) continue;
      visited.add(current.id);

      const node = nodeMap.get(current.id);
      if (node && current.id !== startId) result.push(node);

      if (direction === 'outbound' || direction === 'both') {
        for (const edge of this.kg.getEdgesFrom(current.id)) {
          if (!visited.has(edge.target)) {
            queue.push({ id: edge.target, depth: current.depth + 1 });
          }
        }
      }
      if (direction === 'inbound' || direction === 'both') {
        for (const edge of this.kg.getEdgesTo(current.id)) {
          if (!visited.has(edge.source)) {
            queue.push({ id: edge.source, depth: current.depth + 1 });
          }
        }
      }
    }

    return result;
  }

  /** Aggregate controls by a property (e.g., domain, family). */
  groupControlsBy(frameworkId: string, property: string): Map<string, ComplianceNode[]> {
    const controls = this.kg.query.findNodes({
      types: ['control'],
      frameworkId,
    });

    const groups = new Map<string, ComplianceNode[]>();
    for (const control of controls) {
      const value = String(control.properties[property] ?? 'unspecified');
      const group = groups.get(value) ?? [];
      group.push(control);
      groups.set(value, group);
    }

    return groups;
  }
}

// ─── Graph Analytics ─────────────────────────────────────────────────

/** Analytics engine for compliance graph insights. */
export class GraphAnalytics {
  private kg: ComplianceKnowledgeGraph;

  constructor(kg: ComplianceKnowledgeGraph) {
    this.kg = kg;
  }

  /** Compute a summary of the entire graph. */
  getSummary(): GraphSummary {
    const nodes = this.kg.getAllNodes();
    const edges = this.kg.getAllEdges();

    const nodesByType: Record<string, number> = {};
    for (const n of nodes) {
      nodesByType[n.type] = (nodesByType[n.type] ?? 0) + 1;
    }

    const edgesByRelationship: Record<string, number> = {};
    for (const e of edges) {
      edgesByRelationship[e.relationship] = (edgesByRelationship[e.relationship] ?? 0) + 1;
    }

    const frameworks = nodes
      .filter((n) => n.type === 'framework')
      .map((n) => n.id);

    const avgConfidence = edges.length > 0
      ? edges.reduce((sum, e) => sum + e.confidence, 0) / edges.length
      : 0;

    const nodeCount = nodes.length;
    const maxEdges = nodeCount * (nodeCount - 1);
    const density = maxEdges > 0 ? edges.length / maxEdges : 0;

    return {
      totalNodes: nodeCount,
      totalEdges: edges.length,
      nodesByType: nodesByType as Record<ComplianceNodeType, number>,
      edgesByRelationship: edgesByRelationship as Record<ComplianceEdgeRelationship, number>,
      frameworks,
      averageConfidence: Math.round(avgConfidence * 100) / 100,
      density: Math.round(density * 1000) / 1000,
      connectedComponents: this.countConnectedComponents(),
    };
  }

  /** Analyze control coverage for a framework. */
  analyzeCoverage(frameworkId: string, organizationId?: string): CoverageAnalysis {
    const controls = this.kg.query.findNodes({
      types: ['control'],
      frameworkId,
    });

    const totalControls = controls.length;
    const coveredControls: string[] = [];
    const uncoveredControls: string[] = [];
    const domainStats = new Map<string, { total: number; covered: number }>();

    for (const control of controls) {
      const props = control.properties as unknown as ControlProperties;
      const domain = props.domain ?? 'general';
      const domainStat = domainStats.get(domain) ?? { total: 0, covered: 0 };
      domainStat.total++;

      const hasEvidence = this.kg.getEdgesFrom(control.id).some(
        (e) => e.relationship === 'satisfied_by',
      );
      const hasTechnology = this.kg.getEdgesFrom(control.id).some(
        (e) => e.relationship === 'implemented_by',
      );

      if (hasEvidence || hasTechnology) {
        coveredControls.push(control.id);
        domainStat.covered++;
      } else {
        uncoveredControls.push(control.id);
      }

      domainStats.set(domain, domainStat);
    }

    const byDomain: DomainCoverage[] = [];
    for (const [domain, stat] of domainStats) {
      byDomain.push({
        domain,
        total: stat.total,
        covered: stat.covered,
        percent: stat.total > 0 ? Math.round((stat.covered / stat.total) * 100) : 0,
      });
    }

    return {
      frameworkId,
      totalControls,
      coveredControls: coveredControls.length,
      uncoveredControls,
      coveragePercent: totalControls > 0
        ? Math.round((coveredControls.length / totalControls) * 100)
        : 0,
      byDomain,
    };
  }

  /** Run gap analysis across all frameworks for an organization. */
  analyzeGaps(organizationId: string): GapAnalysis {
    const orgNode = this.kg.getNode(organizationId);
    if (!orgNode || orgNode.type !== 'organization') {
      throw new Error(`Organization node not found: ${organizationId}`);
    }

    const orgProps = orgNode.properties as unknown as OrganizationProperties;
    const frameworkIds = orgProps.frameworksInScope;
    const frameworks: FrameworkGap[] = [];
    const gapCounts = new Map<string, number>();

    for (const fwId of frameworkIds) {
      const controls = this.kg.query.findNodes({
        types: ['control'],
        frameworkId: fwId,
      });

      const controlGaps: ControlGap[] = [];

      for (const control of controls) {
        const implEdges = this.kg.getEdgesFrom(organizationId).filter(
          (e) => e.target === control.id && e.relationship === 'implements',
        );

        const implEdge = implEdges[0];
        const status: ControlStatus = (implEdge?.metadata.status as ControlStatus) ?? 'not_started';

        if (status !== 'implemented' && status !== 'effective' && status !== 'not_applicable') {
          const mitigating = this.findMitigatingControls(control.id);
          const riskScore = this.calculateControlRisk(control, status);

          controlGaps.push({
            controlId: control.id,
            controlName: control.name,
            frameworkId: fwId,
            status,
            mitigatingControls: mitigating,
            riskScore,
            recommendation: this.generateRecommendation(control, status),
          });

          gapCounts.set(control.name, (gapCounts.get(control.name) ?? 0) + 1);
        }
      }

      frameworks.push({
        frameworkId: fwId,
        totalControls: controls.length,
        gaps: controlGaps,
        riskScore: controlGaps.reduce((sum, g) => sum + g.riskScore, 0) / Math.max(controlGaps.length, 1),
      });
    }

    const commonGaps: string[] = [];
    for (const [name, count] of gapCounts) {
      if (count >= 2) commonGaps.push(name);
    }

    return {
      organizationId,
      frameworks,
      commonGaps,
      recommendations: this.generateTopRecommendations(frameworks),
      calculatedAt: new Date().toISOString(),
    };
  }

  /** Detect compliance patterns across the graph. */
  detectPatterns(): CompliancePattern[] {
    const patterns: CompliancePattern[] = [];

    patterns.push(...this.detectControlClusters());
    patterns.push(...this.detectEvidenceGaps());
    patterns.push(...this.detectFrameworkOverlap());
    patterns.push(...this.detectThreatCoverageGaps());
    patterns.push(...this.detectTechnologyReuse());

    return patterns.sort((a, b) => {
      const sevOrder = { high: 0, medium: 1, low: 2, info: 3 };
      return sevOrder[a.severity] - sevOrder[b.severity];
    });
  }

  /** Calculate real-time compliance posture for an organization. */
  calculatePosture(organizationId: string): CompliancePosture {
    const orgNode = this.kg.getNode(organizationId);
    if (!orgNode || orgNode.type !== 'organization') {
      throw new Error(`Organization node not found: ${organizationId}`);
    }

    const orgProps = orgNode.properties as unknown as OrganizationProperties;
    const frameworkPostures: FrameworkPosture[] = [];

    for (const fwId of orgProps.frameworksInScope) {
      const controls = this.kg.query.findNodes({
        types: ['control'],
        frameworkId: fwId,
      });

      let implemented = 0;
      let partial = 0;
      let notStarted = 0;
      let notApplicable = 0;
      const gaps: ControlGap[] = [];

      for (const control of controls) {
        const implEdges = this.kg.getEdgesFrom(organizationId).filter(
          (e) => e.target === control.id && e.relationship === 'implements',
        );

        const status: ControlStatus = (implEdges[0]?.metadata.status as ControlStatus) ?? 'not_started';

        switch (status) {
          case 'implemented':
          case 'effective':
            implemented++;
            break;
          case 'partially_implemented':
          case 'in_progress':
            partial++;
            gaps.push({
              controlId: control.id,
              controlName: control.name,
              frameworkId: fwId,
              status,
              mitigatingControls: this.findMitigatingControls(control.id),
              riskScore: this.calculateControlRisk(control, status),
              recommendation: this.generateRecommendation(control, status),
            });
            break;
          case 'not_applicable':
            notApplicable++;
            break;
          default:
            notStarted++;
            gaps.push({
              controlId: control.id,
              controlName: control.name,
              frameworkId: fwId,
              status,
              mitigatingControls: this.findMitigatingControls(control.id),
              riskScore: this.calculateControlRisk(control, status),
              recommendation: this.generateRecommendation(control, status),
            });
        }
      }

      const applicable = controls.length - notApplicable;
      const score = applicable > 0
        ? Math.round(((implemented * 1.0 + partial * 0.5) / applicable) * 100)
        : 100;

      const fwNode = this.kg.getNode(fwId);
      frameworkPostures.push({
        frameworkId: fwId,
        frameworkName: fwNode?.name ?? fwId,
        score,
        totalControls: controls.length,
        implemented,
        partial,
        notStarted,
        notApplicable,
        gaps,
      });
    }

    const overallScore = frameworkPostures.length > 0
      ? Math.round(frameworkPostures.reduce((s, f) => s + f.score, 0) / frameworkPostures.length)
      : 0;

    return {
      organizationId,
      organizationName: orgNode.name,
      overallScore,
      frameworks: frameworkPostures,
      calculatedAt: new Date().toISOString(),
    };
  }

  /** Calculate degree centrality for all nodes. */
  degreeCentrality(): Map<string, number> {
    const centrality = new Map<string, number>();
    const nodes = this.kg.getAllNodes();
    const maxDegree = Math.max(nodes.length - 1, 1);

    for (const node of nodes) {
      const outDegree = this.kg.getEdgesFrom(node.id).length;
      const inDegree = this.kg.getEdgesTo(node.id).length;
      centrality.set(node.id, (outDegree + inDegree) / maxDegree);
    }

    return centrality;
  }

  /** Find the most critical controls (highest betweenness-like score). */
  findCriticalControls(topN: number = 10): Array<{ nodeId: string; name: string; score: number }> {
    const nodeMap = this.kg.getNodeMap();
    const scores = new Map<string, number>();

    const controlNodes = this.kg.query.findNodes({ types: ['control'] });
    for (const control of controlNodes) {
      const outbound = this.kg.getEdgesFrom(control.id);
      const inbound = this.kg.getEdgesTo(control.id);

      const connectionScore = outbound.length + inbound.length;
      const uniqueFrameworks = new Set<string>();

      for (const e of outbound) {
        const target = nodeMap.get(e.target);
        if (target?.type === 'control') {
          const props = target.properties as unknown as ControlProperties;
          uniqueFrameworks.add(props.frameworkId);
        }
      }
      for (const e of inbound) {
        const source = nodeMap.get(e.source);
        if (source?.type === 'control') {
          const props = source.properties as unknown as ControlProperties;
          uniqueFrameworks.add(props.frameworkId);
        }
      }

      const crossFrameworkBonus = uniqueFrameworks.size * 2;
      scores.set(control.id, connectionScore + crossFrameworkBonus);
    }

    return Array.from(scores.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, topN)
      .map(([nodeId, score]) => ({
        nodeId,
        name: nodeMap.get(nodeId)?.name ?? nodeId,
        score,
      }));
  }

  private findMitigatingControls(controlId: string): string[] {
    const controlNode = this.kg.getNode(controlId);
    if (!controlNode) return [];

    const props = controlNode.properties as unknown as ControlProperties;
    const relatedEdges = this.kg.getEdgesFrom(controlId).filter(
      (e) => e.relationship === 'mapped_to' || e.relationship === 'depends_on',
    );

    return relatedEdges.map((e) => {
      const node = this.kg.getNode(e.target);
      if (!node) return e.target;
      const p = node.properties as unknown as ControlProperties;
      return p.controlId ?? node.name;
    });
  }

  private calculateControlRisk(
    control: ComplianceNode,
    status: ControlStatus,
  ): number {
    let baseRisk = 50;
    switch (status) {
      case 'not_started':
        baseRisk = 90;
        break;
      case 'in_progress':
        baseRisk = 60;
        break;
      case 'partially_implemented':
        baseRisk = 40;
        break;
      case 'non_compliant':
        baseRisk = 95;
        break;
    }

    const threatEdges = this.kg.getEdgesFrom(control.id).filter(
      (e) => e.relationship === 'mitigates',
    );
    const threatMultiplier = 1 + threatEdges.length * 0.1;

    return Math.min(100, Math.round(baseRisk * threatMultiplier));
  }

  private generateRecommendation(
    control: ComplianceNode,
    status: ControlStatus,
  ): string {
    if (status === 'not_started') {
      return `Initiate implementation of control "${control.name}". Assign owner and create implementation plan.`;
    }
    if (status === 'in_progress' || status === 'partially_implemented') {
      return `Accelerate implementation of control "${control.name}". Review blockers and allocate resources.`;
    }
    if (status === 'non_compliant') {
      return `URGENT: Control "${control.name}" is non-compliant. Immediate remediation required.`;
    }
    return `Monitor control "${control.name}" for continued effectiveness.`;
  }

  private generateTopRecommendations(frameworks: FrameworkGap[]): string[] {
    const recs: string[] = [];

    const highRiskFrameworks = frameworks.filter((f) => f.riskScore > 60);
    if (highRiskFrameworks.length > 0) {
      recs.push(
        `Priority: ${highRiskFrameworks.length} framework(s) have risk scores above 60. Focus remediation efforts on: ${highRiskFrameworks.map((f) => f.frameworkId).join(', ')}`,
      );
    }

    const totalGaps = frameworks.reduce((sum, f) => sum + f.gaps.length, 0);
    if (totalGaps > 20) {
      recs.push('Consider phased compliance rollout to manage implementation workload effectively.');
    }

    for (const fw of frameworks) {
      const notStarted = fw.gaps.filter((g) => g.status === 'not_started').length;
      if (notStarted > fw.totalControls * 0.5) {
        recs.push(`Framework ${fw.frameworkId}: Over 50% of controls have not started. Engage compliance team for accelerated onboarding.`);
      }
    }

    return recs;
  }

  private countConnectedComponents(): number {
    const nodes = this.kg.getAllNodes();
    const visited = new Set<string>();
    let components = 0;
    const adjacency = this.kg.getAdjacencyList();

    for (const node of nodes) {
      if (visited.has(node.id)) continue;
      components++;

      const queue = [node.id];
      while (queue.length > 0) {
        const current = queue.shift()!;
        if (visited.has(current)) continue;
        visited.add(current);

        const neighbors = adjacency.get(current) ?? [];
        for (const neighbor of neighbors) {
          if (!visited.has(neighbor.nodeId)) {
            queue.push(neighbor.nodeId);
          }
        }
      }
    }

    return components;
  }

  private detectControlClusters(): CompliancePattern[] {
    const patterns: CompliancePattern[] = [];
    const frameworks = this.kg.query.findNodes({ types: ['framework'] });

    for (const fw of frameworks) {
      const controls = this.kg.query.findNodes({ types: ['control'], frameworkId: fw.id });
      const domainGroups = new Map<string, string[]>();

      for (const c of controls) {
        const props = c.properties as unknown as ControlProperties;
        const domain = props.domain ?? 'general';
        const list = domainGroups.get(domain) ?? [];
        list.push(c.id);
        domainGroups.set(domain, list);
      }

      for (const [domain, ids] of domainGroups) {
        if (ids.length >= 5) {
          patterns.push({
            type: 'control_cluster',
            description: `Dense cluster of ${ids.length} controls in domain "${domain}" of framework ${fw.name}`,
            nodeIds: ids,
            confidence: 0.8,
            severity: 'info',
          });
        }
      }
    }

    return patterns;
  }

  private detectEvidenceGaps(): CompliancePattern[] {
    const patterns: CompliancePattern[] = [];
    const controls = this.kg.query.findNodes({ types: ['control'] });

    for (const control of controls) {
      const evidenceEdges = this.kg.getEdgesFrom(control.id).filter(
        (e) => e.relationship === 'satisfied_by',
      );

      if (evidenceEdges.length === 0) {
        const props = control.properties as unknown as ControlProperties;
        patterns.push({
          type: 'evidence_gap',
          description: `Control "${props.controlId} - ${control.name}" has no evidence artifacts linked`,
          nodeIds: [control.id],
          confidence: 1.0,
          severity: 'medium',
          recommendation: `Collect evidence for control ${props.controlId}. Consider automated evidence collection.`,
        });
      }
    }

    return patterns;
  }

  private detectFrameworkOverlap(): CompliancePattern[] {
    const patterns: CompliancePattern[] = [];
    const frameworks = this.kg.query.findNodes({ types: ['framework'] });

    for (let i = 0; i < frameworks.length; i++) {
      for (let j = i + 1; j < frameworks.length; j++) {
        const fw1 = frameworks[i];
        const fw2 = frameworks[j];

        const controls1 = this.kg.query.findNodes({ types: ['control'], frameworkId: fw1.id });
        const controls2 = this.kg.query.findNodes({ types: ['control'], frameworkId: fw2.id });

        let mappedCount = 0;
        const mappedIds: string[] = [];

        for (const c1 of controls1) {
          const mapped = this.kg.getEdgesFrom(c1.id).filter(
            (e) =>
              e.relationship === 'mapped_to' &&
              controls2.some((c2) => c2.id === e.target),
          );
          if (mapped.length > 0) {
            mappedCount++;
            mappedIds.push(c1.id, ...mapped.map((e) => e.target));
          }
        }

        if (mappedCount >= 3) {
          patterns.push({
            type: 'framework_overlap',
            description: `Frameworks "${fw1.name}" and "${fw2.name}" share ${mappedCount} mapped controls`,
            nodeIds: [...new Set(mappedIds)],
            confidence: 0.7,
            severity: 'info',
            recommendation: `Leverage cross-framework mappings to reduce redundant evidence collection.`,
          });
        }
      }
    }

    return patterns;
  }

  private detectThreatCoverageGaps(): CompliancePattern[] {
    const patterns: CompliancePattern[] = [];
    const threats = this.kg.query.findNodes({ types: ['threat'] });

    for (const threat of threats) {
      const mitigatingControls = this.kg.getEdgesTo(threat.id).filter(
        (e) => e.relationship === 'mitigates',
      );

      if (mitigatingControls.length === 0) {
        const props = threat.properties as unknown as ThreatProperties;
        const severity = props.severity;

        if (severity === 'critical' || severity === 'high') {
          patterns.push({
            type: 'threat_coverage',
            description: `High/critical threat "${threat.name}" (${severity}) has no mitigating controls`,
            nodeIds: [threat.id],
            confidence: 1.0,
            severity: severity === 'critical' ? 'high' : 'medium',
            recommendation: `Map controls to mitigate threat "${threat.name}". Consider implementing controls from relevant frameworks.`,
          });
        }
      }
    }

    return patterns;
  }

  private detectTechnologyReuse(): CompliancePattern[] {
    const patterns: CompliancePattern[] = [];
    const technologies = this.kg.query.findNodes({ types: ['technology'] });

    for (const tech of technologies) {
      const implementEdges = this.kg.getEdgesTo(tech.id).filter(
        (e) => e.relationship === 'implemented_by',
      );

      if (implementEdges.length >= 5) {
        const controlIds = implementEdges.map((e) => e.source);
        patterns.push({
          type: 'technology_reuse',
          description: `Technology "${tech.name}" is used by ${implementEdges.length} controls — key enforcement point`,
          nodeIds: [tech.id, ...controlIds],
          confidence: 0.9,
          severity: 'low',
          recommendation: `Ensure technology "${tech.name}" is properly monitored and maintained as a critical compliance dependency.`,
        });
      }
    }

    return patterns;
  }
}

// ─── Compliance Knowledge Graph ──────────────────────────────────────

/** Main compliance knowledge graph with in-memory adjacency storage. */
export class ComplianceKnowledgeGraph {
  private nodes: Map<string, ComplianceNode> = new Map();
  private edges: Map<string, ComplianceEdge> = new Map();
  private adjacencyOut: Map<string, Set<string>> = new Map();
  private adjacencyIn: Map<string, Set<string>> = new Map();
  private queryEngine: GraphQuery;
  private analyticsEngine: GraphAnalytics;

  constructor() {
    this.queryEngine = new GraphQuery(this);
    this.analyticsEngine = new GraphAnalytics(this);
  }

  /** Get the query engine for traversal and filtering. */
  get query(): GraphQuery {
    return this.queryEngine;
  }

  /** Get the analytics engine for insights and posture. */
  get analytics(): GraphAnalytics {
    return this.analyticsEngine;
  }

  // ── Node Operations ────────────────────────────────────────────────

  /** Add a node to the graph. Returns the node id. */
  addNode(
    type: ComplianceNodeType,
    name: string,
    options?: {
      id?: string;
      description?: string;
      properties?: Record<string, unknown>;
      tags?: string[];
    },
  ): string {
    const id = options?.id ?? `${type}_${crypto.randomUUID().slice(0, 8)}`;
    if (this.nodes.has(id)) {
      throw new Error(`Node already exists: ${id}`);
    }

    const now = new Date().toISOString();
    const node: ComplianceNode = {
      id,
      type,
      name,
      description: options?.description ?? '',
      properties: options?.properties ?? {},
      tags: options?.tags ?? [],
      createdAt: now,
      updatedAt: now,
    };

    this.nodes.set(id, node);
    this.adjacencyOut.set(id, new Set());
    this.adjacencyIn.set(id, new Set());
    return id;
  }

  /** Get a node by id. Returns undefined if not found. */
  getNode(id: string): ComplianceNode | undefined {
    return this.nodes.get(id);
  }

  /** Update mutable fields on a node. */
  updateNode(id: string, updates: Partial<Pick<ComplianceNode, 'name' | 'description' | 'properties' | 'tags'>>): void {
    const node = this.nodes.get(id);
    if (!node) throw new Error(`Node not found: ${id}`);

    if (updates.name !== undefined) node.name = updates.name;
    if (updates.description !== undefined) node.description = updates.description;
    if (updates.properties !== undefined) {
      Object.assign(node.properties, updates.properties);
    }
    if (updates.tags !== undefined) node.tags = updates.tags;
    node.updatedAt = new Date().toISOString();
  }

  /** Remove a node and all connected edges. */
  removeNode(id: string): void {
    if (!this.nodes.has(id)) throw new Error(`Node not found: ${id}`);

    const outEdges = this.adjacencyOut.get(id) ?? new Set();
    for (const edgeId of outEdges) {
      this.removeEdge(edgeId);
    }

    const inEdges = this.adjacencyIn.get(id) ?? new Set();
    for (const edgeId of inEdges) {
      this.removeEdge(edgeId);
    }

    this.nodes.delete(id);
    this.adjacencyOut.delete(id);
    this.adjacencyIn.delete(id);
  }

  /** Check if a node exists. */
  hasNode(id: string): boolean {
    return this.nodes.has(id);
  }

  /** Get all nodes in the graph. */
  getAllNodes(): ComplianceNode[] {
    return Array.from(this.nodes.values());
  }

  /** Get the internal node map for advanced queries. */
  getNodeMap(): Map<string, ComplianceNode> {
    return this.nodes;
  }

  // ── Edge Operations ────────────────────────────────────────────────

  /** Add an edge between two nodes. Returns the edge id. */
  addEdge(
    sourceId: string,
    targetId: string,
    relationship: ComplianceEdgeRelationship,
    options?: {
      id?: string;
      weight?: number;
      confidence?: number;
      metadata?: Record<string, unknown>;
    },
  ): string {
    if (!this.nodes.has(sourceId)) throw new Error(`Source node not found: ${sourceId}`);
    if (!this.nodes.has(targetId)) throw new Error(`Target node not found: ${targetId}`);

    const id = options?.id ?? `edge_${crypto.randomUUID().slice(0, 8)}`;
    if (this.edges.has(id)) {
      throw new Error(`Edge already exists: ${id}`);
    }

    const now = new Date().toISOString();
    const edge: ComplianceEdge = {
      id,
      source: sourceId,
      target: targetId,
      relationship,
      weight: options?.weight ?? 1,
      confidence: options?.confidence ?? 1,
      metadata: options?.metadata ?? {},
      createdAt: now,
      updatedAt: now,
    };

    this.edges.set(id, edge);
    this.adjacencyOut.get(sourceId)!.add(id);
    this.adjacencyIn.get(targetId)!.add(id);
    return id;
  }

  /** Get an edge by id. */
  getEdge(id: string): ComplianceEdge | undefined {
    return this.edges.get(id);
  }

  /** Remove an edge by id. */
  removeEdge(id: string): void {
    const edge = this.edges.get(id);
    if (!edge) return;

    this.adjacencyOut.get(edge.source)?.delete(id);
    this.adjacencyIn.get(edge.target)?.delete(id);
    this.edges.delete(id);
  }

  /** Get all outgoing edges from a node. */
  getEdgesFrom(nodeId: string): ComplianceEdge[] {
    const edgeIds = this.adjacencyOut.get(nodeId) ?? new Set();
    const result: ComplianceEdge[] = [];
    for (const edgeId of edgeIds) {
      const edge = this.edges.get(edgeId);
      if (edge) result.push(edge);
    }
    return result;
  }

  /** Get all incoming edges to a node. */
  getEdgesTo(nodeId: string): ComplianceEdge[] {
    const edgeIds = this.adjacencyIn.get(nodeId) ?? new Set();
    const result: ComplianceEdge[] = [];
    for (const edgeId of edgeIds) {
      const edge = this.edges.get(edgeId);
      if (edge) result.push(edge);
    }
    return result;
  }

  /** Get all edges in the graph. */
  getAllEdges(): ComplianceEdge[] {
    return Array.from(this.edges.values());
  }

  /** Get the adjacency list for graph traversal. */
  getAdjacencyList(): Map<string, Array<{ nodeId: string; edgeId: string }>> {
    const list = new Map<string, Array<{ nodeId: string; edgeId: string }>>();

    for (const [nodeId, edgeIds] of this.adjacencyOut) {
      const neighbors: Array<{ nodeId: string; edgeId: string }> = [];
      for (const edgeId of edgeIds) {
        const edge = this.edges.get(edgeId);
        if (edge) {
          neighbors.push({ nodeId: edge.target, edgeId: edge.id });
        }
      }
      list.set(nodeId, neighbors);
    }

    for (const [nodeId] of this.adjacencyIn) {
      if (!list.has(nodeId)) list.set(nodeId, []);
      const edgeIds = this.adjacencyIn.get(nodeId)!;
      for (const edgeId of edgeIds) {
        const edge = this.edges.get(edgeId);
        if (edge) {
          const existing = list.get(nodeId)!;
          existing.push({ nodeId: edge.source, edgeId: edge.id });
        }
      }
    }

    return list;
  }

  // ── Convenience Methods ────────────────────────────────────────────

  /** Convenience: add a framework node. */
  addFramework(
    name: string,
    properties: FrameworkProperties,
    options?: { id?: string; tags?: string[] },
  ): string {
    return this.addNode('framework', name, {
      id: options?.id,
      properties: properties as unknown as Record<string, unknown>,
      tags: options?.tags,
      description: `${name} compliance framework v${properties.version}`,
    });
  }

  /** Convenience: add a control node and link it to its framework. */
  addControl(
    frameworkId: string,
    controlId: string,
    name: string,
    properties: Omit<ControlProperties, 'frameworkId' | 'controlId'>,
    options?: { id?: string; tags?: string[] },
  ): string {
    if (!this.nodes.has(frameworkId)) {
      throw new Error(`Framework node not found: ${frameworkId}`);
    }

    const nodeId = options?.id ?? `${frameworkId}_${controlId}`;
    const nodeProps: ControlProperties = {
      ...properties as Record<string, unknown>,
      frameworkId,
      controlId,
      title: name,
    } as unknown as ControlProperties;

    const id = this.addNode('control', name, {
      id: nodeId,
      properties: nodeProps as unknown as Record<string, unknown>,
      tags: options?.tags ?? [frameworkId],
      description: properties.description,
    });

    this.addEdge(frameworkId, id, 'contains', { confidence: 1, weight: 1 });
    return id;
  }

  /** Convenience: add an organization node. */
  addOrganization(
    name: string,
    properties: OrganizationProperties,
    options?: { id?: string; tags?: string[] },
  ): string {
    return this.addNode('organization', name, {
      id: options?.id,
      properties: properties as unknown as Record<string, unknown>,
      tags: options?.tags,
    });
  }

  /** Convenience: add a threat node. */
  addThreat(
    name: string,
    properties: ThreatProperties,
    options?: { id?: string; tags?: string[] },
  ): string {
    return this.addNode('threat', name, {
      id: options?.id,
      properties: properties as unknown as Record<string, unknown>,
      tags: options?.tags,
      description: properties.description,
    });
  }

  /** Convenience: add a technology node. */
  addTechnology(
    name: string,
    properties: TechnologyProperties,
    options?: { id?: string; tags?: string[] },
  ): string {
    return this.addNode('technology', name, {
      id: options?.id,
      properties: properties as unknown as Record<string, unknown>,
      tags: options?.tags,
    });
  }

  /** Convenience: add an evidence node and link it to a control. */
  addEvidence(
    controlId: string,
    name: string,
    properties: EvidenceProperties,
    options?: { id?: string; tags?: string[] },
  ): string {
    if (!this.nodes.has(controlId)) {
      throw new Error(`Control node not found: ${controlId}`);
    }

    const id = this.addNode('evidence', name, {
      id: options?.id,
      properties: properties as unknown as Record<string, unknown>,
      tags: options?.tags,
      description: properties.name,
    });

    this.addEdge(controlId, id, 'satisfied_by', { confidence: 1, weight: 1 });
    return id;
  }

  /** Convenience: link a control to a threat (control mitigates threat). */
  linkControlToThreat(controlId: string, threatId: string, options?: { confidence?: number; weight?: number; metadata?: Record<string, unknown> }): string {
    return this.addEdge(controlId, threatId, 'mitigates', {
      confidence: options?.confidence ?? 0.8,
      weight: options?.weight ?? 1,
      metadata: options?.metadata,
    });
  }

  /** Convenience: link a control to a technology (control implemented by technology). */
  linkControlToTechnology(controlId: string, technologyId: string, options?: { confidence?: number; weight?: number; metadata?: Record<string, unknown> }): string {
    return this.addEdge(controlId, technologyId, 'implemented_by', {
      confidence: options?.confidence ?? 0.9,
      weight: options?.weight ?? 1,
      metadata: options?.metadata,
    });
  }

  /** Convenience: create a crosswalk mapping between two controls. */
  addCrosswalk(
    sourceControlId: string,
    targetControlId: string,
    relationship: CrosswalkMapping['relationship'],
    options?: { confidence?: number; notes?: string },
  ): string {
    return this.addEdge(sourceControlId, targetControlId, 'mapped_to', {
      confidence: options?.confidence ?? 0.7,
      weight: 1,
      metadata: { relationship, notes: options?.notes },
    });
  }

  /** Convenience: scope an organization to a framework. */
  scopeOrganizationToFramework(organizationId: string, frameworkId: string): string {
    return this.addEdge(organizationId, frameworkId, 'scoped_to', { confidence: 1, weight: 1 });
  }

  /** Convenience: record that an organization implements a control. */
  recordControlImplementation(
    organizationId: string,
    controlId: string,
    status: ControlStatus,
    options?: { evidence?: string[]; notes?: string },
  ): string {
    return this.addEdge(organizationId, controlId, 'implements', {
      confidence: 1,
      weight: 1,
      metadata: {
        status,
        evidence: options?.evidence ?? [],
        notes: options?.notes,
        implementedAt: new Date().toISOString(),
      },
    });
  }

  // ── Bulk Operations ────────────────────────────────────────────────

  /** Export the entire graph as a serializable object. */
  export(): { nodes: ComplianceNode[]; edges: ComplianceEdge[] } {
    return {
      nodes: this.getAllNodes(),
      edges: this.getAllEdges(),
    };
  }

  /** Import nodes and edges from a serialized graph. */
  import(data: { nodes: ComplianceNode[]; edges: ComplianceEdge[] }): void {
    for (const node of data.nodes) {
      if (this.nodes.has(node.id)) continue;
      this.nodes.set(node.id, node);
      this.adjacencyOut.set(node.id, new Set());
      this.adjacencyIn.set(node.id, new Set());
    }

    for (const edge of data.edges) {
      if (this.edges.has(edge.id)) continue;
      if (!this.nodes.has(edge.source) || !this.nodes.has(edge.target)) continue;
      this.edges.set(edge.id, edge);
      this.adjacencyOut.get(edge.source)!.add(edge.id);
      this.adjacencyIn.get(edge.target)!.add(edge.id);
    }
  }

  /** Clear all nodes and edges. */
  clear(): void {
    this.nodes.clear();
    this.edges.clear();
    this.adjacencyOut.clear();
    this.adjacencyIn.clear();
  }

  /** Get the total number of nodes. */
  get nodeCount(): number {
    return this.nodes.size;
  }

  /** Get the total number of edges. */
  get edgeCount(): number {
    return this.edges.size;
  }
}
// v0.9.0
