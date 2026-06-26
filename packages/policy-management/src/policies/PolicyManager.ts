import { randomUUID } from "node:crypto";
import type { Policy, PolicyTemplate, Attestation, PolicyStatus, PolicyCategory, PolicyStats } from "../types.js";
import { POLICY_TEMPLATES, getTemplateById, getTemplatesByCategory, getTemplatesByFramework } from "../templates.js";

export { POLICY_TEMPLATES, getTemplateById, getTemplatesByCategory, getTemplatesByFramework };

export class PolicyManager {
  private policies: Map<string, Policy> = new Map();
  private templates: PolicyTemplate[] = [...POLICY_TEMPLATES];

  createFromTemplate(templateId: string, owner: string, approver: string): Policy | null {
    const template = this.templates.find((t) => t.id === templateId);
    if (!template) return null;
    const policy = this.createPolicy({
      title: template.name,
      category: template.category,
      owner,
      approver,
      content: template.content,
      framework: template.framework,
    });
    return policy;
  }

  createPolicy(input: { title: string; category: PolicyCategory; owner: string; approver: string; content: string; framework: string }): Policy {
    const policy: Policy = {
      id: randomUUID(),
      title: input.title,
      category: input.category,
      version: 1,
      status: "draft",
      owner: input.owner,
      approver: input.approver,
      content: input.content,
      framework: input.framework,
      effectiveDate: "",
      reviewDate: "",
      changeLog: [],
      attestations: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    this.policies.set(policy.id, policy);
    return policy;
  }

  getPolicy(id: string): Policy | undefined { return this.policies.get(id); }
  listPolicies(): Policy[] { return Array.from(this.policies.values()); }
  getPoliciesByCategory(cat: PolicyCategory): Policy[] { return this.listPolicies().filter((p) => p.category === cat); }
  getTemplates(): PolicyTemplate[] { return [...this.templates]; }

  transitionPolicy(id: string, status: PolicyStatus): boolean {
    const policy = this.policies.get(id);
    if (!policy) return false;
    if (status === "published") {
      policy.effectiveDate = new Date().toISOString();
      policy.reviewDate = new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString();
    }
    policy.status = status;
    policy.updatedAt = new Date().toISOString();
    return true;
  }

  incrementVersion(id: string, changedBy: string, summary: string): boolean {
    const policy = this.policies.get(id);
    if (!policy) return false;
    policy.changeLog.push({ version: policy.version, changedBy, changedAt: new Date().toISOString(), summary });
    policy.version++;
    policy.status = "draft";
    policy.updatedAt = new Date().toISOString();
    return true;
  }

  addAttestation(policyId: string, employeeId: string, employeeName: string): Attestation | null {
    const policy = this.policies.get(policyId);
    if (!policy) return null;
    const attestation: Attestation = { id: randomUUID(), employeeId, employeeName, acknowledgedAt: new Date().toISOString(), attestedVersion: policy.version };
    policy.attestations.push(attestation);
    return attestation;
  }

  getStats(): PolicyStats {
    const policies = this.listPolicies();
    return {
      totalPolicies: policies.length,
      byStatus: {
        draft: policies.filter((p) => p.status === "draft").length,
        under_review: policies.filter((p) => p.status === "under_review").length,
        approved: policies.filter((p) => p.status === "approved").length,
        published: policies.filter((p) => p.status === "published").length,
        archived: policies.filter((p) => p.status === "archived").length,
      },
      byCategory: {
        security: policies.filter((p) => p.category === "security").length,
        privacy: policies.filter((p) => p.category === "privacy").length,
        compliance: policies.filter((p) => p.category === "compliance").length,
        operational: policies.filter((p) => p.category === "operational").length,
        hr: policies.filter((p) => p.category === "hr").length,
        financial: policies.filter((p) => p.category === "financial").length,
      },
      upcomingReviews: policies.filter((p) => p.status === "published" && new Date(p.reviewDate) < new Date(Date.now() + 30 * 24 * 60 * 60 * 1000)).length,
      attestationsPending: 0,
    };
  }
}
