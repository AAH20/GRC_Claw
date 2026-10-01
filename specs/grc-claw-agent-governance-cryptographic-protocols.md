# GRC_Claw Agent Governance — Cryptographic Protocols & Formal Verification

**Version:** 1.0  
**Date:** 2026-10-01  
**Status:** Draft  
**Owner:** GRC_Claw Architecture Team  
**Supersedes:** —  
**Related:** GRC_Claw Agent Governance Spec v1.0, GRC_Claw Integration Spec v1.0

---

## 1. Purpose & Scope

This document deepens the GRC_Claw Agent Governance Specification with cryptographic protocols, formal schemas, and verification procedures. It transforms the conceptual governance model into an implementable, verifiable system.

**In scope:**
- Complete DID document schema with cryptographic verification
- Verifiable credential format for agent capabilities
- Delegation chain cryptographic verification protocol
- Trust score computation algorithm with formal properties
- Agent lifecycle state machine with formal verification
- Cross-organizational trust anchoring protocol

**Out of scope:**
- Implementation-specific code (covered by reference implementation)
- Transport-layer security (covered by Integration Spec §8)
- Policy language semantics (covered by Policy Engine spec)

---

## 2. Complete DID Document Schema

### 2.1 DID Method Specification

GRC_Claw uses the `did:grc` method, conforming to the W3C DID Core v1.0 specification with GRC_Claw extensions.

#### 2.1.1 DID Syntax

```
did                = "did:" method-name ":" method-specific-id
method-name        = "grc"
method-specific-id = (agent-did / org-did / user-did / system-did)

agent-did          = "agent:" uuid
org-did            = "org:" uuid
user-did           = "user:" uuid
system-did         = "system:" 1*( ALPHA / DIGIT / "-" / "." )

uuid               = 8HEXDIG "-" 4HEXDIG "-" 4HEXDIG "-" 4HEXDIG "-" 12HEXDIG
```

#### 2.1.2 DID Document Structure

```json
{
  "@context": [
    "https://www.w3.org/ns/did/v1",
    "https://grc-claw.dev/schemas/did-extensions/v1"
  ],
  "id": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "alsoKnownAs": [
    "did:grc:agent:customer-service-agent"
  ],
  "controller": "did:grc:org:acme-corp",
  "verificationMethod": [
    {
      "id": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#keys-1",
      "type": "Ed25519VerificationKey2020",
      "controller": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "publicKeyMultibase": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
    },
    {
      "id": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#keys-2",
      "type": "EcdsaSecp256r1VerificationKey2019",
      "controller": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "publicKeyJwk": {
        "kty": "EC",
        "crv": "P-256",
        "x": "f83OJ3D2xF1Bg8vub9tLe1gHMzV76e8Tus9uPHvRVEU",
        "y": "x_FEzRu9m36HLN_tue659LNpXW6pCyStikYjKIWI5a0"
      }
    }
  ],
  "authentication": [
    "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#keys-1"
  ],
  "assertionMethod": [
    "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#keys-1",
    "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#keys-2"
  ],
  "keyAgreement": [
    {
      "id": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#key-agreement-1",
      "type": "X25519KeyAgreementKey2020",
      "controller": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "publicKeyMultibase": "z6LSbysY2xFMRpGMhb7tFTLMpeuPRaqaWM1yECx2eTzUkp"
    }
  ],
  "capabilityInvocation": [
    "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#keys-1"
  ],
  "capabilityDelegation": [
    "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#keys-1"
  ],
  "service": [
    {
      "id": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#agent-registry",
      "type": "GRCClawAgentRegistry",
      "serviceEndpoint": "https://registry.grc-claw.dev/agents/7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c"
    },
    {
      "id": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#trust-score",
      "type": "GRCClawTrustService",
      "serviceEndpoint": "https://trust.grc-claw.dev/scores/7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c"
    },
    {
      "id": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#audit-log",
      "type": "GRCClawAuditLog",
      "serviceEndpoint": "https://audit.grc-claw.dev/trails/7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c"
    }
  ],
  "grcExtensions": {
    "agentType": "autonomous",
    "framework": "langchain",
    "version": "2.1.0",
    "owner": {
      "id": "did:grc:org:acme-corp",
      "name": "Acme Corp"
    },
    "deployment": {
      "environment": "production",
      "region": "us-east-1",
      "host": "agent-runner-01.acme.internal"
    },
    "status": "active",
    "createdAt": "2026-09-15T10:30:00Z",
    "lastRotated": "2026-09-15T10:30:00Z",
    "description": "Handles customer inquiries and ticket routing",
    "tags": ["customer-facing", "read-only", "tier-1"],
    "spiffeId": "spiffe://acme.internal/agent/customer-service-agent",
    "attestation": {
      "type": "tpm2.0",
      "pcrMeasurements": [0, 1, 2, 3, 4, 5, 6, 7],
      "quote": "base64-encoded-tpm-quote",
      "verifiedAt": "2026-09-15T10:30:00Z"
    }
  }
}
```

### 2.2 Verification Method Types

| Key Type | Purpose | Algorithm | Format |
|----------|---------|-----------|--------|
| `Ed25519VerificationKey2020` | Authentication, capability invocation | Ed25519 | Multibase |
| `EcdsaSecp256r1VerificationKey2019` | Assertion, audit signing | ECDSA P-256 | JWK |
| `X25519KeyAgreementKey2020` | Session key agreement | X25519 | Multibase |
| `RsaVerificationKey2018` | Legacy compatibility | RSA-4096 | JWK |

### 2.3 DID Document Resolution

```
GET /api/v1/identity/resolve/{did}

Response 200:
{
  "didDocument": { /* DID Document */ },
  "didDocumentMetadata": {
    "created": "2026-09-15T10:30:00Z",
    "updated": "2026-09-15T10:30:00Z",
    "deactivated": false,
    "versionId": "1"
  },
  "resolutionMetadata": {
    "contentType": "application/did+ld+json",
    "retrieved": "2026-10-01T12:00:00Z"
  }
}
```

### 2.4 DID Document Integrity

Every DID document is signed by its controller. The signature covers the canonical form of the document (excluding the `proof` field):

```json
{
  "type": "Ed25519Signature2020",
  "created": "2026-09-15T10:30:00Z",
  "verificationMethod": "did:grc:org:acme-corp#keys-1",
  "proofPurpose": "authentication",
  "proofValue": "z58DAdFfa9SkqZMVPxAQvpNMz5Bw2G4Dk7GwsAqGk0bKQvJj5z3V8W5Y8X9..."
}
```

**Canonicalization:** JSON Canonicalization Scheme (JCS, RFC 8785)  
**Signature:** Ed25519 over SHA-256 of canonical bytes  
**Verification:** Controller's public key from their DID document

---

## 3. Verifiable Credential Format for Agent Capabilities

### 3.1 Credential Architecture

Agent capabilities are issued as W3C Verifiable Credentials (VC) v1.1, using the GRC_Claw capability context. Credentials are signed, revocable, and independently verifiable without contacting the issuer.

```
┌─────────────────────────────────────────────────────────────┐
│              Verifiable Credential Lifecycle                  │
│                                                              │
│  Issuer ──► Credential ──► Holder ──► Verifier              │
│  (Agent)    (Signed VC)   (Agent)    (Policy Engine)        │
│                                                              │
│  1. Issue: Sign capability claims                           │
│  2. Present: Holder presents VC + proof of possession       │
│  3. Verify: Verify signature, revocation, validity         │
│  4. Enforce: Check capability against requested action      │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Credential Schema

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://grc-claw.dev/schemas/capability-credential/v1"
  ],
  "id": "urn:uuid:9d0e1f2a-3b4c-5d6e-7f8a-9b0c1d2e3f4a",
  "type": ["VerifiableCredential", "GRCCapabilityCredential"],
  "issuer": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "issuanceDate": "2026-10-01T09:00:00Z",
  "expirationDate": "2026-10-01T17:00:00Z",
  "credentialSubject": {
    "id": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
    "capability": {
      "actions": ["read", "write"],
      "resources": ["ticket-system", "customer-db"],
      "resourceIds": ["ticket-12345", "customer-789"],
      "conditions": {
        "dataClassification": ["public", "internal"],
        "timeWindow": {
          "start": "2026-10-01T09:00:00Z",
          "end": "2026-10-01T17:00:00Z"
        },
        "rateLimit": {
          "maxActions": 100,
          "window": "1h"
        },
        "fieldRestrictions": {
          "customer-db": ["name", "email", "account-status"]
        }
      }
    },
    "delegation": {
      "delegationId": "del:8c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
      "delegator": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "depth": 1,
      "maxDepth": 2
    }
  },
  "credentialStatus": {
    "id": "https://status.grc-claw.dev/vc/9d0e1f2a-3b4c-5d6e-7f8a-9b0c1d2e3f4a",
    "type": "GRCCredentialStatusList2026"
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-10-01T09:00:00Z",
    "verificationMethod": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#keys-1",
    "proofPurpose": "assertionMethod",
    "proofValue": "z58DAdFfa9SkqZMVPxAQvpNMz5Bw2G4Dk7GwsAqGk0bKQvJj5z3V8W5Y8X9..."
  }
}
```

### 3.3 Credential Status List (Revocation)

Revocation uses a bitstring-based status list for efficient batch verification:

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://grc-claw.dev/schemas/status-list/v1"
  ],
  "id": "https://status.grc-claw.dev/list/issuer-7f3a9b2c",
  "type": ["VerifiableCredential", "GRCStatusList2026"],
  "issuer": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "issuanceDate": "2026-10-01T09:00:00Z",
  "credentialSubject": {
    "id": "https://status.grc-claw.dev/list/issuer-7f3a9b2c",
    "type": "GRCStatusList2026",
    "statusPurpose": "revocation",
    "encodedList": "H4sIAAAAAAAAA-3BMQEAAADCoPVPbQwfoAAAAAAAAAAAAAAAAAAAAAAA"
  },
  "proof": { /* issuer signature */ }
}
```

**Bitstring encoding:** GZIP-compressed, base64url-encoded bitstring where bit `i` = 1 means credential index `i` is revoked.

### 3.4 Credential Presentation Protocol

When an agent presents a capability credential to a verifier:

```json
{
  "@context": [
    "https://www.w3.org/2018/credentials/v1",
    "https://grc-claw.dev/schemas/capability-presentation/v1"
  ],
  "type": ["VerifiablePresentation", "GRCCapabilityPresentation"],
  "holder": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "verifiableCredential": [
    {
      "id": "urn:uuid:9d0e1f2a-3b4c-5d6e-7f8a-9b0c1d2e3f4a",
      "type": ["VerifiableCredential", "GRCCapabilityCredential"],
      "issuer": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
      "issuanceDate": "2026-10-01T09:00:00Z",
      "expirationDate": "2026-10-01T17:00:00Z",
      "credentialSubject": {
        "id": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
        "capability": {
          "actions": ["read", "write"],
          "resources": ["ticket-system", "customer-db"]
        }
      },
      "proof": { /* issuer signature */ }
    }
  ],
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-10-01T10:15:00Z",
    "verificationMethod": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d#keys-1",
    "proofPurpose": "authentication",
    "challenge": "nonce-from-verifier",
    "domain": "policy-engine.grc-claw.dev",
    "proofValue": "z58DAdFfa9SkqZMVPxAQvpNMz5Bw2G4Dk7GwsAqGk0bKQvJj5z3V8W5Y8X9..."
  }
}
```

### 3.5 Credential Verification Algorithm

```
verify_credential(vc, verifier_context) → Result:

1. STRUCTURAL VALIDATION
   a. Parse VC JSON, verify @context includes required contexts
   b. Verify required fields present: id, type, issuer, issuanceDate, 
      expirationDate, credentialSubject, proof
   c. Verify type includes "GRCCapabilityCredential"

2. TEMPORAL VALIDATION
   a. current_time ≥ issuanceDate
   b. current_time ≤ expirationDate
   c. If expired → return EXPIRED

3. ISSUER VERIFICATION
   a. Resolve issuer DID document
   b. Verify issuer DID is active (not deactivated)
   c. Extract verification method matching proof.verificationMethod
   d. Verify issuer DID document proof (controller signature)

4. SIGNATURE VERIFICATION
   a. Canonicalize VC (excluding proof) using JCS
   b. Verify proofValue against canonical bytes using issuer's public key
   c. If invalid → return INVALID_SIGNATURE

5. REVOCATION CHECK
   a. Fetch credentialStatus.encodedList
   b. Decompress bitstring
   c. Check bit at index derived from credential id hash
   d. If bit = 1 → return REVOKED

6. DELEGATION VALIDATION (if credentialSubject.delegation present)
   a. Resolve delegation record
   b. Verify delegation chain (see §4)
   c. Verify capability scope ⊆ delegation scope

7. CONTEXTUAL VALIDATION
   a. Verify credentialSubject.id == presenter DID
   b. Verify challenge matches (if presentation context)
   c. Verify domain matches expected verifier domain

8. Return VALID with extracted capability claims
```

---

## 4. Delegation Chain Cryptographic Verification

### 4.1 Delegation Record (Complete)

Each delegation is a signed record that references its parent, forming a verifiable chain:

```json
{
  "$schema": "https://grc-claw.dev/schemas/delegation/v2",
  "id": "del:8c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
  "delegator": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "delegate": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "scope": {
    "capabilities": ["read:tickets", "write:responses"],
    "resources": ["ticket-system", "customer-db"],
    "constraints": {
      "maxActionsPerSession": 100,
      "allowedOperations": ["read", "write"],
      "deniedOperations": ["delete", "export"],
      "dataClassification": ["public", "internal"],
      "fieldRestrictions": {
        "customer-db": ["name", "email", "account-status"]
      }
    }
  },
  "validity": {
    "issuedAt": "2026-10-01T09:00:00Z",
    "expiresAt": "2026-10-01T17:00:00Z",
    "maxDepth": 2,
    "notBefore": "2026-10-01T09:00:00Z"
  },
  "parentDelegation": null,
  "status": "active",
  "revocation": null,
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-10-01T09:00:00Z",
    "verificationMethod": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c#keys-1",
    "proofPurpose": "assertionMethod",
    "proofValue": "z58DAdFfa9SkqZMVPxAQvpNMz5Bw2G4Dk7GwsAqGk0bKQvJj5z3V8W5Y8X9..."
  }
}
```

### 4.2 Chain Verification Protocol

When agent D acts under a delegation chain A → B → C → D, the verifier must validate the entire chain:

```
verify_delegation_chain(leaf_delegation_id, action, resource) → Result:

1. CHAIN CONSTRUCTION
   a. Start from leaf delegation record
   b. Follow parentDelegation links to root
   c. Collect all delegation records: [D_n, D_n-1, ..., D_1, D_0]
      where D_0 is the root (parentDelegation = null)
   d. If any delegation in chain is missing → return CHAIN_BROKEN

2. DEPTH VALIDATION
   a. chain_length = number of delegations in chain
   b. For each D_i, verify D_i.validity.maxDepth ≥ chain_length - i - 1
   c. If any depth exceeded → return DEPTH_EXCEEDED

3. TEMPORAL VALIDATION
   a. For each D_i in chain:
      - current_time ≥ D_i.validity.notBefore
      - current_time ≤ D_i.validity.expiresAt
   b. For each child D_{i+1} and parent D_i:
      - D_{i+1}.validity.expiresAt ≤ D_i.validity.expiresAt
      - D_{i+1}.validity.notBefore ≥ D_i.validity.notBefore
   c. If any temporal violation → return TEMPORAL_VIOLATION

4. SCOPE NARROWING VALIDATION
   a. For each child D_{i+1} and parent D_i:
      - D_{i+1}.scope.capabilities ⊆ D_i.scope.capabilities
      - D_{i+1}.scope.resources ⊆ D_i.scope.resources
      - D_{i+1}.scope.constraints ⊆ D_i.scope.constraints
        (child constraints must be equal or more restrictive)
   b. If scope widening detected → return SCOPE_VIOLATION

5. SIGNATURE VERIFICATION
   a. For each D_i in chain:
      - Resolve D_i.delegator DID document
      - Extract verification method from proof.verificationMethod
      - Canonicalize D_i (excluding proof) using JCS
      - Verify proofValue against canonical bytes
   b. If any signature invalid → return SIGNATURE_INVALID

6. DELEGATOR AUTHORITY VERIFICATION
   a. For each D_i in chain:
      - D_i.delegator must have capability "admin:delegate" 
        OR be the root agent
      - D_i.delegator must be active (not suspended/revoked)
   b. If delegator lacks authority → return UNAUTHORIZED_DELEGATOR

7. REVOCATION CHECK
   a. For each D_i in chain:
      - D_i.status must be "active"
      - D_i.revocation must be null
   b. If any delegation revoked → return DELEGATION_REVOKED

8. ACTION AUTHORIZATION
   a. action ∈ leaf_delegation.scope.constraints.allowedOperations
   b. action ∉ leaf_delegation.scope.constraints.deniedOperations
   c. resource ∈ leaf_delegation.scope.resources
   d. If action not authorized → return ACTION_NOT_AUTHORIZED

9. CYCLE DETECTION
   a. Verify no agent appears twice in the chain
   b. If cycle detected → return CYCLE_DETECTED

10. Return VALID with effective_scope = leaf_delegation.scope
```

### 4.3 Chain Verification Optimization

For performance, chain verification uses Merkle proofs for batch validation:

```
┌─────────────────────────────────────────────────────────────┐
│              Delegation Chain Merkle Tree                    │
│                                                              │
│                    Root Hash                                 │
│                   /          \                                │
│            Hash(D_0)      Hash(D_1)                          │
│            /      \       /      \                            │
│       Hash(D_2)  Hash(D_3)  ...  Hash(D_n)                  │
│                                                              │
│  Leaf: Hash of canonical delegation record                   │
│  Node: SHA-256(left_child || right_child)                    │
│                                                              │
│  Verification: O(log n) hashes per delegation                │
└─────────────────────────────────────────────────────────────┘
```

### 4.4 Revocation Propagation Protocol

When a delegation is revoked, all descendants must be revoked within a bounded time:

```
revoke_delegation(delegation_id, reason, propagate) → Result:

1. AUTHENTICATE
   a. Verify revoker signature on revocation request
   b. Verify revoker is the delegator OR has admin:revoke capability

2. REVOKE LEAF
   a. Set delegation.status = "revoked"
   b. Set delegation.revocation = {
        "revokedBy": revoker_did,
        "reason": reason,
        "revokedAt": current_time,
        "propagateToChildren": propagate
      }
   c. Sign revocation record
   d. Emit audit event: delegation-revoked

3. PROPAGATE (if propagate = true)
   a. Find all child delegations (delegation.parentDelegation = delegation_id)
   b. For each child:
      - Recursively call revoke_delegation(child.id, "parent-revoked", true)
   c. Terminate all in-flight actions under revoked delegations
   d. Emit audit event: delegation-revocation-propagated

4. UPDATE STATUS LIST
   a. Add delegation_id to issuer's revocation bitstring
   b. Publish updated status list

5. Return revocation_receipt with propagation count
```

**Propagation guarantee:** Revocation propagates synchronously through the chain. Maximum propagation time: 5 seconds for chains up to depth 10.

---

## 5. Trust Score Computation Algorithm with Formal Properties

### 5.1 Mathematical Definition

The trust score is a function mapping an agent's behavioral history to a value in [0, 1]:

```
T: (B, C, O, R) → [0, 1]

where:
  B = behavioral_signals
  C = compliance_signals  
  O = operational_signals
  R = reputation_signals

T = w_b · f_b(B) + w_c · f_c(C) + w_o · f_o(O) + w_r · f_r(R)

subject to:
  w_b + w_c + w_o + w_r = 1
  0 ≤ f_b, f_c, f_o, f_r ≤ 1
  w_b, w_c, w_o, w_r ≥ 0
```

### 5.2 Factor Functions

#### 5.2.1 Behavioral Score

```
f_b(B) = 1 - min(1, (α_v · V + α_a · A + α_f · F) / max(1, N))

where:
  V = weighted_policy_violations_30d
      = Σ (severity_weight(v_i) for each violation v_i in 30 days)
      severity_weight: critical=10, high=5, medium=2, low=1
  
  A = anomalous_actions_30d (count of actions flagged by anomaly detection)
  
  F = failed_actions_30d / max(1, total_actions_30d)
  
  N = total_actions_30d
  
  α_v = 0.5  (violation weight)
  α_a = 0.3  (anomaly weight)
  α_f = 0.2  (failure weight)

Properties:
  - Monotonicity: f_b is non-increasing in V, A, F
  - Boundedness: 0 ≤ f_b ≤ 1
  - Neutral element: f_b(0, 0, 0) = 1 (perfect behavioral score)
```

#### 5.2.2 Compliance Score

```
f_c(C) = P × (1 - min(1, β_a · AF + β_d · D))

where:
  P = passed_checks / max(1, total_checks)  (pass rate)
  
  AF = audit_findings_30d (count)
  
  D = policy_drift_events_30d (count)
  
  β_a = 0.1  (audit finding penalty)
  β_d = 0.05 (drift penalty)

Properties:
  - Monotonicity: f_c is non-decreasing in P, non-increasing in AF, D
  - Boundedness: 0 ≤ f_c ≤ 1
  - Neutral element: f_c(1, 0, 0) = 1
```

#### 5.2.3 Operational Score

```
f_o(O) = U × (1 - min(1, E)) × (1 - L)

where:
  U = uptime_30d (fraction of time operational, 0 to 1)
  
  E = error_rate_30d (fraction of actions resulting in error, 0 to 1)
  
  L = latency_penalty = max(0, (latency_p99 - SLO_p99) / SLO_p99)
      (0 if within SLO, positive if exceeding)

Properties:
  - Monotonicity: f_o is non-decreasing in U, non-increasing in E and L
  - Boundedness: 0 ≤ f_o ≤ 1
  - Neutral element: f_o(1, 0, 0) = 1
```

#### 5.2.4 Reputation Score

```
f_r(R) = min(1, (γ_e · E + γ_s · S + γ_i · I) / N_max)

where:
  E = peer_endorsements (count, capped at 50)
  
  S = successful_cross_org_interactions (count, capped at 200)
  
  I = min(1, incident_free_days / 90)  (fraction of 90-day incident-free period)
  
  γ_e = 0.3  (endorsement weight)
  γ_s = 0.5  (interaction weight)
  γ_i = 0.2  (incident-free weight)
  
  N_max = γ_e · 50 + γ_s · 200 + γ_i · 1  (normalization constant)

Properties:
  - Monotonicity: f_r is non-decreasing in E, S, I
  - Boundedness: 0 ≤ f_r ≤ 1
  - Neutral element: f_r(0, 0, 0) = 0 (new agent starts with zero reputation)
```

### 5.3 Formal Properties

#### 5.3.1 Theorem: Boundedness

**Statement:** For all valid inputs, 0 ≤ T ≤ 1.

**Proof:**
- Each factor f_x ∈ [0, 1] (by construction, each is a product/composition of bounded functions)
- Each weight w_x ≥ 0 and Σw_x = 1
- Therefore T = Σ w_x · f_x ∈ [0, 1] as a convex combination of values in [0, 1] ∎

#### 5.3.2 Theorem: Monotonicity

**Statement:** T is non-increasing in negative signals (violations, anomalies, failures, audit findings, drift, errors, latency) and non-decreasing in positive signals (pass rate, uptime, endorsements, interactions, incident-free days).

**Proof:**
- Each factor function f_x is monotonic in its inputs (by construction)
- Weights are positive constants
- Therefore T, as a positive linear combination of monotonic functions, is monotonic ∎

#### 5.3.3 Theorem: Convergence

**Statement:** For an agent with constant behavior, T converges to a fixed point as the evaluation window stabilizes.

**Proof:**
- As t → ∞, the 30-day rolling window becomes dominated by the steady-state behavior
- Each factor f_x depends only on the windowed signals
- Therefore T converges to the steady-state value ∎

#### 5.3.4 Theorem: Demotion Sensitivity

**Statement:** A single critical policy violation causes T to drop below the `medium` threshold (0.41) within one evaluation period.

**Proof:**
- A critical violation contributes severity_weight = 10 to V
- f_b ≤ 1 - (0.5 × 10) / max(1, N) ≤ 1 - 5/N
- For N ≥ 9 (any non-trivial action count), f_b ≤ 1 - 5/9 ≈ 0.44
- With w_b = 0.40, the behavioral contribution is ≤ 0.40 × 0.44 ≈ 0.18
- Even with perfect other factors: T ≤ 0.18 + 0.30 + 0.20 + 0.10 = 0.78
- But the demotion trigger (critical violation → untrusted) fires independently
- Therefore the agent is demoted to `untrusted` regardless of T ∎

### 5.4 Trust Score Computation Protocol

```
compute_trust_score(agent_id, evaluation_window=30d) → TrustScore:

1. GATHER SIGNALS (from audit trail, monitoring, peer reports)
   a. Query audit events for agent_id in [now - 30d, now]
   b. Classify events into behavioral, compliance, operational, reputation
   c. Aggregate counts and metrics

2. COMPUTE FACTOR SCORES
   a. f_b = behavioral_score(violations, anomalies, failures, total_actions)
   b. f_c = compliance_score(pass_rate, audit_findings, drift_events)
   c. f_o = operational_score(uptime, error_rate, latency_p99)
   d. f_r = reputation_score(endorsements, interactions, incident_free_days)

3. COMPOSITE SCORE
   a. T = 0.40 × f_b + 0.30 × f_c + 0.20 × f_o + 0.10 × f_r
   b. Clamp T to [0, 1]

4. DETERMINE LEVEL
   a. untrusted:  T < 0.21
   b. low:       0.21 ≤ T < 0.41
   c. medium:    0.41 ≤ T < 0.61
   d. high:      0.61 ≤ T < 0.81
   e. privileged: 0.81 ≤ T ≤ 1.00

5. APPLY DEMOTION TRIGGERS (override computed level)
   a. If critical_violation in window → level = untrusted
   b. If 3+ minor_violations in window → level = min(level, current_level - 1)
   c. If anomalous_behavior_detected → level = untrusted (pending review)
   d. If cross_org_anchor_revoked → level = untrusted

6. APPLY PROMOTION RULES (if not demoted)
   a. Check minimum days at current level
   b. Check zero violations in evaluation period
   c. Check additional requirements per promotion path
   d. If all met → level = next_level

7. SIGN AND PUBLISH
   a. Sign trust score record with trust engine's key
   b. Store in audit trail
   c. Publish to trust score service
   d. Emit trust-scored audit event

8. Return TrustScore with all factors, level, and metadata
```

### 5.5 Trust Score Record Format

```json
{
  "$schema": "https://grc-claw.dev/schemas/trust-score/v2",
  "subject": "did:grc:agent:1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "score": 0.87,
  "level": "high",
  "factors": {
    "behavioral": {
      "score": 0.90,
      "weight": 0.40,
      "formula": "1 - min(1, (0.5*V + 0.3*A + 0.2*F) / max(1, N))",
      "signals": {
        "weightedViolations30d": 0,
        "anomalousActions30d": 1,
        "failedActions30d": 3,
        "totalActions30d": 342,
        "violationDetails": []
      }
    },
    "compliance": {
      "score": 0.85,
      "weight": 0.30,
      "formula": "P * (1 - min(1, 0.1*AF + 0.05*D))",
      "signals": {
        "passedChecks": 98,
        "totalChecks": 100,
        "passRate": 0.98,
        "auditFindings30d": 0,
        "policyDriftEvents30d": 0
      }
    },
    "operational": {
      "score": 0.82,
      "weight": 0.20,
      "formula": "U * (1 - min(1, E)) * (1 - L)",
      "signals": {
        "uptime30d": 0.999,
        "errorRate30d": 0.002,
        "latencyP99": 45,
        "sloP99": 100,
        "latencyPenalty": 0
      }
    },
    "reputation": {
      "score": 0.88,
      "weight": 0.10,
      "formula": "min(1, (0.3*E + 0.5*S + 0.2*I) / N_max)",
      "signals": {
        "peerEndorsements": 12,
        "successfulCrossOrgInteractions": 156,
        "incidentFreeDays": 87,
        "incidentFreeFraction": 0.967
      }
    }
  },
  "evaluation": {
    "window": "30d",
    "evaluatedAt": "2026-10-01T12:00:00Z",
    "nextEvaluation": "2026-10-01T18:00:00Z",
    "evaluationPeriod": {
      "start": "2026-09-01T12:00:00Z",
      "end": "2026-10-01T12:00:00Z"
    }
  },
  "demotionTriggers": [],
  "promotionEligibility": {
    "eligible": false,
    "reason": "Insufficient days at current level (45/60)"
  },
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-10-01T12:00:00Z",
    "verificationMethod": "did:grc:system:trust-engine#keys-1",
    "proofPurpose": "assertionMethod",
    "proofValue": "z58DAdFfa9SkqZMVPxAQvpNMz5Bw2G4Dk7GwsAqGk0bKQvJj5z3V8W5Y8X9..."
  }
}
```

---

## 6. Agent Lifecycle State Machine with Formal Verification

### 6.1 State Machine Definition

The agent lifecycle is a deterministic finite state machine (DFT) with states, transitions, and invariants.

#### 6.1.1 Formal Definition

```
M = (S, Σ, δ, s_0, F)

where:
  S = {provisioning, active, suspended, revoked, decommissioned}
  Σ = {activate, suspend, resume, revoke, decommission, rotate_keys, 
       update_metadata, trust_promote, trust_demote}
  δ: S × Σ → S  (transition function)
  s_0 = provisioning  (initial state)
  F = {decommissioned}  (accepting/final states)
```

#### 6.1.2 States

| State | Description | Allowed Operations | Entry Conditions |
|-------|-------------|-------------------|------------------|
| `provisioning` | Identity created, credentials being distributed | Key generation, metadata finalization, policy binding | Registration request received |
| `active` | Fully operational | All operations | Owner attestation verified, credentials issued |
| `suspended` | Temporarily halted | Read-only audit queries, identity verification | Suspension trigger fired |
| `revoked` | Permanently disabled | None (identity retained for audit) | Revocation request from owner or system |
| `decommissioned` | Cleaned up after revocation | None | Retention period expired |

#### 6.1.3 Transition Function δ

```
δ(provisioning, activate)           = active
δ(provisioning, revoke)             = revoked
δ(active, suspend)                  = suspended
δ(active, revoke)                   = revoked
δ(active, decommission)             = decommissioned
δ(suspended, resume)                = active
δ(suspended, revoke)               = revoked
δ(revoked, decommission)            = decommissioned

All other transitions are undefined (rejected).
```

#### 6.1.4 State Transition Diagram

```
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    ▼                                          │
              ┌───────────┐    activate    ┌──────────┐       │
              │provisioning│──────────────►│  active  │       │
              └───────────┘               └────┬─────┘       │
                    │                          │             │
                    │ revoke                   │ suspend     │
                    │                          │             │
                    ▼                          ▼             │
              ┌───────────┐    resume    ┌───────────┐      │
              │  revoked  │◄─────────────│ suspended │      │
              └─────┬─────┘    revoke     └───────────┘      │
                    │                                        │
                    │ decommission                           │
                    │ (after retention)                       │
                    ▼                                        │
              ┌───────────────┐                              │
              │decommissioned │                              │
              └───────────────┘                              │
```

### 6.2 State Invariants

The following invariants must hold at all times:

```
I1: Identity Uniqueness
    ∀ agent ∈ Agents: agent.id is unique
    
I2: Credential Validity
    agent.status ∈ {active, suspended} ⇒ 
      ∃ credential ∈ agent.credentials: 
        credential.status = "valid" ∧ 
        current_time < credential.expiresAt

I3: Policy Binding Completeness
    agent.status = "active" ⇒ 
      agent.policy_bindings ≠ ∅ ∧
      ∀ policy ∈ agent.policy_bindings: policy.status = "active"

I4: Trust Score Currency
    agent.status = "active" ⇒ 
      agent.trust_score.evaluatedAt ≥ now - max_evaluation_interval

I5: Delegation Consistency
    agent.status = "active" ⇒ 
      ∀ delegation ∈ agent.outgoing_delegations:
        delegation.status = "active" ⇒ 
          delegation.delegate.status ∈ {active, suspended}

I6: Audit Trail Continuity
    ∀ state_transition ∈ agent.history:
      state_transition.audit_event_id ∈ AuditTrail ∧
      state_transition.signature_valid = true

I7: Revocation Finality
    agent.status = "revoked" ⇒ 
      ¬∃ transition δ(revoked, _) ∈ Σ: δ(revoked, _) ≠ decommissioned

I8: Decommission Exclusivity
    agent.status = "decommissioned" ⇒ 
      agent.retention_expired = true ∧
      agent.audit_trail_archived = true
```

### 6.3 Transition Guards

Each transition has a guard condition that must be satisfied:

| Transition | Guard | Failure Action |
|------------|-------|-----------------|
| `provisioning → active` | Owner attestation signed AND credentials issued AND policies bound | Reject, stay in provisioning |
| `active → suspended` | Suspension trigger (trust demotion, anomaly, manual) | Reject, stay active |
| `suspended → active` | Suspension reason resolved AND re-verification passed | Reject, stay suspended |
| `active → revoked` | Revocation request from owner OR critical violation OR security incident | Reject, stay active |
| `suspended → revoked` | Revocation request from owner OR critical violation | Reject, stay suspended |
| `revoked → decommissioned` | Retention period expired AND audit trail archived | Reject, stay revoked |

### 6.4 Formal Verification Protocol

```
verify_lifecycle_invariants(agent) → VerificationResult:

1. STATE VALIDITY
   a. agent.status ∈ S (valid state)
   b. If agent.status = provisioning:
      - agent.credentials may be empty or partial
      - agent.policy_bindings may be empty
   c. If agent.status = active:
      - Verify I2, I3, I4, I5
   d. If agent.status = suspended:
      - Verify I2 (credentials still valid)
      - Verify suspension record exists with reason and timestamp
   e. If agent.status = revoked:
      - Verify I7 (no outgoing transitions except decommission)
      - Verify revocation record exists
   f. If agent.status = decommissioned:
      - Verify I8

2. HISTORY VERIFICATION
   a. Reconstruct state machine execution from audit trail
   b. For each transition in history:
      - Verify transition ∈ δ (defined in transition function)
      - Verify guard condition was met
      - Verify transition was signed by authorized party
      - Verify no invariant was violated after transition
   c. If any transition invalid → return HISTORY_VIOLATION

3. TEMPORAL CONSISTENCY
   a. For each transition: timestamp is monotonically increasing
   b. No future-dated transitions
   c. No transitions before agent creation

4. CRYPTOGRAPHIC INTEGRITY
   a. Verify all transition signatures
   b. Verify all credential signatures
   c. Verify all policy binding signatures

5. DELEGATION CONSISTENCY (if active)
   a. For each outgoing delegation:
      - Delegate exists and is in valid state
      - Delegation scope ⊆ agent's own capabilities
      - Delegation chain is valid (see §4)
   b. For each incoming delegation:
      - Delegator exists and was active at delegation time
      - Delegation has not been revoked

6. Return VERIFIED or list of violations
```

### 6.5 Lifecycle Event Format

Every state transition produces a signed lifecycle event:

```json
{
  "$schema": "https://grc-claw.dev/schemas/lifecycle-event/v1",
  "eventId": "evt:lifecycle:5e6f7a8b-9c0d-1e2f-3a4b-5c6d7e8f9a0b",
  "agentId": "did:grc:agent:7f3a9b2c-4d5e-6f7a-8b9c-0d1e2f3a4b5c",
  "transition": {
    "from": "active",
    "to": "suspended",
    "trigger": "trust-demotion",
    "reason": "Critical policy violation: data-exfiltration-attempt",
    "guardEvaluation": {
      "guard": "suspension-trigger",
      "result": "passed",
      "details": "Trust score dropped below 0.21 due to critical violation"
    }
  },
  "timestamp": "2026-10-01T15:30:00Z",
  "actor": "did:grc:system:trust-engine",
  "invariantsChecked": ["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8"],
  "invariantsResult": "all-passed",
  "proof": {
    "type": "Ed25519Signature2020",
    "created": "2026-10-01T15:30:00Z",
    "verificationMethod": "did:grc:system:trust-engine#keys-1",
    "proofPurpose": "assertionMethod",
    "proofValue": "z58DAdFfa9SkqZMVPxAQvpNMz5Bw2G4Dk7GwsAqGk0bKQvJj5z3V8W5Y8X9..."
  }
}
```

---

## 7. Cross-Organizational Trust Anchoring Protocol

### 7.1 Trust Anchor Architecture

Cross-organizational trust is established through a hierarchy of signed trust anchors, enabling verifiable trust across organizational boundaries.

```
┌─────────────────────────────────────────────────────────────────┐
│              Cross-Organizational Trust Hierarchy                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Root of Trust (RoT)                         │    │
│  │  • Self-signed by organization                           │    │
│  │  • Ed25519 keypair, stored in HSM                        │    │
│  │  • Published in organization's DID document              │    │
│  └──────────────────────┬──────────────────────────────────┘    │
│                         │                                        │
│         ┌───────────────┼───────────────┐                       │
│         ▼               ▼               ▼                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ Trust Anchor │ │ Trust Anchor │ │ Trust Anchor │              │
│  │  (Org A)     │ │  (Org B)     │ │  (Org C)     │              │
│  │ Cross-signed │ │ Cross-signed │ │ Cross-signed │              │
│  │ with Org B   │ │ with Org A   │ │ with Org A   │              │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘              │
│         │                │                │                       │
│         ▼                ▼                ▼                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │ Agent Trust  │ │ Agent Trust  │ │ Agent Trust  │              │
│  │ Attestation  │ │ Attestation  │ │ Attestation  │              │
│  │ (signed by   │ │ (signed by   │ │ (signed by   │              │
│  │  Trust Anchor)│ │  Trust Anchor)│ │  Trust Anchor)│              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Trust Anchor Document

```json
{
  "$schema": "https://grc-claw.dev/schemas/trust-anchor/v1",
  "id": "anchor:org-a-to-org-b",
  "type": "bilateral-trust-anchor",
  "organizations": {
    "home": {
      "did": "did:grc:org:acme-corp",
      "name": "Acme Corp",
      "trustAnchorKey": {
        "id": "did:grc:org:acme-corp#trust-anchor-1",
        "type": "Ed25519VerificationKey2020",
        "publicKeyMultibase": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
      }
    },
    "guest": {
      "did": "did:grc:org:partner-inc",
      "name": "Partner Inc",
      "trustAnchorKey": {
        "id": "did:grc:org:partner-inc#trust-anchor-1",
        "type": "Ed25519VerificationKey2020",
        "publicKeyMultibase": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doL"
      }
    }
  },
  "policy": {
    "trustMapping": {
      "method": "conservative-minimum",
      "description": "Effective trust = min(home_trust, guest_trust)",
      "rules": [
        {
          "homeLevel": "privileged",
          "guestLevel": "privileged",
          "effectiveLevel": "privileged"
        },
        {
          "homeLevel": "high",
          "guestLevel": "medium",
          "effectiveLevel": "medium"
        },
        {
          "homeLevel": "medium",
          "guestLevel": "low",
          "effectiveLevel": "low"
        }
      ]
    },
    "scope": {
      "allowedCapabilities": ["read:tickets", "read:analytics"],
      "deniedCapabilities": ["write:responses", "admin:delegate"],
      "dataClassification": ["public", "internal"],
      "maxDelegationDepth": 1
    },
    "constraints": {
      "maxInteractionsPerDay": 1000,
      "requireAuditSharing": true,
      "dataResidency": "home-organization-only"
    }
  },
  "validity": {
    "issuedAt": "2026-10-01T00:00:00Z",
    "expiresAt": "2026-12-31T23:59:59Z",
    "renewalPolicy": "automatic-30d-before-expiry"
  },
  "proofs": [
    {
      "type": "Ed25519Signature2020",
      "created": "2026-10-01T00:00:00Z",
      "verificationMethod": "did:grc:org:acme-corp#trust-anchor-1",
      "proofPurpose": "assertionMethod",
      "proofValue": "z58DAdFfa9SkqZMVPxAQvpNMz5Bw2G4Dk7GwsAqGk0bKQvJj5z3V8W5Y8X9..."
    },
    {
      "type": "Ed25519Signature2020",
      "created": "2026-10-01T00:00:00Z",
      "verificationMethod": "did:grc:org:partner-inc#trust-anchor-1",
      "proofPurpose": "assertionMethod",
      "proofValue": "z58DAdFfa9SkqZMVPxAQvpNMz5Bw2G4Dk7GwsAqGk0bKQvJj5z3V8W5Y8X9..."
    }
  ]
}
```

### 7.3 Trust Anchoring Protocol

```
establish_trust_anchor(org_a, org_b, policy) → TrustAnchor:

1. NEGOTIATION PHASE
   a. Org A and Org B agree on trust mapping policy
   b. Both organizations generate trust anchor keypairs
   c. Public keys exchanged via secure channel (out-of-band)

2. ANCHOR CREATION
   a. Create trust anchor document with both organizations' DIDs and keys
   b. Set policy (trust mapping, scope, constraints)
   c. Set validity period

3. CROSS-SIGNING
   a. Org A signs anchor with its trust anchor key → proof_A
   b. Org B signs anchor with its trust anchor key → proof_B
   c. Both signatures required for anchor to be valid

4. PUBLICATION
   a. Anchor published to both organizations' trust registries
   b. Anchor published to shared trust directory (if applicable)
   c. Audit event emitted: trust-anchor-established

5. ACTIVATION
   a. Anchor status set to "active"
   b. Both organizations' policy engines updated with anchor
   c. Agents in both organizations can now verify cross-org trust

6. Return TrustAnchor with both proofs
```

### 7.4 Cross-Organizational Trust Verification

When agent A (from Org 1) interacts with agent B (from Org 2):

```
verify_cross_org_trust(agent_a, agent_b, action, resource) → Result:

1. IDENTIFY ORGANIZATIONS
   a. org_a = resolve_organization(agent_a.owner)
   b. org_b = resolve_organization(agent_b.owner)
   c. If org_a = org_b → use intra-org trust (skip cross-org protocol)

2. RESOLVE TRUST ANCHOR
   a. anchor = lookup_trust_anchor(org_a, org_b)
   b. If no anchor → return NO_TRUST_ANCHOR
   c. If anchor expired → return ANCHOR_EXPIRED
   d. If anchor revoked → return ANCHOR_REVOKED

3. VERIFY ANCHOR SIGNATURES
   a. Verify org_a's proof on anchor
   b. Verify org_b's proof on anchor
   c. If either invalid → return ANCHOR_INVALID

4. RESOLVE TRUST LEVELS
   a. trust_a = get_trust_score(agent_a).level
   b. trust_b = get_trust_score(agent_b).level
   c. effective_level = apply_mapping(anchor.policy.trustMapping, 
                                       trust_a, trust_b)
   d. If effective_level = "untrusted" → return TRUST_INSUFFICIENT

5. SCOPE VALIDATION
   a. action ∈ anchor.policy.scope.allowedCapabilities
   b. action ∉ anchor.policy.scope.deniedCapabilities
   c. resource.dataClassification ∈ anchor.policy.scope.dataClassification
   d. delegation_depth ≤ anchor.policy.scope.maxDelegationDepth
   e. If scope violation → return SCOPE_VIOLATION

6. CONSTRAINT VALIDATION
   a. interaction_count_today ≤ anchor.policy.constraints.maxInteractionsPerDay
   b. data_residency_check(resource, anchor.policy.constraints.dataResidency)
   c. If constraint violation → return CONSTRAINT_VIOLATION

7. AUDIT SHARING
   a. If anchor.policy.constraints.requireAuditSharing:
      - Create shared audit record visible to both organizations
      - Sign with both organizations' audit keys

8. Return VALID with effective_trust_level and applied_constraints
```

### 7.5 Trust Anchor Revocation

```
revoke_trust_anchor(anchor_id, revoker, reason) → Result:

1. AUTHORIZE
   a. Verify revoker is one of the anchor's organizations
   b. Verify revoker's signature on revocation request

2. REVOKE ANCHOR
   a. Set anchor.status = "revoked"
   b. Set anchor.revocation = {
        "revokedBy": revoker,
        "reason": reason,
        "revokedAt": current_time
      }
   c. Sign revocation record

3. PROPAGATE
   a. Update both organizations' trust registries
   b. Notify all agents with active cross-org sessions under this anchor
   c. Terminate in-flight cross-org actions
   d. Emit audit events: trust-anchor-revoked

4. UPDATE DEPENDENT AGENTS
   a. For all agents with cross-org trust under this anchor:
      - Recompute effective trust (now falls back to untrusted)
      - Apply demotion triggers if necessary
   b. Emit audit events: agent-trust-recomputed

5. Return revocation_receipt
```

### 7.6 Trust Mapping Functions

| Method | Description | Formula |
|--------|-------------|---------|
| `conservative-minimum` | Use the lower trust level | effective = min(home, guest) |
| `weighted-average` | Weighted average of trust scores | effective = (w_h × home + w_g × guest) / (w_h + w_g) |
| `home-dominant` | Home organization's trust dominates | effective = home |
| `guest-dominant` | Guest organization's trust dominates | effective = guest |
| `custom-mapping` | Lookup table | effective = mapping_table[home][guest] |

### 7.7 Cross-Organizational Session Protocol

```
Agent A (Org 1)                                    Agent B (Org 2)
    │                                                    │
    │  1. Cross-org request                             │
    │     (DID, trust attestation, capability, action)  │
    │ ─────────────────────────────────────────────────► │
    │                                                    │
    │  2. Verify A's trust anchor                       │
    │     (resolve Org 1 ↔ Org 2 anchor)                │
    │                                                    │
    │  3. Compute effective trust                       │
    │     effective = min(A.trust, B.trust)             │
    │                                                    │
    │  4. Verify scope and constraints                  │
    │     (action ∈ anchor.scope, depth ≤ max)          │
    │                                                    │
    │  5. Establish session with effective trust        │
    │ ◄───────────────────────────────────────────────── │
    │     (session token, effective trust level)        │
    │                                                    │
    │  6. All actions gated by effective trust          │
    │     and anchor constraints                        │
    │                                                    │
    │  7. Shared audit trail                            │
    │     (both orgs receive audit records)             │
    │                                                    │
    │  8. Session termination                           │
    │     (trust anchor revocation or expiry)           │
    │                                                    │
```

---

## 8. Cryptographic Algorithm Specifications

### 8.1 Algorithm Suite

| Purpose | Algorithm | Key Size | Standard |
|---------|-----------|----------|----------|
| Signing (identity, delegation, trust) | Ed25519 | 256-bit | RFC 8032 |
| Signing (audit, evidence) | ECDSA P-256 | 256-bit | FIPS 186-5 |
| Hashing | SHA-256 | 256-bit | FIPS 180-4 |
| Symmetric encryption | AES-256-GCM | 256-bit | NIST SP 800-38D |
| Key agreement | X25519 | 256-bit | RFC 7748 |
| Canonicalization | JCS (RFC 8785) | — | RFC 8785 |
| Timestamping | RFC 3161 | — | RFC 3161 |

### 8.2 Key Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Key Hierarchy                              │
│                                                              │
│  Root Key (HSM, offline)                                    │
│    │                                                         │
│    ├── Organization Trust Anchor Key                         │
│    │     │                                                   │
│    │     ├── Cross-org trust anchor signatures              │
│    │     └── Agent trust attestation signatures             │
│    │                                                         │
│    ├── Agent Identity Key (Ed25519)                          │
│    │     │                                                   │
│    │     ├── DID document signatures                        │
│    │     ├── Delegation signatures                          │
│    │     ├── Capability credential signatures               │
│    │     └── Session authentication                         │
│    │                                                         │
│    ├── Session Key (X25519, ephemeral)                       │
│    │     │                                                   │
│    │     └── Encrypted communication with other agents      │
│    │                                                         │
│    └── Audit Signing Key (ECDSA P-256)                       │
│          │                                                   │
│          └── Audit event signatures                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 8.3 Key Rotation Schedule

| Key Type | Rotation Period | Rotation Method | Old Key Retention |
|----------|----------------|-----------------|-------------------|
| Root Key | 365 days | Manual, HSM ceremony | Permanent (HSM) |
| Trust Anchor Key | 180 days | Automated, dual-control | 2 rotation periods |
| Agent Identity Key | 90 days | Automated | Life of identity + 7 years |
| Session Key | Per-session | Ephemeral | None (deleted after session) |
| Audit Signing Key | 90 days | Automated | 2 rotation periods |

---

## 9. Verification API Endpoints

### 9.1 DID Resolution

```
GET /api/v1/identity/resolve/{did}
GET /api/v1/identity/verify/{did}
POST /api/v1/identity/verify-signature
```

### 9.2 Credential Verification

```
POST /api/v1/credentials/verify
POST /api/v1/credentials/verify-presentation
GET  /api/v1/credentials/status/{credential_id}
```

### 9.3 Delegation Chain Verification

```
POST /api/v1/delegations/verify-chain
GET  /api/v1/delegations/{delegation_id}/chain
POST /api/v1/delegations/{delegation_id}/revoke
```

### 9.4 Trust Score Verification

```
GET  /api/v1/trust/{agent_id}/score
POST /api/v1/trust/{agent_id}/compute
GET  /api/v1/trust/{agent_id}/history
```

### 9.5 Lifecycle Verification

```
GET  /api/v1/lifecycle/{agent_id}/state
POST /api/v1/lifecycle/{agent_id}/verify-invariants
GET  /api/v1/lifecycle/{agent_id}/history
```

### 9.6 Cross-Org Trust Verification

```
POST /api/v1/cross-org/verify-trust
GET  /api/v1/cross-org/anchors/{org_a}/{org_b}
POST /api/v1/cross-org/anchors/{anchor_id}/revoke
```

---

## 10. Compliance Mapping

### 10.1 New Controls Added

| Control | Description | Standard |
|---------|-------------|----------|
| CRYPTO-01 | All identity operations use Ed25519 signatures | NIST SP 800-63B |
| CRYPTO-02 | All audit events use ECDSA P-256 signatures | SOC 2 CC7.2 |
| CRYPTO-03 | Key rotation enforced at 90-day maximum | ISO 27001 A.10.1.2 |
| CRYPTO-04 | DID documents conform to W3C DID Core v1.0 | W3C DID Core |
| CRYPTO-05 | Credentials conform to W3C VC v1.1 | W3C VC Data Model |
| CRYPTO-06 | Delegation chains verified cryptographically | NIST SP 800-207 |
| CRYPTO-07 | Trust scores computed with formal properties | NIST AI RMF MEASURE |
| CRYPTO-08 | Lifecycle invariants formally verified | ISO 42001 A.8 |
| CRYPTO-09 | Cross-org trust anchors cross-signed | SOC 2 CC6.1 |
| CRYPTO-10 | All signatures use JCS canonicalization | RFC 8785 |

### 10.2 OWASP ASI Coverage

| ASI Risk | Cryptographic Control |
|----------|----------------------|
| ASI03 (Identity & Privilege Abuse) | DID document schema, credential verification, delegation chain verification |
| ASI07 (Insecure Inter-Agent Comms) | X25519 key agreement, session keys, mTLS |
| ASI10 (Rogue Agents) | Lifecycle state machine, trust demotion, revocation propagation |

---

## 11. Appendix A: JSON Schema References

All JSON schemas referenced in this specification are available at:
`https://grc-claw.dev/schemas/{schema-name}/v1`

| Schema | URL |
|--------|-----|
| DID Document | `/schemas/did-document/v1` |
| Capability Credential | `/schemas/capability-credential/v1` |
| Credential Presentation | `/schemas/capability-presentation/v1` |
| Delegation | `/schemas/delegation/v2` |
| Trust Score | `/schemas/trust-score/v2` |
| Lifecycle Event | `/schemas/lifecycle-event/v1` |
| Trust Anchor | `/schemas/trust-anchor/v1` |
| Cross-Org Trust | `/schemas/cross-org-trust/v1` |

---

## 12. Appendix B: Formal Notation

| Symbol | Meaning |
|--------|---------|
| `D` | DID document |
| `VC` | Verifiable credential |
| `VP` | Verifiable presentation |
| `T` | Trust score function |
| `f_b, f_c, f_o, f_r` | Factor score functions |
| `w_b, w_c, w_o, w_r` | Factor weights |
| `δ` | State transition function |
| `S` | Set of states |
| `Σ` | Set of transition labels |
| `I` | Set of invariants |
| `⊆` | Subset (scope narrowing) |
| `∈` | Element of |
| `∀` | For all |
| `∃` | There exists |
| `∧` | Logical AND |
| `∨` | Logical OR |
| `¬` | Logical NOT |
| `⇒` | Implies |

---

## 13. Appendix C: Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-10-01 | GRC_Claw Architecture Team | Initial cryptographic protocols specification |

---

*End of specification.*
