export type ProofSystem = "groth16" | "halo2" | "bulletproofs" | "plonk";

export interface ComplianceProof {
  id: string;
  proofSystem: ProofSystem;
  publicInputs: string[];
  proof: string;
  verificationKey: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

export interface ComplianceCircuit {
  name: string;
  constraints: number;
  publicInputs: string[];
  privateInputs: string[];
  description: string;
}

export interface ProofVerification {
  valid: boolean;
  proofId: string;
  verifiedAt: string;
  metadata: Record<string, unknown>;
}

export interface ZKComplianceInput {
  tenantId: string;
  frameworkCode: string;
  controlId: string;
  evidenceHashes: string[];
  controlStatus: string;
  metadata: Record<string, unknown>;
}

export interface ZKComplianceOutput {
  proof: ComplianceProof;
  verificationKey: string;
  publicSignals: string[];
}
