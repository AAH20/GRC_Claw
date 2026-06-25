import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { AuditManager } from "./audit/AuditManager.js";

describe("AuditManager", () => {
  it("should create audit and add findings", () => {
    const mgr = new AuditManager();
    const audit = mgr.createAudit({ name: "Annual Audit", type: "internal", scope: ["access control"], framework: "ISO 27001", leadAuditor: "Jane", team: ["Jane", "John"], startDate: "2026-01-01", endDate: "2026-03-01" });
    assert.ok(audit.id);
    assert.equal(audit.status, "planning");

    mgr.transitionAudit(audit.id, "fieldwork");
    const finding = mgr.addFinding(audit.id, { severity: "high", status: "open", title: "MFA Missing", description: "MFA not enforced", affectedControls: ["A.9.4"], evidence: [], rootCause: "Policy gap", remediation: "Enable MFA" });
    assert.ok(finding);

    const report = mgr.generateReport(audit.id);
    assert.ok(report);
    assert.equal(report.totalFindings, 1);
  });

  it("should manage CAPA", () => {
    const mgr = new AuditManager();
    const capa = mgr.createCAPA("f1", "corrective", "Fix issue", "Owner", "2026-06-01");
    assert.ok(capa.id);
    assert.equal(capa.status, "open");
  });
});
