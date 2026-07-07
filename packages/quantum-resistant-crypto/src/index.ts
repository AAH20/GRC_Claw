import { createHash, createHmac, randomBytes, scryptSync, generateKeyPairSync, sign as nodeSign, verify as nodeVerify, KeyObject } from 'node:crypto';
import { ml_kem512, ml_kem768, ml_kem1024 } from '@noble/post-quantum/ml-kem.js';
import { ml_dsa44, ml_dsa65, ml_dsa87 } from '@noble/post-quantum/ml-dsa.js';
import { ml_kem768_x25519 } from '@noble/post-quantum/hybrid.js';

// ─── Types ───────────────────────────────────────────────────────────────────

/** ML-KEM (CRYSTALS-Kyber) key encapsulation mechanism key pair, FIPS 203 */
export interface KyberKeyPair {
  publicKey: Uint8Array;
  privateKey: Uint8Array;
  securityLevel: KyberSecurityLevel;
}

/** Result of ML-KEM key encapsulation */
export interface KyberEncapsulation {
  ciphertext: Uint8Array;
  sharedSecret: Uint8Array;
}

/** ML-DSA (CRYSTALS-Dilithium) digital signature key pair, FIPS 204 */
export interface DilithiumKeyPair {
  publicKey: Uint8Array;
  privateKey: Uint8Array;
  securityLevel: DilithiumSecurityLevel;
}

/** ML-DSA signature output */
export interface DilithiumSignatureData {
  signature: Uint8Array;
  algorithm: string;
  securityLevel: DilithiumSecurityLevel;
}

/** Combined hybrid encapsulation (X25519 classical + ML-KEM-768 post-quantum, CG/XWing framework) */
export interface HybridEncapsulation {
  ciphertext: Uint8Array;
  sharedSecret: Uint8Array;
}

/** Combined hybrid signature (Ed25519 classical + ML-DSA post-quantum). Valid only if BOTH verify. */
export interface HybridSignature {
  classicalSignature: Uint8Array;
  postQuantumSignature: DilithiumSignatureData;
  messageHash: Uint8Array;
  timestamp: number;
}

/** Hybrid key material: one Ed25519 pair (classical) + one ML-KEM-768/X25519 pair (post-quantum) */
export interface HybridKeyMaterial {
  classical: { publicKey: KeyObject; privateKey: KeyObject };
  postQuantum: KyberKeyPair;
}

/** Quantum-resistant hash function result */
export interface QuantumHashResult {
  digest: Uint8Array;
  algorithm: string;
  length: number;
}

/** Encryption result containing ciphertext and required metadata */
export interface EncryptionResult {
  ciphertext: Uint8Array;
  nonce: Uint8Array;
  tag: Uint8Array;
  algorithm: string;
}

/** Configuration for quantum-resistant crypto operations */
export interface CryptoConfig {
  /** ML-KEM security level: 1 (ML-KEM-512), 3 (ML-KEM-768), 5 (ML-KEM-1024) */
  kyberSecurityLevel: KyberSecurityLevel;
  /** ML-DSA security level: 2 (ML-DSA-44), 3 (ML-DSA-65), 5 (ML-DSA-87) */
  dilithiumSecurityLevel: DilithiumSecurityLevel;
  /** Enable hybrid classical + post-quantum mode */
  hybridMode: boolean;
  /** Hash algorithm for quantum-resistant hashing */
  hashAlgorithm: 'sha3-256' | 'sha3-512' | 'shake256';
  /** Key derivation iterations for scrypt */
  kdfIterations: number;
}

export type KyberSecurityLevel = 1 | 3 | 5;
export type DilithiumSecurityLevel = 2 | 3 | 5;

const DEFAULT_CONFIG: CryptoConfig = {
  kyberSecurityLevel: 3,
  dilithiumSecurityLevel: 3,
  hybridMode: true,
  hashAlgorithm: 'sha3-256',
  kdfIterations: 16384,
};

// ─── Errors ──────────────────────────────────────────────────────────────────

export class QuantumCryptoError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly operation: string,
  ) {
    super(`[QuantumCrypto:${operation}] ${message}`);
    this.name = 'QuantumCryptoError';
  }
}

export class InvalidKeyError extends QuantumCryptoError {
  constructor(operation: string, detail: string) {
    super(`Invalid key: ${detail}`, 'INVALID_KEY', operation);
    this.name = 'InvalidKeyError';
  }
}

export class VerificationError extends QuantumCryptoError {
  constructor(operation: string, detail: string) {
    super(`Verification failed: ${detail}`, 'VERIFICATION_FAILED', operation);
    this.name = 'VerificationError';
  }
}

export class DecapsulationError extends QuantumCryptoError {
  constructor(operation: string, detail: string) {
    super(`Decapsulation failed: ${detail}`, 'DECAPSULATION_FAILED', operation);
    this.name = 'DecapsulationError';
  }
}

// ─── ML-KEM (Kyber) ────────────────────────────────────────────────────────────

/** Real FIPS 203 ML-KEM byte sizes, per NIST specification (not derived, these are the standard's fixed sizes). */
const KYBER_SIZES: Record<KyberSecurityLevel, { publicKey: number; privateKey: number; ciphertext: number; sharedSecret: number }> = {
  1: { publicKey: 800, privateKey: 1632, ciphertext: 768, sharedSecret: 32 },
  3: { publicKey: 1184, privateKey: 2400, ciphertext: 1088, sharedSecret: 32 },
  5: { publicKey: 1568, privateKey: 3168, ciphertext: 1568, sharedSecret: 32 },
};

function kyberAlgo(level: KyberSecurityLevel) {
  if (level === 1) return ml_kem512;
  if (level === 5) return ml_kem1024;
  return ml_kem768;
}

/**
 * ML-KEM (CRYSTALS-Kyber), FIPS 203, real NIST-standardized key encapsulation,
 * via the audited `@noble/post-quantum` implementation (not a custom scheme).
 *
 * @example
 * ```typescript
 * const kyber = new KyberKEM(3);
 * const keyPair = await kyber.generateKeyPair();
 * const { ciphertext, sharedSecret } = await kyber.encapsulate(keyPair.publicKey);
 * const decrypted = await kyber.decapsulate(ciphertext, keyPair.privateKey);
 * ```
 */
export class KyberKEM {
  private readonly securityLevel: KyberSecurityLevel;
  private readonly algo: typeof ml_kem768;

  constructor(securityLevel: KyberSecurityLevel = 3) {
    this.validateSecurityLevel(securityLevel);
    this.securityLevel = securityLevel;
    this.algo = kyberAlgo(securityLevel);
  }

  private validateSecurityLevel(level: number): asserts level is KyberSecurityLevel {
    if (level !== 1 && level !== 3 && level !== 5) {
      throw new QuantumCryptoError(
        `Invalid Kyber security level: ${level}. Must be 1, 3, or 5.`,
        'INVALID_SECURITY_LEVEL',
        'KyberKEM',
      );
    }
  }

  /** Returns real FIPS 203 byte sizes for the configured security level. */
  sizes(): { publicKey: number; privateKey: number; ciphertext: number; sharedSecret: number } {
    return KYBER_SIZES[this.securityLevel];
  }

  /** Generate a new ML-KEM key pair. */
  async generateKeyPair(): Promise<KyberKeyPair> {
    const keys = this.algo.keygen();
    return { publicKey: keys.publicKey, privateKey: keys.secretKey, securityLevel: this.securityLevel };
  }

  /**
   * Encapsulate a shared secret using the recipient's public key.
   * @throws {InvalidKeyError} If public key size is incorrect.
   */
  async encapsulate(publicKey: Uint8Array): Promise<KyberEncapsulation> {
    this.validateKey(publicKey, this.sizes().publicKey, 'public', 'encapsulate');
    const { cipherText, sharedSecret } = this.algo.encapsulate(publicKey);
    return { ciphertext: cipherText, sharedSecret };
  }

  /**
   * Decapsulate to recover the shared secret from ciphertext.
   * @throws {InvalidKeyError} If key or ciphertext sizes are incorrect.
   * @throws {DecapsulationError} If decapsulation fails.
   */
  async decapsulate(ciphertext: Uint8Array, privateKey: Uint8Array): Promise<Uint8Array> {
    this.validateKey(privateKey, this.sizes().privateKey, 'private', 'decapsulate');
    this.validateKey(ciphertext, this.sizes().ciphertext, 'ciphertext', 'decapsulate');
    try {
      return this.algo.decapsulate(ciphertext, privateKey);
    } catch (e: any) {
      throw new DecapsulationError('decapsulate', e?.message ?? 'unknown error');
    }
  }

  /** Encrypt data using an ML-KEM-derived shared secret with AES-256-GCM. */
  async encrypt(
    plaintext: Uint8Array,
    recipientPublicKey: Uint8Array,
  ): Promise<{ encapsulation: KyberEncapsulation; encrypted: EncryptionResult }> {
    const encapsulation = await this.encapsulate(recipientPublicKey);
    const nonce = randomBytes(12);
    const { createCipheriv } = await import('node:crypto');
    const cipher = createCipheriv('aes-256-gcm', encapsulation.sharedSecret, nonce);
    const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final()]);
    const tag = cipher.getAuthTag();
    return {
      encapsulation,
      encrypted: { ciphertext: new Uint8Array(encrypted), nonce, tag: new Uint8Array(tag), algorithm: 'aes-256-gcm' },
    };
  }

  /** Decrypt data using an ML-KEM private key. */
  async decrypt(
    encapsulation: KyberEncapsulation,
    encrypted: EncryptionResult,
    privateKey: Uint8Array,
  ): Promise<Uint8Array> {
    const sharedSecret = await this.decapsulate(encapsulation.ciphertext, privateKey);
    const { createDecipheriv } = await import('node:crypto');
    const decipher = createDecipheriv('aes-256-gcm', sharedSecret, encrypted.nonce);
    decipher.setAuthTag(Buffer.from(encrypted.tag));
    const decrypted = Buffer.concat([decipher.update(Buffer.from(encrypted.ciphertext)), decipher.final()]);
    return new Uint8Array(decrypted);
  }

  private validateKey(key: Uint8Array, expectedSize: number, keyType: string, operation: string): void {
    if (!(key instanceof Uint8Array)) {
      throw new InvalidKeyError(operation, `${keyType} must be a Uint8Array`);
    }
    if (key.length !== expectedSize) {
      throw new InvalidKeyError(operation, `${keyType} must be ${expectedSize} bytes, got ${key.length}`);
    }
  }
}

// ─── ML-DSA (Dilithium) Signature ──────────────────────────────────────────────

/** Real FIPS 204 ML-DSA byte sizes, per NIST specification. */
const DILITHIUM_SIZES: Record<DilithiumSecurityLevel, { publicKey: number; privateKey: number; signature: number }> = {
  2: { publicKey: 1312, privateKey: 2560, signature: 2420 },
  3: { publicKey: 1952, privateKey: 4032, signature: 3309 },
  5: { publicKey: 2592, privateKey: 4896, signature: 4627 },
};

function dilithiumAlgo(level: DilithiumSecurityLevel) {
  if (level === 2) return ml_dsa44;
  if (level === 5) return ml_dsa87;
  return ml_dsa65;
}

function dilithiumAlgoName(level: DilithiumSecurityLevel): string {
  if (level === 2) return 'ml-dsa-44';
  if (level === 5) return 'ml-dsa-87';
  return 'ml-dsa-65';
}

/**
 * ML-DSA (CRYSTALS-Dilithium), FIPS 204, real NIST-standardized digital signatures,
 * via the audited `@noble/post-quantum` implementation (not a custom scheme).
 *
 * @example
 * ```typescript
 * const dilithium = new DilithiumSignature(3);
 * const keyPair = await dilithium.generateKeyPair();
 * const signature = await dilithium.sign(message, keyPair.privateKey);
 * const valid = await dilithium.verify(signature, message, keyPair.publicKey);
 * ```
 */
export class DilithiumSignature {
  private readonly securityLevel: DilithiumSecurityLevel;
  private readonly algo: typeof ml_dsa65;

  constructor(securityLevel: DilithiumSecurityLevel = 3) {
    this.validateSecurityLevel(securityLevel);
    this.securityLevel = securityLevel;
    this.algo = dilithiumAlgo(securityLevel);
  }

  private validateSecurityLevel(level: number): asserts level is DilithiumSecurityLevel {
    if (level !== 2 && level !== 3 && level !== 5) {
      throw new QuantumCryptoError(
        `Invalid Dilithium security level: ${level}. Must be 2, 3, or 5.`,
        'INVALID_SECURITY_LEVEL',
        'DilithiumSignature',
      );
    }
  }

  /** Returns real FIPS 204 byte sizes for the configured security level. */
  sizes(): { publicKey: number; privateKey: number; signature: number } {
    return DILITHIUM_SIZES[this.securityLevel];
  }

  /** Generate a new ML-DSA key pair. */
  async generateKeyPair(): Promise<DilithiumKeyPair> {
    const keys = this.algo.keygen();
    return { publicKey: keys.publicKey, privateKey: keys.secretKey, securityLevel: this.securityLevel };
  }

  /**
   * Sign a message using the ML-DSA private key.
   * @throws {InvalidKeyError} If private key size is incorrect.
   */
  async sign(message: Uint8Array, privateKey: Uint8Array): Promise<DilithiumSignatureData> {
    this.validateKey(privateKey, this.sizes().privateKey, 'private', 'sign');
    const signature = this.algo.sign(message, privateKey);
    return { signature, algorithm: dilithiumAlgoName(this.securityLevel), securityLevel: this.securityLevel };
  }

  /**
   * Verify an ML-DSA signature.
   * @throws {VerificationError} If signature is invalid.
   * @throws {InvalidKeyError} If public key size is incorrect.
   */
  async verify(signatureData: DilithiumSignatureData, message: Uint8Array, publicKey: Uint8Array): Promise<boolean> {
    this.validateKey(publicKey, this.sizes().publicKey, 'public', 'verify');
    const isValid = this.algo.verify(signatureData.signature, message, publicKey);
    if (!isValid) {
      throw new VerificationError('verify', 'Signature does not match');
    }
    return true;
  }

  private validateKey(key: Uint8Array, expectedSize: number, keyType: string, operation: string): void {
    if (!(key instanceof Uint8Array)) {
      throw new InvalidKeyError(operation, `${keyType} must be a Uint8Array`);
    }
    if (key.length !== expectedSize) {
      throw new InvalidKeyError(operation, `${keyType} must be ${expectedSize} bytes, got ${key.length}`);
    }
  }
}

// ─── Hybrid Mode ──────────────────────────────────────────────────────────────

/**
 * Hybrid classical + post-quantum cryptographic mode.
 *
 * KEM: X25519 (classical) + ML-KEM-768 (post-quantum) via the CG/XWing framework
 * (`@noble/post-quantum/hybrid.js`), a real standards-track hybrid construction,
 * secure as long as either component remains unbroken.
 *
 * Signatures: composite Ed25519 (classical, via Node's native crypto) + ML-DSA
 * (post-quantum). A hybrid signature is valid only if BOTH components verify,
 * so an attacker must break both algorithms, not just one.
 *
 * @example
 * ```typescript
 * const hybrid = new HybridMode({ hybridMode: true });
 * const keys = await hybrid.generateKeyPair();
 * const encapsulation = await hybrid.encapsulate(keys.postQuantum.publicKey);
 * const signature = await hybrid.sign(data, keys);
 * ```
 */
export class HybridMode {
  private readonly dilithium: DilithiumSignature;
  private readonly config: CryptoConfig;

  constructor(config: Partial<CryptoConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.dilithium = new DilithiumSignature(this.config.dilithiumSecurityLevel);
  }

  /** Generate an Ed25519 classical pair and an ML-DSA post-quantum pair for hybrid signing. */
  async generateKeyPair(): Promise<{ classical: { publicKey: KeyObject; privateKey: KeyObject }; postQuantum: DilithiumKeyPair }> {
    const { publicKey, privateKey } = generateKeyPairSync('ed25519');
    const postQuantum = await this.dilithium.generateKeyPair();
    return { classical: { publicKey, privateKey }, postQuantum };
  }

  /** Hybrid key encapsulation: X25519 + ML-KEM-768 (CG/XWing framework, real construction). */
  async encapsulate(publicKey: Uint8Array): Promise<HybridEncapsulation> {
    const { cipherText, sharedSecret } = ml_kem768_x25519.encapsulate(publicKey);
    return { ciphertext: cipherText, sharedSecret };
  }

  /** Hybrid decapsulation: X25519 + ML-KEM-768. */
  async decapsulate(ciphertext: Uint8Array, privateKey: Uint8Array): Promise<Uint8Array> {
    return ml_kem768_x25519.decapsulate(ciphertext, privateKey);
  }

  /** Generate an X25519 + ML-KEM-768 hybrid KEM key pair. */
  generateHybridKemKeyPair(): { publicKey: Uint8Array; privateKey: Uint8Array } {
    const keys = ml_kem768_x25519.keygen();
    return { publicKey: keys.publicKey, privateKey: keys.secretKey };
  }

  /**
   * Hybrid digital signature: sign with Ed25519 (classical) AND ML-DSA (post-quantum).
   * Verification requires both to pass.
   */
  async sign(
    message: Uint8Array,
    keys: { classical: { privateKey: KeyObject }; postQuantum: DilithiumKeyPair },
  ): Promise<HybridSignature> {
    const messageHash = new Uint8Array(createHash('sha3-256').update(message).digest());
    const classicalSignature = new Uint8Array(nodeSign(null, Buffer.from(messageHash), keys.classical.privateKey));
    const postQuantumSignature = await this.dilithium.sign(messageHash, keys.postQuantum.privateKey);
    return { classicalSignature, postQuantumSignature, messageHash, timestamp: Date.now() };
  }

  /**
   * Verify a hybrid digital signature. Valid only if BOTH the classical and
   * post-quantum components verify against the message hash.
   * @throws {VerificationError} If either component fails.
   */
  async verify(
    signature: HybridSignature,
    keys: { classical: { publicKey: KeyObject }; postQuantum: { publicKey: Uint8Array } },
  ): Promise<boolean> {
    const classicalValid = nodeVerify(
      null,
      Buffer.from(signature.messageHash),
      keys.classical.publicKey,
      Buffer.from(signature.classicalSignature),
    );

    let pqValid = false;
    try {
      pqValid = await this.dilithium.verify(signature.postQuantumSignature, signature.messageHash, keys.postQuantum.publicKey);
    } catch {
      pqValid = false;
    }

    if (!classicalValid || !pqValid) {
      throw new VerificationError('HybridMode.verify', 'One or more signature components are invalid');
    }
    return true;
  }

  /** Encrypt data using the hybrid X25519 + ML-KEM-768 shared secret with AES-256-GCM. */
  async encrypt(
    plaintext: Uint8Array,
    hybridPublicKey: Uint8Array,
  ): Promise<{ encapsulation: HybridEncapsulation; encrypted: EncryptionResult }> {
    const encapsulation = await this.encapsulate(hybridPublicKey);
    const nonce = randomBytes(12);
    const { createCipheriv } = await import('node:crypto');
    const cipher = createCipheriv('aes-256-gcm', encapsulation.sharedSecret, nonce);
    const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final()]);
    const tag = cipher.getAuthTag();
    return {
      encapsulation,
      encrypted: { ciphertext: new Uint8Array(encrypted), nonce, tag: new Uint8Array(tag), algorithm: 'aes-256-gcm' },
    };
  }

  /** Decrypt hybrid-encrypted data. */
  async decrypt(
    encapsulation: HybridEncapsulation,
    encrypted: EncryptionResult,
    hybridPrivateKey: Uint8Array,
  ): Promise<Uint8Array> {
    const sharedSecret = await this.decapsulate(encapsulation.ciphertext, hybridPrivateKey);
    const { createDecipheriv } = await import('node:crypto');
    const decipher = createDecipheriv('aes-256-gcm', sharedSecret, encrypted.nonce);
    decipher.setAuthTag(Buffer.from(encrypted.tag));
    const decrypted = Buffer.concat([decipher.update(Buffer.from(encrypted.ciphertext)), decipher.final()]);
    return new Uint8Array(decrypted);
  }
}

// ─── Quantum Hash ─────────────────────────────────────────────────────────────

/**
 * Quantum-resistant hash functions.
 *
 * Provides SHA-3 and SHAKE-based hashing that remains secure against quantum
 * attacks (Grover's algorithm gives only a quadratic speedup on hash preimage
 * search, so doubling output length restores the original security margin).
 * This part of the original implementation was already sound; unchanged here.
 */
export class QuantumHash {
  private readonly config: CryptoConfig;

  constructor(config: Partial<CryptoConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  async digest(data: Uint8Array): Promise<QuantumHashResult> {
    if (!(data instanceof Uint8Array)) {
      throw new QuantumCryptoError('Data must be a Uint8Array', 'INVALID_INPUT', 'QuantumHash.digest');
    }
    const hash = createHash(this.config.hashAlgorithm);
    hash.update(data);
    const digest = hash.digest();
    return { digest: new Uint8Array(digest), algorithm: this.config.hashAlgorithm, length: digest.length };
  }

  async hmac(key: Uint8Array, data: Uint8Array): Promise<QuantumHashResult> {
    if (!(key instanceof Uint8Array) || !(data instanceof Uint8Array)) {
      throw new QuantumCryptoError('Key and data must be Uint8Arrays', 'INVALID_INPUT', 'QuantumHash.hmac');
    }
    const algorithm = this.config.hashAlgorithm === 'shake256' ? 'sha3-256' : this.config.hashAlgorithm;
    const hmacResult = createHmac(algorithm, key);
    hmacResult.update(data);
    const digest = hmacResult.digest();
    return { digest: new Uint8Array(digest), algorithm: `hmac-${algorithm}`, length: digest.length };
  }

  async deriveKey(password: Uint8Array, salt: Uint8Array, keyLength: number = 32): Promise<Uint8Array> {
    if (!(password instanceof Uint8Array) || !(salt instanceof Uint8Array)) {
      throw new QuantumCryptoError('Password and salt must be Uint8Arrays', 'INVALID_INPUT', 'QuantumHash.deriveKey');
    }
    const derived = scryptSync(Buffer.from(password), Buffer.from(salt), keyLength, {
      N: this.config.kdfIterations, r: 8, p: 1, maxmem: 256 * 1024 * 1024,
    });
    return new Uint8Array(derived);
  }

  async chain(data: Uint8Array, rounds: number = 1000): Promise<QuantumHashResult> {
    if (rounds < 1) {
      throw new QuantumCryptoError('Rounds must be >= 1', 'INVALID_INPUT', 'QuantumHash.chain');
    }
    let current = Buffer.from(data);
    for (let i = 0; i < rounds; i++) {
      const hash = createHash(this.config.hashAlgorithm);
      hash.update(current);
      current = hash.digest();
    }
    return { digest: new Uint8Array(current), algorithm: `${this.config.hashAlgorithm}:${rounds}`, length: current.length };
  }
}

// ─── Main Facade ──────────────────────────────────────────────────────────────

/**
 * Unified quantum-resistant cryptography facade over real, NIST-standardized
 * ML-KEM (FIPS 203) and ML-DSA (FIPS 204) implementations.
 */
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
    hybridKeyPair: { classical: { publicKey: KeyObject; privateKey: KeyObject }; postQuantum: DilithiumKeyPair };
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

  async sign(data: Uint8Array, privateKey: Uint8Array): Promise<DilithiumSignatureData> {
    return this.dilithium.sign(data, privateKey);
  }

  async verify(signature: DilithiumSignatureData, data: Uint8Array, publicKey: Uint8Array): Promise<boolean> {
    return this.dilithium.verify(signature, data, publicKey);
  }

  async digest(data: Uint8Array): Promise<QuantumHashResult> {
    return this.hash.digest(data);
  }

  async hmac(key: Uint8Array, data: Uint8Array): Promise<QuantumHashResult> {
    return this.hash.hmac(key, data);
  }

  async deriveKey(password: Uint8Array, salt: Uint8Array, keyLength?: number): Promise<Uint8Array> {
    return this.hash.deriveKey(password, salt, keyLength);
  }

  async kyberEncrypt(
    plaintext: Uint8Array,
    recipientPublicKey: Uint8Array,
  ): Promise<{ encapsulation: KyberEncapsulation; encrypted: EncryptionResult }> {
    return this.kyber.encrypt(plaintext, recipientPublicKey);
  }

  async kyberDecrypt(
    encapsulation: KyberEncapsulation,
    encrypted: EncryptionResult,
    privateKey: Uint8Array,
  ): Promise<Uint8Array> {
    return this.kyber.decrypt(encapsulation, encrypted, privateKey);
  }
}

// ─── Utility Functions ────────────────────────────────────────────────────────

export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('');
}

export function hexToBytes(hex: string): Uint8Array {
  if (hex.length % 2 !== 0) {
    throw new QuantumCryptoError('Hex string must have even length', 'INVALID_HEX', 'hexToBytes');
  }
  if (!/^[0-9a-fA-F]*$/.test(hex)) {
    throw new QuantumCryptoError('Hex string contains invalid characters', 'INVALID_HEX', 'hexToBytes');
  }
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16);
  }
  return bytes;
}

export function secureCompare(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a[i] ^ b[i];
  }
  return result === 0;
}

export function getAlgorithmInfo(
  kyberLevel: KyberSecurityLevel,
  dilithiumLevel: DilithiumSecurityLevel,
): {
  kyber: { name: string; nistLevel: number; classicalSecurityBits: number };
  dilithium: { name: string; nistLevel: number; classicalSecurityBits: number };
} {
  const kyberInfo: Record<KyberSecurityLevel, { name: string; nistLevel: number; classicalSecurityBits: number }> = {
    1: { name: 'ML-KEM-512', nistLevel: 1, classicalSecurityBits: 128 },
    3: { name: 'ML-KEM-768', nistLevel: 3, classicalSecurityBits: 192 },
    5: { name: 'ML-KEM-1024', nistLevel: 5, classicalSecurityBits: 256 },
  };
  const dilithiumInfo: Record<DilithiumSecurityLevel, { name: string; nistLevel: number; classicalSecurityBits: number }> = {
    2: { name: 'ML-DSA-44', nistLevel: 2, classicalSecurityBits: 128 },
    3: { name: 'ML-DSA-65', nistLevel: 3, classicalSecurityBits: 192 },
    5: { name: 'ML-DSA-87', nistLevel: 5, classicalSecurityBits: 256 },
  };
  return { kyber: kyberInfo[kyberLevel], dilithium: dilithiumInfo[dilithiumLevel] };
}
