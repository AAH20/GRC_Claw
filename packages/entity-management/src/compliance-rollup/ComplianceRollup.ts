import type {
  EntityComplianceStatus,
  GroupCompliancePosture,
  WeightedComplianceScore,
  CrossEntityRisk,
  WeakestEntitySummary,
  SharedControlMapping,
  FrameworkCode,
} from '../types.js';
import type { EntityManager } from '../EntityManager.js';

export class ComplianceRollup {
  private manager: EntityManager;

  constructor(manager: EntityManager) {
    this.manager = manager;
  }

  calculateGroupCompliancePosture(): GroupCompliancePosture {
    const entities = this.manager.listEntities();
    const totalEntities = entities.length;

    let compliantEntities = 0;
    let partiallyCompliantEntities = 0;
    let nonCompliantEntities = 0;
    let unassessedEntities = 0;

    const entityScores: WeightedComplianceScore[] = [];
    let totalWeightedScore = 0;
    let totalWeight = 0;

    for (const entity of entities) {
      const statuses = this.manager.getComplianceStatuses(entity.id);
      const weight = this.calculateEntityWeight(entity);

      let score = entity.complianceScore;
      if (statuses.length > 0) {
        score = this.calculateEntityComplianceScore(statuses);
      }

      entityScores.push({
        entityId: entity.id,
        entityName: entity.name,
        rawScore: score,
        weight,
        weightedScore: score * weight,
      });

      if (statuses.length === 0) {
        unassessedEntities++;
      } else if (score >= 90) {
        compliantEntities++;
      } else if (score >= 50) {
        partiallyCompliantEntities++;
      } else {
        nonCompliantEntities++;
      }

      totalWeightedScore += score * weight;
      totalWeight += weight;
    }

    const weightedComplianceScore = totalWeight > 0 ? totalWeightedScore / totalWeight : 0;

    return {
      totalEntities,
      compliantEntities,
      partiallyCompliantEntities,
      nonCompliantEntities,
      unassessedEntities,
      weightedComplianceScore,
      entityScores,
    };
  }

  calculateEntityComplianceScore(statuses: EntityComplianceStatus[]): number {
    if (statuses.length === 0) return 0;

    let totalControls = 0;
    let compliant = 0;

    for (const status of statuses) {
      totalControls += status.totalControls;
      compliant += status.compliant;
    }

    return totalControls > 0 ? (compliant / totalControls) * 100 : 0;
  }

  calculateEntityWeight(entity: { metadata: Record<string, unknown> }): number {
    const employeeCount = (entity.metadata as Record<string, unknown>)?.employeeCount as number | undefined;
    const annualRevenue = (entity.metadata as Record<string, unknown>)?.annualRevenue as number | undefined;

    if (annualRevenue && annualRevenue > 0) {
      return annualRevenue;
    }
    if (employeeCount && employeeCount > 0) {
      return employeeCount * 75000;
    }
    return 1;
  }

  rollupScoresToParent(parentId: string): EntityComplianceStatus[] {
    const parentStatuses = this.manager.getComplianceStatuses(parentId);
    const children = this.manager.getChildren(parentId);

    if (children.length === 0 && parentStatuses.length === 0) return [];

    const frameworkMap = new Map<FrameworkCode, {
      totalControls: number;
      compliant: number;
      nonCompliant: number;
      notAssessed: number;
      lastAssessedAt: string;
    }>();

    for (const status of parentStatuses) {
      frameworkMap.set(status.framework, {
        totalControls: status.totalControls,
        compliant: status.compliant,
        nonCompliant: status.nonCompliant,
        notAssessed: status.notAssessed,
        lastAssessedAt: status.lastAssessedAt,
      });
    }

    for (const child of children) {
      const childStatuses = this.manager.getComplianceStatuses(child.id);
      const childWeight = this.calculateEntityWeight(child);

      for (const cs of childStatuses) {
        const existing = frameworkMap.get(cs.framework) || {
          totalControls: 0,
          compliant: 0,
          nonCompliant: 0,
          notAssessed: 0,
          lastAssessedAt: cs.lastAssessedAt,
        };

        const weightFactor = childWeight / 100;
        existing.totalControls += Math.round(cs.totalControls * weightFactor);
        existing.compliant += Math.round(cs.compliant * weightFactor);
        existing.nonCompliant += Math.round(cs.nonCompliant * weightFactor);
        existing.notAssessed += Math.round(cs.notAssessed * weightFactor);
        if (cs.lastAssessedAt > existing.lastAssessedAt) {
          existing.lastAssessedAt = cs.lastAssessedAt;
        }

        frameworkMap.set(cs.framework, existing);
      }
    }

    const rolledUp: EntityComplianceStatus[] = [];
    for (const [framework, data] of frameworkMap) {
      rolledUp.push({
        entityId: parentId,
        framework,
        ...data,
      });
    }

    return rolledUp;
  }

  identifyCrossEntityRisks(): CrossEntityRisk[] {
    const entities = this.manager.listEntities();
    const risks: CrossEntityRisk[] = [];

    const sharedControls = this.findSharedControls();
    for (const mapping of sharedControls) {
      const nonCompliantEntities = Object.entries(mapping.status)
        .filter(([, status]) => status === 'non-compliant' || status === 'partial')
        .map(([entityId]) => entityId);

      if (nonCompliantEntities.length >= 2) {
        risks.push({
          riskId: `risk-shared-${mapping.controlId}`,
          affectedEntityIds: nonCompliantEntities,
          description: `Shared control ${mapping.controlCode} is non-compliant across ${nonCompliantEntities.length} entities`,
          severity: nonCompliantEntities.length >= 3 ? 'critical' : 'high',
          likelihood: 0.8,
          impact: nonCompliantEntities.length * 0.3,
          riskScore: nonCompliantEntities.length * 0.24,
          sharedControlIds: [mapping.controlId],
        });
      }
    }

    const jurisdictionGroups = new Map<string, typeof entities>();
    for (const entity of entities) {
      const list = jurisdictionGroups.get(entity.jurisdiction) || [];
      list.push(entity);
      jurisdictionGroups.set(entity.jurisdiction, list);
    }

    for (const [jurisdiction, group] of jurisdictionGroups) {
      const lowScoreEntities = group.filter(e => e.complianceScore < 50);
      if (lowScoreEntities.length >= 2) {
        risks.push({
          riskId: `risk-jurisdiction-${jurisdiction.toLowerCase().replace(/\s+/g, '-')}`,
          affectedEntityIds: lowScoreEntities.map(e => e.id),
          description: `Multiple entities in ${jurisdiction} have low compliance scores`,
          severity: 'high',
          likelihood: 0.7,
          impact: lowScoreEntities.length * 0.2,
          riskScore: lowScoreEntities.length * 0.14,
          sharedControlIds: [],
        });
      }
    }

    return risks;
  }

  findSharedControls(): SharedControlMapping[] {
    const entities = this.manager.listEntities();
    const controlEntityMap = new Map<string, Map<string, 'compliant' | 'non-compliant' | 'partial' | 'not-applicable' | 'not-tested'>>();

    for (const entity of entities) {
      const statuses = this.manager.getComplianceStatuses(entity.id);
      for (const status of statuses) {
        const complianceRatio = status.totalControls > 0 ? status.compliant / status.totalControls : 0;
        const sharedStatus = complianceRatio >= 0.9 ? 'compliant' as const
          : complianceRatio >= 0.5 ? 'partial' as const
          : status.totalControls > 0 ? 'non-compliant' as const
          : 'not-tested' as const;

        if (!controlEntityMap.has(status.framework)) {
          controlEntityMap.set(status.framework, new Map());
        }
        controlEntityMap.get(status.framework)!.set(entity.id, sharedStatus);
      }
    }

    const mappings: SharedControlMapping[] = [];
    for (const [framework, entityStatuses] of controlEntityMap) {
      if (entityStatuses.size >= 2) {
        const statusRecord: Record<string, 'compliant' | 'non-compliant' | 'partial' | 'not-applicable' | 'not-tested'> = {};
        for (const [entityId, status] of entityStatuses) {
          statusRecord[entityId] = status;
        }
        mappings.push({
          controlId: `shared-${framework}`,
          controlCode: `${framework.toUpperCase()}-SHARED`,
          entityIds: Array.from(entityStatuses.keys()),
          status: statusRecord,
          shared: true,
        });
      }
    }

    return mappings;
  }

  getWeakestEntities(count: number): WeakestEntitySummary[] {
    const entities = this.manager.listEntities();
    return entities
      .sort((a, b) => a.complianceScore - b.complianceScore)
      .slice(0, count)
      .map(entity => {
        const statuses = this.manager.getComplianceStatuses(entity.id);
        let biggestGap = 'No compliance data available';
        let lowestScore = 100;

        for (const status of statuses) {
          const score = status.totalControls > 0 ? (status.compliant / status.totalControls) * 100 : 0;
          if (score < lowestScore) {
            lowestScore = score;
            biggestGap = status.framework;
          }
        }

        return {
          entityId: entity.id,
          entityName: entity.name,
          complianceScore: entity.complianceScore,
          riskScore: entity.riskScore,
          biggestGap,
        };
      });
  }

  aggregateRisksAcrossEntities(entityIds: string[]): CrossEntityRisk[] {
    const allRisks: CrossEntityRisk[] = [];
    const seenRisks = new Set<string>();

    for (const entityId of entityIds) {
      const entity = this.manager.getEntity(entityId);
      if (!entity) continue;

      const statuses = this.manager.getComplianceStatuses(entityId);
      for (const status of statuses) {
        const score = status.totalControls > 0 ? (status.compliant / status.totalControls) * 100 : 0;
        if (score < 70) {
          const riskKey = `${entityId}-${status.framework}`;
          if (!seenRisks.has(riskKey)) {
            seenRisks.add(riskKey);
            allRisks.push({
              riskId: `risk-entity-${entityId}-${status.framework}`,
              affectedEntityIds: [entityId],
              description: `Entity ${entity.name} has ${score.toFixed(1)}% compliance on ${status.framework}`,
              severity: score < 50 ? 'critical' : 'high',
              likelihood: 0.6,
              impact: 1 - score / 100,
              riskScore: (1 - score / 100) * 0.6,
              sharedControlIds: [],
            });
          }
        }
      }
    }

    return allRisks;
  }
}
