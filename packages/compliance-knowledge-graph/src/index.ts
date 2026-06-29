/**
 * @grc-claw/compliance-knowledge-graph
 *
 * Living knowledge graph of global compliance requirements.
 * Maps relationships between frameworks, controls, threats, technologies, and evidence.
 *
 * @module @grc-claw/compliance-knowledge-graph
 */

// ─── Enums ────────────────────────────────────────────────────────────────────

/** Canonical node types in the compliance knowledge graph. */
export enum ComplianceType {
  FRAMEWORK = "framework",
  CONTROL = "control",
  THREAT = "threat",
  TECHNOLOGY = "technology",
  EVIDENCE = "evidence",
  ORGANIZATION = "organization",
  POLICY = "policy",
  PROCEDURE = "procedure",
  INCIDENT = "incident",
  VULNERABILITY = "vulnerability",
}

/** Canonical edge (relationship) types between compliance nodes. */
export enum RelationshipType {
  IMPLEMENTS = "implements",
  MITIGATES = "mitigates",
  REQUIRES = "requires",
  PRODUCES = "produces",
  CONSUMES = "consumes",
  DEPENDS_ON = "depends_on",
  MAPS_TO = "maps_to",
  SUPERSEDES = "supersedes",
  RELATES_TO = "relates_to",
}

// ─── Interfaces ───────────────────────────────────────────────────────────────

/** A node in the compliance knowledge graph. */
export interface ComplianceNode {
  /** Unique identifier (e.g. `iso27001:A.5.1.1`). */
  id: string;
  /** Canonical type classification. */
  type: ComplianceType;
  /** Human-readable name. */
  name: string;
  /** Arbitrary key-value properties (severity, status, owner, …). */
  properties: Record<string, unknown>;
  /** Optional tags for faceted filtering. */
  tags?: string[];
  /** ISO-8601 creation timestamp. */
  createdAt?: string;
  /** ISO-8601 last-update timestamp. */
  updatedAt?: string;
}

/** A directed, weighted edge between two compliance nodes. */
export interface ComplianceEdge {
  /** Source node id. */
  from: string;
  /** Target node id. */
  to: string;
  /** Relationship classification. */
  relationship: RelationshipType;
  /** Numeric weight (0-1) for risk propagation and scoring. */
  weight: number;
  /** Arbitrary metadata attached to the edge. */
  metadata?: Record<string, unknown>;
}

/** Serialised form of the entire knowledge graph. */
export interface KnowledgeGraphJSON {
  nodes: ComplianceNode[];
  edges: ComplianceEdge[];
  version: string;
  exportedAt: string;
}

/** Statistics summary returned by `getStatistics`. */
export interface GraphStatistics {
  totalNodes: number;
  totalEdges: number;
  nodesByType: Record<string, number>;
  edgesByRelationship: Record<string, number>;
  averageOutDegree: number;
  stronglyConnectedComponents: number;
  isolatedNodes: number;
}

/** A single gap identified by the gap-analysis engine. */
export interface Gap {
  controlId: string;
  controlName: string;
  framework: string;
  severity: "critical" | "high" | "medium" | "low";
  description: string;
  recommendedActions: string[];
}

/** A risk-propagation result for a single node. */
export interface RiskScore {
  nodeId: string;
  nodeName: string;
  inherentRisk: number;
  residualRisk: number;
  propagationPath: string[];
}

/** Crosswalk mapping between two frameworks. */
export interface CrosswalkMapping {
  sourceId: string;
  sourceName: string;
  targetId: string;
  targetName: string;
  confidence: number;
  notes?: string;
  /** Alias for targetId when mapping between frameworks */
  targetFrameworkId?: string;
  /** Alias for targetId when mapping between controls */
  targetControlId?: string;
}

// ─── Knowledge Graph ──────────────────────────────────────────────────────────

export class KnowledgeGraph {
  private nodes: Map<string, ComplianceNode> = new Map();
  private edges: ComplianceEdge[] = [];
  private adjacencyOut: Map<string, ComplianceEdge[]> = new Map();
  private adjacencyIn: Map<string, ComplianceEdge[]> = new Map();

  // ── Node operations ─────────────────────────────────────────────────────

  /**
   * Add a node to the graph. Overwrites if id already exists.
   * @returns The added node.
   */
  addNode(node: ComplianceNode): ComplianceNode {
    const now = new Date().toISOString();
    const enriched: ComplianceNode = {
      ...node,
      createdAt: node.createdAt ?? now,
      updatedAt: now,
    };
    this.nodes.set(enriched.id, enriched);
    if (!this.adjacencyOut.has(enriched.id)) this.adjacencyOut.set(enriched.id, []);
    if (!this.adjacencyIn.has(enriched.id)) this.adjacencyIn.set(enriched.id, []);
    return enriched;
  }

  /**
   * Retrieve a node by id.
   * @throws {Error} if the node does not exist.
   */
  getNode(id: string): ComplianceNode {
    const node = this.nodes.get(id);
    if (!node) throw new Error(`Node not found: ${id}`);
    return node;
  }

  /**
   * Check whether a node exists.
   */
  hasNode(id: string): boolean {
    return this.nodes.has(id);
  }

  /**
   * Remove a node and all its connected edges.
   */
  removeNode(id: string): boolean {
    if (!this.nodes.has(id)) return false;
    this.nodes.delete(id);
    this.edges = this.edges.filter((e) => e.from !== id && e.to !== id);
    this.adjacencyOut.delete(id);
    this.adjacencyIn.delete(id);
    for (const [, list] of this.adjacencyOut) {
      const idx = list.findIndex((e) => e.to === id);
      if (idx !== -1) list.splice(idx, 1);
    }
    for (const [, list] of this.adjacencyIn) {
      const idx = list.findIndex((e) => e.from === id);
      if (idx !== -1) list.splice(idx, 1);
    }
    return true;
  }

  // ── Edge operations ─────────────────────────────────────────────────────

  /**
   * Add a directed edge. Both endpoints must already exist.
   * @throws {Error} if either endpoint is missing.
   */
  addEdge(edge: ComplianceEdge): ComplianceEdge {
    if (!this.nodes.has(edge.from)) throw new Error(`Source node not found: ${edge.from}`);
    if (!this.nodes.has(edge.to)) throw new Error(`Target node not found: ${edge.to}`);
    const clamped: ComplianceEdge = {
      ...edge,
      weight: Math.max(0, Math.min(1, edge.weight)),
    };
    this.edges.push(clamped);
    this.adjacencyOut.get(edge.from)!.push(clamped);
    this.adjacencyIn.get(edge.to)!.push(clamped);
    return clamped;
  }

  /**
   * Get all edges where `id` is the source or target.
   */
  getEdges(id: string): ComplianceEdge[] {
    return [
      ...(this.adjacencyOut.get(id) ?? []),
      ...(this.adjacencyIn.get(id) ?? []),
    ];
  }

  /**
   * Get outgoing edges from a node.
   */
  getOutEdges(id: string): ComplianceEdge[] {
    return [...(this.adjacencyOut.get(id) ?? [])];
  }

  /**
   * Get incoming edges to a node.
   */
  getInEdges(id: string): ComplianceEdge[] {
    return [...(this.adjacencyIn.get(id) ?? [])];
  }

  /**
   * Remove a specific edge.
   */
  removeEdge(from: string, to: string, relationship: RelationshipType): boolean {
    const idx = this.edges.findIndex(
      (e) => e.from === from && e.to === to && e.relationship === relationship,
    );
    if (idx === -1) return false;
    this.edges.splice(idx, 1);
    const outList = this.adjacencyOut.get(from);
    if (outList) {
      const i = outList.findIndex(
        (e) => e.to === to && e.relationship === relationship,
      );
      if (i !== -1) outList.splice(i, 1);
    }
    const inList = this.adjacencyIn.get(to);
    if (inList) {
      const i = inList.findIndex(
        (e) => e.from === from && e.relationship === relationship,
      );
      if (i !== -1) inList.splice(i, 1);
    }
    return true;
  }

  // ── Traversal ───────────────────────────────────────────────────────────

  /**
   * Find the shortest path (BFS) between two nodes.
   * @returns Ordered list of node ids, or empty array if unreachable.
   */
  findPath(from: string, to: string): string[] {
    if (!this.nodes.has(from) || !this.nodes.has(to)) return [];
    if (from === to) return [from];

    const visited = new Set<string>([from]);
    const parent = new Map<string, string>();
    const queue: string[] = [from];

    while (queue.length > 0) {
      const current = queue.shift()!;
      for (const edge of this.adjacencyOut.get(current) ?? []) {
        if (visited.has(edge.to)) continue;
        visited.add(edge.to);
        parent.set(edge.to, current);
        if (edge.to === to) {
          const path: string[] = [to];
          let cur = to;
          while (parent.has(cur)) {
            cur = parent.get(cur)!;
            path.unshift(cur);
          }
          return path;
        }
        queue.push(edge.to);
      }
    }
    return [];
  }

  /**
   * Collect all nodes reachable from `id` within `depth` hops.
   * @returns Set of reachable node ids (excluding the start node).
   */
  findConnected(id: string, depth: number = 2): Set<string> {
    const result = new Set<string>();
    if (!this.nodes.has(id)) return result;

    let frontier = new Set<string>([id]);
    for (let d = 0; d < depth; d++) {
      const next = new Set<string>();
      for (const nodeId of frontier) {
        for (const edge of this.adjacencyOut.get(nodeId) ?? []) {
          if (!result.has(edge.to) && edge.to !== id) {
            next.add(edge.to);
            result.add(edge.to);
          }
        }
        for (const edge of this.adjacencyIn.get(nodeId) ?? []) {
          if (!result.has(edge.from) && edge.from !== id) {
            next.add(edge.from);
            result.add(edge.from);
          }
        }
      }
      frontier = next;
    }
    return result;
  }

  // ── Query ───────────────────────────────────────────────────────────────

  /**
   * Return all nodes of a given type.
   */
  queryByType(type: ComplianceType): ComplianceNode[] {
    const result: ComplianceNode[] = [];
    for (const node of this.nodes.values()) {
      if (node.type === type) result.push(node);
    }
    return result;
  }

  /**
   * Return all nodes whose `properties[key]` equals `value` (strict equality).
   */
  queryByProperty(key: string, value: unknown): ComplianceNode[] {
    const result: ComplianceNode[] = [];
    for (const node of this.nodes.values()) {
      if (node.properties[key] === value) result.push(node);
    }
    return result;
  }

  /**
   * Return nodes whose name or id match a fuzzy substring (case-insensitive).
   */
  search(query: string): ComplianceNode[] {
    const q = query.toLowerCase();
    const result: ComplianceNode[] = [];
    for (const node of this.nodes.values()) {
      if (
        node.name.toLowerCase().includes(q) ||
        node.id.toLowerCase().includes(q)
      ) {
        result.push(node);
      }
    }
    return result;
  }

  /**
   * Return all node ids in the graph.
   */
  getAllNodeIds(): string[] {
    return [...this.nodes.keys()];
  }

  /**
   * Return all nodes in the graph.
   */
  getAllNodes(): ComplianceNode[] {
    return [...this.nodes.values()];
  }

  /**
   * Return all edges in the graph.
   */
  getAllEdges(): ComplianceEdge[] {
    return [...this.edges];
  }

  // ── Merge & Diff ────────────────────────────────────────────────────────

  /**
   * Merge another graph into this one.
   * - Nodes with the same id are deep-merged (properties merged, updatedAt refreshed).
   * - Edges are deduplicated by (from, to, relationship).
   * @returns Number of new nodes and edges added.
   */
  mergeGraph(other: KnowledgeGraph): { nodesAdded: number; edgesAdded: number } {
    let nodesAdded = 0;
    let edgesAdded = 0;

    for (const node of other.getAllNodes()) {
      if (this.nodes.has(node.id)) {
        const existing = this.nodes.get(node.id)!;
        existing.properties = { ...existing.properties, ...node.properties };
        existing.updatedAt = new Date().toISOString();
        if (node.tags) {
          existing.tags = [...new Set([...(existing.tags ?? []), ...node.tags])];
        }
      } else {
        this.addNode(node);
        nodesAdded++;
      }
    }

    for (const edge of other.getAllEdges()) {
      const exists = this.edges.some(
        (e) =>
          e.from === edge.from &&
          e.to === edge.to &&
          e.relationship === edge.relationship,
      );
      if (!exists) {
        try {
          this.addEdge(edge);
          edgesAdded++;
        } catch {
          // Skip edges whose endpoints may not have been merged
        }
      }
    }

    return { nodesAdded, edgesAdded };
  }

  /**
   * Compute a diff between this graph and another.
   * @returns Nodes/edges present in `other` but not in `this` (added) and vice-versa (removed).
   */
  diffGraph(other: KnowledgeGraph): {
    addedNodes: ComplianceNode[];
    removedNodes: ComplianceNode[];
    addedEdges: ComplianceEdge[];
    removedEdges: ComplianceEdge[];
  } {
    const addedNodes: ComplianceNode[] = [];
    const removedNodes: ComplianceNode[] = [];
    const addedEdges: ComplianceEdge[] = [];
    const removedEdges: ComplianceEdge[] = [];

    for (const node of other.getAllNodes()) {
      if (!this.nodes.has(node.id)) addedNodes.push(node);
    }
    for (const node of this.getAllNodes()) {
      if (!other.hasNode(node.id)) removedNodes.push(node);
    }

    const otherEdgeKeys = new Set(
      other.getAllEdges().map((e) => `${e.from}|${e.to}|${e.relationship}`),
    );
    const thisEdgeKeys = new Set(
      this.edges.map((e) => `${e.from}|${e.to}|${e.relationship}`),
    );

    for (const edge of other.getAllEdges()) {
      const key = `${edge.from}|${edge.to}|${edge.relationship}`;
      if (!thisEdgeKeys.has(key)) addedEdges.push(edge);
    }
    for (const edge of this.edges) {
      const key = `${edge.from}|${edge.to}|${edge.relationship}`;
      if (!otherEdgeKeys.has(key)) removedEdges.push(edge);
    }

    return { addedNodes, removedNodes, addedEdges, removedEdges };
  }

  // ── Serialisation ───────────────────────────────────────────────────────

  /**
   * Serialize the graph to a JSON-safe object.
   */
  toJSON(): KnowledgeGraphJSON {
    return {
      nodes: this.getAllNodes(),
      edges: this.getAllEdges(),
      version: "0.8.0",
      exportedAt: new Date().toISOString(),
    };
  }

  /**
   * Hydrate a graph from a previously serialized JSON object.
   */
  static fromJSON(data: KnowledgeGraphJSON): KnowledgeGraph {
    const graph = new KnowledgeGraph();
    for (const node of data.nodes) graph.addNode(node);
    for (const edge of data.edges) {
      try {
        graph.addEdge(edge);
      } catch {
        // Skip edges with missing endpoints during deserialization
      }
    }
    return graph;
  }

  /**
   * Clear all nodes and edges.
   */
  clear(): void {
    this.nodes.clear();
    this.edges = [];
    this.adjacencyOut.clear();
    this.adjacencyIn.clear();
  }

  // ── Statistics ──────────────────────────────────────────────────────────

  /**
   * Compute graph statistics.
   */
  getStatistics(): GraphStatistics {
    const nodesByType: Record<string, number> = {};
    for (const node of this.nodes.values()) {
      nodesByType[node.type] = (nodesByType[node.type] ?? 0) + 1;
    }

    const edgesByRelationship: Record<string, number> = {};
    for (const edge of this.edges) {
      edgesByRelationship[edge.relationship] =
        (edgesByRelationship[edge.relationship] ?? 0) + 1;
    }

    let isolated = 0;
    for (const id of this.nodes.keys()) {
      if (
        (this.adjacencyOut.get(id)?.length ?? 0) === 0 &&
        (this.adjacencyIn.get(id)?.length ?? 0) === 0
      ) {
        isolated++;
      }
    }

    const totalNodes = this.nodes.size;
    const totalEdges = this.edges.length;

    return {
      totalNodes,
      totalEdges,
      nodesByType,
      edgesByRelationship,
      averageOutDegree: totalNodes > 0 ? totalEdges / totalNodes : 0,
      stronglyConnectedComponents: this.countSCC(),
      isolatedNodes: isolated,
    };
  }

  /**
   * Count strongly connected components (Tarjan's algorithm).
   */
  private countSCC(): number {
    let index = 0;
    const stack: string[] = [];
    const onStack = new Set<string>();
    const indices = new Map<string, number>();
    const lowlinks = new Map<string, number>();
    let sccCount = 0;

    const strongConnect = (v: string) => {
      indices.set(v, index);
      lowlinks.set(v, index);
      index++;
      stack.push(v);
      onStack.add(v);

      for (const edge of this.adjacencyOut.get(v) ?? []) {
        const w = edge.to;
        if (!indices.has(w)) {
          strongConnect(w);
          lowlinks.set(v, Math.min(lowlinks.get(v)!, lowlinks.get(w)!));
        } else if (onStack.has(w)) {
          lowlinks.set(v, Math.min(lowlinks.get(v)!, indices.get(w)!));
        }
      }

      if (lowlinks.get(v) === indices.get(v)) {
        sccCount++;
        let w: string;
        do {
          w = stack.pop()!;
          onStack.delete(w);
        } while (w !== v);
      }
    };

    for (const id of this.nodes.keys()) {
      if (!indices.has(id)) strongConnect(id);
    }

    return sccCount;
  }

  // ── Analytics facade ────────────────────────────────────────────────────

  /** Analytics helper that wraps standalone functions for convenience. */
  get analytics() {
    return {
      getSummary: () => this.getStatistics(),
      calculatePosture: (orgId?: string) => {
        const frameworks = this.queryByType(ComplianceType.FRAMEWORK);
        if (frameworks.length === 0) {
          return { overallScore: 0, frameworkPostures: [], gaps: [] };
        }
        const frameworkPostures = frameworks.map(fw => {
          const controls = this.queryByType(ComplianceType.CONTROL)
            .filter(c => c.properties["framework"] === fw.id);
          const implemented = controls.filter(c => c.properties["implemented"] === true);
          return {
            frameworkId: fw.id,
            score: controls.length > 0 ? Math.round((implemented.length / controls.length) * 100) : 0,
            totalControls: controls.length,
            implementedControls: implemented.length,
          };
        });
        const overallScore = frameworkPostures.length > 0
          ? Math.round(frameworkPostures.reduce((s, fp) => s + fp.score, 0) / frameworkPostures.length)
          : 0;
        const gaps = this.queryByType(ComplianceType.CONTROL)
          .filter(c => c.properties["implemented"] !== true)
          .map(c => ({ controlId: c.id, framework: c.properties["framework"] as string }));
        return { overallScore, frameworkPostures, gaps };
      },
      detectPatterns: () => {
        const controls = this.queryByType(ComplianceType.CONTROL);
        const frameworks = new Set(controls.map(c => c.properties["framework"]));
        return Array.from(frameworks).map(fw => ({
          type: "framework_cluster" as const,
          framework: fw,
          controlCount: controls.filter(c => c.properties["framework"] === fw).length,
        }));
      },
    };
  }

  /**
   * Query nodes by property key-value pair.
   * Returns a query builder object for chaining.
   */
  get query() {
    const self = this;
    return {
      /**
       * Query nodes by filters.
       */
      find(filters: { type?: ComplianceType; properties?: Record<string, unknown> }): ComplianceNode[] {
        if (filters.type && filters.properties) {
          return self.queryByType(filters.type).filter(node =>
            Object.entries(filters.properties!).every(([k, v]) => node.properties[k] === v)
          );
        }
        if (filters.type) return self.queryByType(filters.type);
        if (filters.properties) {
          return Array.from(self.nodes.values()).filter(node =>
            Object.entries(filters.properties!).every(([k, v]) => node.properties[k] === v)
          );
        }
        return Array.from(self.nodes.values());
      },

      /**
       * Get crosswalk mappings from a framework.
       */
      getCrosswalk(frameworkId: string): CrosswalkMapping[] {
        const frameworks = self.queryByType(ComplianceType.FRAMEWORK);
        const allMappings: CrosswalkMapping[] = [];
        for (const fw of frameworks) {
          if (fw.id !== frameworkId) {
            allMappings.push(...crosswalk(self, frameworkId, fw.id));
          }
        }
        return allMappings;
      },
    };
  }

  /**
   * Get crosswalk mappings between frameworks.
   */
  getCrosswalk(sourceFramework: string, targetFramework: string): CrosswalkMapping[] {
    return crosswalk(this, sourceFramework, targetFramework);
  }
}

// ─── Crosswalk Mapping Engine ─────────────────────────────────────────────────

/**
 * Map controls from one framework to another using shared edge relationships.
 */
export function crosswalk(
  graph: KnowledgeGraph,
  sourceFramework: string,
  targetFramework: string,
): CrosswalkMapping[] {
  const mappings: CrosswalkMapping[] = [];
  const sourceControls = graph
    .queryByType(ComplianceType.CONTROL)
    .filter((c) => c.properties["framework"] === sourceFramework);

  for (const src of sourceControls) {
    const path = graph.findPath(src.id, targetFramework);
    if (path.length > 0) {
      // Walk the path looking for controls in the target framework
      for (const nodeId of path) {
        const node = graph.getNode(nodeId);
        if (
          node.type === ComplianceType.CONTROL &&
          node.properties["framework"] === targetFramework
        ) {
          mappings.push({
            sourceId: src.id,
            sourceName: src.name,
            targetId: node.id,
            targetName: node.name,
            confidence: computeConfidence(graph, src.id, node.id),
          });
        }
      }
    }

    // Also check direct MAPS_TO edges
    for (const edge of graph.getOutEdges(src.id)) {
      if (edge.relationship === RelationshipType.MAPS_TO) {
        const target = graph.getNode(edge.to);
        if (target.properties["framework"] === targetFramework) {
          mappings.push({
            sourceId: src.id,
            sourceName: src.name,
            targetId: target.id,
            targetName: target.name,
            confidence: edge.weight,
            notes: edge.metadata?.["notes"] as string | undefined,
          });
        }
      }
    }
  }

  // Deduplicate by (sourceId, targetId)
  const seen = new Set<string>();
  return mappings.filter((m) => {
    const key = `${m.sourceId}|${m.targetId}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function computeConfidence(
  graph: KnowledgeGraph,
  from: string,
  to: string,
): number {
  const path = graph.findPath(from, to);
  if (path.length === 0) return 0;
  // Confidence decays with path length
  return Math.max(0, 1 - (path.length - 1) * 0.15);
}

// ─── Compliance Posture Calculator ────────────────────────────────────────────

/**
 * Calculate the compliance posture of an organisation against a framework.
 *
 * @param graph        The knowledge graph
 * @param frameworkId  The framework node id (e.g. `iso27001`)
 * @param implemented  Set of control ids the organisation has implemented
 * @returns Score 0-100 and a breakdown by control category
 */
export function calculatePosture(
  graph: KnowledgeGraph,
  frameworkId: string,
  implemented: Set<string>,
): { score: number; breakdown: Record<string, { total: number; implemented: number; pct: number }> } {
  const framework = graph.getNode(frameworkId);
  if (framework.type !== ComplianceType.FRAMEWORK) {
    throw new Error(`${frameworkId} is not a framework node`);
  }

  const controls = graph
    .queryByType(ComplianceType.CONTROL)
    .filter((c) => {
      // Direct requirement edge from framework
      return graph
        .getInEdges(c.id)
        .some(
          (e) =>
            e.from === frameworkId && e.relationship === RelationshipType.REQUIRES,
        );
    });

  const breakdown: Record<string, { total: number; implemented: number; pct: number }> = {};
  let totalWeight = 0;
  let implementedWeight = 0;

  for (const ctrl of controls) {
    const category = (ctrl.properties["category"] as string) ?? "uncategorised";
    if (!breakdown[category]) {
      breakdown[category] = { total: 0, implemented: 0, pct: 0 };
    }
    const weight = (ctrl.properties["weight"] as number) ?? 1;
    breakdown[category].total++;
    totalWeight += weight;

    if (implemented.has(ctrl.id)) {
      breakdown[category].implemented++;
      implementedWeight += weight;
    }
  }

  for (const cat of Object.keys(breakdown)) {
    const b = breakdown[cat];
    b.pct = b.total > 0 ? Math.round((b.implemented / b.total) * 100) : 0;
  }

  const score = totalWeight > 0 ? Math.round((implementedWeight / totalWeight) * 100) : 0;
  return { score, breakdown };
}

// ─── Gap Analysis Engine ──────────────────────────────────────────────────────

/**
 * Identify compliance gaps — controls required by a framework but not implemented.
 *
 * @param graph        The knowledge graph
 * @param frameworkId  The framework node id
 * @param implemented  Set of control ids the organisation has implemented
 * @param threats      Optional set of active threat ids to elevate severity
 */
export function analyseGaps(
  graph: KnowledgeGraph,
  frameworkId: string,
  implemented: Set<string>,
  threats?: Set<string>,
): Gap[] {
  const framework = graph.getNode(frameworkId);
  if (framework.type !== ComplianceType.FRAMEWORK) {
    throw new Error(`${frameworkId} is not a framework node`);
  }

  const gaps: Gap[] = [];
  const controls = graph
    .queryByType(ComplianceType.CONTROL)
    .filter((c) =>
      graph
        .getInEdges(c.id)
        .some(
          (e) =>
            e.from === frameworkId && e.relationship === RelationshipType.REQUIRES,
        ),
    );

  for (const ctrl of controls) {
    if (implemented.has(ctrl.id)) continue;

    let severity: Gap["severity"] = (ctrl.properties["severity"] as Gap["severity"]) ?? "medium";

    // Elevate severity if active threats mitigate against this control
    if (threats) {
      const mitigations = graph
        .getInEdges(ctrl.id)
        .filter((e) => e.relationship === RelationshipType.MITIGATES);
      for (const m of mitigations) {
        if (threats.has(m.from)) {
          severity = "critical";
          break;
        }
      }
    }

    const recommendedActions: string[] = [];
    // Look for technologies that implement this control
    const techEdges = graph
      .getInEdges(ctrl.id)
      .filter((e) => e.relationship === RelationshipType.IMPLEMENTS);
    for (const te of techEdges) {
      const tech = graph.getNode(te.from);
      recommendedActions.push(`Deploy ${tech.name}`);
    }

    // Look for procedures that support this control
    const procEdges = graph
      .getInEdges(ctrl.id)
      .filter((e) => e.relationship === RelationshipType.RELATES_TO && e.metadata?.["role"] === "supports");
    for (const pe of procEdges) {
      const proc = graph.getNode(pe.from);
      recommendedActions.push(`Establish ${proc.name}`);
    }

    if (recommendedActions.length === 0) {
      recommendedActions.push(`Review and implement control: ${ctrl.name}`);
    }

    gaps.push({
      controlId: ctrl.id,
      controlName: ctrl.name,
      framework: framework.name,
      severity,
      description: (ctrl.properties["description"] as string) ?? `Control ${ctrl.name} is not implemented`,
      recommendedActions,
    });
  }

  // Sort by severity
  const severityOrder: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 };
  gaps.sort((a, b) => (severityOrder[a.severity] ?? 99) - (severityOrder[b.severity] ?? 99));

  return gaps;
}

// ─── Risk Propagation Analyzer ────────────────────────────────────────────────

/**
 * Propagate risk scores through the graph using a weighted, dampened model.
 *
 * Each node's residual risk = inherent risk * product(1 - edge_weight * dampening_factor)
 * along the shortest path from each connected threat.
 *
 * @param graph      The knowledge graph
 * @param threats    Map of threat node id → base risk score (0-1)
 * @param dampening  Dampening factor per hop (default 0.6)
 */
export function propagateRisk(
  graph: KnowledgeGraph,
  threats: Map<string, number>,
  dampening: number = 0.6,
): RiskScore[] {
  const scores: RiskScore[] = [];
  const allNodes = graph.getAllNodes();

  for (const node of allNodes) {
    if (node.type === ComplianceType.THREAT) continue;

    let maxRisk = 0;
    let worstPath: string[] = [];

    for (const [threatId, baseRisk] of threats) {
      const path = graph.findPath(threatId, node.id);
      if (path.length === 0) continue;

      let propagatedRisk = baseRisk;
      for (let i = 0; i < path.length - 1; i++) {
        const edges = graph
          .getOutEdges(path[i])
          .filter((e) => e.to === path[i + 1]);
        const maxWeight = edges.reduce((max, e) => Math.max(max, e.weight), 0);
        propagatedRisk *= 1 - maxWeight * dampening;
      }

      if (propagatedRisk > maxRisk) {
        maxRisk = propagatedRisk;
        worstPath = path;
      }
    }

    if (maxRisk > 0) {
      scores.push({
        nodeId: node.id,
        nodeName: node.name,
        inherentRisk: Math.round(maxRisk * 100) / 100,
        residualRisk: Math.round(maxRisk * 100) / 100,
        propagationPath: worstPath,
      });
    }
  }

  scores.sort((a, b) => b.inherentRisk - a.inherentRisk);
  return scores;
}

// ─── Pre-built Framework Knowledge ────────────────────────────────────────────

/**
 * Seed a KnowledgeGraph with nodes and edges for major global frameworks.
 *
 * Covers: ISO 27001, SOC 2, NIST CSF, HIPAA, PCI DSS, GDPR, FedRAMP, CMMC,
 * CIS Controls, DORA, NIS2, and the EU AI Act.
 */
export function seedFrameworkKnowledge(): KnowledgeGraph {
  const g = new KnowledgeGraph();

  // ── Frameworks ──────────────────────────────────────────────────────────

  const frameworks: ComplianceNode[] = [
    { id: "iso27001", type: ComplianceType.FRAMEWORK, name: "ISO/IEC 27001:2022", properties: { standard: "ISO", version: "2022", scope: "information security" }, tags: ["international", "isms"] },
    { id: "soc2", type: ComplianceType.FRAMEWORK, name: "SOC 2 Type II", properties: { standard: "AICPA", version: "2017", scope: "service organisations" }, tags: ["us", "trust-services"] },
    { id: "nist-csf", type: ComplianceType.FRAMEWORK, name: "NIST Cybersecurity Framework", properties: { standard: "NIST", version: "2.0", scope: "cybersecurity risk" }, tags: ["us", "critical-infrastructure"] },
    { id: "hipaa", type: ComplianceType.FRAMEWORK, name: "HIPAA", properties: { standard: "HHS", version: "1996/amended", scope: "protected health information" }, tags: ["us", "healthcare"] },
    { id: "pci-dss", type: ComplianceType.FRAMEWORK, name: "PCI DSS", properties: { standard: "PCI SSC", version: "4.0", scope: "cardholder data" }, tags: ["global", "payments"] },
    { id: "gdpr", type: ComplianceType.FRAMEWORK, name: "GDPR", properties: { standard: "EU", version: "2016/679", scope: "personal data" }, tags: ["eu", "privacy"] },
    { id: "fedramp", type: ComplianceType.FRAMEWORK, name: "FedRAMP", properties: { standard: "GSA", version: "Rev 5", scope: "federal cloud" }, tags: ["us", "government", "cloud"] },
    { id: "cmmc", type: ComplianceType.FRAMEWORK, name: "CMMC 2.0", properties: { standard: "DoD", version: "2.0", scope: "defense industrial base" }, tags: ["us", "defense"] },
    { id: "cis-controls", type: ComplianceType.FRAMEWORK, name: "CIS Controls v8", properties: { standard: "CIS", version: "8", scope: "cyber hygiene" }, tags: ["global", "prescriptive"] },
    { id: "dora", type: ComplianceType.FRAMEWORK, name: "DORA", properties: { standard: "EU", version: "2022/2554", scope: "digital operational resilience" }, tags: ["eu", "financial"] },
    { id: "nis2", type: ComplianceType.FRAMEWORK, name: "NIS2 Directive", properties: { standard: "EU", version: "2022/2555", scope: "network and information systems" }, tags: ["eu", "critical-infrastructure"] },
    { id: "eu-ai-act", type: ComplianceType.FRAMEWORK, name: "EU AI Act", properties: { standard: "EU", version: "2024/1689", scope: "artificial intelligence" }, tags: ["eu", "ai"] },
  ];

  for (const fw of frameworks) g.addNode(fw);

  // ── Controls (representative subset per framework) ──────────────────────

  const controls: ComplianceNode[] = [
    // ISO 27001 Annex A
    { id: "iso27001:A.5.1", type: ComplianceType.CONTROL, name: "Policies for Information Security", properties: { framework: "iso27001", category: "organisational", weight: 1 } },
    { id: "iso27001:A.5.2", type: ComplianceType.CONTROL, name: "Information Security Roles & Responsibilities", properties: { framework: "iso27001", category: "organisational", weight: 1 } },
    { id: "iso27001:A.6.1", type: ComplianceType.CONTROL, name: "Screening", properties: { framework: "iso27001", category: "people", weight: 0.8 } },
    { id: "iso27001:A.8.1", type: ComplianceType.CONTROL, name: "User Endpoint Devices", properties: { framework: "iso27001", category: "technological", weight: 1 } },
    { id: "iso27001:A.8.2", type: ComplianceType.CONTROL, name: "Privileged Access Rights", properties: { framework: "iso27001", category: "technological", weight: 1 } },
    { id: "iso27001:A.8.3", type: ComplianceType.CONTROL, name: "Information Access Restriction", properties: { framework: "iso27001", category: "technological", weight: 1 } },
    { id: "iso27001:A.8.5", type: ComplianceType.CONTROL, name: "Secure Authentication", properties: { framework: "iso27001", category: "technological", weight: 1 } },
    { id: "iso27001:A.8.6", type: ComplianceType.CONTROL, name: "Capacity Management", properties: { framework: "iso27001", category: "technological", weight: 0.7 } },
    { id: "iso27001:A.8.7", type: ComplianceType.CONTROL, name: "Protection Against Malware", properties: { framework: "iso27001", category: "technological", weight: 1 } },
    { id: "iso27001:A.8.8", type: ComplianceType.CONTROL, name: "Management of Technical Vulnerabilities", properties: { framework: "iso27001", category: "technological", weight: 1 } },
    { id: "iso27001:A.8.9", type: ComplianceType.CONTROL, name: "Configuration Management", properties: { framework: "iso27001", category: "technological", weight: 0.9 } },
    { id: "iso27001:A.8.10", type: ComplianceType.CONTROL, name: "Information Deletion", properties: { framework: "iso27001", category: "technological", weight: 0.7 } },
    { id: "iso27001:A.8.11", type: ComplianceType.CONTROL, name: "Data Masking", properties: { framework: "iso27001", category: "technological", weight: 0.8 } },
    { id: "iso27001:A.8.12", type: ComplianceType.CONTROL, name: "Data Leakage Prevention", properties: { framework: "iso27001", category: "technological", weight: 1 } },
    { id: "iso27001:A.8.13", type: ComplianceType.CONTROL, name: "Information Backup", properties: { framework: "iso27001", category: "technological", weight: 1 } },
    { id: "iso27001:A.8.14", type: ComplianceType.CONTROL, name: "Redundancy of Information Processing", properties: { framework: "iso27001", category: "technological", weight: 0.8 } },
    { id: "iso27001:A.8.15", type: ComplianceType.CONTROL, name: "Logging", properties: { framework: "iso27001", category: "technological", weight: 1 } },
    { id: "iso27001:A.8.16", type: ComplianceType.CONTROL, name: "Monitoring Activities", properties: { framework: "iso27001", category: "technological", weight: 1 } },
    { id: "iso27001:A.8.23", type: ComplianceType.CONTROL, name: "Web Filtering", properties: { framework: "iso27001", category: "technological", weight: 0.8 } },
    { id: "iso27001:A.8.24", type: ComplianceType.CONTROL, name: "Use of Cryptography", properties: { framework: "iso27001", category: "technological", weight: 1 } },

    // SOC 2 Trust Services Criteria
    { id: "soc2:CC1.1", type: ComplianceType.CONTROL, name: "COSO Principle 1 — Integrity & Ethics", properties: { framework: "soc2", category: "governance", weight: 1 } },
    { id: "soc2:CC2.1", type: ComplianceType.CONTROL, name: "Internal Communication", properties: { framework: "soc2", category: "communication", weight: 0.9 } },
    { id: "soc2:CC3.1", type: ComplianceType.CONTROL, name: "Risk Assessment", properties: { framework: "soc2", category: "risk", weight: 1 } },
    { id: "soc2:CC4.1", type: ComplianceType.CONTROL, name: "Monitoring Controls", properties: { framework: "soc2", category: "monitoring", weight: 1 } },
    { id: "soc2:CC5.1", type: ComplianceType.CONTROL, name: "Control Activities", properties: { framework: "soc2", category: "control-activities", weight: 1 } },
    { id: "soc2:CC6.1", type: ComplianceType.CONTROL, name: "Logical Access Controls", properties: { framework: "soc2", category: "logical-access", weight: 1 } },
    { id: "soc2:CC6.2", type: ComplianceType.CONTROL, name: "User Authentication", properties: { framework: "soc2", category: "logical-access", weight: 1 } },
    { id: "soc2:CC6.3", type: ComplianceType.CONTROL, name: "User Authorization", properties: { framework: "soc2", category: "logical-access", weight: 1 } },
    { id: "soc2:CC7.1", type: ComplianceType.CONTROL, name: "System Operations", properties: { framework: "soc2", category: "operations", weight: 1 } },
    { id: "soc2:CC7.2", type: ComplianceType.CONTROL, name: "Change Management", properties: { framework: "soc2", category: "operations", weight: 1 } },
    { id: "soc2:CC8.1", type: ComplianceType.CONTROL, name: "Risk Mitigation", properties: { framework: "soc2", category: "risk", weight: 1 } },
    { id: "soc2:CC9.1", type: ComplianceType.CONTROL, name: "Vendor Management", properties: { framework: "soc2", category: "vendor", weight: 0.9 } },

    // NIST CSF 2.0
    { id: "nist-csf:GV.1", type: ComplianceType.CONTROL, name: "Organizational Context", properties: { framework: "nist-csf", category: "govern", weight: 1 } },
    { id: "nist-csf:GV.2", type: ComplianceType.CONTROL, name: "Risk Management Strategy", properties: { framework: "nist-csf", category: "govern", weight: 1 } },
    { id: "nist-csf:GV.3", type: ComplianceType.CONTROL, name: "Roles, Responsibilities & Authorities", properties: { framework: "nist-csf", category: "govern", weight: 1 } },
    { id: "nist-csf:GV.4", type: ComplianceType.CONTROL, name: "Critical Infrastructure", properties: { framework: "nist-csf", category: "govern", weight: 0.9 } },
    { id: "nist-csf:ID.1", type: ComplianceType.CONTROL, name: "Asset Management", properties: { framework: "nist-csf", category: "identify", weight: 1 } },
    { id: "nist-csf:ID.2", type: ComplianceType.CONTROL, name: "Risk Assessment", properties: { framework: "nist-csf", category: "identify", weight: 1 } },
    { id: "nist-csf:PR.1", type: ComplianceType.CONTROL, name: "Identity Management & Access Control", properties: { framework: "nist-csf", category: "protect", weight: 1 } },
    { id: "nist-csf:PR.2", type: ComplianceType.CONTROL, name: "Awareness & Training", properties: { framework: "nist-csf", category: "protect", weight: 0.9 } },
    { id: "nist-csf:PR.3", type: ComplianceType.CONTROL, name: "Data Security", properties: { framework: "nist-csf", category: "protect", weight: 1 } },
    { id: "nist-csf:PR.4", type: ComplianceType.CONTROL, name: "Information Protection Processes", properties: { framework: "nist-csf", category: "protect", weight: 1 } },
    { id: "nist-csf:PR.5", type: ComplianceType.CONTROL, name: "Protective Technology", properties: { framework: "nist-csf", category: "protect", weight: 1 } },
    { id: "nist-csf:DE.1", type: ComplianceType.CONTROL, name: "Continuous Monitoring", properties: { framework: "nist-csf", category: "detect", weight: 1 } },
    { id: "nist-csf:DE.2", type: ComplianceType.CONTROL, name: "Adverse Event Analysis", properties: { framework: "nist-csf", category: "detect", weight: 1 } },
    { id: "nist-csf:RS.1", type: ComplianceType.CONTROL, name: "Incident Management", properties: { framework: "nist-csf", category: "respond", weight: 1 } },
    { id: "nist-csf:RS.2", type: ComplianceType.CONTROL, name: "Incident Analysis", properties: { framework: "nist-csf", category: "respond", weight: 1 } },
    { id: "nist-csf:RC.1", type: ComplianceType.CONTROL, name: "Incident Recovery Plan", properties: { framework: "nist-csf", category: "recover", weight: 1 } },

    // HIPAA
    { id: "hipaa:164.308", type: ComplianceType.CONTROL, name: "Administrative Safeguards", properties: { framework: "hipaa", category: "administrative", weight: 1 } },
    { id: "hipaa:164.310", type: ComplianceType.CONTROL, name: "Physical Safeguards", properties: { framework: "hipaa", category: "physical", weight: 1 } },
    { id: "hipaa:164.312", type: ComplianceType.CONTROL, name: "Technical Safeguards", properties: { framework: "hipaa", category: "technical", weight: 1 } },
    { id: "hipaa:164.314", type: ComplianceType.CONTROL, name: "Organizational Requirements", properties: { framework: "hipaa", category: "organizational", weight: 0.9 } },
    { id: "hipaa:164.502", type: ComplianceType.CONTROL, name: "Uses and Disclosures of PHI", properties: { framework: "hipaa", category: "privacy", weight: 1 } },
    { id: "hipaa:164.504", type: ComplianceType.CONTROL, name: "Business Associate Contracts", properties: { framework: "hipaa", category: "privacy", weight: 0.9 } },
    { id: "hipaa:164.520", type: ComplianceType.CONTROL, name: "Notice of Privacy Practices", properties: { framework: "hipaa", category: "privacy", weight: 0.8 } },
    { id: "hipaa:164.530", type: ComplianceType.CONTROL, name: "Privacy Policies and Procedures", properties: { framework: "hipaa", category: "privacy", weight: 0.9 } },

    // PCI DSS 4.0
    { id: "pci-dss:1", type: ComplianceType.CONTROL, name: "Install and Maintain Network Security Controls", properties: { framework: "pci-dss", category: "network", weight: 1 } },
    { id: "pci-dss:2", type: ComplianceType.CONTROL, name: "Apply Secure Configurations", properties: { framework: "pci-dss", category: "configuration", weight: 1 } },
    { id: "pci-dss:3", type: ComplianceType.CONTROL, name: "Protect Stored Account Data", properties: { framework: "pci-dss", category: "data-protection", weight: 1 } },
    { id: "pci-dss:4", type: ComplianceType.CONTROL, name: "Protect Cardholder Data with Strong Cryptography During Transmission", properties: { framework: "pci-dss", category: "data-protection", weight: 1 } },
    { id: "pci-dss:5", type: ComplianceType.CONTROL, name: "Protect All Systems and Networks from Malicious Software", properties: { framework: "pci-dss", category: "malware", weight: 1 } },
    { id: "pci-dss:6", type: ComplianceType.CONTROL, name: "Develop and Maintain Secure Systems and Software", properties: { framework: "pci-dss", category: "secure-sdlc", weight: 1 } },
    { id: "pci-dss:7", type: ComplianceType.CONTROL, name: "Restrict Access to System Components by Business Need to Know", properties: { framework: "pci-dss", category: "access-control", weight: 1 } },
    { id: "pci-dss:8", type: ComplianceType.CONTROL, name: "Identify Users and Authenticate Access", properties: { framework: "pci-dss", category: "identity", weight: 1 } },
    { id: "pci-dss:9", type: ComplianceType.CONTROL, name: "Restrict Physical Access to Cardholder Data", properties: { framework: "pci-dss", category: "physical", weight: 1 } },
    { id: "pci-dss:10", type: ComplianceType.CONTROL, name: "Log and Monitor All Access", properties: { framework: "pci-dss", category: "logging", weight: 1 } },
    { id: "pci-dss:11", type: ComplianceType.CONTROL, name: "Test Security of Systems and Networks Regularly", properties: { framework: "pci-dss", category: "testing", weight: 1 } },
    { id: "pci-dss:12", type: ComplianceType.CONTROL, name: "Support Information Security with Organizational Policies and Programs", properties: { framework: "pci-dss", category: "governance", weight: 1 } },

    // GDPR
    { id: "gdpr:art5", type: ComplianceType.CONTROL, name: "Principles of Data Processing", properties: { framework: "gdpr", category: "principles", weight: 1 } },
    { id: "gdpr:art6", type: ComplianceType.CONTROL, name: "Lawful Basis for Processing", properties: { framework: "gdpr", category: "lawfulness", weight: 1 } },
    { id: "gdpr:art13", type: ComplianceType.CONTROL, name: "Information to Be Provided (Direct Collection)", properties: { framework: "gdpr", category: "transparency", weight: 0.9 } },
    { id: "gdpr:art17", type: ComplianceType.CONTROL, name: "Right to Erasure", properties: { framework: "gdpr", category: "data-subject-rights", weight: 1 } },
    { id: "gdpr:art20", type: ComplianceType.CONTROL, name: "Right to Data Portability", properties: { framework: "gdpr", category: "data-subject-rights", weight: 0.8 } },
    { id: "gdpr:art25", type: ComplianceType.CONTROL, name: "Data Protection by Design and Default", properties: { framework: "gdpr", category: "privacy-by-design", weight: 1 } },
    { id: "gdpr:art28", type: ComplianceType.CONTROL, name: "Processor Obligations", properties: { framework: "gdpr", category: "processor", weight: 1 } },
    { id: "gdpr:art30", type: ComplianceType.CONTROL, name: "Records of Processing Activities", properties: { framework: "gdpr", category: "documentation", weight: 0.9 } },
    { id: "gdpr:art32", type: ComplianceType.CONTROL, name: "Security of Processing", properties: { framework: "gdpr", category: "security", weight: 1 } },
    { id: "gdpr:art33", type: ComplianceType.CONTROL, name: "Breach Notification to Authority", properties: { framework: "gdpr", category: "incident", weight: 1 } },
    { id: "gdpr:art35", type: ComplianceType.CONTROL, name: "Data Protection Impact Assessment", properties: { framework: "gdpr", category: "risk-assessment", weight: 1 } },

    // FedRAMP
    { id: "fedramp:ac", type: ComplianceType.CONTROL, name: "Access Control Family", properties: { framework: "fedramp", category: "access-control", weight: 1 } },
    { id: "fedramp:au", type: ComplianceType.CONTROL, name: "Audit and Accountability Family", properties: { framework: "fedramp", category: "audit", weight: 1 } },
    { id: "fedramp:cm", type: ComplianceType.CONTROL, name: "Configuration Management Family", properties: { framework: "fedramp", category: "configuration", weight: 1 } },
    { id: "fedramp:ia", type: ComplianceType.CONTROL, name: "Identification and Authentication Family", properties: { framework: "fedramp", category: "identity", weight: 1 } },
    { id: "fedramp:ir", type: ComplianceType.CONTROL, name: "Incident Response Family", properties: { framework: "fedramp", category: "incident", weight: 1 } },
    { id: "fedramp:ra", type: ComplianceType.CONTROL, name: "Risk Assessment Family", properties: { framework: "fedramp", category: "risk", weight: 1 } },
    { id: "fedramp:sa", type: ComplianceType.CONTROL, name: "System and Services Acquisition Family", properties: { framework: "fedramp", category: "acquisition", weight: 1 } },
    { id: "fedramp:sc", type: ComplianceType.CONTROL, name: "System and Communications Protection Family", properties: { framework: "fedramp", category: "system-protection", weight: 1 } },
    { id: "fedramp:si", type: ComplianceType.CONTROL, name: "System and Information Integrity Family", properties: { framework: "fedramp", category: "integrity", weight: 1 } },

    // CMMC 2.0
    { id: "cmmc:ac", type: ComplianceType.CONTROL, name: "Access Control (CMMC)", properties: { framework: "cmmc", category: "access-control", weight: 1 } },
    { id: "cmmc:au", type: ComplianceType.CONTROL, name: "Audit and Accountability (CMMC)", properties: { framework: "cmmc", category: "audit", weight: 1 } },
    { id: "cmmc:cm", type: ComplianceType.CONTROL, name: "Configuration Management (CMMC)", properties: { framework: "cmmc", category: "configuration", weight: 1 } },
    { id: "cmmc:ia", type: ComplianceType.CONTROL, name: "Identification and Authentication (CMMC)", properties: { framework: "cmmc", category: "identity", weight: 1 } },
    { id: "cmmc:ir", type: ComplianceType.CONTROL, name: "Incident Response (CMMC)", properties: { framework: "cmmc", category: "incident", weight: 1 } },
    { id: "cmmc:mp", type: ComplianceType.CONTROL, name: "Media Protection (CMMC)", properties: { framework: "cmmc", category: "media", weight: 0.9 } },
    { id: "cmmc:pe", type: ComplianceType.CONTROL, name: "Physical Protection (CMMC)", properties: { framework: "cmmc", category: "physical", weight: 0.9 } },
    { id: "cmmc:sc", type: ComplianceType.CONTROL, name: "System and Communications Protection (CMMC)", properties: { framework: "cmmc", category: "system-protection", weight: 1 } },
    { id: "cmmc:si", type: ComplianceType.CONTROL, name: "System and Information Integrity (CMMC)", properties: { framework: "cmmc", category: "integrity", weight: 1 } },

    // CIS Controls v8
    { id: "cis:1", type: ComplianceType.CONTROL, name: "Inventory and Control of Enterprise Assets", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:2", type: ComplianceType.CONTROL, name: "Inventory and Control of Software Assets", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:3", type: ComplianceType.CONTROL, name: "Data Protection", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:4", type: ComplianceType.CONTROL, name: "Secure Configuration of Assets and Software", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:5", type: ComplianceType.CONTROL, name: "Account Management", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:6", type: ComplianceType.CONTROL, name: "Access Control Management", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:7", type: ComplianceType.CONTROL, name: "Continuous Vulnerability Management", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:8", type: ComplianceType.CONTROL, name: "Audit Log Management", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:9", type: ComplianceType.CONTROL, name: "Email and Web Browser Protections", properties: { framework: "cis-controls", category: "ig1", weight: 0.9 } },
    { id: "cis:10", type: ComplianceType.CONTROL, name: "Malware Defenses", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:11", type: ComplianceType.CONTROL, name: "Data Recovery", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:12", type: ComplianceType.CONTROL, name: "Network Infrastructure Management", properties: { framework: "cis-controls", category: "ig1", weight: 1 } },
    { id: "cis:13", type: ComplianceType.CONTROL, name: "Network Monitoring and Defense", properties: { framework: "cis-controls", category: "ig2", weight: 1 } },
    { id: "cis:14", type: ComplianceType.CONTROL, name: "Security Awareness and Skills Training", properties: { framework: "cis-controls", category: "ig1", weight: 0.9 } },
    { id: "cis:15", type: ComplianceType.CONTROL, name: "Service Provider Management", properties: { framework: "cis-controls", category: "ig2", weight: 0.9 } },
    { id: "cis:16", type: ComplianceType.CONTROL, name: "Application Software Security", properties: { framework: "cis-controls", category: "ig2", weight: 1 } },
    { id: "cis:17", type: ComplianceType.CONTROL, name: "Incident Response Management", properties: { framework: "cis-controls", category: "ig2", weight: 1 } },
    { id: "cis:18", type: ComplianceType.CONTROL, name: "Penetration Testing", properties: { framework: "cis-controls", category: "ig2", weight: 0.9 } },

    // DORA
    { id: "dora:art5", type: ComplianceType.CONTROL, name: "ICT Risk Management Framework", properties: { framework: "dora", category: "risk-management", weight: 1 } },
    { id: "dora:art6", type: ComplianceType.CONTROL, name: "ICT Systems, Protocols and Tools", properties: { framework: "dora", category: "ict-systems", weight: 1 } },
    { id: "dora:art7", type: ComplianceType.CONTROL, name: "Identification of ICT Risk", properties: { framework: "dora", category: "risk-identification", weight: 1 } },
    { id: "dora:art8", type: ComplianceType.CONTROL, name: "Protection and Prevention Measures", properties: { framework: "dora", category: "protection", weight: 1 } },
    { id: "dora:art9", type: ComplianceType.CONTROL, name: "Detection Capabilities", properties: { framework: "dora", category: "detection", weight: 1 } },
    { id: "dora:art10", type: ComplianceType.CONTROL, name: "Response and Recovery", properties: { framework: "dora", category: "response-recovery", weight: 1 } },
    { id: "dora:art11", type: ComplianceType.CONTROL, name: "Backup Policies and Recovery Methods", properties: { framework: "dora", category: "backup-recovery", weight: 1 } },
    { id: "dora:art28", type: ComplianceType.CONTROL, name: "ICT Third-Party Risk Management", properties: { framework: "dora", category: "third-party", weight: 1 } },
    { id: "dora:art30", type: ComplianceType.CONTROL, name: "Register of Information", properties: { framework: "dora", category: "documentation", weight: 0.9 } },

    // NIS2
    { id: "nis2:art20", type: ComplianceType.CONTROL, name: "Cybersecurity Risk Management Measures", properties: { framework: "nis2", category: "risk-management", weight: 1 } },
    { id: "nis2:art21", type: ComplianceType.CONTROL, name: "Cybersecurity Risk Management Measures (Detailed)", properties: { framework: "nis2", category: "risk-management", weight: 1 } },
    { id: "nis2:art22", type: ComplianceType.CONTROL, name: "EU-wide Coordinated Risk Assessments", properties: { framework: "nis2", category: "risk-assessment", weight: 0.9 } },
    { id: "nis2:art23", type: ComplianceType.CONTROL, name: "Cybersecurity Incident Reporting", properties: { framework: "nis2", category: "incident-reporting", weight: 1 } },
    { id: "nis2:art24", type: ComplianceType.CONTROL, name: "Domain Name Registration Data", properties: { framework: "nis2", category: "domain-security", weight: 0.7 } },
    { id: "nis2:art25", type: ComplianceType.CONTROL, name: "Supply Chain Security", properties: { framework: "nis2", category: "supply-chain", weight: 1 } },
    { id: "nis2:art26", type: ComplianceType.CONTROL, name: "Peer Reviews", properties: { framework: "nis2", category: "governance", weight: 0.8 } },

    // EU AI Act
    { id: "eu-ai-act:art9", type: ComplianceType.CONTROL, name: "Risk Management System for AI", properties: { framework: "eu-ai-act", category: "risk-management", weight: 1 } },
    { id: "eu-ai-act:art10", type: ComplianceType.CONTROL, name: "Data and Data Governance for AI", properties: { framework: "eu-ai-act", category: "data-governance", weight: 1 } },
    { id: "eu-ai-act:art11", type: ComplianceType.CONTROL, name: "Technical Documentation", properties: { framework: "eu-ai-act", category: "documentation", weight: 1 } },
    { id: "eu-ai-act:art12", type: ComplianceType.CONTROL, name: "Record-Keeping (AI)", properties: { framework: "eu-ai-act", category: "logging", weight: 1 } },
    { id: "eu-ai-act:art13", type: ComplianceType.CONTROL, name: "Transparency and Information to Deployers", properties: { framework: "eu-ai-act", category: "transparency", weight: 1 } },
    { id: "eu-ai-act:art14", type: ComplianceType.CONTROL, name: "Human Oversight", properties: { framework: "eu-ai-act", category: "oversight", weight: 1 } },
    { id: "eu-ai-act:art15", type: ComplianceType.CONTROL, name: "Accuracy, Robustness and Cybersecurity of AI", properties: { framework: "eu-ai-act", category: "security", weight: 1 } },
    { id: "eu-ai-act:art16", type: ComplianceType.CONTROL, name: "Quality Management System (AI)", properties: { framework: "eu-ai-act", category: "quality", weight: 1 } },
    { id: "eu-ai-act:art27", type: ComplianceType.CONTROL, name: "Fundamental Rights Impact Assessment", properties: { framework: "eu-ai-act", category: "impact-assessment", weight: 1 } },
  ];

  for (const ctrl of controls) g.addNode(ctrl);

  // ── Threats ─────────────────────────────────────────────────────────────

  const threats: ComplianceNode[] = [
    { id: "threat:ransomware", type: ComplianceType.THREAT, name: "Ransomware Attack", properties: { severity: "critical", mitre: "T1486" }, tags: ["malware", "encryption"] },
    { id: "threat:phishing", type: ComplianceType.THREAT, name: "Phishing / Social Engineering", properties: { severity: "high", mitre: "T1566" }, tags: ["social-engineering"] },
    { id: "threat:insider", type: ComplianceType.THREAT, name: "Insider Threat", properties: { severity: "high", mitre: "T1078" }, tags: ["insider", "privilege"] },
    { id: "threat:supply-chain", type: ComplianceType.THREAT, name: "Supply Chain Compromise", properties: { severity: "critical", mitre: "T1195" }, tags: ["supply-chain"] },
    { id: "threat:ddos", type: ComplianceType.THREAT, name: "Distributed Denial of Service", properties: { severity: "high", mitre: "T1498" }, tags: ["availability"] },
    { id: "threat:data-breach", type: ComplianceType.THREAT, name: "Data Breach / Exfiltration", properties: { severity: "critical", mitre: "T1041" }, tags: ["data-loss"] },
    { id: "threat:apt", type: ComplianceType.THREAT, name: "Advanced Persistent Threat", properties: { severity: "critical", mitre: "T1059" }, tags: ["nation-state"] },
    { id: "threat:zero-day", type: ComplianceType.THREAT, name: "Zero-Day Exploit", properties: { severity: "critical", mitre: "T1203" }, tags: ["vulnerability"] },
    { id: "threat:credential-stuffing", type: ComplianceType.THREAT, name: "Credential Stuffing", properties: { severity: "high", mitre: "T1110" }, tags: ["authentication"] },
    { id: "threat:ai-adversarial", type: ComplianceType.THREAT, name: "Adversarial AI / Model Poisoning", properties: { severity: "high", mitre: "ML001" }, tags: ["ai"] },
  ];

  for (const t of threats) g.addNode(t);

  // ── Technologies ────────────────────────────────────────────────────────

  const technologies: ComplianceNode[] = [
    { id: "tech:siem", type: ComplianceType.TECHNOLOGY, name: "SIEM Platform", properties: { category: "monitoring", vendors: "Splunk, Sentinel, Elastic" } },
    { id: "tech:edr", type: ComplianceType.TECHNOLOGY, name: "Endpoint Detection & Response", properties: { category: "endpoint", vendors: "CrowdStrike, SentinelOne, Defender" } },
    { id: "tech:iam", type: ComplianceType.TECHNOLOGY, name: "Identity & Access Management", properties: { category: "identity", vendors: "Okta, Entra ID, Ping" } },
    { id: "tech:pam", type: ComplianceType.TECHNOLOGY, name: "Privileged Access Management", properties: { category: "identity", vendors: "CyberArk, BeyondTrust" } },
    { id: "tech:dlp", type: ComplianceType.TECHNOLOGY, name: "Data Loss Prevention", properties: { category: "data-protection", vendors: "Symantec, Digital Guardian" } },
    { id: "tech:encryption", type: ComplianceType.TECHNOLOGY, name: "Encryption & Key Management", properties: { category: "cryptography", vendors: "AWS KMS, HashiCorp Vault" } },
    { id: "tech:vuln-scanner", type: ComplianceType.TECHNOLOGY, name: "Vulnerability Management", properties: { category: "vulnerability", vendors: "Tenable, Qualys, Rapid7" } },
    { id: "tech:firewall", type: ComplianceType.TECHNOLOGY, name: "Next-Gen Firewall", properties: { category: "network", vendors: "Palo Alto, Fortinet, Check Point" } },
    { id: "tech:waf", type: ComplianceType.TECHNOLOGY, name: "Web Application Firewall", properties: { category: "application", vendors: "Cloudflare, AWS WAF, F5" } },
    { id: "tech:backup", type: ComplianceType.TECHNOLOGY, name: "Backup & Disaster Recovery", properties: { category: "resilience", vendors: "Veeam, Commvault, AWS Backup" } },
    { id: "tech:grc-platform", type: ComplianceType.TECHNOLOGY, name: "GRC Platform", properties: { category: "governance", vendors: "ServiceNow, Archer, A2Z SOC" } },
    { id: "tech:casb", type: ComplianceType.TECHNOLOGY, name: "Cloud Access Security Broker", properties: { category: "cloud", vendors: "Netskope, Zscaler, Microsoft Defender" } },
    { id: "tech:code-scanner", type: ComplianceType.TECHNOLOGY, name: "Static/Dynamic Application Security Testing", properties: { category: "application-security", vendors: "Snyk, Checkmarx, Veracode" } },
    { id: "tech:ai-monitor", type: ComplianceType.TECHNOLOGY, name: "AI Model Monitoring & Governance", properties: { category: "ai-governance", vendors: "Fiddler, Arize, Arthur" } },
  ];

  for (const t of technologies) g.addNode(t);

  // ── Framework → Control edges (REQUIRES) ────────────────────────────────

  const fwCtrlEdges: Array<{ fw: string; ctrl: string }> = [
    // ISO 27001
    ...["iso27001:A.5.1","iso27001:A.5.2","iso27001:A.6.1","iso27001:A.8.1","iso27001:A.8.2","iso27001:A.8.3","iso27001:A.8.5","iso27001:A.8.6","iso27001:A.8.7","iso27001:A.8.8","iso27001:A.8.9","iso27001:A.8.10","iso27001:A.8.11","iso27001:A.8.12","iso27001:A.8.13","iso27001:A.8.14","iso27001:A.8.15","iso27001:A.8.16","iso27001:A.8.23","iso27001:A.8.24"].map(c => ({ fw: "iso27001", ctrl: c })),
    // SOC 2
    ...["soc2:CC1.1","soc2:CC2.1","soc2:CC3.1","soc2:CC4.1","soc2:CC5.1","soc2:CC6.1","soc2:CC6.2","soc2:CC6.3","soc2:CC7.1","soc2:CC7.2","soc2:CC8.1","soc2:CC9.1"].map(c => ({ fw: "soc2", ctrl: c })),
    // NIST CSF
    ...["nist-csf:GV.1","nist-csf:GV.2","nist-csf:GV.3","nist-csf:GV.4","nist-csf:ID.1","nist-csf:ID.2","nist-csf:PR.1","nist-csf:PR.2","nist-csf:PR.3","nist-csf:PR.4","nist-csf:PR.5","nist-csf:DE.1","nist-csf:DE.2","nist-csf:RS.1","nist-csf:RS.2","nist-csf:RC.1"].map(c => ({ fw: "nist-csf", ctrl: c })),
    // HIPAA
    ...["hipaa:164.308","hipaa:164.310","hipaa:164.312","hipaa:164.314","hipaa:164.502","hipaa:164.504","hipaa:164.520","hipaa:164.530"].map(c => ({ fw: "hipaa", ctrl: c })),
    // PCI DSS
    ...["pci-dss:1","pci-dss:2","pci-dss:3","pci-dss:4","pci-dss:5","pci-dss:6","pci-dss:7","pci-dss:8","pci-dss:9","pci-dss:10","pci-dss:11","pci-dss:12"].map(c => ({ fw: "pci-dss", ctrl: c })),
    // GDPR
    ...["gdpr:art5","gdpr:art6","gdpr:art13","gdpr:art17","gdpr:art20","gdpr:art25","gdpr:art28","gdpr:art30","gdpr:art32","gdpr:art33","gdpr:art35"].map(c => ({ fw: "gdpr", ctrl: c })),
    // FedRAMP
    ...["fedramp:ac","fedramp:au","fedramp:cm","fedramp:ia","fedramp:ir","fedramp:ra","fedramp:sa","fedramp:sc","fedramp:si"].map(c => ({ fw: "fedramp", ctrl: c })),
    // CMMC
    ...["cmmc:ac","cmmc:au","cmmc:cm","cmmc:ia","cmmc:ir","cmmc:mp","cmmc:pe","cmmc:sc","cmmc:si"].map(c => ({ fw: "cmmc", ctrl: c })),
    // CIS Controls
    ...["cis:1","cis:2","cis:3","cis:4","cis:5","cis:6","cis:7","cis:8","cis:9","cis:10","cis:11","cis:12","cis:13","cis:14","cis:15","cis:16","cis:17","cis:18"].map(c => ({ fw: "cis-controls", ctrl: c })),
    // DORA
    ...["dora:art5","dora:art6","dora:art7","dora:art8","dora:art9","dora:art10","dora:art11","dora:art28","dora:art30"].map(c => ({ fw: "dora", ctrl: c })),
    // NIS2
    ...["nis2:art20","nis2:art21","nis2:art22","nis2:art23","nis2:art24","nis2:art25","nis2:art26"].map(c => ({ fw: "nis2", ctrl: c })),
    // EU AI Act
    ...["eu-ai-act:art9","eu-ai-act:art10","eu-ai-act:art11","eu-ai-act:art12","eu-ai-act:art13","eu-ai-act:art14","eu-ai-act:art15","eu-ai-act:art16","eu-ai-act:art27"].map(c => ({ fw: "eu-ai-act", ctrl: c })),
  ];

  for (const { fw, ctrl } of fwCtrlEdges) {
    g.addEdge({ from: fw, to: ctrl, relationship: RelationshipType.REQUIRES, weight: 1 });
  }

  // ── Technology → Control edges (IMPLEMENTS) ─────────────────────────────

  const techCtrlEdges: Array<{ tech: string; ctrl: string; weight: number }> = [
    // SIEM
    { tech: "tech:siem", ctrl: "iso27001:A.8.15", weight: 0.9 },
    { tech: "tech:siem", ctrl: "iso27001:A.8.16", weight: 0.95 },
    { tech: "tech:siem", ctrl: "soc2:CC4.1", weight: 0.9 },
    { tech: "tech:siem", ctrl: "soc2:CC7.1", weight: 0.85 },
    { tech: "tech:siem", ctrl: "nist-csf:DE.1", weight: 0.95 },
    { tech: "tech:siem", ctrl: "nist-csf:DE.2", weight: 0.9 },
    { tech: "tech:siem", ctrl: "pci-dss:10", weight: 0.95 },
    { tech: "tech:siem", ctrl: "fedramp:au", weight: 0.9 },
    { tech: "tech:siem", ctrl: "dora:art9", weight: 0.9 },
    { tech: "tech:siem", ctrl: "cis:8", weight: 0.95 },
    { tech: "tech:siem", ctrl: "cis:13", weight: 0.9 },
    // EDR
    { tech: "tech:edr", ctrl: "iso27001:A.8.7", weight: 0.9 },
    { tech: "tech:edr", ctrl: "pci-dss:5", weight: 0.9 },
    { tech: "tech:edr", ctrl: "cis:10", weight: 0.95 },
    { tech: "tech:edr", ctrl: "nist-csf:PR.5", weight: 0.85 },
    // IAM
    { tech: "tech:iam", ctrl: "iso27001:A.8.2", weight: 0.9 },
    { tech: "tech:iam", ctrl: "iso27001:A.8.5", weight: 0.95 },
    { tech: "tech:iam", ctrl: "soc2:CC6.1", weight: 0.95 },
    { tech: "tech:iam", ctrl: "soc2:CC6.2", weight: 0.95 },
    { tech: "tech:iam", ctrl: "soc2:CC6.3", weight: 0.9 },
    { tech: "tech:iam", ctrl: "nist-csf:PR.1", weight: 0.95 },
    { tech: "tech:iam", ctrl: "pci-dss:7", weight: 0.9 },
    { tech: "tech:iam", ctrl: "pci-dss:8", weight: 0.95 },
    { tech: "tech:iam", ctrl: "hipaa:164.312", weight: 0.9 },
    { tech: "tech:iam", ctrl: "cis:5", weight: 0.9 },
    { tech: "tech:iam", ctrl: "cis:6", weight: 0.95 },
    // PAM
    { tech: "tech:pam", ctrl: "iso27001:A.8.2", weight: 0.95 },
    { tech: "tech:pam", ctrl: "soc2:CC6.3", weight: 0.9 },
    { tech: "tech:pam", ctrl: "cmmc:ac", weight: 0.9 },
    // DLP
    { tech: "tech:dlp", ctrl: "iso27001:A.8.12", weight: 0.95 },
    { tech: "tech:dlp", ctrl: "pci-dss:3", weight: 0.85 },
    { tech: "tech:dlp", ctrl: "gdpr:art32", weight: 0.85 },
    { tech: "tech:dlp", ctrl: "hipaa:164.312", weight: 0.8 },
    // Encryption
    { tech: "tech:encryption", ctrl: "iso27001:A.8.24", weight: 0.95 },
    { tech: "tech:encryption", ctrl: "pci-dss:3", weight: 0.9 },
    { tech: "tech:encryption", ctrl: "pci-dss:4", weight: 0.95 },
    { tech: "tech:encryption", ctrl: "gdpr:art32", weight: 0.9 },
    { tech: "tech:encryption", ctrl: "hipaa:164.312", weight: 0.9 },
    // Vulnerability Scanner
    { tech: "tech:vuln-scanner", ctrl: "iso27001:A.8.8", weight: 0.95 },
    { tech: "tech:vuln-scanner", ctrl: "pci-dss:11", weight: 0.95 },
    { tech: "tech:vuln-scanner", ctrl: "cis:7", weight: 0.95 },
    { tech: "tech:vuln-scanner", ctrl: "nist-csf:DE.1", weight: 0.8 },
    // Firewall
    { tech: "tech:firewall", ctrl: "iso27001:A.8.23", weight: 0.85 },
    { tech: "tech:firewall", ctrl: "pci-dss:1", weight: 0.95 },
    { tech: "tech:firewall", ctrl: "cis:12", weight: 0.9 },
    { tech: "tech:firewall", ctrl: "fedramp:sc", weight: 0.9 },
    // WAF
    { tech: "tech:waf", ctrl: "pci-dss:6", weight: 0.85 },
    { tech: "tech:waf", ctrl: "cis:16", weight: 0.8 },
    // Backup
    { tech: "tech:backup", ctrl: "iso27001:A.8.13", weight: 0.95 },
    { tech: "tech:backup", ctrl: "iso27001:A.8.14", weight: 0.85 },
    { tech: "tech:backup", ctrl: "cis:11", weight: 0.95 },
    { tech: "tech:backup", ctrl: "dora:art11", weight: 0.9 },
    // GRC Platform
    { tech: "tech:grc-platform", ctrl: "iso27001:A.5.1", weight: 0.85 },
    { tech: "tech:grc-platform", ctrl: "soc2:CC1.1", weight: 0.8 },
    { tech: "tech:grc-platform", ctrl: "dora:art30", weight: 0.9 },
    { tech: "tech:grc-platform", ctrl: "gdpr:art30", weight: 0.85 },
    // CASB
    { tech: "tech:casb", ctrl: "iso27001:A.8.3", weight: 0.85 },
    { tech: "tech:casb", ctrl: "soc2:CC6.1", weight: 0.8 },
    { tech: "tech:casb", ctrl: "cis:3", weight: 0.8 },
    // Code Scanner
    { tech: "tech:code-scanner", ctrl: "pci-dss:6", weight: 0.9 },
    { tech: "tech:code-scanner", ctrl: "cis:16", weight: 0.9 },
    { tech: "tech:code-scanner", ctrl: "soc2:CC7.2", weight: 0.8 },
    // AI Monitor
    { tech: "tech:ai-monitor", ctrl: "eu-ai-act:art9", weight: 0.85 },
    { tech: "tech:ai-monitor", ctrl: "eu-ai-act:art12", weight: 0.9 },
    { tech: "tech:ai-monitor", ctrl: "eu-ai-act:art15", weight: 0.85 },
  ];

  for (const { tech, ctrl, weight } of techCtrlEdges) {
    g.addEdge({ from: tech, to: ctrl, relationship: RelationshipType.IMPLEMENTS, weight });
  }

  // ── Threat → Control edges (MITIGATES) ──────────────────────────────────

  const threatCtrlEdges: Array<{ threat: string; ctrl: string; weight: number }> = [
    { threat: "threat:ransomware", ctrl: "iso27001:A.8.7", weight: 0.85 },
    { threat: "threat:ransomware", ctrl: "iso27001:A.8.13", weight: 0.9 },
    { threat: "threat:ransomware", ctrl: "cis:11", weight: 0.9 },
    { threat: "threat:phishing", ctrl: "iso27001:A.8.23", weight: 0.7 },
    { threat: "threat:phishing", ctrl: "cis:9", weight: 0.85 },
    { threat: "threat:phishing", ctrl: "cis:14", weight: 0.8 },
    { threat: "threat:insider", ctrl: "iso27001:A.8.2", weight: 0.9 },
    { threat: "threat:insider", ctrl: "iso27001:A.8.3", weight: 0.85 },
    { threat: "threat:insider", ctrl: "soc2:CC6.3", weight: 0.85 },
    { threat: "threat:supply-chain", ctrl: "soc2:CC9.1", weight: 0.85 },
    { threat: "threat:supply-chain", ctrl: "dora:art28", weight: 0.9 },
    { threat: "threat:supply-chain", ctrl: "nis2:art25", weight: 0.9 },
    { threat: "threat:supply-chain", ctrl: "cis:15", weight: 0.85 },
    { threat: "threat:ddos", ctrl: "pci-dss:1", weight: 0.7 },
    { threat: "threat:ddos", ctrl: "dora:art8", weight: 0.75 },
    { threat: "threat:data-breach", ctrl: "iso27001:A.8.12", weight: 0.9 },
    { threat: "threat:data-breach", ctrl: "gdpr:art32", weight: 0.9 },
    { threat: "threat:data-breach", ctrl: "pci-dss:3", weight: 0.9 },
    { threat: "threat:data-breach", ctrl: "hipaa:164.312", weight: 0.85 },
    { threat: "threat:apt", ctrl: "iso27001:A.8.16", weight: 0.8 },
    { threat: "threat:apt", ctrl: "nist-csf:DE.1", weight: 0.85 },
    { threat: "threat:apt", ctrl: "fedramp:au", weight: 0.8 },
    { threat: "threat:zero-day", ctrl: "iso27001:A.8.8", weight: 0.85 },
    { threat: "threat:zero-day", ctrl: "pci-dss:6", weight: 0.8 },
    { threat: "threat:zero-day", ctrl: "cis:7", weight: 0.85 },
    { threat: "threat:credential-stuffing", ctrl: "iso27001:A.8.5", weight: 0.9 },
    { threat: "threat:credential-stuffing", ctrl: "pci-dss:8", weight: 0.9 },
    { threat: "threat:credential-stuffing", ctrl: "soc2:CC6.2", weight: 0.9 },
    { threat: "threat:ai-adversarial", ctrl: "eu-ai-act:art9", weight: 0.85 },
    { threat: "threat:ai-adversarial", ctrl: "eu-ai-act:art15", weight: 0.9 },
    { threat: "threat:ai-adversarial", ctrl: "eu-ai-act:art14", weight: 0.8 },
  ];

  for (const { threat, ctrl, weight } of threatCtrlEdges) {
    g.addEdge({ from: threat, to: ctrl, relationship: RelationshipType.MITIGATES, weight });
  }

  // ── Cross-framework MAPS_TO edges ───────────────────────────────────────

  const crosswalkEdges: Array<{ from: string; to: string; weight: number; notes?: string }> = [
    // ISO 27001 ↔ SOC 2
    { from: "iso27001:A.8.15", to: "soc2:CC4.1", weight: 0.9, notes: "Logging ↔ Monitoring" },
    { from: "iso27001:A.8.16", to: "soc2:CC7.1", weight: 0.85, notes: "Monitoring ↔ System Operations" },
    { from: "iso27001:A.8.2", to: "soc2:CC6.3", weight: 0.9, notes: "Privileged Access ↔ Authorization" },
    { from: "iso27001:A.8.5", to: "soc2:CC6.2", weight: 0.9, notes: "Authentication ↔ User Authentication" },
    { from: "iso27001:A.5.1", to: "soc2:CC1.1", weight: 0.85, notes: "Policies ↔ Integrity & Ethics" },

    // ISO 27001 ↔ NIST CSF
    { from: "iso27001:A.8.2", to: "nist-csf:PR.1", weight: 0.95, notes: "Privileged Access ↔ IAM" },
    { from: "iso27001:A.8.16", to: "nist-csf:DE.1", weight: 0.9, notes: "Monitoring ↔ Continuous Monitoring" },
    { from: "iso27001:A.8.7", to: "nist-csf:PR.5", weight: 0.85, notes: "Malware ↔ Protective Technology" },
    { from: "iso27001:A.8.24", to: "nist-csf:PR.3", weight: 0.9, notes: "Cryptography ↔ Data Security" },

    // ISO 27001 ↔ PCI DSS
    { from: "iso27001:A.8.8", to: "pci-dss:11", weight: 0.9, notes: "Vuln Mgmt ↔ Testing" },
    { from: "iso27001:A.8.7", to: "pci-dss:5", weight: 0.9, notes: "Malware ↔ Malware Defenses" },
    { from: "iso27001:A.8.15", to: "pci-dss:10", weight: 0.95, notes: "Logging ↔ Log and Monitor" },

    // SOC 2 ↔ NIST CSF
    { from: "soc2:CC6.1", to: "nist-csf:PR.1", weight: 0.9, notes: "Logical Access ↔ IAM" },
    { from: "soc2:CC7.1", to: "nist-csf:DE.1", weight: 0.85, notes: "System Ops ↔ Monitoring" },

    // NIST CSF ↔ FedRAMP
    { from: "nist-csf:PR.1", to: "fedramp:ac", weight: 0.9, notes: "IAM ↔ Access Control" },
    { from: "nist-csf:DE.1", to: "fedramp:au", weight: 0.9, notes: "Monitoring ↔ Audit" },
    { from: "nist-csf:RS.1", to: "fedramp:ir", weight: 0.95, notes: "Incident Mgmt ↔ IR" },

    // NIST CSF ↔ CMMC
    { from: "nist-csf:PR.1", to: "cmmc:ac", weight: 0.9 },
    { from: "nist-csf:DE.1", to: "cmmc:au", weight: 0.85 },

    // FedRAMP ↔ CMMC (both NIST 800-53 based)
    { from: "fedramp:ac", to: "cmmc:ac", weight: 0.95, notes: "Same NIST 800-53 family" },
    { from: "fedramp:au", to: "cmmc:au", weight: 0.95 },
    { from: "fedramp:cm", to: "cmmc:cm", weight: 0.95 },
    { from: "fedramp:ia", to: "cmmc:ia", weight: 0.95 },
    { from: "fedramp:ir", to: "cmmc:ir", weight: 0.95 },
    { from: "fedramp:sc", to: "cmmc:sc", weight: 0.95 },
    { from: "fedramp:si", to: "cmmc:si", weight: 0.95 },

    // GDPR ↔ ISO 27001
    { from: "gdpr:art32", to: "iso27001:A.8.24", weight: 0.8, notes: "Security of Processing ↔ Cryptography" },
    { from: "gdpr:art32", to: "iso27001:A.8.12", weight: 0.75, notes: "Security of Processing ↔ DLP" },

    // DORA ↔ NIST CSF
    { from: "dora:art9", to: "nist-csf:DE.1", weight: 0.85, notes: "Detection ↔ Monitoring" },
    { from: "dora:art10", to: "nist-csf:RS.1", weight: 0.85, notes: "Response & Recovery ↔ Incident Mgmt" },
    { from: "dora:art8", to: "nist-csf:PR.5", weight: 0.8, notes: "Protection ↔ Protective Tech" },

    // NIS2 ↔ ISO 27001
    { from: "nis2:art20", to: "iso27001:A.5.1", weight: 0.8, notes: "Risk Mgmt ↔ Policies" },
    { from: "nis2:art23", to: "iso27001:A.8.16", weight: 0.75, notes: "Incident Reporting ↔ Monitoring" },

    // EU AI Act ↔ ISO 27001
    { from: "eu-ai-act:art15", to: "iso27001:A.8.8", weight: 0.7, notes: "AI Security ↔ Vuln Mgmt" },
    { from: "eu-ai-act:art12", to: "iso27001:A.8.15", weight: 0.75, notes: "AI Logging ↔ Logging" },
  ];

  for (const { from, to, weight, notes } of crosswalkEdges) {
    g.addEdge({
      from,
      to,
      relationship: RelationshipType.MAPS_TO,
      weight,
      metadata: notes ? { notes } : undefined,
    });
  }

  return g;
}

// ─── Exports ──────────────────────────────────────────────────────────────────

export default KnowledgeGraph;

/** Alias for backward compatibility */
export { KnowledgeGraph as ComplianceKnowledgeGraph };
