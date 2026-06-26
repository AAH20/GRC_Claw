import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { EvidenceCollectorEngine } from "./EvidenceCollector.js";
import type {
  SystemAdapter,
  MFAEvidence,
  EncryptionEvidence,
  AccessControlEvidence,
  LoggingEvidence,
  PatchEvidence,
  NetworkSecurityEvidence,
  BackupEvidence,
} from "./types.js";

/** Mock SystemAdapter for testing */
const createMockAdapter = (): SystemAdapter => ({
  queryMFA: async (): Promise<MFAEvidence> => ({
    enforced: true,
    totalUsers: 100,
    mfaEnabledUsers: 98,
    methods: ["totp", "sms"],
    lastEnforcedAt: "2025-01-15T00:00:00Z",
  }),
  queryEncryptionAtRest: async (): Promise<EncryptionEvidence> => ({
    enabled: true,
    algorithm: "AES-256",
    keyRotationDays: 90,
    lastRotatedAt: "2025-06-01T00:00:00Z",
    details: { provider: "aws-kms" },
  }),
  queryEncryptionInTransit: async (): Promise<EncryptionEvidence> => ({
    enabled: true,
    algorithm: "TLS-1.3",
    details: { minVersion: "TLSv1.3" },
  }),
  queryAccessControl: async (): Promise<AccessControlEvidence> => ({
    leastPrivilege: true,
    totalRoles: 25,
    excessiveRoles: 2,
    lastAuditAt: "2025-05-01T00:00:00Z",
    details: {},
  }),
  queryLogging: async (): Promise<LoggingEvidence> => ({
    enabled: true,
    logTypes: ["audit", "security", "application"],
    retentionDays: 365,
    alertingEnabled: true,
    lastConfiguredAt: "2025-03-01T00:00:00Z",
  }),
  queryPatchManagement: async (): Promise<PatchEvidence> => ({
    lastPatchDate: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
    pendingPatches: 3,
    criticalPatches: 0,
    autoUpdateEnabled: true,
    details: {},
  }),
  queryNetworkSecurity: async (): Promise<NetworkSecurityEvidence> => ({
    firewallEnabled: true,
    segmentationEnabled: true,
    totalRules: 42,
    openPorts: 3,
    lastAuditAt: "2025-06-10T00:00:00Z",
  }),
  queryBackup: async (): Promise<BackupEvidence> => ({
    configured: true,
    frequency: "daily",
    lastBackupAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
    retentionDays: 90,
    testedAt: "2025-06-01T00:00:00Z",
    testPassed: true,
  }),
});

describe("EvidenceCollectorEngine", () => {
  it("should collect MFA evidence", async () => {
    const engine = new EvidenceCollectorEngine(createMockAdapter());
    const result = await engine.collectSingle({
      category: "mfa",
      framework: "SOC2",
      controlId: "CC6.1",
    });

    assert.ok(result.id);
    assert.equal(result.category, "mfa");
    assert.equal(result.framework, "SOC2");
    assert.equal(result.controlId, "CC6.1");
    assert.ok(result.hash.startsWith("sha256:"));
    assert.equal(result.status, "compliant");
  });

  it("should collect encryption evidence", async () => {
    const engine = new EvidenceCollectorEngine(createMockAdapter());
    const result = await engine.collectSingle({
      category: "encryption",
      framework: "ISO27001",
      controlId: "A.10.1.1",
    });

    assert.equal(result.category, "encryption");
    assert.equal(result.framework, "ISO27001");
    assert.equal(result.status, "compliant");
  });

  it("should collect multiple evidence types in batch", async () => {
    const engine = new EvidenceCollectorEngine(createMockAdapter());
    const result = await engine.collect([
      { category: "mfa", framework: "SOC2", controlId: "CC6.1" },
      { category: "logging", framework: "SOC2", controlId: "CC7.1" },
      { category: "backup", framework: "SOC2", controlId: "CC7.2" },
    ]);

    assert.equal(result.items.length, 3);
    assert.equal(result.errors.length, 0);
    assert.equal(result.status, "completed");
  });

  it("should provide compliance summary", async () => {
    const engine = new EvidenceCollectorEngine(createMockAdapter());
    await engine.collect([
      { category: "mfa", framework: "SOC2", controlId: "CC6.1" },
      { category: "encryption", framework: "SOC2", controlId: "CC6.2" },
      { category: "logging", framework: "SOC2", controlId: "CC7.1" },
    ]);

    const summary = engine.getComplianceSummary("SOC2");
    assert.equal(summary.total, 3);
    assert.ok(summary.compliancePercentage >= 0);
  });

  it("should filter evidence by framework", async () => {
    const engine = new EvidenceCollectorEngine(createMockAdapter());
    await engine.collect([
      { category: "mfa", framework: "SOC2", controlId: "CC6.1" },
      { category: "mfa", framework: "ISO27001", controlId: "A.9.4.2" },
    ]);

    const soc2 = engine.getEvidenceByFramework("SOC2");
    const iso = engine.getEvidenceByFramework("ISO27001");
    assert.equal(soc2.length, 1);
    assert.equal(iso.length, 1);
  });

  it("should handle adapter errors gracefully", async () => {
    const failingAdapter: SystemAdapter = {
      ...createMockAdapter(),
      queryMFA: async () => {
        throw new Error("IdP unavailable");
      },
    };

    const engine = new EvidenceCollectorEngine(failingAdapter);
    const result = await engine.collect([
      { category: "mfa", framework: "SOC2", controlId: "CC6.1" },
    ]);

    assert.equal(result.items.length, 0);
    assert.equal(result.errors.length, 1);
    assert.ok(result.errors[0].includes("IdP unavailable"));
  });

  it("should clear evidence store", async () => {
    const engine = new EvidenceCollectorEngine(createMockAdapter());
    await engine.collect([
      { category: "mfa", framework: "SOC2", controlId: "CC6.1" },
    ]);
    assert.equal(engine.getAllEvidence().length, 1);

    engine.clearEvidence();
    assert.equal(engine.getAllEvidence().length, 0);
  });
});
