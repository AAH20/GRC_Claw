import { createHash } from "node:crypto";

export interface MerkleProof {
  root: string;
  leaf: string;
  leafIndex: number;
  path: string[];
  pathIndices: number[];
}

export class MerkleTree {
  private leaves: string[];
  private layers: string[][];

  constructor(leaves: string[]) {
    if (leaves.length === 0) throw new Error("MerkleTree requires at least one leaf");
    this.leaves = leaves.map((l) => this.hash(l));
    this.layers = [this.leaves];
    this.build();
  }

  private hash(data: string): string {
    return createHash("sha256").update(data).digest("hex");
  }

  private hashPair(left: string, right: string): string {
    const sorted = left < right ? left + right : right + left;
    return this.hash(sorted);
  }

  private build(): void {
    let current = this.leaves;
    while (current.length > 1) {
      const next: string[] = [];
      for (let i = 0; i < current.length; i += 2) {
        const left = current[i];
        const right = i + 1 < current.length ? current[i + 1] : left;
        next.push(this.hashPair(left, right));
      }
      this.layers.push(next);
      current = next;
    }
  }

  get root(): string {
    return this.layers[this.layers.length - 1][0];
  }

  getProof(leafIndex: number): MerkleProof {
    if (leafIndex < 0 || leafIndex >= this.leaves.length) {
      throw new Error(`Leaf index ${leafIndex} out of range`);
    }
    const path: string[] = [];
    const pathIndices: number[] = [];
    let idx = leafIndex;
    for (let i = 0; i < this.layers.length - 1; i++) {
      const layer = this.layers[i];
      const isRight = idx % 2 === 1;
      const siblingIdx = isRight ? idx - 1 : idx + 1;
      const sibling = siblingIdx < layer.length ? layer[siblingIdx] : layer[idx];
      path.push(sibling);
      pathIndices.push(isRight ? 0 : 1);
      idx = Math.floor(idx / 2);
    }
    return { root: this.root, leaf: this.leaves[leafIndex], leafIndex, path, pathIndices };
  }

  static verify(proof: MerkleProof): boolean {
    const hash = (a: string, b: string): string => {
      const sorted = a < b ? a + b : b + a;
      return createHash("sha256").update(sorted).digest("hex");
    };
    let current = proof.leaf;
    for (let i = 0; i < proof.path.length; i++) {
      const sibling = proof.path[i];
      current = proof.pathIndices[i] === 1 ? hash(current, sibling) : hash(sibling, current);
    }
    return current === proof.root;
  }
}
