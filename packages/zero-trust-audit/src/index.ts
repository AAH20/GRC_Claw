import { createHash, createSign, createVerify, generateKeyPairSync, randomUUID } from "node:crypto";

// ─── Types ───────────────────────────────────────────────────────────────────

export interface AuditRecord {
  id: string;
  timestamp: string;
  actor: string;
  action: string;
  resource: string;
  metadata: Record<string, unknown>;
  hash: string;
  previousHash: string;
  signature: string;
}

export interface AuditChain {
  records: AuditRecord[];
  merkleRoot: string;
  genesisHash: string;
  lastHash: string;
  length: number;
}

export interface EvidenceRecord {
  id: string;
  type: string;
  hash: string;
  timestamp: string;
  source: string;
  metadata: Record<string, unknown>;
  attestations: Attestation[];
}

export interface Attestation {
  attester: string;
  timestamp: string;
  signature: string;
  statement: string;
}

export interface MerkleProof {
  leaf: string;
  index: number;
  siblings: string[];
  path: number[];
}

export interface KeyPair {
  publicKey: string;
  privateKey: string;
}

export interface ChainFilter {
  actor?: string;
  action?: string;
  resource?: string;
  from?: string;
  to?: string;
}

export interface Pagination {
  offset?: number;
  limit?: number;
}

export interface ChainStatistics {
  length: number;
  genesisHash: string;
  lastHash: string;
  merkleRoot: string;
  firstTimestamp: string | null;
  lastTimestamp: string | null;
  actors: string[];
  actions: string[];
  isValid: boolean;
}

export interface CourtExport {
  chain: AuditChain;
  period: { from: string; to: string };
  exportedAt: string;
  exportedBy: string;
  recordCount: number;
  merkleRoot: string;
  integrityHash: string;
  format: "json" | "csv" | "pdf";
}

export interface Affidavit {
  id: string;
  chainId: string;
  attestor: string;
  statement: string;
  recordCount: number;
  merkleRoot: string;
  period: { from: string; to: string };
  generatedAt: string;
  signature: string;
}

export interface Notarization {
  chainId: string;
  notary: string;
  timestamp: string;
  merkleRoot: string;
  recordCount: number;
  signature: string;
  certificateId: string;
}

export interface EvidenceReport {
  generatedAt: string;
  period: { from: string; to: string };
  totalRecords: number;
  totalEvidence: number;
  chainValid: boolean;
  records: AuditRecord[];
  evidence: EvidenceRecord[];
  merkleRoot: string;
}

// ─── CryptoSigner ────────────────────────────────────────────────────────────

export class CryptoSigner {
  /**
   * Generate an Ed25519 key pair for signing.
   */
  static generateKeyPair(): KeyPair {
    const { publicKey, privateKey } = generateKeyPairSync("ed25519", {
      publicKeyEncoding: { type: "spki", format: "pem" },
      privateKeyEncoding: { type: "pkcs8", format: "pem" },
    });
    return { publicKey, privateKey };
  }

  /**
   * Sign data with an Ed25519 private key.
   */
  static sign(data: string, privateKey: string): string {
    const signer = createSign("Ed25519");
    signer.update(data);
    return signer.sign(privateKey, "base64");
  }

  /**
   * Verify an Ed25519 signature.
   */
  static verify(data: string, signature: string, publicKey: string): boolean {
    try {
      const verifier = createVerify("Ed25519");
      verifier.update(data);
      return verifier.verify(publicKey, signature, "base64");
    } catch {
      return false;
    }
  }

  /**
   * Compute SHA-256 hash of data.
   */
  static hash(data: string): string {
    return createHash("sha256").update(data).digest("hex");
  }

  /**
   * Compute hash chain over records — each record's hash includes the previous.
   */
  static hashChain(records: AuditRecord[]): string {
    if (records.length === 0) return "";
    let chain = "";
    for (const rec of records) {
      chain = CryptoSigner.hash(chain + rec.hash);
    }
    return chain;
  }
}

// ─── MerkleTree ──────────────────────────────────────────────────────────────

export class MerkleTree {
  private leaves: string[] = [];
  private layers: string[][] = [];

  /**
   * Build a Merkle tree from leaf hashes.
   */
  buildTree(leaves: string[]): void {
    if (leaves.length === 0) {
      this.leaves = [];
      this.layers = [];
      return;
    }
    this.leaves = [...leaves];
    this.rebuild();
  }

  /**
   * Add a leaf and rebuild the tree.
   */
  addLeaf(leaf: string): void {
    this.leaves.push(leaf);
    this.rebuild();
  }

  /**
   * Get the Merkle root.
   */
  getRoot(): string {
    if (this.layers.length === 0) return "";
    return this.layers[this.layers.length - 1][0] ?? "";
  }

  /**
   * Get the number of leaves.
   */
  getTreeSize(): number {
    return this.leaves.length;
  }

  /**
   * Generate a Merkle proof for a leaf.
   */
  getProof(leaf: string): MerkleProof | null {
    const index = this.leaves.indexOf(leaf);
    if (index === -1) return null;

    const siblings: string[] = [];
    const path: number[] = [];
    let idx = index;

    for (let layer = 0; layer < this.layers.length - 1; layer++) {
      const currentLayer = this.layers[layer]!;
      const isRightNode = idx % 2 === 1;
      const siblingIndex = isRightNode ? idx - 1 : idx + 1;

      if (siblingIndex < currentLayer.length) {
        siblings.push(currentLayer[siblingIndex]!);
      } else {
        siblings.push(currentLayer[idx]!);
      }
      path.push(isRightNode ? 1 : 0);
      idx = Math.floor(idx / 2);
    }

    return { leaf, index, siblings, path };
  }

  /**
   * Verify a Merkle proof against a root.
   */
  static verifyProof(leaf: string, proof: MerkleProof, root: string): boolean {
    let hash = leaf;
    for (let i = 0; i < proof.siblings.length; i++) {
      const sibling = proof.siblings[i]!;
      if (proof.path[i] === 1) {
        hash = CryptoSigner.hash(sibling + hash);
      } else {
        hash = CryptoSigner.hash(hash + sibling);
      }
    }
    return hash === root;
  }

  private rebuild(): void {
    this.layers = [];
    if (this.leaves.length === 0) return;

    this.layers.push([...this.leaves]);
    let current = [...this.leaves];

    while (current.length > 1) {
      const next: string[] = [];
      for (let i = 0; i < current.length; i += 2) {
        const left = current[i]!;
        const right = current[i + 1] ?? left;
        next.push(CryptoSigner.hash(left + right));
      }
      this.layers.push(next);
      current = next;
    }
  }
}

// ─── EvidenceVault ───────────────────────────────────────────────────────────

export class EvidenceVault {
  private evidence = new Map<string, EvidenceRecord>();

  /**
   * Store an evidence record.
   */
  storeEvidence(evidence: Omit<EvidenceRecord, "hash" | "attestations">): EvidenceRecord {
    const hash = CryptoSigner.hash(
      JSON.stringify({ id: evidence.id, type: evidence.type, source: evidence.source, metadata: evidence.metadata }),
    );
    const record: EvidenceRecord = { ...evidence, hash, attestations: [] };
    this.evidence.set(record.id, record);
    return record;
  }

  /**
   * Retrieve evidence by ID.
   */
  retrieveEvidence(id: string): EvidenceRecord | null {
    return this.evidence.get(id) ?? null;
  }

  /**
   * Verify evidence integrity by recomputing its hash.
   */
  verifyEvidence(id: string): boolean {
    const record = this.evidence.get(id);
    if (!record) return false;
    const expected = CryptoSigner.hash(
      JSON.stringify({ id: record.id, type: record.type, source: record.source, metadata: record.metadata }),
    );
    return record.hash === expected;
  }

  /**
   * Add an attestation to evidence.
   */
  attestEvidence(id: string, attester: string, privateKey?: string): Attestation | null {
    const record = this.evidence.get(id);
    if (!record) return null;

    const statement = `I attest that evidence ${id} is authentic and unaltered.`;
    const signature = privateKey
      ? CryptoSigner.sign(statement, privateKey)
      : CryptoSigner.hash(statement + attester);

    const attestation: Attestation = {
      attester,
      timestamp: new Date().toISOString(),
      signature,
      statement,
    };
    record.attestations.push(attestation);
    return attestation;
  }

  /**
   * Export evidence as JSON or CSV.
   */
  exportEvidence(id: string, format: "json" | "csv"): string | null {
    const record = this.evidence.get(id);
    if (!record) return null;
    if (format === "json") return JSON.stringify(record, null, 2);
    return this.toCsv(record);
  }

  /**
   * Get the full attestation chain for evidence.
   */
  getEvidenceChain(id: string): Attestation[] {
    return this.evidence.get(id)?.attestations ?? [];
  }

  /**
   * Generate an audit report filtered by criteria.
   */
  generateReport(filters?: { type?: string; source?: string; from?: string; to?: string }): EvidenceRecord[] {
    let results = Array.from(this.evidence.values());
    if (filters?.type) results = results.filter((e) => e.type === filters.type);
    if (filters?.source) results = results.filter((e) => e.source === filters.source);
    if (filters?.from) results = results.filter((e) => e.timestamp >= filters.from!);
    if (filters?.to) results = results.filter((e) => e.timestamp <= filters.to!);
    return results;
  }

  private toCsv(record: EvidenceRecord): string {
    const lines = [
      "field,value",
      `id,${record.id}`,
      `type,${record.type}`,
      `hash,${record.hash}`,
      `timestamp,${record.timestamp}`,
      `source,${record.source}`,
      `attestations,${record.attestations.length}`,
    ];
    return lines.join("\n");
  }
}

// ─── CourtAdmissibleExporter ─────────────────────────────────────────────────

export class CourtAdmissibleExporter {
  /**
   * Export a chain as court-admissible evidence.
   */
  exportForCourt(chain: AuditChain, period: { from: string; to: string }): CourtExport {
    const exportedAt = new Date().toISOString();
    const serialized = JSON.stringify(chain);
    const integrityHash = CryptoSigner.hash(serialized);

    return {
      chain,
      period,
      exportedAt,
      exportedBy: "GRC_Claw Zero-Trust Audit System",
      recordCount: chain.length,
      merkleRoot: chain.merkleRoot,
      integrityHash,
      format: "json",
    };
  }

  /**
   * Generate a sworn affidavit for a chain.
   */
  generateAffidavit(chain: AuditChain, attestor: string, privateKey?: string): Affidavit {
    const now = new Date().toISOString();
    const statement = `I, ${attestor}, hereby affirm that the attached audit chain of ${chain.length} records, with Merkle root ${chain.merkleRoot}, is a true and accurate record of events occurring between the chain's genesis and its most recent entry, and that the chain has not been tampered with or altered in any way.`;
    const signature = privateKey
      ? CryptoSigner.sign(statement, privateKey)
      : CryptoSigner.hash(statement + attestor);

    const firstRecord = chain.records[0];
    const lastRecord = chain.records[chain.records.length - 1];

    return {
      id: randomUUID(),
      chainId: chain.genesisHash,
      attestor,
      statement,
      recordCount: chain.length,
      merkleRoot: chain.merkleRoot,
      period: {
        from: firstRecord?.timestamp ?? "",
        to: lastRecord?.timestamp ?? "",
      },
      generatedAt: now,
      signature,
    };
  }

  /**
   * Notarize a chain — creates a signed certificate of authenticity.
   */
  notarize(chain: AuditChain, notary: string, privateKey?: string): Notarization {
    const now = new Date().toISOString();
    const payload = `${chain.genesisHash}:${chain.merkleRoot}:${chain.length}:${now}`;
    const signature = privateKey
      ? CryptoSigner.sign(payload, privateKey)
      : CryptoSigner.hash(payload + notary);

    return {
      chainId: chain.genesisHash,
      notary,
      timestamp: now,
      merkleRoot: chain.merkleRoot,
      recordCount: chain.length,
      signature,
      certificateId: CryptoSigner.hash(`notarize:${chain.genesisHash}:${now}`),
    };
  }

  /**
   * Verify a notarization certificate.
   */
  verifyNotarization(notarization: Notarization, publicKey?: string): boolean {
    if (!publicKey) {
      const payload = `${notarization.chainId}:${notarization.merkleRoot}:${notarization.recordCount}:${notarization.timestamp}`;
      const expected = CryptoSigner.hash(payload + notarization.notary);
      return notarization.signature === expected;
    }
    const payload = `${notarization.chainId}:${notarization.merkleRoot}:${notarization.recordCount}:${notarization.timestamp}`;
    return CryptoSigner.verify(payload, notarization.signature, publicKey);
  }
}

// ─── ZeroTrustAuditTrail ─────────────────────────────────────────────────────

export class ZeroTrustAuditTrail {
  private records: AuditRecord[] = [];
  private merkleTree = new MerkleTree();
  private signingKeys: KeyPair;

  constructor(keys?: KeyPair) {
    this.signingKeys = keys ?? CryptoSigner.generateKeyPair();
  }

  /**
   * Record an immutable audit event.
   */
  recordEvent(
    actor: string,
    action: string,
    resource: string,
    metadata: Record<string, unknown> = {},
  ): AuditRecord {
    const id = randomUUID();
    const timestamp = new Date().toISOString();
    const previousHash = this.records.length > 0 ? this.records[this.records.length - 1]!.hash : "0".repeat(64);

    const hashInput = JSON.stringify({ id, timestamp, actor, action, resource, metadata, previousHash });
    const hash = CryptoSigner.hash(hashInput);
    const signature = CryptoSigner.sign(hash, this.signingKeys.privateKey);

    const record: AuditRecord = {
      id,
      timestamp,
      actor,
      action,
      resource,
      metadata,
      hash,
      previousHash,
      signature,
    };

    this.records.push(record);
    this.merkleTree.addLeaf(hash);
    return record;
  }

  /**
   * Verify the integrity of the entire chain.
   */
  verifyChain(): boolean {
    for (let i = 0; i < this.records.length; i++) {
      const record = this.records[i]!;
      const expectedPrev = i === 0 ? "0".repeat(64) : this.records[i - 1]!.hash;
      if (record.previousHash !== expectedPrev) return false;

      const hashInput = JSON.stringify({
        id: record.id,
        timestamp: record.timestamp,
        actor: record.actor,
        action: record.action,
        resource: record.resource,
        metadata: record.metadata,
        previousHash: record.previousHash,
      });
      if (CryptoSigner.hash(hashInput) !== record.hash) return false;
      if (!CryptoSigner.verify(record.hash, record.signature, this.signingKeys.publicKey)) return false;
    }
    return true;
  }

  /**
   * Verify a single record's hash and signature.
   */
  verifyRecord(id: string): boolean {
    const record = this.records.find((r) => r.id === id);
    if (!record) return false;

    const hashInput = JSON.stringify({
      id: record.id,
      timestamp: record.timestamp,
      actor: record.actor,
      action: record.action,
      resource: record.resource,
      metadata: record.metadata,
      previousHash: record.previousHash,
    });
    if (CryptoSigner.hash(hashInput) !== record.hash) return false;
    return CryptoSigner.verify(record.hash, record.signature, this.signingKeys.publicKey);
  }

  /**
   * Get a record by ID.
   */
  getRecord(id: string): AuditRecord | null {
    return this.records.find((r) => r.id === id) ?? null;
  }

  /**
   * Query records with optional filters and pagination.
   */
  getRecords(filters?: ChainFilter, pagination?: Pagination): AuditRecord[] {
    let results = [...this.records];

    if (filters?.actor) results = results.filter((r) => r.actor === filters.actor);
    if (filters?.action) results = results.filter((r) => r.action === filters.action);
    if (filters?.resource) results = results.filter((r) => r.resource === filters.resource);
    if (filters?.from) results = results.filter((r) => r.timestamp >= filters.from!);
    if (filters?.to) results = results.filter((r) => r.timestamp <= filters.to!);

    const offset = pagination?.offset ?? 0;
    const limit = pagination?.limit ?? results.length;
    return results.slice(offset, offset + limit);
  }

  /**
   * Get a segment of the chain.
   */
  getChain(from?: number, to?: number): AuditChain {
    const start = from ?? 0;
    const end = to ?? this.records.length;
    const segment = this.records.slice(start, end);

    return {
      records: segment,
      merkleRoot: this.merkleTree.getRoot(),
      genesisHash: this.records[0]?.hash ?? "",
      lastHash: this.records[this.records.length - 1]?.hash ?? "",
      length: segment.length,
    };
  }

  /**
   * Export the chain as JSON or CSV.
   */
  exportChain(format: "json" | "csv"): string {
    if (format === "json") {
      return JSON.stringify(this.getChain(), null, 2);
    }
    const header = "id,timestamp,actor,action,resource,hash,previousHash";
    const rows = this.records.map(
      (r) => `${r.id},${r.timestamp},${r.actor},${r.action},${r.resource},${r.hash},${r.previousHash}`,
    );
    return [header, ...rows].join("\n");
  }

  /**
   * Import a chain from JSON, replacing current state.
   */
  importChain(data: string): void {
    const parsed = JSON.parse(data) as AuditChain;
    if (!Array.isArray(parsed.records)) {
      throw new Error("Invalid chain data: records must be an array");
    }
    this.records = parsed.records;
    this.merkleTree.buildTree(this.records.map((r) => r.hash));
  }

  /**
   * Get chain statistics.
   */
  getStatistics(): ChainStatistics {
    const actors = [...new Set(this.records.map((r) => r.actor))];
    const actions = [...new Set(this.records.map((r) => r.action))];

    return {
      length: this.records.length,
      genesisHash: this.records[0]?.hash ?? "",
      lastHash: this.records[this.records.length - 1]?.hash ?? "",
      merkleRoot: this.merkleTree.getRoot(),
      firstTimestamp: this.records[0]?.timestamp ?? null,
      lastTimestamp: this.records[this.records.length - 1]?.timestamp ?? null,
      actors,
      actions,
      isValid: this.verifyChain(),
    };
  }

  /**
   * Get the signing public key (for external verification).
   */
  getPublicKey(): string {
    return this.signingKeys.publicKey;
  }

  /**
   * Verify the entire chain integrity.
   * Alias for verifyChain() for backward compatibility.
   */
  verify(): { valid: boolean; length: number; errors: string[] } {
    const valid = this.verifyChain();
    return {
      valid,
      length: this.records.length,
      errors: valid ? [] : ["Chain integrity check failed"],
    };
  }

  /**
   * Export evidence for a specific record or all records.
   * @param format - "json", "csv", "xml", or "pdf"
   */
  exportEvidence(formatOrOpts: "json" | "csv" | "xml" | "pdf" | { format: "json" | "csv" | "xml" | "pdf" } = "json"): string {
    const format = typeof formatOrOpts === "string" ? formatOrOpts : formatOrOpts.format;
    const records = this.getRecords();
    if (format === "csv") {
      if (records.length === 0) return "";
      const header = "id,timestamp,actor,action,resource,hash";
      const rows = records.map(r =>
        `${r.id},${r.timestamp},${r.actor},${r.action},${r.resource},${r.hash}`
      );
      return [header, ...rows].join("\n");
    }
    return JSON.stringify(records, null, 2);
  }
}
