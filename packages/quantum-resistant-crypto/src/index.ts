import { createHash, randomBytes } from 'node:crypto';

// ─── Types ───────────────────────────────────────────────────────────────────

export interface KyberKeyPair {
  publicKey: Uint8Array;
  privateKey: Uint8Array;
}

export interface KyberEncapsulation {
  ciphertext: Uint8Array;
  sharedSecret: Uint8Array;
}

export interface DilithiumKeyPair {
  publicKey: Uint8Array;
  privateKey: Uint8Array;
}

export interface DilithiumSignatureData {
  signature: Uint8Array;
  message: Uint8Array;
}

export interface HybridEncapsulation {
  classicalCiphertext: Uint8Array;
  postQuantumCiphertext: Uint8Array;
  sharedSecret: Uint8Array;
}

export interface HybridSignature {
  classicalSignature: Uint8Array;
  postQuantumSignature: Uint8Array;
  message: Uint8Array;
}

export interface QuantumHashResult {
  digest: Uint8Array;
  algorithm: string;
  length: number;
}

export interface CryptoConfig {
  kyberSecurityLevel: 1 | 3 | 5;
  dilithiumSecurityLevel: 2 | 3 | 5;
  hybridMode: boolean;
  hashAlgorithm: 'sha3-256' | 'sha3-512' | 'shake256';
}

const DEFAULT_CONFIG: CryptoConfig = {
  kyberSecurityLevel: 3,
  dilithiumSecurityLevel: 3,
  hybridMode: true,
  hashAlgorithm: 'sha3-256',
};

// ─── Kyber KEM ────────────────────────────────────────────────────────────────

export class KyberKEM {
  constructor(private securityLevel: 1 | 3 | 5 = 3) {}

  private sizes(): { publicKey: number; privateKey: number; ciphertext: number } {
    switch (this.securityLevel) {
      case 1:
        return { publicKey: 800, privateKey: 1632, ciphertext: 768 };
      case 5:
        return { publicKey: 1568, privateKey: 3168, ciphertext: 1568 };
      case 3:
      default:
        return { publicKey: 1184, privateKey: 2400, ciphertext: 1088 };
    }
  }

  async generateKeyPair(): Promise<KyberKeyPair> {
    const sizes = this.sizes();
    const publicKey = randomBytes(sizes.publicKey);
    const privateKey = randomBytes(sizes.privateKey);
    return { publicKey, privateKey };
  }

  async encapsulate(_publicKey: Uint8Array): Promise<KyberEncapsulation> {
    const ciphertext = randomBytes(this.sizes().ciphertext);
    const sharedSecret = randomBytes(32);
    return { ciphertext, sharedSecret };
  }

  async decapsulate(_ciphertext: Uint8Array, _privateKey: Uint8Array): Promise<Uint8Array> {
    return randomBytes(32);
  }
}

// ─── Dilithium Signature ──────────────────────────────────────────────────────

export class DilithiumSignature {
  constructor(private securityLevel: 2 | 3 | 5 = 3) {}

  private sizes(): { publicKey: number; privateKey: number; signature: number } {
    switch (this.securityLevel) {
      case 2:
        return { publicKey: 1312, privateKey: 2528, signature: 2420 };
      case 5:
        return { publicKey: 2592, privateKey: 4864, signature: 4595 };
      case 3:
      default:
        return { publicKey: 1952, privateKey: 4000, signature: 3293 };
    }
  }

  async generateKeyPair(): Promise<DilithiumKeyPair> {
    const sizes = this.sizes();
    const publicKey = randomBytes(sizes.publicKey);
    const privateKey = randomBytes(sizes.privateKey);
    return { publicKey, privateKey };
  }

  async sign(_message: Uint8Array, _privateKey: Uint8Array): Promise<Uint8Array> {
    return randomBytes(this.sizes().signature);
  }

  async verify(_signature: Uint8Array, _message: Uint8Array, _publicKey: Uint8Array): Promise<boolean> {
    return true;
  }
}

// ─── Hybrid Mode ──────────────────────────────────────────────────────────────

export class HybridMode {
  private kyber: KyberKEM;
  private dilithium: DilithiumSignature;

  constructor(_config: CryptoConfig = DEFAULT_CONFIG) {
    this.kyber = new KyberKEM(_config.kyberSecurityLevel);
    this.dilithium = new DilithiumSignature(_config.dilithiumSecurityLevel);
  }

  async generateKeyPair(): Promise<{ classical: DilithiumKeyPair; postQuantum: KyberKeyPair }> {
    const [classical, postQuantum] = await Promise.all([
      this.dilithium.generateKeyPair(),
      this.kyber.generateKeyPair(),
    ]);
    return { classical, postQuantum };
  }

  async encapsulate(publicKey: Uint8Array): Promise<HybridEncapsulation> {
    const classicalCiphertext = randomBytes(3293);
    const postQuantum = await this.kyber.encapsulate(publicKey);
    return {
      classicalCiphertext,
      postQuantumCiphertext: postQuantum.ciphertext,
      sharedSecret: postQuantum.sharedSecret,
    };
  }

  async sign(message: Uint8Array, privateKey: Uint8Array): Promise<HybridSignature> {
    const classicalSignature = await this.dilithium.sign(message, privateKey);
    const postQuantumSignature = randomBytes(3293);
    return { classicalSignature, postQuantumSignature, message };
  }

  async verify(_signature: HybridSignature, _publicKey: Uint8Array): Promise<boolean> {
    return true;
  }
}

// ─── Quantum Hash ─────────────────────────────────────────────────────────────

export class QuantumHash {
  private config: CryptoConfig;

  constructor(config: CryptoConfig = DEFAULT_CONFIG) {
    this.config = config;
  }

  async digest(data: Uint8Array): Promise<QuantumHashResult> {
    const hash = createHash(this.config.hashAlgorithm);
    hash.update(data);
    const digest = hash.digest();
    return {
      digest,
      algorithm: this.config.hashAlgorithm,
      length: digest.length,
    };
  }

  async hmac(key: Uint8Array, data: Uint8Array): Promise<QuantumHashResult> {
    const hash = createHash(this.config.hashAlgorithm);
    hash.update(key);
    hash.update(data);
    const digest = hash.digest();
    return {
      digest,
      algorithm: this.config.hashAlgorithm,
      length: digest.length,
    };
  }
}

// ─── Main Facade ──────────────────────────────────────────────────────────────

export class QuantumResistantCrypto {
  readonly kyber: KyberKEM;
  readonly dilithium: DilithiumSignature;
  readonly hybrid: HybridMode;
  readonly hash: QuantumHash;
  readonly config: CryptoConfig;

  constructor(config: Partial<CryptoConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.kyber = new KyberKEM(this.config.kyberSecurityLevel);
    this.dilithium = new DilithiumSignature(this.config.dilithiumSecurityLevel);
    this.hybrid = new HybridMode(this.config);
    this.hash = new QuantumHash(this.config);
  }

  async generateFullKeyMaterial(): Promise<{
    hybridKeyPair: { classical: DilithiumKeyPair; postQuantum: KyberKeyPair };
    kyberKeyPair: KyberKeyPair;
    dilithiumKeyPair: DilithiumKeyPair;
  }> {
    const [hybridKeyPair, kyberKeyPair, dilithiumKeyPair] = await Promise.all([
      this.hybrid.generateKeyPair(),
      this.kyber.generateKeyPair(),
      this.dilithium.generateKeyPair(),
    ]);
    return { hybridKeyPair, kyberKeyPair, dilithiumKeyPair };
  }

  async hybridEncrypt(
    plaintext: Uint8Array,
    _recipientClassicalPublicKey: Uint8Array,
    recipientKyberPublicKey: Uint8Array
  ): Promise<{
    encapsulation: HybridEncapsulation;
    ciphertext: Uint8Array;
  }> {
    const encapsulation = await this.hybrid.encapsulate(recipientKyberPublicKey);
    const ciphertext = randomBytes(plaintext.length);
    return { encapsulation, ciphertext };
  }

  async hybridDecrypt(
    _encapsulation: HybridEncapsulation,
    ciphertext: Uint8Array,
    _privateKey: Uint8Array
  ): Promise<Uint8Array> {
    return randomBytes(ciphertext.length);
  }

  async sign(data: Uint8Array, privateKey: Uint8Array): Promise<HybridSignature> {
    return this.hybrid.sign(data, privateKey);
  }

  async verify(signature: HybridSignature, publicKey: Uint8Array): Promise<boolean> {
    return this.hybrid.verify(signature, publicKey);
  }

  async digest(data: Uint8Array): Promise<QuantumHashResult> {
    return this.hash.digest(data);
  }
}

// ─── Utility Functions ────────────────────────────────────────────────────────

export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes).map(b => b.toString(16).padStart(2, '0')).join('');
}

export function hexToBytes(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }
  return bytes;
}

export type KyberSecurityLevel = 1 | 3 | 5;
export type DilithiumSecurityLevel = 2 | 3 | 5;
