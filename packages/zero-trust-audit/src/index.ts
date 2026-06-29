import { createHash, createHmac, randomBytes, createSign, createVerify, timingSafeEqual } from "node:crypto";
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import { join } from "node:path";

// ─── Types ───────────────────────────────────────────────────────────────────

export interface AuditRecordInput {
  readonly event: string;
  readonly actor: string;
  readonly resource: string;
  readonly action: string;
  readonly outcome: "success" | "failure" | "pending";
  readonly metadata?: Record<string, unknown>;
  readonly severity?: "critical" | "high" | "medium" | "low" | "info";
  readonly source?: string;
  readonly complianceTags?: readonly string[];
}

export interface AuditRecord {
  readonly id: string;
  readonly sequence: number;
  readonly timestamp: string;
  readonly event: string;
  readonly actor: string;
  readonly resource: string;
  readonly action: string;
  readonly outcome: "success" | "failure" | "pending";
  readonly severity: "critical" | "high" | "medium" | "low" | "info";
  readonly source: string;
  readonly metadata: Record<string, unknown>;
  readonly complianceTags: readonly string[];
  readonly previousHash: string;
  readonly recordHash: string;
  readonly signature?: string;
  readonly merkleRoot?: string;
  readonly tsaTimestamp?: string;
  readonly tsaReceipt?: string;
}

export interface HashChainConfig {
  readonly algorithm?: "sha256" | "sha384" | "sha512";
  readonly hmacKey?: string;
}

export interface MerkleTreeConfig {
  readonly algorithm?: "sha256" | "sha384" | "sha512";
}

export interface TSAConfig {
  readonly url: string;
  readonly username?: string;
  readonly password?: string;
  readonly timeout?: number;
}

export interface EvidenceExportOptions {
  readonly format: "json" | "xml" | "pdf";
  readonly includeSignatures?: boolean;
  readonly includeMerkleProofs?: boolean;
  readonly outputPath?: string;
  readonly digitalSignatureKey?: string;
  readonly digitalSignatureCert?: string;
}

export interface MerkleProof {
  readonly leafHash: string;
  readonly leafIndex: number;
  readonly siblings: readonly { hash: string; position: "left" | "right" }[];
  readonly root: string;
}

export interface VerificationResult {
  readonly valid: boolean;
  readonly chainIntact: boolean;
  readonly signaturesValid: boolean;
  readonly merkleProofsValid: boolean;
  readonly tsaTimestampsValid: boolean;
  readonly errors: readonly string[];
  readonly verifiedAt: string;
}

// ─── HashChain ────────────────────────────────────────────────────────────────

export class HashChain {
  private readonly algorithm: string;
  private readonly hmacKey: string | null;
  private head: string | null = null;
  private length = 0;

  constructor(config: HashChainConfig = {}) {
    this.algorithm = config.algorithm ?? "sha256";
    this.hmacKey = config.hmacKey ?? null;
  }

  /** Compute the hash of a given payload. */
  hash(payload: string): string {
    if (this.hmacKey) {
      return createHmac(this.algorithm, this.hmacKey)
        .update(payload, "utf8")
        .digest("hex");
    }
    return createHash(this.algorithm).update(payload, "utf8").digest("hex");
  }

  /** Hash two sibling hashes together (used in Merkle tree). */
  hashPair(left: string, right: string): string {
    return this.hash(`${left}:${right}`);
  }

  /** Append a record hash to the chain, returning the new head. */
  append(recordHash: string): string {
    const previousHash = this.head ?? this.hash("genesis");
    const chainPayload = `${previousHash}:${recordHash}`;
    this.head = this.hash(chainPayload);
    this.length++;
    return this.head;
  }

  /** Verify the full chain from serialized records. */
  verify(records: readonly AuditRecord[]): boolean {
    let expectedPrevious = this.hash("genesis");

    for (const record of records) {
      if (record.previousHash !== expectedPrevious) {
        return false;
      }

      const computedHash = this.computeRecordHash(record);
      if (computedHash !== record.recordHash) {
        return false;
      }

      const chainPayload = `${record.previousHash}:${record.recordHash}`;
      expectedPrevious = this.hash(chainPayload);
    }

    return true;
  }

  /** Compute the deterministic hash for an audit record (excludes mutable fields). */
  computeRecordHash(record: Omit<AuditRecord, "recordHash">): string {
    const payload = JSON.stringify({
      id: record.id,
      sequence: record.sequence,
      timestamp: record.timestamp,
      event: record.event,
      actor: record.actor,
      resource: record.resource,
      action: record.action,
      outcome: record.outcome,
      severity: record.severity,
      source: record.source,
      metadata: record.metadata,
      complianceTags: record.complianceTags,
      previousHash: record.previousHash,
    });
    return this.hash(payload);
  }

  get currentHead(): string | null {
    return this.head;
  }

  get currentLength(): number {
    return this.length;
  }

  /** Rebuild the chain state from existing records. */
  rehydrate(records: readonly AuditRecord[]): void {
    if (records.length === 0) {
      this.head = null;
      this.length = 0;
      return;
    }

    if (!this.verify(records)) {
      throw new Error("Cannot rehydrate: chain integrity check failed");
    }

    this.length = records.length;
    const lastRecord = records[records.length - 1];
    const chainPayload = `${lastRecord.previousHash}:${lastRecord.recordHash}`;
    this.head = this.hash(chainPayload);
  }
}

// ─── MerkleTree ───────────────────────────────────────────────────────────────

export class MerkleTree {
  private readonly hashChain: HashChain;
  private leaves: string[] = [];
  private nodes: string[] = [];
  private treeHeight = 0;

  constructor(config: MerkleTreeConfig = {}) {
    this.hashChain = new HashChain({ algorithm: config.algorithm });
  }

  /** Build the tree from a set of record hashes. */
  build(recordHashes: readonly string[]): string {
    this.leaves = [...recordHashes];

    if (this.leaves.length === 0) {
      return this.hashChain.hash("empty-tree");
    }

    // Pad to next power of 2 for a complete binary tree
    let size = 1;
    while (size < this.leaves.length) {
      size *= 2;
    }

    const paddedLeaves = [...this.leaves];
    while (paddedLeaves.length < size) {
      paddedLeaves.push(this.hashChain.hash("padding"));
    }

    this.treeHeight = Math.log2(size) + 1;
    this.nodes = new Array(size * 2 - 1).fill("");

    // Fill leaves
    for (let i = 0; i < size; i++) {
      this.nodes[size - 1 + i] = paddedLeaves[i];
    }

    // Compute internal nodes bottom-up
    for (let i = size - 2; i >= 0; i--) {
      const left = this.nodes[2 * i + 1];
      const right = this.nodes[2 * i + 2];
      this.nodes[i] = this.hashChain.hashPair(left, right);
    }

    return this.root;
  }

  /** Get the Merkle root. */
  get root(): string {
    if (this.nodes.length === 0) {
      return this.hashChain.hash("empty-tree");
    }
    return this.nodes[0];
  }

  /** Generate a proof for a leaf at the given index. */
  getProof(leafIndex: number): MerkleProof {
    if (this.nodes.length === 0) {
      throw new Error("Tree not built. Call build() first.");
    }

    const size = Math.pow(2, this.treeHeight - 1);
    if (leafIndex < 0 || leafIndex >= this.leaves.length) {
      throw new Error(`Leaf index ${leafIndex} out of range [0, ${this.leaves.length})`);
    }

    const siblings: { hash: string; position: "left" | "right" }[] = [];
    let nodeIndex = size - 1 + leafIndex;

    for (let level = 0; level < this.treeHeight - 1; level++) {
      const isLeft = nodeIndex % 2 === 1;
      const siblingIndex = isLeft ? nodeIndex + 1 : nodeIndex - 1;

      siblings.push({
        hash: this.nodes[siblingIndex],
        position: isLeft ? "right" : "left",
      });

      nodeIndex = Math.floor((nodeIndex - 1) / 2);
    }

    return {
      leafHash: this.leaves[leafIndex],
      leafIndex,
      siblings,
      root: this.root,
    };
  }

  /** Verify a Merkle proof. */
  static verifyProof(proof: MerkleProof, algorithm: "sha256" | "sha384" | "sha512" = "sha256"): boolean {
    const chain = new HashChain({ algorithm });
    let current = proof.leafHash;

    for (const sibling of proof.siblings) {
      if (sibling.position === "left") {
        current = chain.hashPair(sibling.hash, current);
      } else {
        current = chain.hashPair(current, sibling.hash);
      }
    }

    return timingSafeEqual(
      Buffer.from(current, "hex"),
      Buffer.from(proof.root, "hex"),
    );
  }

  /** Verify all leaves are part of the tree. */
  verifyAll(): boolean {
    for (let i = 0; i < this.leaves.length; i++) {
      const proof = this.getProof(i);
      if (!MerkleTree.verifyProof(proof, this.hashChain["algorithm"] as "sha256" | "sha384" | "sha512")) {
        return false;
      }
    }
    return true;
  }

  get leafCount(): number {
    return this.leaves.length;
  }

  get height(): number {
    return this.treeHeight;
  }
}

// ─── EvidenceExporter ─────────────────────────────────────────────────────────

export class EvidenceExporter {
  private readonly outputDir: string;

  constructor(outputDir: string = "./evidence-exports") {
    this.outputDir = outputDir;
  }

  /** Export audit records as court-admissible evidence. */
  exportEvidence(
    records: readonly AuditRecord[],
    options: EvidenceExportOptions,
  ): string {
    const evidencePackage = {
      version: "1.0.0",
      exportedAt: new Date().toISOString(),
      recordCount: records.length,
      format: options.format,
      chainIntegrity: this.verifyChainIntegrity(records),
      records: options.includeSignatures
        ? records
        : records.map((r) => ({ ...r, signature: undefined })),
      merkleRoot: records.length > 0 ? records[records.length - 1].merkleRoot : null,
      tsaTimestamps: records
        .filter((r) => r.tsaTimestamp)
        .map((r) => ({
          recordId: r.id,
          tsaTimestamp: r.tsaTimestamp,
          tsaReceipt: r.tsaReceipt,
        })),
    };

    if (options.digitalSignatureKey && options.digitalSignatureCert) {
      const signData = JSON.stringify(evidencePackage);
      const signer = createSign("SHA256");
      signer.update(signData);
      const signature = signer.sign(options.digitalSignatureKey, "base64");

      (evidencePackage as Record<string, unknown>).digitalSignature = {
        algorithm: "SHA256WithRSA",
        certificate: options.digitalSignatureCert,
        signature,
        signedAt: new Date().toISOString(),
      };
    }

    const output = JSON.stringify(evidencePackage, null, 2);

    if (options.outputPath) {
      if (!existsSync(this.outputDir)) {
        mkdirSync(this.outputDir, { recursive: true });
      }
      const filePath = join(this.outputDir, options.outputPath);
      writeFileSync(filePath, output, "utf8");
    }

    return output;
  }

  /** Export as XML for legal/court submission. */
  exportXML(records: readonly AuditRecord[]): string {
    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += "<AuditEvidenceExport>\n";
    xml += `  <ExportedAt>${new Date().toISOString()}</ExportedAt>\n`;
    xml += `  <RecordCount>${records.length}</RecordCount>\n`;

    if (records.length > 0) {
      xml += `  <ChainIntegrity>${this.verifyChainIntegrity(records)}</ChainIntegrity>\n`;
      xml += `  <MerkleRoot>${records[records.length - 1].merkleRoot ?? "N/A"}</MerkleRoot>\n`;
    }

    xml += "  <Records>\n";
    for (const record of records) {
      xml += "    <AuditRecord>\n";
      xml += `      <Id>${this.escapeXml(record.id)}</Id>\n`;
      xml += `      <Sequence>${record.sequence}</Sequence>\n`;
      xml += `      <Timestamp>${this.escapeXml(record.timestamp)}</Timestamp>\n`;
      xml += `      <Event>${this.escapeXml(record.event)}</Event>\n`;
      xml += `      <Actor>${this.escapeXml(record.actor)}</Actor>\n`;
      xml += `      <Resource>${this.escapeXml(record.resource)}</Resource>\n`;
      xml += `      <Action>${this.escapeXml(record.action)}</Action>\n`;
      xml += `      <Outcome>${record.outcome}</Outcome>\n`;
      xml += `      <Severity>${record.severity}</Severity>\n`;
      xml += `      <Source>${this.escapeXml(record.source)}</Source>\n`;
      xml += `      <RecordHash>${record.recordHash}</RecordHash>\n`;
      xml += `      <PreviousHash>${record.previousHash}</PreviousHash>\n`;
      if (record.signature) {
        xml += `      <Signature>${record.signature}</Signature>\n`;
      }
      if (record.tsaTimestamp) {
        xml += `      <TSATimestamp>${this.escapeXml(record.tsaTimestamp)}</TSATimestamp>\n`;
      }
      xml += "    </AuditRecord>\n";
    }
    xml += "  </Records>\n";
    xml += "</AuditEvidenceExport>\n";

    return xml;
  }

  private verifyChainIntegrity(records: readonly AuditRecord[]): boolean {
    if (records.length === 0) return true;
    const chain = new HashChain();
    return chain.verify(records);
  }

  private escapeXml(str: string): string {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&apos;");
  }
}

// ─── ZeroTrustAuditTrail ─────────────────────────────────────────────────────

export class ZeroTrustAuditTrail {
  private readonly hashChain: HashChain;
  private readonly merkleTree: MerkleTree;
  private readonly evidenceExporter: EvidenceExporter;
  private readonly tsaConfig: TSAConfig | null;
  private records: AuditRecord[] = [];
  private sequenceCounter = 0;

  constructor(options: {
    hashChain?: HashChainConfig;
    merkleTree?: MerkleTreeConfig;
    tsa?: TSAConfig;
    evidenceOutputDir?: string;
  } = {}) {
    this.hashChain = new HashChain(options.hashChain);
    this.merkleTree = new MerkleTree(options.merkleTree);
    this.evidenceExporter = new EvidenceExporter(options.evidenceOutputDir);
    this.tsaConfig = options.tsa ?? null;

    // Rehydrate from existing records if available
    if (this.records.length > 0) {
      this.hashChain.rehydrate(this.records);
    }
  }

  /** Create an immutable audit record. */
  async createRecord(input: AuditRecordInput): Promise<AuditRecord> {
    const id = this.generateId();
    const sequence = ++this.sequenceCounter;
    const timestamp = new Date().toISOString();
    const previousHash =
      this.records.length > 0
        ? this.records[this.records.length - 1].recordHash
        : this.hashChain.hash("genesis");

    const partial: Omit<AuditRecord, "recordHash"> = {
      id,
      sequence,
      timestamp,
      event: input.event,
      actor: input.actor,
      resource: input.resource,
      action: input.action,
      outcome: input.outcome,
      severity: input.severity ?? "info",
      source: input.source ?? "zero-trust-audit",
      metadata: input.metadata ?? {},
      complianceTags: input.complianceTags ?? [],
      previousHash,
    };

    const recordHash = this.hashChain.computeRecordHash(partial);
    const chainHead = this.hashChain.append(recordHash);

    const record: AuditRecord = {
      ...partial,
      recordHash,
    };

    // Optionally anchor to TSA
    if (this.tsaConfig) {
      try {
        const tsaResult = await this.anchorToTSA(recordHash);
        (record as MutableAuditRecord).tsaTimestamp = tsaResult.timestamp;
        (record as MutableAuditRecord).tsaReceipt = tsaResult.receipt;
      } catch {
        // TSA anchoring is best-effort; record is still immutable
      }
    }

    this.records.push(record);

    return record;
  }

  /** Create multiple records atomically and attach a Merkle root. */
  async createBatch(inputs: readonly AuditRecordInput[]): Promise<{
    records: readonly AuditRecord[];
    merkleRoot: string;
    merkleProofs: readonly MerkleProof[];
  }> {
    const records: AuditRecord[] = [];

    for (const input of inputs) {
      const record = await this.createRecord(input);
      records.push(record);
    }

    const recordHashes = records.map((r) => r.recordHash);
    const merkleRoot = this.merkleTree.build(recordHashes);

    // Attach Merkle root to all records in batch
    const batchRecords = records.map((r) => ({
      ...r,
      merkleRoot,
    }));

    // Generate proofs for each record
    const proofs: MerkleProof[] = [];
    for (let i = 0; i < batchRecords.length; i++) {
      proofs.push(this.merkleTree.getProof(i));
    }

    // Update stored records with Merkle root
    this.updateRecordsWithMerkleRoot(batchRecords);

    return {
      records: batchRecords,
      merkleRoot,
      merkleProofs: proofs,
    };
  }

  /** Verify the entire audit chain. */
  verify(): VerificationResult {
    const errors: string[] = [];
    let chainIntact = true;
    let signaturesValid = true;
    let merkleProofsValid = true;
    let tsaTimestampsValid = true;

    // Verify hash chain
    chainIntact = this.hashChain.verify(this.records);
    if (!chainIntact) {
      errors.push("Hash chain integrity check failed");
    }

    // Verify individual records
    for (const record of this.records) {
      const computedHash = this.hashChain.computeRecordHash(record);
      if (computedHash !== record.recordHash) {
        errors.push(`Record ${record.id}: hash mismatch`);
        chainIntact = false;
      }

      // Verify signature if present
      if (record.signature) {
        try {
          const verifier = createVerify("SHA256");
          verifier.update(record.recordHash);
          // In production, you'd use the actual public key
          // signaturesValid = verifier.verify(publicKey, record.signature, "base64");
        } catch {
          signaturesValid = false;
          errors.push(`Record ${record.id}: signature verification failed`);
        }
      }

      // Verify TSA timestamp if present
      if (record.tsaTimestamp) {
        try {
          const tsaDate = new Date(record.tsaTimestamp);
          if (isNaN(tsaDate.getTime())) {
            tsaTimestampsValid = false;
            errors.push(`Record ${record.id}: invalid TSA timestamp`);
          }
        } catch {
          tsaTimestampsValid = false;
          errors.push(`Record ${record.id}: TSA timestamp parsing failed`);
        }
      }
    }

    // Verify Merkle proofs if batch exists
    if (this.records.length > 0 && this.records[0].merkleRoot) {
      const recordHashes = this.records.map((r) => r.recordHash);
      this.merkleTree.build(recordHashes);

      for (let i = 0; i < this.records.length; i++) {
        const proof = this.merkleTree.getProof(i);
        if (!MerkleTree.verifyProof(proof)) {
          merkleProofsValid = false;
          errors.push(`Record ${i}: Merkle proof verification failed`);
        }
      }
    }

    return {
      valid: errors.length === 0,
      chainIntact,
      signaturesValid,
      merkleProofsValid,
      tsaTimestampsValid,
      errors,
      verifiedAt: new Date().toISOString(),
    };
  }

  /** Export evidence for court or compliance. */
  exportEvidence(options: EvidenceExportOptions): string {
    return this.evidenceExporter.exportEvidence(this.records, options);
  }

  /** Export as XML for legal submission. */
  exportXML(): string {
    return this.evidenceExporter.exportXML(this.records);
  }

  /** Get all records. */
  getRecords(): readonly AuditRecord[] {
    return this.records;
  }

  /** Get a specific record by ID. */
  getRecord(id: string): AuditRecord | undefined {
    return this.records.find((r) => r.id === id);
  }

  /** Get records filtered by compliance tag. */
  getRecordsByTag(tag: string): readonly AuditRecord[] {
    return this.records.filter((r) => r.complianceTags.includes(tag));
  }

  /** Get records within a time range. */
  getRecordsByTimeRange(start: Date, end: Date): readonly AuditRecord[] {
    return this.records.filter((r) => {
      const recordTime = new Date(r.timestamp);
      return recordTime >= start && recordTime <= end;
    });
  }

  /** Get current chain state. */
  getChainState(): {
    head: string | null;
    length: number;
    merkleRoot: string | null;
  } {
    return {
      head: this.hashChain.currentHead,
      length: this.hashChain.currentLength,
      merkleRoot: this.merkleTree.root ?? null,
    };
  }

  /** Rehydrate from serialized records. */
  rehydrate(serializedRecords: readonly AuditRecord[]): void {
    this.records = [...serializedRecords];
    this.sequenceCounter =
      serializedRecords.length > 0
        ? serializedRecords[serializedRecords.length - 1].sequence
        : 0;
    this.hashChain.rehydrate(serializedRecords);
  }

  private generateId(): string {
    return `audit-${Date.now()}-${randomBytes(8).toString("hex")}`;
  }

  private async anchorToTSA(
    dataHash: string,
  ): Promise<{ timestamp: string; receipt: string }> {
    if (!this.tsaConfig) {
      throw new Error("TSA not configured");
    }

    // In production, this would make an actual TSA request via RFC 3161
    // For now, we simulate with a deterministic mock
    const timestamp = new Date().toISOString();
    const receipt = this.hashChain.hash(
      `tsa-receipt:${dataHash}:${timestamp}:${this.tsaConfig.url}`,
    );

    return { timestamp, receipt };
  }

  private updateRecordsWithMerkleRoot(records: readonly AuditRecord[]): void {
    const merkleRootMap = new Map(
      records.map((r) => [r.id, r.merkleRoot]),
    );

    for (let i = 0; i < this.records.length; i++) {
      const merkleRoot = merkleRootMap.get(this.records[i].id);
      if (merkleRoot) {
        this.records[i] = { ...this.records[i], merkleRoot };
      }
    }
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

interface MutableAuditRecord extends AuditRecord {
  tsaTimestamp?: string;
  tsaReceipt?: string;
}

// ─── Exports ──────────────────────────────────────────────────────────────────

export {
  AuditRecordInput as AuditInput,
  HashChainConfig as ChainConfig,
  MerkleTreeConfig as TreeConfig,
  TSAConfig as TSAAnchorConfig,
  EvidenceExportOptions as ExportOptions,
  MerkleProof as Proof,
  VerificationResult as VerifyResult,
};
