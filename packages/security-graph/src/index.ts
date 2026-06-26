/**
 * @grc-claw/security-graph
 * Real-time Security Graph with attack path analysis and risk scoring
 *
 * Connects Agents, Tools, Policies, Evidence, Alerts, Controls, and
 * Infrastructure into a unified graph. Enables attack path tracing,
 * blast radius analysis, and continuous risk scoring.
 */
import * as crypto from 'crypto';

// ─── Core Graph Types ────────────────────────────────────────────────

export type NodeType =
  | 'agent'
  | 'tool'
  | 'control'
  | 'evidence'
  | 'alert'
  | 'identity'
  | 'infrastructure'
  | 'framework'
  | 'policy'
  | 'tenant';

export type EdgeRelationship =
  | 'invoked'
  | 'certified_by'
  | 'violated'
  | 'produced'
  | 'mitigates'
  | 'depends_on'
  | 'owns'
  | 'detected'
  | 'remediates'
  | 'authenticated_by'
  | 'scoped_to';

export type EdgeResult = 'pass' | 'fail' | 'blocked' | 'pending' | 'unknown';

export interface SecurityNode {
  id: string;
  type: NodeType;
  name: string;
  riskScore: number;          // 0-100, real-time
  properties: Record<string, unknown>;
  lastSeen: string;
  firstSeen: string;
  tags: string[];
}

export interface SecurityEdge {
  id: string;
  source: string;
  target: string;
  relationship: EdgeRelationship;
  metadata: {
    timestamp: string;
    sessionId?: string;
    result: EdgeResult;
    confidence: number;       // 0-1
    details?: string;
  };
}

export interface AttackPathSegment {
  node: SecurityNode;
  edge: SecurityEdge;
  riskContribution: number;
}

export interface AttackPath {
  id: string;
  segments: AttackPathSegment[];
  totalRisk: number;
  startNode: string;
  endNode: string;
  discoveredAt: string;
}

export interface RiskAssessment {
  agentDid: string;
  overallRisk: number;
  riskFactors: {
    factor: string;
    score: number;
    weight: number;
    details: string;
  }[];
  recommendedActions: string[];
  assessedAt: string;
}

export interface BlastRadius {
  controlId: string;
  affectedNodes: SecurityNode[];
  affectedEdges: SecurityEdge[];
  impactScore: number;
  cascadeDepth: number;
  assessedAt: string;
}

export interface CompliancePosture {
  tenantId: string;
  framework: string;
  overallScore: number;       // 0-100
  controlScores: { controlId: string; score: number; status: 'pass' | 'fail' | 'partial' }[];
  trend: { date: string; score: number }[];
  lastEvaluated: string;
}

// ─── Security Graph Engine ───────────────────────────────────────────

export class SecurityGraph {
  private nodes: Map<string, SecurityNode> = new Map();
  private edges: Map<string, SecurityEdge> = new Map();
  private adjacency: Map<string, Set<string>> = new Map();
  private reverseAdjacency: Map<string, Set<string>> = new Map();
  private postureCache: Map<string, CompliancePosture> = new Map();

  // ── Node Operations ──

  addNode(node: Omit<SecurityNode, 'firstSeen' | 'lastSeen'>): SecurityNode {
    const now = new Date().toISOString();
    const existing = this.nodes.get(node.id);
    const fullNode: SecurityNode = {
      ...node,
      firstSeen: existing?.firstSeen ?? now,
      lastSeen: now,
    };
    this.nodes.set(node.id, fullNode);
    if (!this.adjacency.has(node.id)) this.adjacency.set(node.id, new Set());
    if (!this.reverseAdjacency.has(node.id)) this.reverseAdjacency.set(node.id, new Set());
    return fullNode;
  }

  getNode(id: string): SecurityNode | undefined {
    return this.nodes.get(id);
  }

  getNodesByType(type: NodeType): SecurityNode[] {
    return Array.from(this.nodes.values()).filter((n) => n.type === type);
  }

  // ── Edge Operations ──

  addEdge(edge: Omit<SecurityEdge, 'id'>): SecurityEdge {
    const edgeId = `edge_${crypto.randomUUID().substring(0, 8)}`;
    const fullEdge: SecurityEdge = { ...edge, id: edgeId };
    this.edges.set(edgeId, fullEdge);

    // Update adjacency
    const fwd = this.adjacency.get(edge.source);
    if (fwd) fwd.add(edgeId);

    const rev = this.reverseAdjacency.get(edge.target);
    if (rev) rev.add(edgeId);

    return fullEdge;
  }

  getEdgesFrom(nodeId: string): SecurityEdge[] {
    const edgeIds = this.adjacency.get(nodeId);
    if (!edgeIds) return [];
    return Array.from(edgeIds).map((id) => this.edges.get(id)).filter(Boolean) as SecurityEdge[];
  }

  getEdgesTo(nodeId: string): SecurityEdge[] {
    const edgeIds = this.reverseAdjacency.get(nodeId);
    if (!edgeIds) return [];
    return Array.from(edgeIds).map((id) => this.edges.get(id)).filter(Boolean) as SecurityEdge[];
  }

  // ── Attack Path Analysis ──

  /** Trace attack paths from a compromised node using BFS */
  traceAttackPaths(startNodeId: string, maxDepth = 5): AttackPath[] {
    const startNode = this.nodes.get(startNodeId);
    if (!startNode) return [];

    const paths: AttackPath[] = [];
    const queue: { nodeId: string; path: AttackPathSegment[]; depth: number }[] = [];
    const visited = new Set<string>();

    queue.push({ nodeId: startNodeId, path: [], depth: 0 });

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (current.depth >= maxDepth) continue;
      if (visited.has(current.nodeId)) continue;
      visited.add(current.nodeId);

      const outEdges = this.getEdgesFrom(current.nodeId);
      for (const edge of outEdges) {
        const targetNode = this.nodes.get(edge.target);
        if (!targetNode) continue;

        const segment: AttackPathSegment = {
          node: targetNode,
          edge,
          riskContribution: targetNode.riskScore * (1 / (current.depth + 1)),
        };

        const newPath = [...current.path, segment];

        // Record path if it reaches a high-value target
        if (targetNode.type === 'control' || targetNode.type === 'evidence' || targetNode.type === 'infrastructure') {
          const totalRisk = newPath.reduce((sum, s) => sum + s.riskContribution, 0);
          paths.push({
            id: `attack_path_${crypto.randomUUID().substring(0, 8)}`,
            segments: newPath,
            totalRisk: Math.min(100, totalRisk),
            startNode: startNodeId,
            endNode: edge.target,
            discoveredAt: new Date().toISOString(),
          });
        }

        queue.push({ nodeId: edge.target, path: newPath, depth: current.depth + 1 });
      }
    }

    return paths.sort((a, b) => b.totalRisk - a.totalRisk);
  }

  // ── Risk Assessment ──

  /** Calculate real-time risk score for an agent */
  assessAgentRisk(agentDid: string): RiskAssessment {
    const agentNode = this.nodes.get(agentDid);
    const riskFactors: RiskAssessment['riskFactors'] = [];

    // Factor 1: Direct violations
    const violations = this.getEdgesFrom(agentDid).filter((e) => e.relationship === 'violated');
    const violationScore = Math.min(40, violations.length * 10);
    riskFactors.push({
      factor: 'policy_violations',
      score: violationScore,
      weight: 0.35,
      details: `${violations.length} policy violations detected`,
    });

    // Factor 2: Tool invocation pattern
    const invocations = this.getEdgesFrom(agentDid).filter((e) => e.relationship === 'invoked');
    const destructiveInvocations = invocations.filter((e) =>
      e.metadata.details?.includes('destructive')
    );
    const invocationRisk = Math.min(30, destructiveInvocations.length * 15);
    riskFactors.push({
      factor: 'destructive_tool_usage',
      score: invocationRisk,
      weight: 0.25,
      details: `${destructiveInvocations.length} destructive tool invocations`,
    });

    // Factor 3: Missing certifications
    const certEdges = this.getEdgesFrom(agentDid).filter((e) => e.relationship === 'certified_by');
    const certScore = certEdges.length >= 3 ? 0 : (3 - certEdges.length) * 10;
    riskFactors.push({
      factor: 'certification_gaps',
      score: certScore,
      weight: 0.2,
      details: `${certEdges.length} active certifications`,
    });

    // Factor 4: Attack path exposure
    const attackPaths = this.traceAttackPaths(agentDid, 3);
    const exposureScore = Math.min(30, attackPaths.length * 5);
    riskFactors.push({
      factor: 'attack_path_exposure',
      score: exposureScore,
      weight: 0.2,
      details: `${attackPaths.length} potential attack paths`,
    });

    const overallRisk = riskFactors.reduce((sum, f) => sum + f.score * f.weight, 0);
    const recommendedActions: string[] = [];

    if (violationScore > 0) recommendedActions.push('Review and remediate policy violations');
    if (invocationRisk > 0) recommendedActions.push('Audit destructive tool access permissions');
    if (certScore > 0) recommendedActions.push('Obtain missing framework certifications');
    if (exposureScore > 0) recommendedActions.push('Reduce blast radius by applying least-privilege controls');

    return {
      agentDid,
      overallRisk: Math.round(overallRisk * 100) / 100,
      riskFactors,
      recommendedActions,
      assessedAt: new Date().toISOString(),
    };
  }

  // ── Blast Radius ──

  /** Calculate the blast radius if a control fails */
  calculateBlastRadius(controlId: string, maxDepth = 4): BlastRadius {
    const affectedNodes: SecurityNode[] = [];
    const affectedEdges: SecurityEdge[] = [];
    const visited = new Set<string>();
    const queue: { nodeId: string; depth: number }[] = [{ nodeId: controlId, depth: 0 }];

    while (queue.length > 0) {
      const current = queue.shift()!;
      if (current.depth >= maxDepth || visited.has(current.nodeId)) continue;
      visited.add(current.nodeId);

      const node = this.nodes.get(current.nodeId);
      if (node && current.nodeId !== controlId) affectedNodes.push(node);

      // Follow both forward and reverse edges
      const allEdges = [...this.getEdgesFrom(current.nodeId), ...this.getEdgesTo(current.nodeId)];
      for (const edge of allEdges) {
        affectedEdges.push(edge);
        const nextNodeId = edge.source === current.nodeId ? edge.target : edge.source;
        if (!visited.has(nextNodeId)) {
          queue.push({ nodeId: nextNodeId, depth: current.depth + 1 });
        }
      }
    }

    const impactScore = Math.min(100, affectedNodes.length * 5 + affectedEdges.length * 2);

    return {
      controlId,
      affectedNodes,
      affectedEdges,
      impactScore,
      cascadeDepth: maxDepth,
      assessedAt: new Date().toISOString(),
    };
  }

  // ── Compliance Posture ──

  /** Calculate real-time compliance posture score */
  calculateCompliancePosture(tenantId: string, framework: string): CompliancePosture {
    const controlNodes = this.getNodesByType('control').filter(
      (n) => n.tags.includes(framework) && (n.properties.tenantId === tenantId || !n.properties.tenantId)
    );

    const controlScores = controlNodes.map((control) => {
      const edges = this.getEdgesTo(control.id);
      const passEdges = edges.filter((e) => e.metadata.result === 'pass');
      const failEdges = edges.filter((e) => e.metadata.result === 'fail');
      const total = passEdges.length + failEdges.length;
      const score = total > 0 ? (passEdges.length / total) * 100 : 50;
      const status: 'pass' | 'fail' | 'partial' =
        score >= 90 ? 'pass' : score >= 50 ? 'partial' : 'fail';

      return { controlId: control.id, score: Math.round(score), status };
    });

    const overallScore = controlScores.length > 0
      ? controlScores.reduce((sum, c) => sum + c.score, 0) / controlScores.length
      : 0;

    const posture: CompliancePosture = {
      tenantId,
      framework,
      overallScore: Math.round(overallScore * 100) / 100,
      controlScores,
      trend: [],
      lastEvaluated: new Date().toISOString(),
    };

    // Cache for trend analysis
    const cacheKey = `${tenantId}_${framework}`;
    const existing = this.postureCache.get(cacheKey);
    if (existing) {
      posture.trend = [...existing.trend, { date: new Date().toISOString(), score: posture.overallScore }].slice(-90);
    } else {
      posture.trend = [{ date: new Date().toISOString(), score: posture.overallScore }];
    }
    this.postureCache.set(cacheKey, posture);

    return posture;
  }

  // ── Graph Queries ──

  /** Find all agents with access to specific tool types */
  queryAgentsByToolAccess(toolName: string): SecurityNode[] {
    const toolNode = Array.from(this.nodes.values()).find(
      (n) => n.type === 'tool' && n.name === toolName
    );
    if (!toolNode) return [];

    const edges = this.getEdgesTo(toolNode.id).filter((e) => e.relationship === 'invoked');
    return edges
      .map((e) => this.nodes.get(e.source))
      .filter((n): n is SecurityNode => n !== undefined && n.type === 'agent');
  }

  /** Find all uncertified agents accessing sensitive tools */
  findUncertifiedAccess(framework: string): {
    agent: SecurityNode;
    tool: SecurityNode;
    edge: SecurityEdge;
  }[] {
    const results: { agent: SecurityNode; tool: SecurityNode; edge: SecurityEdge }[] = [];
    const agents = this.getNodesByType('agent');

    for (const agent of agents) {
      const certEdges = this.getEdgesFrom(agent.id).filter(
        (e) => e.relationship === 'certified_by' && e.metadata.details?.includes(framework)
      );

      if (certEdges.length === 0) {
        const toolEdges = this.getEdgesFrom(agent.id).filter((e) => e.relationship === 'invoked');
        for (const edge of toolEdges) {
          const tool = this.nodes.get(edge.target);
          if (tool && tool.type === 'tool') {
            results.push({ agent, tool, edge });
          }
        }
      }
    }

    return results;
  }

  // ── Statistics ──

  getStats(): {
    totalNodes: number;
    totalEdges: number;
    nodesByType: Record<string, number>;
    avgRiskScore: number;
    highRiskNodes: number;
  } {
    const allNodes = Array.from(this.nodes.values());
    const nodesByType: Record<string, number> = {};
    for (const n of allNodes) {
      nodesByType[n.type] = (nodesByType[n.type] ?? 0) + 1;
    }

    const avgRisk = allNodes.length > 0
      ? allNodes.reduce((sum, n) => sum + n.riskScore, 0) / allNodes.length
      : 0;

    return {
      totalNodes: this.nodes.size,
      totalEdges: this.edges.size,
      nodesByType,
      avgRiskScore: Math.round(avgRisk * 100) / 100,
      highRiskNodes: allNodes.filter((n) => n.riskScore >= 70).length,
    };
  }
}

export { SecurityGraphSeeder } from './seeder.js';
