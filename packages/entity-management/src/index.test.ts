import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { EntityManager } from './EntityManager.js';
import type {
  Entity,
  EntityComplianceStatus,
  FrameworkCode,
} from './types.js';

describe('EntityManager', () => {
  let manager: EntityManager;

  beforeEach(() => {
    manager = new EntityManager();
  });

  describe('CRUD operations', () => {
    it('should create an entity', () => {
      const entity = manager.createEntity({
        name: 'Acme Corp',
        type: 'parent',
        jurisdiction: 'US',
        industry: 'technology',
        metadata: { employeeCount: 500, annualRevenue: 50_000_000 },
      });

      assert.ok(entity.id);
      assert.equal(entity.name, 'Acme Corp');
      assert.equal(entity.type, 'parent');
      assert.equal(entity.jurisdiction, 'US');
      assert.equal(entity.industry, 'technology');
      assert.equal(entity.complianceScore, 0);
      assert.equal(entity.riskScore, 0);
      assert.ok(entity.createdAt);
      assert.ok(entity.updatedAt);
    });

    it('should get an entity by id', () => {
      const created = manager.createEntity({
        name: 'Test Entity',
        type: 'parent',
        jurisdiction: 'EU',
        industry: 'technology',
        metadata: {},
      });

      const retrieved = manager.getEntity(created.id);
      assert.ok(retrieved);
      assert.equal(retrieved.id, created.id);
      assert.equal(retrieved.name, 'Test Entity');
    });

    it('should return undefined for non-existent entity', () => {
      assert.equal(manager.getEntity('non-existent'), undefined);
    });

    it('should list entities with filters', () => {
      manager.createEntity({ name: 'US Tech', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      manager.createEntity({ name: 'EU Finance', type: 'parent', jurisdiction: 'EU', industry: 'financial_services', metadata: {} });
      manager.createEntity({ name: 'US Retail', type: 'subsidiary', jurisdiction: 'US', industry: 'retail', metadata: {} });

      assert.equal(manager.listEntities().length, 3);
      assert.equal(manager.listEntities({ jurisdiction: 'US' }).length, 2);
      assert.equal(manager.listEntities({ jurisdiction: 'EU' }).length, 1);
      assert.equal(manager.listEntities({ industry: 'technology' }).length, 1);
      assert.equal(manager.listEntities({ type: 'subsidiary' }).length, 1);
    });

    it('should update an entity', () => {
      const created = manager.createEntity({
        name: 'Original Name',
        type: 'parent',
        jurisdiction: 'US',
        industry: 'technology',
        metadata: {},
      });

      const updated = manager.updateEntity(created.id, { name: 'Updated Name', riskScore: 3.5 });
      assert.ok(updated);
      assert.equal(updated.name, 'Updated Name');
      assert.equal(updated.riskScore, 3.5);
      assert.ok(updated.updatedAt >= created.updatedAt);
    });

    it('should return undefined when updating non-existent entity', () => {
      assert.equal(manager.updateEntity('non-existent', { name: 'X' }), undefined);
    });

    it('should delete an entity and re-parent its children', () => {
      const parent = manager.createEntity({ name: 'Parent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const child = manager.createEntity({ name: 'Child', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {}, parentId: parent.id });

      assert.ok(manager.getEntity(child.id));
      assert.ok(manager.getEntity(parent.id));

      const deleted = manager.deleteEntity(parent.id);
      assert.ok(deleted);
      assert.equal(manager.getEntity(parent.id), undefined);

      const orphan = manager.getEntity(child.id);
      assert.ok(orphan);
      assert.equal(orphan.parentId, undefined);
    });

    it('should return false when deleting non-existent entity', () => {
      assert.equal(manager.deleteEntity('non-existent'), false);
    });
  });

  describe('Hierarchy management', () => {
    it('should create parent-child relationships', () => {
      const parent = manager.createEntity({ name: 'Parent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const child = manager.createEntity({ name: 'Child', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });

      const rel = manager.addRelationship(parent.id, child.id, 'subsidiary');
      assert.ok(rel);
      assert.equal(rel.parentEntityId, parent.id);
      assert.equal(rel.childEntityId, child.id);
      assert.equal(rel.relationshipType, 'subsidiary');
      assert.equal(rel.status, 'active');
    });

    it('should not allow self-referencing relationships', () => {
      const entity = manager.createEntity({ name: 'Self', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const rel = manager.addRelationship(entity.id, entity.id, 'subsidiary');
      assert.equal(rel, undefined);
    });

    it('should return undefined for relationships with non-existent entities', () => {
      const entity = manager.createEntity({ name: 'Entity', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      assert.equal(manager.addRelationship(entity.id, 'non-existent', 'subsidiary'), undefined);
      assert.equal(manager.addRelationship('non-existent', entity.id, 'subsidiary'), undefined);
    });

    it('should get children of an entity', () => {
      const parent = manager.createEntity({ name: 'Parent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const child1 = manager.createEntity({ name: 'Child 1', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const child2 = manager.createEntity({ name: 'Child 2', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });

      manager.addRelationship(parent.id, child1.id, 'subsidiary');
      manager.addRelationship(parent.id, child2.id, 'branch');

      const children = manager.getChildren(parent.id);
      assert.equal(children.length, 2);
      assert.ok(children.some(c => c.id === child1.id));
      assert.ok(children.some(c => c.id === child2.id));
    });

    it('should get all descendants recursively', () => {
      const grandparent = manager.createEntity({ name: 'Grandparent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const parent = manager.createEntity({ name: 'Parent', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const child = manager.createEntity({ name: 'Child', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const grandchild = manager.createEntity({ name: 'Grandchild', type: 'branch', jurisdiction: 'US', industry: 'technology', metadata: {} });

      manager.addRelationship(grandparent.id, parent.id, 'subsidiary');
      manager.addRelationship(parent.id, child.id, 'subsidiary');
      manager.addRelationship(child.id, grandchild.id, 'branch');

      const descendants = manager.getDescendants(grandparent.id);
      assert.equal(descendants.length, 3);
      assert.ok(descendants.some(d => d.id === parent.id));
      assert.ok(descendants.some(d => d.id === child.id));
      assert.ok(descendants.some(d => d.id === grandchild.id));
    });

    it('should get ancestors', () => {
      const grandparent = manager.createEntity({ name: 'Grandparent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const parent = manager.createEntity({ name: 'Parent', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const child = manager.createEntity({ name: 'Child', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });

      manager.addRelationship(grandparent.id, parent.id, 'subsidiary');
      manager.addRelationship(parent.id, child.id, 'subsidiary');

      const ancestors = manager.getAncestors(child.id);
      assert.equal(ancestors.length, 2);
      assert.equal(ancestors[0].id, parent.id);
      assert.equal(ancestors[1].id, grandparent.id);
    });

    it('should build entity tree', () => {
      const root = manager.createEntity({ name: 'Root', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const child = manager.createEntity({ name: 'Child', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const grandchild = manager.createEntity({ name: 'Grandchild', type: 'branch', jurisdiction: 'US', industry: 'technology', metadata: {} });

      manager.addRelationship(root.id, child.id, 'subsidiary');
      manager.addRelationship(child.id, grandchild.id, 'branch');

      const tree = manager.getEntityTree();
      assert.equal(tree.length, 1);
      assert.equal(tree[0].entity.id, root.id);
      assert.equal(tree[0].children.length, 1);
      assert.equal(tree[0].children[0].entity.id, child.id);
      assert.equal(tree[0].children[0].children.length, 1);
      assert.equal(tree[0].children[0].children[0].entity.id, grandchild.id);
    });

    it('should return multiple roots', () => {
      manager.createEntity({ name: 'Root 1', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      manager.createEntity({ name: 'Root 2', type: 'parent', jurisdiction: 'EU', industry: 'financial_services', metadata: {} });

      const tree = manager.getEntityTree();
      assert.equal(tree.length, 2);
    });
  });

  describe('Compliance rollup', () => {
    it('should rollup compliance scores from children to parent', () => {
      const parent = manager.createEntity({ name: 'Parent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: { annualRevenue: 100_000_000 } });
      const child = manager.createEntity({ name: 'Child', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: { annualRevenue: 50_000_000 } });

      manager.addRelationship(parent.id, child.id, 'subsidiary');

      manager.setComplianceStatuses(child.id, [{
        entityId: child.id,
        framework: 'soc2',
        totalControls: 100,
        compliant: 80,
        nonCompliant: 15,
        notAssessed: 5,
        lastAssessedAt: '2025-01-01',
      }]);

      const rollup = manager['rollup'];
      const rolledUp = rollup.rollupScoresToParent(parent.id);
      assert.ok(rolledUp.length > 0);

      const soc2 = rolledUp.find(r => r.framework === 'soc2');
      assert.ok(soc2);
      assert.ok(soc2.totalControls > 0);
    });

    it('should calculate group compliance posture', () => {
      const parent = manager.createEntity({ name: 'Parent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: { annualRevenue: 200_000_000 } });
      const child1 = manager.createEntity({ name: 'Child 1', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: { annualRevenue: 50_000_000 } });
      const child2 = manager.createEntity({ name: 'Child 2', type: 'subsidiary', jurisdiction: 'EU', industry: 'financial_services', metadata: { annualRevenue: 30_000_000 } });

      manager.addRelationship(parent.id, child1.id, 'subsidiary');
      manager.addRelationship(parent.id, child2.id, 'subsidiary');

      manager.setComplianceStatuses(parent.id, [{
        entityId: parent.id, framework: 'iso27001', totalControls: 100, compliant: 95, nonCompliant: 3, notAssessed: 2, lastAssessedAt: '2025-06-01',
      }]);
      manager.setComplianceStatuses(child1.id, [{
        entityId: child1.id, framework: 'soc2', totalControls: 80, compliant: 60, nonCompliant: 15, notAssessed: 5, lastAssessedAt: '2025-05-15',
      }]);
      manager.setComplianceStatuses(child2.id, [{
        entityId: child2.id, framework: 'gdpr', totalControls: 50, compliant: 45, nonCompliant: 3, notAssessed: 2, lastAssessedAt: '2025-06-10',
      }]);

      const rollup = manager['rollup'];
      const posture = rollup.calculateGroupCompliancePosture();

      assert.equal(posture.totalEntities, 3);
      assert.equal(posture.entityScores.length, 3);
      assert.ok(posture.weightedComplianceScore > 0);
      assert.ok(posture.weightedComplianceScore <= 100);
    });

    it('should identify weakest entities', () => {
      const e1 = manager.createEntity({ name: 'Strong', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const e2 = manager.createEntity({ name: 'Weak', type: 'subsidiary', jurisdiction: 'EU', industry: 'financial_services', metadata: {} });
      const e3 = manager.createEntity({ name: 'Medium', type: 'division', jurisdiction: 'US', industry: 'technology', metadata: {} });

      manager.updateEntity(e1.id, { complianceScore: 95, riskScore: 1 });
      manager.updateEntity(e2.id, { complianceScore: 30, riskScore: 8 });
      manager.updateEntity(e3.id, { complianceScore: 65, riskScore: 4 });

      manager.setComplianceStatuses(e2.id, [{
        entityId: e2.id, framework: 'gdpr', totalControls: 50, compliant: 10, nonCompliant: 35, notAssessed: 5, lastAssessedAt: '2025-01-01',
      }]);

      const rollup = manager['rollup'];
      const weakest = rollup.getWeakestEntities(2);
      assert.equal(weakest.length, 2);
      assert.equal(weakest[0].entityName, 'Weak');
      assert.equal(weakest[1].entityName, 'Medium');
    });
  });

  describe('Cross-entity risk identification', () => {
    it('should identify risks from shared non-compliant controls', () => {
      const parent = manager.createEntity({ name: 'Parent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: { annualRevenue: 100_000_000 } });
      const child1 = manager.createEntity({ name: 'Child 1', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: { annualRevenue: 50_000_000 } });
      const child2 = manager.createEntity({ name: 'Child 2', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: { annualRevenue: 30_000_000 } });

      manager.addRelationship(parent.id, child1.id, 'subsidiary');
      manager.addRelationship(parent.id, child2.id, 'subsidiary');

      manager.setComplianceStatuses(child1.id, [{
        entityId: child1.id, framework: 'soc2', totalControls: 100, compliant: 20, nonCompliant: 70, notAssessed: 10, lastAssessedAt: '2025-01-01',
      }]);
      manager.setComplianceStatuses(child2.id, [{
        entityId: child2.id, framework: 'soc2', totalControls: 100, compliant: 30, nonCompliant: 60, notAssessed: 10, lastAssessedAt: '2025-01-01',
      }]);

      const rollup = manager['rollup'];
      const risks = rollup.identifyCrossEntityRisks();
      assert.ok(risks.length > 0);
      const sharedRisk = risks.find(r => r.description.includes('Shared control'));
      assert.ok(sharedRisk);
      assert.equal(sharedRisk.affectedEntityIds.length, 2);
    });

    it('should identify jurisdiction-level risks', () => {
      const e1 = manager.createEntity({ name: 'EU Entity 1', type: 'parent', jurisdiction: 'EU', industry: 'technology', metadata: {} });
      const e2 = manager.createEntity({ name: 'EU Entity 2', type: 'subsidiary', jurisdiction: 'EU', industry: 'financial_services', metadata: {} });

      manager.updateEntity(e1.id, { complianceScore: 30 });
      manager.updateEntity(e2.id, { complianceScore: 40 });

      const rollup = manager['rollup'];
      const risks = rollup.identifyCrossEntityRisks();
      const jurisdictionRisk = risks.find(r => r.description.includes('EU'));
      assert.ok(jurisdictionRisk);
    });
  });

  describe('Jurisdiction coverage', () => {
    it('should report jurisdiction coverage', () => {
      manager.createEntity({ name: 'US Entity 1', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      manager.createEntity({ name: 'US Entity 2', type: 'subsidiary', jurisdiction: 'US', industry: 'financial_services', metadata: {} });
      manager.createEntity({ name: 'EU Entity', type: 'parent', jurisdiction: 'EU', industry: 'technology', metadata: {} });

      const usCoverage = manager.getJurisdictionCoverage('US');
      assert.equal(usCoverage.entityIds.length, 2);
      assert.equal(usCoverage.jurisdiction, 'US');

      const euCoverage = manager.getJurisdictionCoverage('EU');
      assert.equal(euCoverage.entityIds.length, 1);
    });
  });

  describe('Industry framework recommendations', () => {
    it('should recommend frameworks for financial services', () => {
      const recs = manager.getIndustryFrameworkRecommendations('financial_services');
      assert.ok(recs.length > 0);
      assert.ok(recs[0].frameworks.includes('iso27001'));
      assert.ok(recs[0].frameworks.includes('soc2'));
      assert.ok(recs[0].frameworks.includes('pci-dss'));
      assert.equal(recs[0].priority, 'required');
    });

    it('should recommend frameworks for technology', () => {
      const recs = manager.getIndustryFrameworkRecommendations('technology');
      assert.ok(recs.length > 0);
      assert.ok(recs[0].frameworks.includes('iso27001'));
      assert.ok(recs[0].frameworks.includes('soc2'));
      assert.ok(recs[0].frameworks.includes('iso42001'));
    });

    it('should return empty array for unknown industry', () => {
      const recs = manager.getIndustryFrameworkRecommendations('unknown_industry');
      assert.equal(recs.length, 0);
    });
  });

  describe('Consolidated report', () => {
    it('should generate a consolidated report', () => {
      const parent = manager.createEntity({ name: 'Parent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: { annualRevenue: 200_000_000 } });
      const child = manager.createEntity({ name: 'Child', type: 'subsidiary', jurisdiction: 'EU', industry: 'financial_services', metadata: { annualRevenue: 50_000_000 } });

      manager.addRelationship(parent.id, child.id, 'subsidiary');

      manager.setComplianceStatuses(parent.id, [{
        entityId: parent.id, framework: 'iso27001', totalControls: 100, compliant: 90, nonCompliant: 8, notAssessed: 2, lastAssessedAt: '2025-06-01',
      }]);
      manager.setComplianceStatuses(child.id, [{
        entityId: child.id, framework: 'soc2', totalControls: 80, compliant: 60, nonCompliant: 15, notAssessed: 5, lastAssessedAt: '2025-05-15',
      }]);

      const report = manager.getConsolidatedReport();
      assert.ok(report.generatedAt);
      assert.equal(report.entities.length, 2);
      assert.ok(report.overallComplianceScore >= 0);
      assert.ok(report.overallRiskScore >= 0);
      assert.ok(report.jurisdictionBreakdown.length >= 1);
      assert.ok(report.frameworkBreakdown.length >= 1);
      assert.ok(Array.isArray(report.crossEntityRisks));
      assert.ok(Array.isArray(report.weakestEntities));
    });

    it('should handle empty entity list', () => {
      const report = manager.getConsolidatedReport();
      assert.equal(report.entities.length, 0);
      assert.equal(report.overallComplianceScore, 0);
      assert.equal(report.overallRiskScore, 0);
      assert.equal(report.jurisdictionBreakdown.length, 0);
      assert.equal(report.frameworkBreakdown.length, 0);
    });
  });

  describe('Edge cases', () => {
    it('should handle multiple relationship types', () => {
      const parent = manager.createEntity({ name: 'Parent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const sub = manager.createEntity({ name: 'Sub', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const branch = manager.createEntity({ name: 'Branch', type: 'branch', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const division = manager.createEntity({ name: 'Division', type: 'division', jurisdiction: 'US', industry: 'technology', metadata: {} });

      manager.addRelationship(parent.id, sub.id, 'subsidiary');
      manager.addRelationship(parent.id, branch.id, 'branch');
      manager.addRelationship(parent.id, division.id, 'division');

      assert.equal(manager.getChildren(parent.id).length, 3);
    });

    it('should not duplicate relationships', () => {
      const parent = manager.createEntity({ name: 'Parent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const child = manager.createEntity({ name: 'Child', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });

      manager.addRelationship(parent.id, child.id, 'subsidiary');
      const rel2 = manager.addRelationship(parent.id, child.id, 'branch');

      assert.ok(rel2);
      assert.equal(manager.getChildren(parent.id).length, 1);
    });

    it('should handle entities with no children in tree', () => {
      manager.createEntity({ name: 'Orphan 1', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      manager.createEntity({ name: 'Orphan 2', type: 'parent', jurisdiction: 'EU', industry: 'financial_services', metadata: {} });

      const tree = manager.getEntityTree();
      assert.equal(tree.length, 2);
      assert.equal(tree[0].children.length, 0);
      assert.equal(tree[1].children.length, 0);
    });

    it('should calculate compliance score from statuses', () => {
      const entity = manager.createEntity({ name: 'Entity', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });

      manager.setComplianceStatuses(entity.id, [
        { entityId: entity.id, framework: 'iso27001', totalControls: 100, compliant: 80, nonCompliant: 15, notAssessed: 5, lastAssessedAt: '2025-01-01' },
        { entityId: entity.id, framework: 'soc2', totalControls: 50, compliant: 40, nonCompliant: 5, notAssessed: 5, lastAssessedAt: '2025-01-01' },
      ]);

      const rollup = manager['rollup'];
      const statuses = manager.getComplianceStatuses(entity.id);
      const score = rollup.calculateEntityComplianceScore(statuses);

      assert.ok(score > 0);
      assert.ok(score <= 100);
    });

    it('should get all frameworks for entity including parent and child frameworks', () => {
      const parent = manager.createEntity({ name: 'Parent', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      const child = manager.createEntity({ name: 'Child', type: 'subsidiary', jurisdiction: 'US', industry: 'financial_services', metadata: {} });

      manager.addRelationship(parent.id, child.id, 'subsidiary');

      manager.setComplianceStatuses(parent.id, [{
        entityId: parent.id, framework: 'iso27001', totalControls: 100, compliant: 80, nonCompliant: 15, notAssessed: 5, lastAssessedAt: '2025-01-01',
      }]);
      manager.setComplianceStatuses(child.id, [{
        entityId: child.id, framework: 'soc2', totalControls: 50, compliant: 40, nonCompliant: 5, notAssessed: 5, lastAssessedAt: '2025-01-01',
      }]);

      const frameworks = manager.getAllFrameworksForEntity(child.id);
      assert.ok(frameworks.includes('iso27001'));
      assert.ok(frameworks.includes('soc2'));
    });

    it('should return empty frameworks for non-existent entity', () => {
      assert.equal(manager.getAllFrameworksForEntity('non-existent').length, 0);
    });

    it('should return empty ancestors for root entity', () => {
      const root = manager.createEntity({ name: 'Root', type: 'parent', jurisdiction: 'US', industry: 'technology', metadata: {} });
      assert.equal(manager.getAncestors(root.id).length, 0);
    });

    it('should return empty children for leaf entity', () => {
      const leaf = manager.createEntity({ name: 'Leaf', type: 'subsidiary', jurisdiction: 'US', industry: 'technology', metadata: {} });
      assert.equal(manager.getChildren(leaf.id).length, 0);
    });
  });
});
