import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { PolicyManager } from "./policies/PolicyManager.js";

describe("PolicyManager", () => {
  it("should create policy from template", () => {
    const mgr = new PolicyManager();
    const policy = mgr.createFromTemplate("tpl-1", "CISO", "CEO");
    assert.ok(policy);
    assert.equal(policy.title, "Information Security Policy");
    assert.equal(policy.version, 1);
  });

  it("should manage policy lifecycle", () => {
    const mgr = new PolicyManager();
    const policy = mgr.createFromTemplate("tpl-2", "Owner", "Approver");
    mgr.transitionPolicy(policy.id, "under_review");
    mgr.transitionPolicy(policy.id, "approved");
    mgr.transitionPolicy(policy.id, "published");
    assert.equal(policy.status, "published");
    assert.ok(policy.effectiveDate);
  });

  it("should increment version", () => {
    const mgr = new PolicyManager();
    const policy = mgr.createFromTemplate("tpl-3", "O", "A");
    mgr.incrementVersion(policy.id, "CISO", "Updated for new regulation");
    assert.equal(policy.version, 2);
    assert.equal(policy.changeLog.length, 1);
  });

  it("should add attestation", () => {
    const mgr = new PolicyManager();
    const policy = mgr.createFromTemplate("tpl-1", "O", "A");
    const att = mgr.addAttestation(policy.id, "emp-1", "John Doe");
    assert.ok(att);
    assert.equal(policy.attestations.length, 1);
  });

  it("should list templates", () => {
    const mgr = new PolicyManager();
    assert.ok(mgr.getTemplates().length >= 5);
  });
});
