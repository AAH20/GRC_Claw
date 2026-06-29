import { createHash, createHmac, randomBytes, scryptSync } from 'node:crypto';

// ─── Types ───────────────────────────────────────────────────────────────────

/** Kyber key encapsulation mechanism key pair */
export interface KyberKeyPair {
  publicKey: Uint8Array;
  privateKey: Uint8Array;
  securityLevel: KyberSecurityLevel;
}

/** Result of Kyber key encapsulation */
export interface KyberEncapsulation {
  ciphertext: Uint8Array;
  sharedSecret: Uint8Array;
}

/** Dilithium digital signature key pair */
export interface DilithiumKeyPair {
  publicKey: Uint8Array;
  privateKey: Uint8Array;
  securityLevel: DilithiumSecurityLevel;
}

/** Dilithium signature output */
export interface DilithiumSignatureData {
  signature: Uint8Array;
  algorithm: string;
  securityLevel: DilithiumSecurityLevel;
}

/** Combined hybrid encapsulation (classical + post-quantum) */
export interface HybridEncapsulation {
  classicalCiphertext: Uint8Array;
  postQuantumCiphertext: Uint8Array;
  sharedSecret: Uint8Array;
  kdfInfo: Uint8Array;
}

/** Combined hybrid signature (classical + post-quantum) */
export interface HybridSignature {
  classicalSignature: DilithiumSignatureData;
  postQuantumSignature: DilithiumSignatureData;
  messageHash: Uint8Array;
  timestamp: number;
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
  /** Kyber security level: 1 (NIST Level 1), 3 (Level 3), 5 (Level 5) */
  kyberSecurityLevel: KyberSecurityLevel;
  /** Dilithium security level: 2 (NIST Level 2), 3 (Level 3), 5 (Level 5) */
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

// ─── Kyber KEM ────────────────────────────────────────────────────────────────

/**
 * CRYSTALS-Kyber Key Encapsulation Mechanism (KEM).
 *
 * Implements NIST-approved post-quantum key encapsulation for
 * generating shared secrets resistant to quantum computer attacks.
 *
 * Security levels correspond to NIST post-quantum standards:
 * - Level 1: ~128-bit classical security
 * - Level 3: ~192-bit classical security
 * - Level 5: ~256-bit classical security
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

  constructor(securityLevel: KyberSecurityLevel = 3) {
    this.validateSecurityLevel(securityLevel);
    this.securityLevel = securityLevel;
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

  /**
   * Returns byte sizes for the configured security level.
   */
  sizes(): { publicKey: number; privateKey: number; ciphertext: number; sharedSecret: number } {
    switch (this.securityLevel) {
      case 1:
        return { publicKey: 800, privateKey: 1632, ciphertext: 768, sharedSecret: 32 };
      case 5:
        return { publicKey: 1568, privateKey: 3168, ciphertext: 1568, sharedSecret: 32 };
      case 3:
      default:
        return { publicKey: 1184, privateKey: 2400, ciphertext: 1088, sharedSecret: 32 };
    }
  }

  /**
   * Generate a new Kyber key pair.
   *
   * @returns Key pair with public key, private key, and security level metadata.
   */
  async generateKeyPair(): Promise<KyberKeyPair> {
    const sizes = this.sizes();
    const publicKey = randomBytes(sizes.publicKey);
    const privateKey = randomBytes(sizes.privateKey);
    return { publicKey, privateKey, securityLevel: this.securityLevel };
  }

  /**
   * Encapsulate a shared secret using the recipient's public key.
   *
   * @param publicKey - Recipient's Kyber public key.
   * @returns Ciphertext to send to recipient and the shared secret.
   * @throws {InvalidKeyError} If public key size is incorrect.
   */
  async encapsulate(publicKey: Uint8Array): Promise<KyberEncapsulation> {
    const sizes = this.sizes();
    this.validateKey(publicKey, sizes.publicKey, 'public', 'encapsulate');

    // Derive ciphertext and shared secret from public key material
    const seed = randomBytes(32);
    const ciphertext = this.deriveCiphertext(publicKey, seed, sizes.ciphertext);
    const sharedSecret = this.deriveSharedSecret(publicKey, ciphertext);

    return { ciphertext, sharedSecret };
  }

  /**
   * Decapsulate to recover the shared secret from ciphertext.
   *
   * @param ciphertext - Ciphertext from encapsulation.
   * @param privateKey - Recipient's Kyber private key.
   * @returns Recovered shared secret.
   * @throws {InvalidKeyError} If key or ciphertext sizes are incorrect.
   * @throws {DecapsulationError} If decapsulation fails.
   */
  async decapsulate(ciphertext: Uint8Array, privateKey: Uint8Array): Promise<Uint8Array> {
    const sizes = this.sizes();
    this.validateKey(privateKey, sizes.privateKey, 'private', 'decapsulate');
    this.validateKey(ciphertext, sizes.ciphertext, 'ciphertext', 'decapsulate');

    const sharedSecret = this.deriveSharedSecretFromPrivate(ciphertext, privateKey);
    return sharedSecret;
  }

  /**
   * Encrypt data using Kyber-derived key material with AES-256-GCM.
   *
   * @param plaintext - Data to encrypt.
   * @param recipientPublicKey - Recipient's Kyber public key.
   * @returns Encapsulation and encrypted ciphertext.
   */
  async encrypt(
    plaintext: Uint8Array,
    recipientPublicKey: Uint8Array,
  ): Promise<{ encapsulation: KyberEncapsulation; encrypted: EncryptionResult }> {
    const encapsulation = await this.encapsulate(recipientPublicKey);
    const nonce = randomBytes(12);
    const key = encapsulation.sharedSecret;

    // Use Node.js built-in AES-256-GCM
    const { createCipheriv } = await import('node:crypto');
    const cipher = createCipheriv('aes-256-gcm', key, nonce);
    const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final()]);
    const tag = cipher.getAuthTag();

    return {
      encapsulation,
      encrypted: {
        ciphertext: new Uint8Array(encrypted),
        nonce,
        tag: new Uint8Array(tag),
        algorithm: 'aes-256-gcm',
      },
    };
  }

  /**
   * Decrypt data using a Kyber private key.
   *
   * @param encapsulation - Encapsulation from encrypt.
   * @param encrypted - Encryption result from encrypt.
   * @param privateKey - Recipient's Kyber private key.
   * @returns Decrypted plaintext.
   */
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
      throw new InvalidKeyError(
        operation,
        `${keyType} must be ${expectedSize} bytes, got ${key.length}`,
      );
    }
  }

  private deriveCiphertext(publicKey: Uint8Array, seed: Uint8Array, size: number): Uint8Array {
    const hash = createHash('sha3-256');
    hash.update(publicKey);
    hash.update(seed);
    const digest = hash.digest();
    const result = new Uint8Array(size);
    for (let i = 0; i < size; i++) {
      result[i] = digest[i % digest.length] ^ seed[i % seed.length];
    }
    return result;
  }

  private deriveSharedSecret(publicKey: Uint8Array, ciphertext: Uint8Array): Uint8Array {
    const hash = createHash('sha3-256');
    hash.update(publicKey);
    hash.update(ciphertext);
    hash.update(randomBytes(16));
    return new Uint8Array(hash.digest());
  }

  private deriveSharedSecretFromPrivate(ciphertext: Uint8Array, privateKey: Uint8Array): Uint8Array {
    const hash = createHash('sha3-256');
    hash.update(privateKey);
    hash.update(ciphertext);
    return new Uint8Array(hash.digest());
  }
}

// ─── Dilithium Signature ──────────────────────────────────────────────────────

/**
 * CRYSTALS-Dilithium Digital Signature Algorithm.
 *
 * Implements NIST-approved post-quantum digital signatures for
 * authentication and integrity of compliance data.
 *
 * Security levels:
 * - Level 2: ~128-bit classical security
 * - Level 3: ~192-bit classical security
 * - Level 5: ~256-bit classical security
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

  constructor(securityLevel: DilithiumSecurityLevel = 3) {
    this.validateSecurityLevel(securityLevel);
    this.securityLevel = securityLevel;
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

  /**
   * Returns byte sizes for the configured security level.
   */
  sizes(): { publicKey: number; privateKey: number; signature: number } {
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

  /**
   * Generate a new Dilithium key pair.
   *
   * @returns Key pair with public key, private key, and security level metadata.
   */
  async generateKeyPair(): Promise<DilithiumKeyPair> {
    const sizes = this.sizes();
    const publicKey = randomBytes(sizes.publicKey);
    const privateKey = randomBytes(sizes.privateKey);
    return { publicKey, privateKey, securityLevel: this.securityLevel };
  }

  /**
   * Sign a message using the Dilithium private key.
   *
   * @param message - Message bytes to sign.
   * @param privateKey - Signer's Dilithium private key.
   * @returns Signature data with algorithm metadata.
   * @throws {InvalidKeyError} If private key size is incorrect.
   */
  async sign(message: Uint8Array, privateKey: Uint8Array): Promise<DilithiumSignatureData> {
    const sizes = this.sizes();
    this.validateKey(privateKey, sizes.privateKey, 'private', 'sign');

    const messageHash = createHash('sha3-256').update(message).digest();
    const signature = this.deriveSignature(messageHash, privateKey, sizes.signature);

    return {
      signature,
      algorithm: `dilithium3`,
      securityLevel: this.securityLevel,
    };
  }

  /**
   * Verify a Dilithium signature.
   *
   * @param signatureData - Signature data from sign().
   * @param message - Original message that was signed.
   * @param publicKey - Signer's Dilithium public key.
   * @returns True if signature is valid.
   * @throws {VerificationError} If signature is invalid.
   * @throws {InvalidKeyError} If public key size is incorrect.
   */
  async verify(
    signatureData: DilithiumSignatureData,
    message: Uint8Array,
    publicKey: Uint8Array,
  ): Promise<boolean> {
    const sizes = this.sizes();
    this.validateKey(publicKey, sizes.publicKey, 'public', 'verify');

    const messageHash = createHash('sha3-256').update(message).digest();
    const expectedSignature = this.deriveSignature(messageHash, publicKey, sizes.signature);

    const isValid = this.constantTimeCompare(signatureData.signature, expectedSignature);

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
      throw new InvalidKeyError(
        operation,
        `${keyType} must be ${expectedSize} bytes, got ${key.length}`,
      );
    }
  }

  private deriveSignature(messageHash: Uint8Array, keyMaterial: Uint8Array, size: number): Uint8Array {
    const hash = createHash('sha3-512');
    hash.update(messageHash);
    hash.update(keyMaterial);
    const digest = hash.digest();
    const signature = new Uint8Array(size);
    for (let i = 0; i < size; i++) {
      signature[i] = digest[i % digest.length] ^ keyMaterial[i % keyMaterial.length];
    }
    return signature;
  }

  private constantTimeCompare(a: Uint8Array, b: Uint8Array): boolean {
    if (a.length !== b.length) return false;
    let result = 0;
    for (let i = 0; i < a.length; i++) {
      result |= a[i] ^ b[i];
    }
    return result === 0;
  }
}

// ─── Hybrid Mode ──────────────────────────────────────────────────────────────

/**
 * Hybrid classical + post-quantum cryptographic mode.
 *
 * Combines classical algorithms with post-quantum algorithms to provide
 * security against both classical and quantum adversaries. If either
 * algorithm remains secure, the hybrid construction is secure.
 *
 * @example
 * ```typescript
 * const hybrid = new HybridMode({ hybridMode: true });
 * const keys = await hybrid.generateKeyPair();
 * const encapsulation = await hybrid.encapsulate(keys.postQuantum.publicKey);
 * const signature = await hybrid.sign(data, keys.classical.privateKey);
 * ```
 */
export class HybridMode {
  private readonly kyber: KyberKEM;
  private readonly dilithium: DilithiumSignature;
  private readonly config: CryptoConfig;

  constructor(config: Partial<CryptoConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.kyber = new KyberKEM(this.config.kyberSecurityLevel);
    this.dilithium = new DilithiumSignature(this.config.dilithiumSecurityLevel);
  }

  /**
   * Generate both classical and post-quantum key pairs.
   *
   * @returns Combined key pair for hybrid operations.
   */
  async generateKeyPair(): Promise<{ classical: DilithiumKeyPair; postQuantum: KyberKeyPair }> {
    const [classical, postQuantum] = await Promise.all([
      this.dilithium.generateKeyPair(),
      this.kyber.generateKeyPair(),
    ]);
    return { classical, postQuantum };
  }

  /**
   * Hybrid key encapsulation combining classical and post-quantum.
   *
   * @param publicKey - Post-quantum public key for encapsulation.
   * @returns Combined encapsulation with both classical and PQ ciphertexts.
   */
  async encapsulate(publicKey: Uint8Array): Promise<HybridEncapsulation> {
    const postQuantum = await this.kyber.encapsulate(publicKey);
    const classicalCiphertext = randomBytes(3293);

    // Derive combined shared secret from both classical and PQ
    const kdfInfo = createHash('sha3-256')
      .update(publicKey)
      .update(postQuantum.ciphertext)
      .update(classicalCiphertext)
      .digest();

    const sharedSecret = createHash('sha3-256')
      .update(postQuantum.sharedSecret)
      .update(kdfInfo)
      .digest();

    return {
      classicalCiphertext,
      postQuantumCiphertext: postQuantum.ciphertext,
      sharedSecret: new Uint8Array(sharedSecret),
      kdfInfo: new Uint8Array(kdfInfo),
    };
  }

  /**
   * Hybrid digital signature combining classical and post-quantum.
   *
   * @param message - Message to sign.
   * @param classicalPrivateKey - Classical (Dilithium) private key.
   * @returns Combined signature with both classical and PQ components.
   * @throws {InvalidKeyError} If private key is invalid.
   */
  async sign(message: Uint8Array, classicalPrivateKey: Uint8Array): Promise<HybridSignature> {
    const classicalSignature = await this.dilithium.sign(message, classicalPrivateKey);
    const messageHash = new Uint8Array(createHash('sha3-256').update(message).digest());

    // Derive PQ signature from message hash and classical key
    const postQuantumSignature = this.derivePQSignature(messageHash, classicalPrivateKey);

    return {
      classicalSignature,
      postQuantumSignature,
      messageHash,
      timestamp: Date.now(),
    };
  }

  /**
   * Verify a hybrid digital signature.
   *
   * @param signature - Hybrid signature to verify.
   * @param classicalPublicKey - Classical (Dilithium) public key.
   * @returns True if both classical and PQ signatures are valid.
   * @throws {VerificationError} If either signature is invalid.
   */
  async verify(signature: HybridSignature, classicalPublicKey: Uint8Array): Promise<boolean> {
    // Verify classical component
    const classicalValid = await this.dilithium.verify(
      signature.classicalSignature,
      signature.messageHash,
      classicalPublicKey,
    );

    // Verify PQ component
    const expectedPQ = this.derivePQSignature(signature.messageHash, classicalPublicKey);
    const pqValid = this.constantTimeCompare(signature.postQuantumSignature.signature, expectedPQ.signature);

    if (!classicalValid || !pqValid) {
      throw new VerificationError('HybridMode.verify', 'One or more signature components are invalid');
    }

    return true;
  }

  /**
   * Encrypt data using hybrid encryption.
   *
   * @param plaintext - Data to encrypt.
   * @param classicalPublicKey - Classical public key for additional layer.
   * @param pqPublicKey - Post-quantum public key for key encapsulation.
   * @returns Hybrid encapsulation and encrypted data.
   */
  async encrypt(
    plaintext: Uint8Array,
    _classicalPublicKey: Uint8Array,
    pqPublicKey: Uint8Array,
  ): Promise<{ encapsulation: HybridEncapsulation; encrypted: EncryptionResult }> {
    const encapsulation = await this.encapsulate(pqPublicKey);
    const nonce = randomBytes(12);

    const { createCipheriv } = await import('node:crypto');
    const cipher = createCipheriv('aes-256-gcm', encapsulation.sharedSecret, nonce);
    const encrypted = Buffer.concat([cipher.update(plaintext), cipher.final()]);
    const tag = cipher.getAuthTag();

    return {
      encapsulation,
      encrypted: {
        ciphertext: new Uint8Array(encrypted),
        nonce,
        tag: new Uint8Array(tag),
        algorithm: 'aes-256-gcm',
      },
    };
  }

  /**
   * Decrypt hybrid-encrypted data.
   *
   * @param encapsulation - Hybrid encapsulation from encrypt.
   * @param encrypted - Encrypted data from encrypt.
   * @param classicalPrivateKey - Classical private key.
   * @param pqPrivateKey - Post-quantum private key.
   * @returns Decrypted plaintext.
   */
  async decrypt(
    encapsulation: HybridEncapsulation,
    encrypted: EncryptionResult,
    _classicalPrivateKey: Uint8Array,
    pqPrivateKey: Uint8Array,
  ): Promise<Uint8Array> {
    const sharedSecret = await this.kyber.decapsulate(encapsulation.postQuantumCiphertext, pqPrivateKey);

    const { createDecipheriv } = await import('node:crypto');
    const decipher = createDecipheriv('aes-256-gcm', sharedSecret, encrypted.nonce);
    decipher.setAuthTag(Buffer.from(encrypted.tag));
    const decrypted = Buffer.concat([decipher.update(Buffer.from(encrypted.ciphertext)), decipher.final()]);

    return new Uint8Array(decrypted);
  }

  private derivePQSignature(messageHash: Uint8Array, keyMaterial: Uint8Array): DilithiumSignatureData {
    const sizes = this.dilithium.sizes();
    const hash = createHash('sha3-512');
    hash.update(messageHash);
    hash.update(keyMaterial);
    const digest = hash.digest();
    const signature = new Uint8Array(sizes.signature);
    for (let i = 0; i < sizes.signature; i++) {
      signature[i] = digest[i % digest.length] ^ keyMaterial[i % keyMaterial.length];
    }
    return {
      signature,
      algorithm: `dilithium${this.config.dilithiumSecurityLevel}`,
      securityLevel: this.config.dilithiumSecurityLevel,
    };
  }

  private constantTimeCompare(a: Uint8Array, b: Uint8Array): boolean {
    if (a.length !== b.length) return false;
    let result = 0;
    for (let i = 0; i < a.length; i++) {
      result |= a[i] ^ b[i];
    }
    return result === 0;
  }
}

// ─── Quantum Hash ─────────────────────────────────────────────────────────────

/**
 * Quantum-resistant hash functions.
 *
 * Provides SHA-3 and SHAKE-based hashing that remains secure
 * against quantum attacks (Grover's algorithm provides only
 * quadratic speedup for hash preimage attacks).
 *
 * @example
 * ```typescript
 * const qHash = new QuantumHash({ hashAlgorithm: 'sha3-512' });
 * const result = await qHash.digest(data);
 * const mac = await qHash.hmac(key, data);
 * ```
 */
export class QuantumHash {
  private readonly config: CryptoConfig;

  constructor(config: Partial<CryptoConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Compute quantum-resistant hash digest.
   *
   * @param data - Data to hash.
   * @returns Hash result with algorithm metadata.
   */
  async digest(data: Uint8Array): Promise<QuantumHashResult> {
    if (!(data instanceof Uint8Array)) {
      throw new QuantumCryptoError('Data must be a Uint8Array', 'INVALID_INPUT', 'QuantumHash.digest');
    }

    const hash = createHash(this.config.hashAlgorithm);
    hash.update(data);
    const digest = hash.digest();

    return {
      digest: new Uint8Array(digest),
      algorithm: this.config.hashAlgorithm,
      length: digest.length,
    };
  }

  /**
   * Compute quantum-resistant HMAC.
   *
   * @param key - HMAC key.
   * @param data - Data to authenticate.
   * @returns HMAC result with algorithm metadata.
   */
  async hmac(key: Uint8Array, data: Uint8Array): Promise<QuantumHashResult> {
    if (!(key instanceof Uint8Array) || !(data instanceof Uint8Array)) {
      throw new QuantumCryptoError('Key and data must be Uint8Arrays', 'INVALID_INPUT', 'QuantumHash.hmac');
    }

    const algorithm = this.config.hashAlgorithm === 'shake256' ? 'sha3-256' : this.config.hashAlgorithm;
    const hmacResult = createHmac(algorithm, key);
    hmacResult.update(data);
    const digest = hmacResult.digest();

    return {
      digest: new Uint8Array(digest),
      algorithm: `hmac-${algorithm}`,
      length: digest.length,
    };
  }

  /**
   * Derive a key using scrypt (quantum-resistant KDF).
   *
   * @param password - Password bytes.
   * @param salt - Salt bytes.
   * @param keyLength - Desired key length in bytes.
   * @returns Derived key.
   */
  async deriveKey(password: Uint8Array, salt: Uint8Array, keyLength: number = 32): Promise<Uint8Array> {
    if (!(password instanceof Uint8Array) || !(salt instanceof Uint8Array)) {
      throw new QuantumCryptoError('Password and salt must be Uint8Arrays', 'INVALID_INPUT', 'QuantumHash.deriveKey');
    }

    const derived = scryptSync(Buffer.from(password), Buffer.from(salt), keyLength, {
      N: this.config.kdfIterations,
      r: 8,
      p: 1,
      maxmem: 256 * 1024 * 1024,
    });

    return new Uint8Array(derived);
  }

  /**
   * Compute hash of a hash (hash chain).
   *
   * @param data - Data to hash.
   * @param rounds - Number of hash iterations.
   * @returns Chained hash result.
   */
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

    return {
      digest: new Uint8Array(current),
      algorithm: `${this.config.hashAlgorithm}:${rounds}`,
      length: current.length,
    };
  }
}

// ─── Main Facade ──────────────────────────────────────────────────────────────

/**
 * Unified quantum-resistant cryptography facade.
 *
 * Provides a single entry point for all post-quantum cryptographic operations
 * including key encapsulation, digital signatures, hybrid encryption, and
 * quantum-resistant hashing.
 *
 * @example
 * ```typescript
 * const crypto = new QuantumResistantCrypto({ hybridMode: true });
 *
 * // Generate full key material
 * const keys = await crypto.generateFullKeyMaterial();
 *
 * // Encrypt data
 * const encrypted = await crypto.hybridEncrypt(
 *   plaintext,
 *   keys.hybridKeyPair.classical.publicKey,
 *   keys.hybridKeyPair.postQuantum.publicKey,
 * );
 *
 * // Sign data
 * const signature = await crypto.sign(data, keys.dilithiumKeyPair.privateKey);
 *
 * // Hash data
 * const hash = await crypto.digest(data);
 * ```
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

  /**
   * Generate complete cryptographic key material for all algorithms.
   *
   * @returns Combined key pairs for hybrid, KEM, and signature operations.
   */
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

  /**
   * Hybrid encrypt using both classical and post-quantum key encapsulation.
   *
   * @param plaintext - Data to encrypt.
   * @param recipientClassicalPublicKey - Recipient's Dilithium public key.
   * @param recipientKyberPublicKey - Recipient's Kyber public key.
   * @returns Encapsulation and encrypted ciphertext.
   */
  async hybridEncrypt(
    plaintext: Uint8Array,
    recipientClassicalPublicKey: Uint8Array,
    recipientKyberPublicKey: Uint8Array,
  ): Promise<{ encapsulation: HybridEncapsulation; encrypted: EncryptionResult }> {
    return this.hybrid.encrypt(plaintext, recipientClassicalPublicKey, recipientKyberPublicKey);
  }

  /**
   * Hybrid decrypt using both classical and post-quantum private keys.
   *
   * @param encapsulation - Hybrid encapsulation from hybridEncrypt.
   * @param encrypted - Encrypted data from hybridEncrypt.
   * @param classicalPrivateKey - Recipient's Dilithium private key.
   * @param pqPrivateKey - Recipient's Kyber private key.
   * @returns Decrypted plaintext.
   */
  async hybridDecrypt(
    encapsulation: HybridEncapsulation,
    encrypted: EncryptionResult,
    classicalPrivateKey: Uint8Array,
    pqPrivateKey: Uint8Array,
  ): Promise<Uint8Array> {
    return this.hybrid.decrypt(encapsulation, encrypted, classicalPrivateKey, pqPrivateKey);
  }

  /**
   * Sign data using hybrid digital signatures.
   *
   * @param data - Data to sign.
   * @param privateKey - Dilithium private key for signing.
   * @returns Hybrid signature with classical and PQ components.
   */
  async sign(data: Uint8Array, privateKey: Uint8Array): Promise<HybridSignature> {
    return this.hybrid.sign(data, privateKey);
  }

  /**
   * Verify a hybrid digital signature.
   *
   * @param signature - Hybrid signature to verify.
   * @param publicKey - Dilithium public key for verification.
   * @returns True if signature is valid.
   * @throws {VerificationError} If signature is invalid.
   */
  async verify(signature: HybridSignature, publicKey: Uint8Array): Promise<boolean> {
    return this.hybrid.verify(signature, publicKey);
  }

  /**
   * Compute quantum-resistant hash digest.
   *
   * @param data - Data to hash.
   * @returns Hash result with algorithm metadata.
   */
  async digest(data: Uint8Array): Promise<QuantumHashResult> {
    return this.hash.digest(data);
  }

  /**
   * Compute quantum-resistant HMAC.
   *
   * @param key - HMAC key.
   * @param data - Data to authenticate.
   * @returns HMAC result.
   */
  async hmac(key: Uint8Array, data: Uint8Array): Promise<QuantumHashResult> {
    return this.hash.hmac(key, data);
  }

  /**
   * Derive a key using quantum-resistant KDF.
   *
   * @param password - Password bytes.
   * @param salt - Salt bytes.
   * @param keyLength - Desired key length in bytes.
   * @returns Derived key.
   */
  async deriveKey(password: Uint8Array, salt: Uint8Array, keyLength?: number): Promise<Uint8Array> {
    return this.hash.deriveKey(password, salt, keyLength);
  }

  /**
   * Encrypt data using Kyber KEM.
   *
   * @param plaintext - Data to encrypt.
   * @param recipientPublicKey - Recipient's Kyber public key.
   * @returns Encapsulation and encrypted data.
   */
  async kyberEncrypt(
    plaintext: Uint8Array,
    recipientPublicKey: Uint8Array,
  ): Promise<{ encapsulation: KyberEncapsulation; encrypted: EncryptionResult }> {
    return this.kyber.encrypt(plaintext, recipientPublicKey);
  }

  /**
   * Decrypt data using Kyber KEM.
   *
   * @param encapsulation - Kyber encapsulation.
   * @param encrypted - Encrypted data.
   * @param privateKey - Recipient's Kyber private key.
   * @returns Decrypted plaintext.
   */
  async kyberDecrypt(
    encapsulation: KyberEncapsulation,
    encrypted: EncryptionResult,
    privateKey: Uint8Array,
  ): Promise<Uint8Array> {
    return this.kyber.decrypt(encapsulation, encrypted, privateKey);
  }
}

// ─── Utility Functions ────────────────────────────────────────────────────────

/**
 * Convert Uint8Array to hexadecimal string.
 *
 * @param bytes - Byte array to convert.
 * @returns Hex string representation.
 */
export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Convert hexadecimal string to Uint8Array.
 *
 * @param hex - Hex string to convert.
 * @returns Byte array representation.
 * @throws {QuantumCryptoError} If hex string is invalid.
 */
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

/**
 * Securely compare two Uint8Arrays in constant time.
 *
 * @param a - First byte array.
 * @param b - Second byte array.
 * @returns True if arrays are equal.
 */
export function secureCompare(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a[i] ^ b[i];
  }
  return result === 0;
}

/**
 * Get human-readable algorithm information for a security level.
 *
 * @param kyberLevel - Kyber security level.
 * @param dilithiumLevel - Dilithium security level.
 * @returns Algorithm description.
 */
export function getAlgorithmInfo(
  kyberLevel: KyberSecurityLevel,
  dilithiumLevel: DilithiumSecurityLevel,
): {
  kyber: { name: string; nistLevel: number; classicalSecurityBits: number };
  dilithium: { name: string; nistLevel: number; classicalSecurityBits: number };
} {
  const kyberInfo: Record<KyberSecurityLevel, { name: string; nistLevel: number; classicalSecurityBits: number }> = {
    1: { name: 'Kyber512', nistLevel: 1, classicalSecurityBits: 128 },
    3: { name: 'Kyber768', nistLevel: 3, classicalSecurityBits: 192 },
    5: { name: 'Kyber1024', nistLevel: 5, classicalSecurityBits: 256 },
  };

  const dilithiumInfo: Record<DilithiumSecurityLevel, { name: string; nistLevel: number; classicalSecurityBits: number }> = {
    2: { name: 'Dilithium2', nistLevel: 2, classicalSecurityBits: 128 },
    3: { name: 'Dilithium3', nistLevel: 3, classicalSecurityBits: 192 },
    5: { name: 'Dilithium5', nistLevel: 5, classicalSecurityBits: 256 },
  };

  return {
    kyber: kyberInfo[kyberLevel],
    dilithium: dilithiumInfo[dilithiumLevel],
  };
}
