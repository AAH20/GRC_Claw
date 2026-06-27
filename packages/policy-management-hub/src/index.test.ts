import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { PolicyManagementHub } from "./PolicyManagementHub.js";

describe("PolicyManagementHub", () => {
  const hub = new PolicyManagementHub();

  it("should have 52 built-in templates", () => {
    const templates = hub.getTemplates();
    assert.equal(templates.length, 52);
  });

  it("should create a policy", () => {
    const policy = hub.createPolicy({
      title: "Test Security Policy",
      category: "security",
      content: "Test content",
      summary: "Test summary",
      owner: "admin",
      department: "IT",
      framework: "ISO 27001",
      effectiveDate: "2025-01-01",
      reviewDate: "2026-01-01",
      tags: ["security", "test"],
    });
    assert.equal(policy.status, "draft");
    assert.equal(policy.version, 1);
    assert.equal(policy.title, "Test Security Policy");
  });

  it("should initiate approval workflow", () => {
    const policy = hub.createPolicy({
      title: "Approval Test Policy",
      category: "compliance",
      content: "Content",
      summary: "Summary",
      owner: "admin",
      department: "Legal",
      framework: "SOC 2",
      effectiveDate: "2025-01-01",
      reviewDate: "2026-01-01",
    });

    const workflow = hub.initiateApproval(policy.id, [
      { assigneeId: "mgr-1", assigneeName: "Manager 1", role: "Manager" },
      { assigneeId: "ciso-1", assigneeName: "CISO", role: "CISO" },
    ], "admin");

    assert.equal(workflow.steps.length, 2);
    assert.equal(workflow.isComplete, false);
    assert.equal(hub.getPolicy(policy.id)?.status, "under_review");
  });

  it("should complete approval and publish", () => {
    const policy = hub.createPolicy({
      title: "Publish Test Policy",
      category: "operational",
      content: "Content",
      summary: "Summary",
      owner: "admin",
      department: "Ops",
      framework: "General",
      effectiveDate: "2025-01-01",
      reviewDate: "2026-01-01",
    });

    const workflow = hub.initiateApproval(policy.id, [
      { assigneeId: "mgr-1", assigneeName: "Manager", role: "Manager" },
    ], "admin");

    hub.approveStep(workflow.id, workflow.steps[0].id, "mgr-1", "Looks good");

    const updatedPolicy = hub.getPolicy(policy.id);
    assert.equal(updatedPolicy?.status, "approved");

    hub.publishPolicy(policy.id, "admin");
    assert.equal(hub.getPolicy(policy.id)?.status, "published");
  });

  it("should assign and complete attestations", () => {
    const policy = hub.createPolicy({
      title: "Attestation Test Policy",
      category: "hr",
      content: "Content",
      summary: "Summary",
      owner: "admin",
      department: "HR",
      framework: "General",
      effectiveDate: "2025-01-01",
      reviewDate: "2026-01-01",
    });

    const attestations = hub.assignAttestation(policy.id, [
      { employeeId: "emp-1", employeeName: "Alice", employeeEmail: "alice@test.com", department: "Engineering" },
      { employeeId: "emp-2", employeeName: "Bob", employeeEmail: "bob@test.com", department: "Sales" },
    ], "2025-06-01");

    assert.equal(attestations.length, 2);
    assert.equal(attestations[0].status, "pending");

    hub.completeAttestation(policy.id, "emp-1");
    const policyAttestations = hub.getPolicy(policy.id)?.attestations;
    assert.equal(policyAttestations?.filter((a) => a.status === "attested").length, 1);
  });

  it("should map policy to controls", () => {
    const policy = hub.createPolicy({
      title: "Control Mapping Test",
      category: "security",
      content: "Content",
      summary: "Summary",
      owner: "admin",
      department: "IT",
      framework: "ISO 27001",
      effectiveDate: "2025-01-01",
      reviewDate: "2026-01-01",
    });

    hub.mapToControl(policy.id, "A.5.1.1", "ISO 27001", "Information security policy", "admin");
    hub.mapToControl(policy.id, "A.9.4.2", "ISO 27001", "MFA requirement", "admin");

    const p = hub.getPolicy(policy.id);
    assert.equal(p?.controlMappings.length, 2);
  });

  it("should search and filter policies", () => {
    hub.createPolicy({
      title: "Search Test Security",
      category: "security",
      content: "Contains searchable text",
      summary: "Security summary",
      owner: "admin",
      department: "IT",
      framework: "ISO 27001",
      effectiveDate: "2025-01-01",
      reviewDate: "2026-01-01",
    });

    const results = hub.searchPolicies({ query: "searchable" });
    assert.ok(results.length >= 1);
    assert.ok(results.some((p) => p.title === "Search Test Security"));
  });

  it("should return correct stats", () => {
    const stats = hub.getStats();
    assert.ok(stats.totalPolicies > 0);
    assert.ok(typeof stats.byStatus === "object");
    assert.ok(typeof stats.byCategory === "object");
  });

  it("should get templates by category", () => {
    const securityTemplates = hub.getTemplatesByCategory("security");
    assert.ok(securityTemplates.length > 0);
    assert.ok(securityTemplates.every((t) => t.category === "security"));
  });

  it("should get templates by framework", () => {
    const iso27001Templates = hub.getTemplatesByFramework("ISO 27001");
    assert.ok(iso27001Templates.length > 0);
  });

  it("should reject approval step", () => {
    const policy = hub.createPolicy({
      title: "Reject Test Policy",
      category: "security",
      content: "Content",
      summary: "Summary",
      owner: "admin",
      department: "IT",
      framework: "ISO 27001",
      effectiveDate: "2025-01-01",
      reviewDate: "2026-01-01",
    });

    const workflow = hub.initiateApproval(policy.id, [
      { assigneeId: "mgr-1", assigneeName: "Manager", role: "Manager" },
    ], "admin");

    hub.rejectStep(workflow.id, workflow.steps[0].id, "mgr-1", "Needs more detail");
    assert.equal(hub.getPolicy(policy.id)?.status, "revision_needed");
  });

  it("should track events", () => {
    const policy = hub.createPolicy({
      title: "Event Tracking Policy",
      category: "compliance",
      content: "Content",
      summary: "Summary",
      owner: "admin",
      department: "Legal",
      framework: "SOC 2",
      effectiveDate: "2025-01-01",
      reviewDate: "2026-01-01",
    });

    const events = hub.getEvents(policy.id);
    assert.ok(events.length >= 1);
    assert.equal(events[0].kind, "policy_created");
  });
});
