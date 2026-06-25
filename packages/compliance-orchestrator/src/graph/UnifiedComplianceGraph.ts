import { createHash } from 'node:crypto';
import type {
  FrameworkCode,
  RegulationAST,
  ASTControlNode,
  CrosswalkEntry,
  ComplianceState,
  ControlStatus,
  DriftEvent,
  RiskAssessment,
  EvidenceChain,
  CollectedEvidence,
} from '../types.js';

export interface GraphNode {
  id: string;
  type: 'framework' | 'control' | 'evidence' | 'agent' | 'infrastructure' | 'risk' | 'org';
  label: string;
  properties: Record<string, unknown>;
  framework?: FrameworkCode;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  weight: number;
  properties: Record<string, unknown>;
}

export interface AttackPath {
  nodes: string[];
  edges: string[];
  riskScore: number;
  description: string;
}

export interface BlastRadius {
  controlId: string;
  impactScore: number;
  affectedControls: string[];
  affectedSystems: string[];
  propagationDepth: number;
}

export interface CompliancePosture {
  orgId: string;
  timestamp: string;
  overallScore: number;
  frameworkScores: Map<FrameworkCode, number>;
  controlCompliance: Map<string, boolean>;
  riskHeatmap: RiskHeatmapEntry[];
  recommendations: Recommendation[];
}

export interface RiskHeatmapEntry {
  controlFamily: string;
  severity: string;
  count: number;
  riskScore: number;
}

export interface Recommendation {
  id: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  controlId: string;
  title: string;
  description: string;
  estimatedImpact: number;
  estimatedEffort: string;
}

export class UnifiedComplianceGraph {
  private nodes: Map<string, GraphNode> = new Map();
  private edges: GraphEdge[] = [];
  private adjacencyList: Map<string, GraphEdge[]> = new Map();

  constructor(asts: RegulationAST[]) {
    for (const ast of asts) {
      this.addFrameworkNode(ast);
      for (const control of ast.controls) {
        this.addControlNode(control, ast.framework);
      }
    }
  }

  private addFrameworkNode(ast: RegulationAST): void {
    this.nodes.set(`framework:${ast.framework}`, {
      id: `framework:${ast.framework}`,
      type: 'framework',
      label: ast.metadata.title,
      properties: {
        version: ast.version,
        issuer: ast.metadata.issuer,
        totalControls: ast.metadata.totalControls,
        families: ast.metadata.families,
      },
      framework: ast.framework,
    });
  }

  private addControlNode(control: ASTControlNode, framework: FrameworkCode): void {
    const nodeId = `control:${framework}:${control.code}`;
    this.nodes.set(nodeId, {
      id: nodeId,
      type: 'control',
      label: `${control.code} - ${control.title}`,
      properties: {
        id: control.id,
        code: control.code,
        title: control.title,
        crossRefs: control.crossRefs,
        severity: control.severity,
      },
      framework,
    });

    this.edges.push({
      source: `framework:${framework}`,
      target: nodeId,
      relationship: 'contains',
      weight: 1,
      properties: {},
    });
  }

  addCrosswalks(crosswalks: CrosswalkEntry[]): void {
    for (const cw of crosswalks) {
      const sourceId = `control:${cw.sourceFramework}:${cw.sourceControl}`;
      const targetId = `control:${cw.targetFramework}:${cw.targetControl}`;

      if (this.nodes.has(sourceId) && this.nodes.has(targetId)) {
        this.edges.push({
          source: sourceId,
          target: targetId,
          relationship: cw.relationship,
          weight: cw.confidence,
          properties: { confidence: cw.confidence },
        });
      }
    }
  }

  addEvidenceNode(evidence: CollectedEvidence, controlId: string): void {
    const nodeId = `evidence:${evidence.id}`;
    this.nodes.set(nodeId, {
      id: nodeId,
      type: 'evidence',
      label: `${evidence.type} for ${controlId}`,
      properties: {
        hash: evidence.hash,
        timestamp: evidence.timestamp,
        valid: evidence.valid,
        source: evidence.source,
      },
    });

    this.edges.push({
      source: nodeId,
      target: `control:${controlId}`,
      relationship: 'supports',
      weight: evidence.valid ? 1 : 0,
      properties: { valid: evidence.valid },
    });
  }

  addAgentNode(agentId: string, role: string, tools: string[]): void {
    const nodeId = `agent:${agentId}`;
    this.nodes.set(nodeId, {
      id: nodeId,
      type: 'agent',
      label: `Agent ${agentId}`,
      properties: { role, tools },
    });
  }

  addInfrastructureNode(systemId: string, systemType: string, controls: string[]): void {
    const nodeId = `infra:${systemId}`;
    this.nodes.set(nodeId, {
      id: nodeId,
      type: 'infrastructure',
      label: systemId,
      properties: { systemType, controls },
    });

    for (const control of controls) {
      this.edges.push({
        source: nodeId,
        target: `control:${control}`,
        relationship: 'implements',
        weight: 0.8,
        properties: {},
      });
    }
  }

  traceAttackPaths(startNodeId: string, maxDepth: number = 5): AttackPath[] {
    const paths: AttackPath[] = [];
    const visited = new Set<string>();
    const queue: { nodeId: string; path: string[]; edges: string[] }[] = [];

    queue.push({ nodeId: startNodeId, path: [startNodeId], edges: [] });
    visited.add(startNodeId);

    while (queue.length > 0 && paths.length < 10) {
      const current = queue.shift()!;
      const neighbors = this.adjacencyList.get(current.nodeId) ?? [];

      for (const edge of neighbors) {
        const targetId = edge.source === current.nodeId ? edge.target : edge.source;
        if (visited.has(targetId)) continue;
        visited.add(targetId);

        const newPath = [...current.path, targetId];
        const newEdges = [...current.edges, edge.relationship];

        if (newPath.length > 1) {
          paths.push({
            nodes: newPath,
            edges: newEdges,
            riskScore: this.calculatePathRisk(newPath),
            description: this.describeAttackPath(newPath),
          });
        }

        if (newPath.length < maxDepth) {
          queue.push({ nodeId: targetId, path: newPath, edges: newEdges });
        }
      }
    }

    return paths.sort((a, b) => b.riskScore - a.riskScore);
  }

  calculateBlastRadius(controlId: string): BlastRadius {
    const affectedControls: string[] = [];
    const affectedSystems: string[] = [];
    let propagationDepth = 0;

    const bfs = (startId: string, depth: number = 0): void => {
      if (depth > 3) return;
      const outgoing = this.edges.filter((e) => e.source === startId && e.relationship !== 'contains');

      for (const edge of outgoing) {
        const targetNode = this.nodes.get(edge.target);
        if (!targetNode) continue;

        if (targetNode.type === 'control') {
          affectedControls.push(edge.target);
        } else if (targetNode.type === 'infrastructure') {
          affectedSystems.push(edge.target);
        }

        propagationDepth = Math.max(propagationDepth, depth + 1);
        bfs(edge.target, depth + 1);
      }
    };

    bfs(controlId);

    const impactScore = Math.min(
      (affectedControls.length * 0.3 + affectedSystems.length * 0.5 + propagationDepth * 0.2),
      1
    );

    return {
      controlId,
      impactScore,
      affectedControls: [...new Set(affectedControls)],
      affectedSystems: [...new Set(affectedSystems)],
      propagationDepth,
    };
  }

  assessAgentRisk(agentId: string, context: { tool: string; args: Record<string, unknown> }): number {
    const agentNode = this.nodes.get(`agent:${agentId}`);
    if (!agentNode) return 1.0;

    const connectedControls = this.edges
      .filter((e) => e.source === `agent:${agentId}`)
      .map((e) => this.nodes.get(e.target))
      .filter((n) => n?.type === 'control');

    const vulnerableControls = connectedControls.filter((n) => {
      const evidence = this.edges.filter((e) => e.target === n?.id && e.relationship === 'supports');
      return evidence.length === 0;
    });

    return vulnerableControls.length / Math.max(connectedControls.length, 1);
  }

  calculateCompliancePosture(orgId: string, states: ComplianceState[]): CompliancePosture {
    const frameworkScores = new Map<FrameworkCode, number>();
    const controlCompliance = new Map<string, boolean>();
    const riskHeatmap: RiskHeatmapEntry[] = [];
    const recommendations: Recommendation[] = [];

    for (const state of states) {
      const compliant = state.controlStatuses.filter((s) => s.status === 'compliant').length;
      const total = state.controlStatuses.length;
      const score = total > 0 ? (compliant / total) * 100 : 0;
      frameworkScores.set(state.framework, score);

      for (const cs of state.controlStatuses) {
        controlCompliance.set(cs.controlId, cs.status === 'compliant');

        if (cs.status !== 'compliant' && cs.issues.length > 0) {
          recommendations.push({
            id: `rec-${cs.controlId}-${Date.now()}`,
            priority: cs.issues[0].severity === 'CRITICAL' ? 'critical' : 'high',
            controlId: cs.controlId,
            title: `Remediate ${cs.controlId}`,
            description: cs.issues[0].description,
            estimatedImpact: cs.score,
            estimatedEffort: '1-4 hours',
          });
        }
      }

      for (const risk of state.risks) {
        const existing = riskHeatmap.find(
          (r) => r.severity === (risk.riskScore > 0.7 ? 'CRITICAL' : risk.riskScore > 0.4 ? 'HIGH' : 'MEDIUM')
        );
        if (existing) {
          existing.count++;
          existing.riskScore += risk.riskScore;
        } else {
          riskHeatmap.push({
            controlFamily: risk.controlId.split('-')[0],
            severity: risk.riskScore > 0.7 ? 'CRITICAL' : risk.riskScore > 0.4 ? 'HIGH' : 'MEDIUM',
            count: 1,
            riskScore: risk.riskScore,
          });
        }
      }
    }

    const overallScore = Array.from(frameworkScores.values()).reduce((a, b) => a + b, 0) / Math.max(frameworkScores.size, 1);

    return {
      orgId,
      timestamp: new Date().toISOString(),
      overallScore,
      frameworkScores,
      controlCompliance,
      riskHeatmap,
      recommendations: recommendations.sort((a, b) => {
        const priorityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
        return priorityOrder[a.priority] - priorityOrder[b.priority];
      }),
    };
  }

  private calculatePathRisk(path: string[]): number {
    let risk = 0;
    for (const nodeId of path) {
      const node = this.nodes.get(nodeId);
      if (node?.type === 'control') {
        const severity = (node.properties.severity as string) ?? 'MEDIUM';
        const severityScore = { LOW: 0.2, MEDIUM: 0.5, HIGH: 0.8, CRITICAL: 1.0 };
        risk += severityScore[severity as keyof typeof severityScore] ?? 0.5;
      }
    }
    return Math.min(risk / path.length, 1);
  }

  private describeAttackPath(path: string[]): string {
    const descriptions = path.map((nodeId) => {
      const node = this.nodes.get(nodeId);
      if (!node) return nodeId;
      return `${node.type}(${node.label})`;
    });
    return descriptions.join(' → ');
  }

  getGraphHash(): string {
    const content = JSON.stringify({
      nodeCount: this.nodes.size,
      edgeCount: this.edges.length,
      nodeTypes: Array.from(this.nodes.values()).reduce((acc, n) => {
        acc[n.type] = (acc[n.type] ?? 0) + 1;
        return acc;
      }, {} as Record<string, number>),
    });
    return createHash('sha256').update(content).digest('hex');
  }
}
