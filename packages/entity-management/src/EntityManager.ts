import type {
  Entity,
  EntityRelationship,
  EntityComplianceStatus,
  EntityType,
  RelationshipType,
  RelationshipStatus,
  EntityTreeNode,
  JurisdictionCoverage,
  ConsolidatedReport,
  FrameworkCode,
  CrossEntityRisk,
  WeakestEntitySummary,
  IndustryFrameworkRecommendation,
} from './types.js';
import { ComplianceRollup } from './compliance-rollup/ComplianceRollup.js';

function generateId(): string {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).substring(2, 10);
  return `ent-${ts}-${rand}`;
}

export interface EntityManagerDatabase {
  query<T = Record<string, unknown>>(sql: string, params?: unknown[]): Promise<{ rows: T[]; rowCount: number }>;
  execute(sql: string, params?: unknown[]): Promise<void>;
}

const INDUSTRY_FRAMEWORKS: IndustryFrameworkRecommendation[] = [
  { industry: 'financial_services', frameworks: ['iso27001', 'soc2', 'pci-dss', 'dora', 'gdpr'], rationale: 'Financial services require strong data protection, payment security, and operational resilience', priority: 'required' },
  { industry: 'healthcare', frameworks: ['iso27001', 'hipaa', 'soc2', 'gdpr'], rationale: 'Healthcare requires patient data protection and regulatory compliance', priority: 'required' },
  { industry: 'technology', frameworks: ['iso27001', 'soc2', 'iso42001', 'nist-csf'], rationale: 'Technology companies benefit from AI governance and broad security frameworks', priority: 'recommended' },
  { industry: 'manufacturing', frameworks: ['iso27001', 'tisax', 'nist-csf'], rationale: 'Manufacturing needs supply chain security and data protection', priority: 'recommended' },
  { industry: 'government', frameworks: ['fedramp', 'cmmc', 'nist-csf'], rationale: 'Government entities require federal compliance frameworks', priority: 'required' },
  { industry: 'retail', frameworks: ['pci-dss', 'iso27001', 'soc2', 'gdpr'], rationale: 'Retail requires payment security and customer data protection', priority: 'required' },
  { industry: 'telecommunications', frameworks: ['iso27001', 'soc2', 'nist-csf', 'nis2'], rationale: 'Telecom requires network security and incident reporting', priority: 'required' },
  { industry: 'energy', frameworks: ['iso27001', 'nist-csf', 'soc2'], rationale: 'Energy sector needs critical infrastructure protection', priority: 'required' },
];

export class EntityManager {
  private entities: Map<string, Entity> = new Map();
  private relationships: Map<string, EntityRelationship> = new Map();
  private complianceStatuses: Map<string, EntityComplianceStatus[]> = new Map();
  private rollup: ComplianceRollup;
  private readonly db?: EntityManagerDatabase;

  constructor(database?: EntityManagerDatabase) {
    this.rollup = new ComplianceRollup(this);
    this.db = database;
  }

  createEntity(input: Omit<Entity, 'id' | 'createdAt' | 'updatedAt' | 'complianceScore' | 'riskScore'>): Entity {
    const now = new Date().toISOString();
    const entity: Entity = {
      ...input,
      id: generateId(),
      complianceScore: 0,
      riskScore: 0,
      createdAt: now,
      updatedAt: now,
    };
    this.entities.set(entity.id, entity);

    if (entity.parentId) {
      this.addRelationship(entity.parentId, entity.id, input.type === 'branch' ? 'branch' : 'subsidiary');
    }

    if (this.db) {
      const db = this.db;
      void db.execute(
        `INSERT INTO entities (id, name, type, jurisdiction, industry, parent_id, metadata, compliance_score, risk_score, created_at, updated_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
         ON CONFLICT (id) DO NOTHING`,
        [
          entity.id,
          entity.name,
          entity.type,
          entity.jurisdiction,
          entity.industry,
          entity.parentId ?? null,
          JSON.stringify(entity.metadata),
          entity.complianceScore,
          entity.riskScore,
          entity.createdAt,
          entity.updatedAt,
        ],
      ).catch(() => {
        // fall back to in-memory only
      });
    }

    return entity;
  }

  getEntity(id: string): Entity | undefined {
    return this.entities.get(id);
  }

  listEntities(filter?: { jurisdiction?: string; industry?: string; type?: EntityType; parentId?: string }): Entity[] {
    let result = Array.from(this.entities.values());
    if (filter?.jurisdiction) result = result.filter(e => e.jurisdiction === filter.jurisdiction);
    if (filter?.industry) result = result.filter(e => e.industry === filter.industry);
    if (filter?.type) result = result.filter(e => e.type === filter.type);
    if (filter?.parentId !== undefined) result = result.filter(e => e.parentId === filter.parentId);
    return result;
  }

  async loadFromDatabase(): Promise<void> {
    if (!this.db) return;
    try {
      const { rows: entityRows } = await this.db.query<{
        id: string;
        name: string;
        type: EntityType;
        jurisdiction: string;
        industry: string;
        parent_id: string | null;
        metadata: Entity['metadata'];
        compliance_score: number;
        risk_score: number;
        created_at: string;
        updated_at: string;
      }>(`SELECT * FROM entities`);
      for (const row of entityRows) {
        const entity: Entity = {
          id: row.id,
          name: row.name,
          type: row.type,
          jurisdiction: row.jurisdiction,
          industry: row.industry,
          parentId: row.parent_id ?? undefined,
          metadata: row.metadata,
          complianceScore: row.compliance_score,
          riskScore: row.risk_score,
          createdAt: row.created_at,
          updatedAt: row.updated_at,
        };
        this.entities.set(entity.id, entity);
      }

      const { rows: relRows } = await this.db.query<{
        id: string;
        parent_entity_id: string;
        child_entity_id: string;
        relationship_type: RelationshipType;
        status: RelationshipStatus;
        created_at: string;
        updated_at: string;
      }>(`SELECT * FROM entity_relationships`);
      for (const row of relRows) {
        const rel: EntityRelationship = {
          id: row.id,
          parentEntityId: row.parent_entity_id,
          childEntityId: row.child_entity_id,
          relationshipType: row.relationship_type,
          status: row.status,
          createdAt: row.created_at,
          updatedAt: row.updated_at,
        };
        this.relationships.set(rel.id, rel);
      }
    } catch {
      // fall back to empty in-memory state
    }
  }

  updateEntity(id: string, updates: Partial<Omit<Entity, 'id' | 'createdAt'>>): Entity | undefined {
    const entity = this.entities.get(id);
    if (!entity) return undefined;
    const updated: Entity = { ...entity, ...updates, updatedAt: new Date().toISOString() };
    this.entities.set(id, updated);

    if (this.db) {
      const db = this.db;
      void db.execute(
        `UPDATE entities SET name=$2, type=$3, jurisdiction=$4, industry=$5, parent_id=$6, metadata=$7, compliance_score=$8, risk_score=$9, updated_at=$10
         WHERE id=$1`,
        [
          updated.id,
          updated.name,
          updated.type,
          updated.jurisdiction,
          updated.industry,
          updated.parentId ?? null,
          JSON.stringify(updated.metadata),
          updated.complianceScore,
          updated.riskScore,
          updated.updatedAt,
        ],
      ).catch(() => {});
    }

    return updated;
  }

  deleteEntity(id: string): boolean {
    const entity = this.entities.get(id);
    if (!entity) return false;

    const children = this.getChildren(id);
    for (const child of children) {
      child.parentId = undefined;
      this.entities.set(child.id, child);
    }

    for (const [relId, rel] of this.relationships) {
      if (rel.parentEntityId === id || rel.childEntityId === id) {
        this.relationships.delete(relId);
      }
    }

    this.complianceStatuses.delete(id);
    this.entities.delete(id);

    if (this.db) {
      const db = this.db;
      void db.execute(`DELETE FROM entities WHERE id = $1`, [id]).catch(() => {});
      void db.execute(`DELETE FROM entity_relationships WHERE parent_entity_id = $1 OR child_entity_id = $1`, [id]).catch(() => {});
    }

    return true;
  }

  addRelationship(
    parentEntityId: string,
    childEntityId: string,
    relationshipType: RelationshipType = 'subsidiary',
    status: RelationshipStatus = 'active',
  ): EntityRelationship | undefined {
    const parent = this.entities.get(parentEntityId);
    const child = this.entities.get(childEntityId);
    if (!parent || !child || parentEntityId === childEntityId) return undefined;

    const now = new Date().toISOString();
    const existing = Array.from(this.relationships.values()).find(
      r => r.parentEntityId === parentEntityId && r.childEntityId === childEntityId,
    );
    if (existing) {
      existing.relationshipType = relationshipType;
      existing.status = status;
      existing.updatedAt = now;
      return existing;
    }

    const relationship: EntityRelationship = {
      id: generateId(),
      parentEntityId,
      childEntityId,
      relationshipType,
      status,
      createdAt: now,
      updatedAt: now,
    };
    this.relationships.set(relationship.id, relationship);

    const childUpdated = { ...child, parentId: parentEntityId, updatedAt: now };
    this.entities.set(childEntityId, childUpdated);

    if (this.db) {
      const db = this.db;
      void db.execute(
        `INSERT INTO entity_relationships (id, parent_entity_id, child_entity_id, relationship_type, status, created_at, updated_at)
         VALUES ($1, $2, $3, $4, $5, $6, $7)
         ON CONFLICT (id) DO NOTHING`,
        [
          relationship.id,
          relationship.parentEntityId,
          relationship.childEntityId,
          relationship.relationshipType,
          relationship.status,
          relationship.createdAt,
          relationship.updatedAt,
        ],
      ).catch(() => {});
    }

    return relationship;
  }

  getChildren(entityId: string): Entity[] {
    const children: Entity[] = [];
    for (const rel of this.relationships.values()) {
      if (rel.parentEntityId === entityId && rel.status === 'active') {
        const child = this.entities.get(rel.childEntityId);
        if (child) children.push(child);
      }
    }
    return children;
  }

  getDescendants(entityId: string): Entity[] {
    const descendants: Entity[] = [];
    const stack = [...this.getChildren(entityId)];
    while (stack.length > 0) {
      const current = stack.pop()!;
      descendants.push(current);
      stack.push(...this.getChildren(current.id));
    }
    return descendants;
  }

  getAncestors(entityId: string): Entity[] {
    const ancestors: Entity[] = [];
    const entity = this.entities.get(entityId);
    if (!entity) return ancestors;

    let current = entity;
    while (current.parentId) {
      const parent = this.entities.get(current.parentId);
      if (!parent) break;
      ancestors.push(parent);
      current = parent;
    }
    return ancestors;
  }

  setComplianceStatuses(entityId: string, statuses: EntityComplianceStatus[]): void {
    this.complianceStatuses.set(entityId, statuses);
  }

  getComplianceStatuses(entityId: string): EntityComplianceStatus[] {
    return this.complianceStatuses.get(entityId) || [];
  }

  getEntityTree(): EntityTreeNode[] {
    const roots = Array.from(this.entities.values()).filter(e => !e.parentId);
    return roots.map(root => this.buildTreeNode(root));
  }

  private buildTreeNode(entity: Entity): EntityTreeNode {
    const children = this.getChildren(entity.id);
    return {
      entity,
      children: children.map(child => this.buildTreeNode(child)),
      complianceStatuses: this.getComplianceStatuses(entity.id),
    };
  }

  getJurisdictionCoverage(jurisdiction: string): JurisdictionCoverage {
    const entities = this.listEntities({ jurisdiction });
    const frameworks = new Set<FrameworkCode>();
    const complianceScores: Record<string, number> = {};

    for (const entity of entities) {
      complianceScores[entity.id] = entity.complianceScore;
      const statuses = this.getComplianceStatuses(entity.id);
      for (const s of statuses) {
        frameworks.add(s.framework);
      }
    }

    return {
      jurisdiction,
      entityIds: entities.map(e => e.id),
      frameworks: Array.from(frameworks),
      complianceScores,
    };
  }

  getConsolidatedReport(): ConsolidatedReport {
    const entities = Array.from(this.entities.values());

    const complianceReport = this.rollup.calculateGroupCompliancePosture();
    const crossEntityRisks = this.rollup.identifyCrossEntityRisks();
    const weakestEntities = this.rollup.getWeakestEntities(5);

    const overallComplianceScore = entities.length > 0
      ? entities.reduce((sum, e) => sum + e.complianceScore, 0) / entities.length
      : 0;

    const overallRiskScore = entities.length > 0
      ? entities.reduce((sum, e) => sum + e.riskScore, 0) / entities.length
      : 0;

    const jurisdictionMap = new Map<string, Entity[]>();
    for (const entity of entities) {
      const list = jurisdictionMap.get(entity.jurisdiction) || [];
      list.push(entity);
      jurisdictionMap.set(entity.jurisdiction, list);
    }

    const jurisdictionBreakdown: JurisdictionCoverage[] = [];
    for (const [jurisdiction, ents] of jurisdictionMap) {
      jurisdictionBreakdown.push(this.getJurisdictionCoverage(jurisdiction));
    }

    const frameworkMap = new Map<FrameworkCode, {
      totalControls: number;
      compliant: number;
      nonCompliant: number;
      notAssessed: number;
      entityScores: Record<string, number>;
    }>();

    for (const entity of entities) {
      const statuses = this.getComplianceStatuses(entity.id);
      for (const s of statuses) {
        const existing = frameworkMap.get(s.framework) || {
          totalControls: 0, compliant: 0, nonCompliant: 0, notAssessed: 0, entityScores: {},
        };
        existing.totalControls += s.totalControls;
        existing.compliant += s.compliant;
        existing.nonCompliant += s.nonCompliant;
        existing.notAssessed += s.notAssessed;
        existing.entityScores[entity.id] = s.totalControls > 0
          ? (s.compliant / s.totalControls) * 100
          : 0;
        frameworkMap.set(s.framework, existing);
      }
    }

    const frameworkBreakdown = Array.from(frameworkMap.entries()).map(([framework, data]) => ({
      framework,
      ...data,
      scorePercent: data.totalControls > 0 ? (data.compliant / data.totalControls) * 100 : 0,
    }));

    return {
      generatedAt: new Date().toISOString(),
      entities,
      overallComplianceScore,
      overallRiskScore,
      jurisdictionBreakdown,
      frameworkBreakdown,
      crossEntityRisks,
      weakestEntities,
    };
  }

  getIndustryFrameworkRecommendations(industry: string): IndustryFrameworkRecommendation[] {
    return INDUSTRY_FRAMEWORKS.filter(r => r.industry === industry);
  }

  getAllFrameworksForEntity(entityId: string): FrameworkCode[] {
    const entity = this.entities.get(entityId);
    if (!entity) return [];

    const frameworks = new Set<FrameworkCode>();
    const ancestors = this.getAncestors(entityId);
    const descendants = this.getDescendants(entityId);
    const allEntities = [entity, ...ancestors, ...descendants];

    for (const e of allEntities) {
      const statuses = this.getComplianceStatuses(e.id);
      for (const s of statuses) {
        frameworks.add(s.framework);
      }
      const recommendations = this.getIndustryFrameworkRecommendations(e.industry);
      for (const rec of recommendations) {
        for (const f of rec.frameworks) {
          frameworks.add(f);
        }
      }
    }

    return Array.from(frameworks);
  }
}
