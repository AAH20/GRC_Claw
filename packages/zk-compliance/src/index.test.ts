import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ComplianceProver } from "./proofs/ComplianceProver.js";

describe("ComplianceProver", () => {
  it("should generate a ZK proof", async () => {
    const prover = new ComplianceProver();
    const proof = await prover.generateProof({
      evidenceHashes: ["hash1", "hash2"],
      controlStatus: "implemented",
      frameworkCode: "iso27001",
      controlId: "A.5.1",
    });
    assert.ok(proof.id.startsWith("zk-proof-"));
    assert.equal(proof.proofSystem, "groth16");
    assert.ok(proof.proof);
    assert.ok(proof.verificationKey);
  });

  it("should verify a valid proof", async () => {
    const prover = new ComplianceProver();
    const proof = await prover.generateProof({
      evidenceHashes: ["hash1"],
      controlStatus: "implemented",
      frameworkCode: "iso27001",
      controlId: "A.5.1",
    });
    const verification = await prover.verifyProof(proof);
    assert.ok(verification.valid);
  });

  it("should return circuit constraints", () => {
    const prover = new ComplianceProver();
    const circuits = prover.getCircuitConstraints();
    assert.equal(circuits.length, 3);
    assert.ok(circuits.some((c) => c.name === "evidence-integrity"));
  });
});
