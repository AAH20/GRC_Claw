import { createHash } from 'node:crypto';

export type EvidenceGraphNodeType =
  | 'organization'
  | 'trust_score'
  | 'control'
  | 'evidence'
  | 'control_test'
  | 'zk_bundle'
  | 'risk_scenario'
  | 'threat_model'
  | 'compliance_pack'
  | 'framework'
  | 'agent_memory'
  | 'behavioral_anomaly'
  | 'saas_app'
  | 'attack_surface_finding'
  | 'pr_scan'
  | 'vendor_questionnaire'
  | 'data_store_asset'
  | 'agent_action'
  | 'exposure_signal'
  | 'knowledge_graph'
  | 'posture'
  | 'predictive_compliance'
  | 'compliance_marketplace'
  | 'zero_trust_audit'
  | 'automation'
  | 'policy_decision'
  | 'quantum_key_material'
  | 'nl_compliance_answer'
  | 'real_time_alert';

export type EvidenceGraphEdgeType =
  | 'owns'
  | 'scores'
  | 'proves'
  | 'tests'
  | 'seals'
  | 'quantifies'
  | 'threatens'
  | 'maps_to'
  | 'derived_from'
  | 'recommended_for'
  | 'observes'
  | 'gates'
  | 'answers'
  | 'classifies'
  | 'detects'
  | 'writes'
  | 'resolves'
  | 'has_posture'
  | 'derives'
  | 'forecasts'
  | 'extends'
  | 'verifies';

export type EvidenceGraphObjectKind = 'node' | 'edge';

export interface EvidenceGraphObject {
  orgSlug: string;
  graphId: string;
  objectKind: EvidenceGraphObjectKind;
  objectType: EvidenceGraphNodeType | EvidenceGraphEdgeType | string;
  label: string;
  source: string;
  sourceTable?: string;
  sourceId?: string;
  fromId?: string;
  toId?: string;
  framework?: string;
  controlIds?: string[];
  weight?: number;
  confidence?: number;
  payload?: Record<string, unknown>;
  objectHash: string;
  createdAt: string;
  updatedAt?: string;
}

export interface EvidenceGraphNode {
  id: string;
  type: string;
  label: string;
  source: string;
  weight: number;
  metadata?: Record<string, unknown>;
}

export interface EvidenceGraphEdge {
  id: string;
  type: string;
  from: string;
  to: string;
  label: string;
  confidence: number;
  metadata?: Record<string, unknown>;
}

export interface EvidenceGraphSnapshotInput {
  orgSlug: string;
  objects?: EvidenceGraphObject[];
  nodes?: EvidenceGraphNode[];
  edges?: EvidenceGraphEdge[];
  recommendations?: string[];
  generatedAt?: string;
  extraSummary?: Record<string, unknown>;
}

export interface EvidenceGraphSnapshot {
  ok: true;
  graph_hash: string;
  generated_at: string;
  organizationId: string;
  summary: Record<string, unknown>;
  nodes: EvidenceGraphNode[];
  edges: EvidenceGraphEdge[];
  recommendations: string[];
  objects: EvidenceGraphObject[];
}

type NewNodeObject = Omit<EvidenceGraphObject, 'objectKind' | 'objectHash' | 'createdAt' | 'updatedAt' | 'fromId' | 'toId'> & {
  createdAt?: string;
  updatedAt?: string;
};

type NewEdgeObject = Omit<EvidenceGraphObject, 'objectKind' | 'objectHash' | 'createdAt'> & {
  fromId: string;
  toId: string;
  createdAt?: string;
};

function stable(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stable);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>)
        .filter(([, nested]) => nested !== undefined)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([key, nested]) => [key, stable(nested)]),
    );
  }
  return value;
}

function stableStringify(value: unknown): string {
  return JSON.stringify(stable(value));
}

function sha256(value: unknown): string {
  return createHash('sha256').update(stableStringify(value)).digest('hex');
}

export function evidenceGraphId(prefix: string, value: unknown): string {
  return `${prefix}:${sha256(value).slice(0, 16)}`;
}

export function evidenceObjectHash(
  object: Omit<EvidenceGraphObject, 'objectHash' | 'createdAt' | 'updatedAt'> | EvidenceGraphObject,
): string {
  const { objectHash: _objectHash, createdAt: _createdAt, updatedAt: _updatedAt, ...hashable } = object as EvidenceGraphObject;
  return sha256(hashable);
}

export function nodeObject(input: NewNodeObject): EvidenceGraphObject {
  const base: Omit<EvidenceGraphObject, 'objectHash'> = {
    ...input,
    objectKind: 'node',
    createdAt: input.createdAt ?? new Date().toISOString(),
  };
  return { ...base, objectHash: evidenceObjectHash(base) };
}

export function edgeObject(input: NewEdgeObject): EvidenceGraphObject {
  const base: Omit<EvidenceGraphObject, 'objectHash'> = {
    ...input,
    objectKind: 'edge',
    createdAt: input.createdAt ?? new Date().toISOString(),
  };
  return { ...base, objectHash: evidenceObjectHash(base) };
}

function nodeMetadata(object: EvidenceGraphObject): Record<string, unknown> {
  return {
    source_table: object.sourceTable,
    source_id: object.sourceId,
    framework: object.framework,
    control_ids: object.controlIds,
    object_hash: object.objectHash,
    ...(object.payload ?? {}),
  };
}

function edgeMetadata(object: EvidenceGraphObject): Record<string, unknown> {
  return {
    source_table: object.sourceTable,
    source_id: object.sourceId,
    framework: object.framework,
    control_ids: object.controlIds,
    object_hash: object.objectHash,
    ...(object.payload ?? {}),
  };
}

export function objectsToSnapshot(input: EvidenceGraphSnapshotInput): EvidenceGraphSnapshot {
  const generatedAt = input.generatedAt ?? new Date().toISOString();
  const orgNodeId = `org:${input.orgSlug}`;
  const nodes = new Map<string, EvidenceGraphNode>();
  const edges = new Map<string, EvidenceGraphEdge>();
  const objects = [...(input.objects ?? [])];

  nodes.set(orgNodeId, {
    id: orgNodeId,
    type: 'organization',
    label: input.orgSlug,
    source: 'evidence-graph',
    weight: 100,
    metadata: { generated_at: generatedAt },
  });

  for (const node of input.nodes ?? []) {
    nodes.set(node.id, node);
  }

  for (const edge of input.edges ?? []) {
    edges.set(edge.id, edge);
  }

  for (const object of objects) {
    if (object.objectKind === 'node') {
      nodes.set(object.graphId, {
        id: object.graphId,
        type: String(object.objectType),
        label: object.label,
        source: object.source,
        weight: object.weight ?? 65,
        metadata: nodeMetadata(object),
      });

      if (object.graphId !== orgNodeId) {
        const edgeId = evidenceGraphId('edge', { from: orgNodeId, to: object.graphId, type: 'owns' });
        edges.set(edgeId, {
          id: edgeId,
          type: 'owns',
          from: orgNodeId,
          to: object.graphId,
          label: 'organization owns graph object',
          confidence: 0.98,
          metadata: { object_hash: object.objectHash },
        });
      }

      for (const controlId of object.controlIds ?? []) {
        const controlNodeId = `control:${controlId}`;
        nodes.set(controlNodeId, {
          id: controlNodeId,
          type: 'control',
          label: controlId,
          source: object.framework ?? 'control-mapping',
          weight: 80,
          metadata: { framework: object.framework },
        });
        const mapsToId = evidenceGraphId('edge', { from: object.graphId, to: controlNodeId, type: 'maps_to' });
        edges.set(mapsToId, {
          id: mapsToId,
          type: 'maps_to',
          from: object.graphId,
          to: controlNodeId,
          label: 'object maps to control',
          confidence: object.confidence ?? 0.8,
          metadata: { framework: object.framework, object_hash: object.objectHash },
        });
      }
    } else if (object.fromId && object.toId) {
      edges.set(object.graphId, {
        id: object.graphId,
        type: String(object.objectType),
        from: object.fromId,
        to: object.toId,
        label: object.label,
        confidence: object.confidence ?? 0.75,
        metadata: edgeMetadata(object),
      });
    }
  }

  const nodeList = [...nodes.values()].sort((a, b) => a.id.localeCompare(b.id));
  const edgeList = [...edges.values()].sort((a, b) => a.id.localeCompare(b.id));
  const recommendations = [...(input.recommendations ?? [])];
  const graphHash = sha256({
    orgSlug: input.orgSlug,
    nodes: nodeList,
    edges: edgeList,
    recommendations,
  });

  return {
    ok: true,
    graph_hash: graphHash,
    generated_at: generatedAt,
    organizationId: input.orgSlug,
    summary: {
      nodes: nodeList.length,
      edges: edgeList.length,
      graph_objects: objects.length,
      ...(input.extraSummary ?? {}),
    },
    nodes: nodeList,
    edges: edgeList,
    recommendations,
    objects: objects.sort((a, b) => a.graphId.localeCompare(b.graphId)),
  };
}

export function buildEvidenceGraphSnapshot(input: EvidenceGraphSnapshotInput): EvidenceGraphSnapshot {
  const objects = [...(input.objects ?? [])];

  for (const node of input.nodes ?? []) {
    objects.push(
      nodeObject({
        orgSlug: input.orgSlug,
        graphId: node.id,
        objectType: node.type,
        label: node.label,
        source: node.source,
        weight: node.weight,
        payload: node.metadata,
      }),
    );
  }

  for (const edge of input.edges ?? []) {
    objects.push(
      edgeObject({
        orgSlug: input.orgSlug,
        graphId: edge.id,
        objectType: edge.type,
        label: edge.label,
        source: edge.metadata?.source ? String(edge.metadata.source) : 'evidence-graph',
        fromId: edge.from,
        toId: edge.to,
        confidence: edge.confidence,
        payload: edge.metadata,
      }),
    );
  }

  return objectsToSnapshot({ ...input, objects, nodes: undefined, edges: undefined });
}
