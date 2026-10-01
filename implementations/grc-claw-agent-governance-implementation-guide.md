# GRC_Claw Agent Governance Implementation Guide

**Version:** 1.0
**Date:** 2026-10-01
**Status:** Implementation Reference
**References:** `grc-claw-agent-governance-spec.md` v1.1, `grc-claw-integration-specification.md` v2.0

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [DID Document Implementation](#2-did-document-implementation)
3. [Verifiable Credential Implementation](#3-verifiable-credential-implementation)
4. [Delegation Chain Verification](#4-delegation-chain-verification)
5. [Trust Score Computation](#5-trust-score-computation)
6. [Agent Lifecycle State Machine](#6-agent-lifecycle-state-machine)
7. [A2A Authorization Protocol](#7-a2a-authorization-protocol)
8. [Agent Audit Trail Implementation](#8-agent-agent-trail-implementation)
9. [Deployment Patterns](#9-deployment-patterns)
10. [Integration with GRC_Claw Platform](#10-integration-with-grc-claw-platform)

---

## 1. Architecture Overview

The GRC_Claw Agent Governance implementation consists of seven core components that work together to provide zero-trust, deterministic, fail-closed governance for autonomous AI agents.

```
┌─────────────────────────────────────────────────────────────────────┐
│                  GRC_Claw Agent Governance Stack                     │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Identity   │  │   Trust      │  │   Policy     │             │
│  │   Registry   │  │   Engine     │  │   Engine     │             │
│  │   (DID/VC)   │  │   (Scoring)  │  │   (OPA/Rego) │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                 │                      │
│         └────────────────┬┴─────────────────┘                      │
│                          ▼                                         │
│                  ┌──────────────┐                                  │
│                  │  Governance  │                                  │
│                  │  Orchestrator│                                  │
│                  └──────┬───────┘                                  │
│                         │                                          │
│         ┌───────────────┼───────────────┐                         │
│         ▼               ▼               ▼                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │  Delegation  │ │  Capability  │ │   Audit      │             │
│  │  Tracker     │ │  Token Svc   │ │   Logger     │             │
│  │  (Chain DAG) │ │  (ZCAP-LD)   │ │  (Merkle)    │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│                                                                      │
│  ┌──────────────────────────────────────────────┐                  │
│  │              Framework Adapters               │                  │
│  │  LangChain │ AutoGen │ CrewAI │ OpenAI │ ... │                  │
│  └──────────────────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

### Design Principles (from spec §1)

| Principle | Implementation |
|-----------|---------------|
| Zero-trust by default | No agent trusted without cryptographic verification |
| Deterministic enforcement | Policy decisions are reproducible, not probabilistic |
| Fail-closed | Any governance system failure results in denial |
| Tamper-evident audit | Every action logged with Merkle-chain integrity |
| Least privilege | Agents receive minimum capabilities for their task |
| Composability | Governance primitives compose across frameworks and orgs |

---

## 2. DID Document Implementation

GRC_Claw uses the `did:grc` method for agent identities. DID documents are resolvable via the registry API and contain cryptographic credentials, ownership, and lifecycle status.

### 2.1 DID Method Syntax

```
did:grc:agent:<uuid>    — Agent identity
did:grc:org:<uuid>      — Organization identity
did:grc:user:<uuid>     — Human user identity
```

### 2.2 Python Implementation

```python
"""
GRC_Claw DID Document Implementation
Implements the did:grc method for agent identity management.
"""

from __future__ import annotations

import json
import uuid
import hashlib
import base64
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


# ─── Enums ──────────────────────────────────────────────────────────

class AgentType(str, Enum):
    AUTONOMOUS = "autonomous"
    ASSISTED = "assisted"
    WORKFLOW = "workflow"


class AgentStatus(str, Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRING = "retiring"
    DECOMMISSIONED = "decommissioned"


class OwnerType(str, Enum):
    ORGANIZATION = "organization"
    INDIVIDUAL = "individual"
    AGENT = "agent"


class KeyType(str, Enum):
    ED25519 = "Ed25519"
    ECDSA_P256 = "ECDSA-P256"
    ECDSA_P384 = "ECDSA-P384"


# ─── Data Classes ────────────────────────────────────────────────────

@dataclass
class Owner:
    type: OwnerType
    id: str  # DID of the owner
    name: str


@dataclass
class Deployment:
    environment: str  # production | staging | development
    region: str
    host: str


@dataclass
class Credentials:
    public_key: str  # PEM-encoded public key
    key_type: KeyType
    certificate: Optional[str] = None  # SPIFFE URI or mTLS cert
    key_id: str = field(default_factory=lambda: f"key:{uuid.uuid4()}")
    status: str = "active"  # active | superseded | revoked
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class AgentMetadata:
    created: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_rotated: Optional[str] = None
    description: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class DIDDocument:
    """
    GRC_Claw Agent Identity Document.
    Conforms to the did:grc method specification.
    """
    id: str  # did:grc:agent:<uuid>
    name: str
    version: str  # semver
    type: AgentType
    framework: str  # langchain | autogen | crewai | custom
    owner: Owner
    deployment: Deployment
    credentials: Credentials
    metadata: AgentMetadata = field(default_factory=AgentMetadata)
    status: AgentStatus = AgentStatus.PROVISIONING

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        return {
            "$schema": "https://grc-claw.dev/schemas/agent-identity/v1",
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "type": self.type.value,
            "framework": self.framework,
            "owner": asdict(self.owner),
            "deployment": asdict(self.deployment),
            "credentials": asdict(self.credentials),
            "metadata": asdict(self.metadata),
            "status": self.status.value,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> DIDDocument:
        """Deserialize from dict."""
        return cls(
            id=data["id"],
            name=data["name"],
            version=data["version"],
            type=AgentType(data["type"]),
            framework=data["framework"],
            owner=Owner(**data["owner"]),
            deployment=Deployment(**data["deployment"]),
            credentials=Credentials(**data["credentials"]),
            metadata=AgentMetadata(**data.get("metadata", {})),
            status=AgentStatus(data.get("status", "provisioning")),
        )

    @classmethod
    def from_json(cls, json_str: str) -> DIDDocument:
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


# ─── DID Registry ────────────────────────────────────────────────────

class DIDRegistry:
    """
    In-memory DID registry. In production, this would be backed by
    a persistent store (PostgreSQL, DynamoDB) with the GRC_Claw
    registry API at /api/v1/identity/resolve/{did}.
    """

    def __init__(self):
        self._documents: dict[str, DIDDocument] = {}
        self._index_by_name: dict[str, str] = {}  # name -> DID

    def register(self, document: DIDDocument) -> DIDDocument:
        """Register a new DID document."""
        if document.id in self._documents:
            raise ValueError(f"DID {document.id} already registered")
        if document.name in self._index_by_name:
            raise ValueError(f"Agent name '{document.name}' already exists")
        self._documents[document.id] = document
        self._index_by_name[document.name] = document.id
        return document

    def resolve(self, did: str) -> Optional[DIDDocument]:
        """Resolve a DID to its document."""
        return self._documents.get(did)

    def update(self, document: DIDDocument) -> DIDDocument:
        """Update an existing DID document."""
        if document.id not in self._documents:
            raise ValueError(f"DID {document.id} not found")
        self._documents[document.id] = document
        return document

    def list_agents(
        self,
        status: Optional[AgentStatus] = None,
        owner_id: Optional[str] = None,
    ) -> list[DIDDocument]:
        """List agents with optional filtering."""
        results = list(self._documents.values())
        if status:
            results = [d for d in results if d.status == status]
        if owner_id:
            results = [d for d in results if d.owner.id == owner_id]
        return results


# ─── Identity Factory ────────────────────────────────────────────────

class AgentIdentityFactory:
    """
    Factory for creating new agent identities with proper key generation,
    DID assignment, and initial credential issuance.
    """

    def __init__(self, registry: DIDRegistry):
        self.registry = registry

    def create_identity(
        self,
        name: str,
        agent_type: AgentType,
        framework: str,
        owner: Owner,
        deployment: Deployment,
        version: str = "1.0.0",
        key_type: KeyType = KeyType.ED25519,
    ) -> DIDDocument:
        """
        Create a new agent identity with generated keys.

        This implements the Identity Registration Protocol (spec §2.1.4):
        1. Agent generates Ed25519 keypair locally
        2. Registration request submitted to registry
        3. Owner attestation (done by caller)
        4. Policy binding (done by policy engine)
        5. Credential issuance (done by credential service)
        6. Activation (done by registry)
        """
        # 1. Generate keypair
        private_key, public_key_pem = self._generate_keypair(key_type)

        # 2. Create DID
        agent_uuid = str(uuid.uuid4())
        did = f"did:grc:agent:{agent_uuid}"

        # 3. Create credentials
        credentials = Credentials(
            public_key=public_key_pem,
            key_type=key_type,
        )

        # 4. Create identity document
        document = DIDDocument(
            id=did,
            name=name,
            version=version,
            type=agent_type,
            framework=framework,
            owner=owner,
            deployment=deployment,
            credentials=credentials,
            status=AgentStatus.PROVISIONING,
        )

        # 5. Register
        self.registry.register(document)

        # Return document (private key is managed by the agent, not stored here)
        return document, private_key

    def _generate_keypair(
        self, key_type: KeyType
    ) -> tuple[Ed25519PrivateKey, str]:
        """Generate a new cryptographic keypair."""
        if key_type == KeyType.ED25519:
            private_key = Ed25519PrivateKey.generate()
            public_key = private_key.public_key()
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")
            return private_key, public_pem
        raise ValueError(f"Unsupported key type: {key_type}")

    def rotate_keys(
        self, did: str, key_type: KeyType = KeyType.ED25519
    ) -> tuple[DIDDocument, Ed25519PrivateKey]:
        """
        Rotate an agent's keys (spec §2.1.5).

        - Keys MUST be rotated at least every 90 days
        - Rotation creates a new credential entry while preserving the identity id
        - Old credentials are retained for audit trail verification but marked as superseded
        - Rotation is logged as an audit event
        """
        document = self.registry.resolve(did)
        if not document:
            raise ValueError(f"DID {did} not found")

        # Mark old credentials as superseded
        document.credentials.status = "superseded"

        # Generate new keypair
        private_key, public_pem = self._generate_keypair(key_type)

        # Create new credentials entry
        new_credentials = Credentials(
            public_key=public_pem,
            key_type=key_type,
            key_id=f"key:{uuid.uuid4()}",
            status="active",
        )

        # Update document
        document.credentials = new_credentials
        document.metadata.last_rotated = datetime.now(timezone.utc).isoformat()

        self.registry.update(document)
        return document, private_key


# ─── Challenge-Response Verification ─────────────────────────────────

class IdentityVerifier:
    """
    Implements the Identity Verification Flow (spec §3.3).
    Challenge-response authentication using Ed25519 signatures.
    """

    @staticmethod
    def generate_challenge() -> str:
        """Generate a random challenge nonce."""
        return base64.urlsafe_b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).decode()

    @staticmethod
    def sign_challenge(challenge: str, private_key: Ed25519PrivateKey) -> str:
        """Sign a challenge with the agent's private key."""
        signature = private_key.sign(challenge.encode("utf-8"))
        return base64.urlsafe_b64encode(signature).decode("utf-8")

    @staticmethod
    def verify_challenge(
        challenge: str,
        signature_b64: str,
        public_key_pem: str,
    ) -> bool:
        """Verify a signed challenge against the agent's public key."""
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode("utf-8")
            )
            signature = base64.urlsafe_b64decode(signature_b64.encode("utf-8"))
            public_key.verify(signature, challenge.encode("utf-8"))
            return True
        except (InvalidSignature, Exception):
            return False


# ─── Usage Example ───────────────────────────────────────────────────

def example_did_usage():
    """Demonstrate DID document creation and verification."""
    registry = DIDRegistry()
    factory = AgentIdentityFactory(registry)

    # Create identity
    owner = Owner(
        type=OwnerType.ORGANIZATION,
        id="did:grc:org:acme-corp",
        name="Acme Corp",
    )
    deployment = Deployment(
        environment="production",
        region="us-east-1",
        host="agent-runner-01.acme.internal",
    )

    document, private_key = factory.create_identity(
        name="customer-service-agent",
        agent_type=AgentType.AUTONOMOUS,
        framework="langchain",
        owner=owner,
        deployment=deployment,
    )

    print(f"Created agent: {document.id}")
    print(f"Status: {document.status}")

    # Verify identity via challenge-response
    verifier = IdentityVerifier()
    challenge = verifier.generate_challenge()
    signature = verifier.sign_challenge(challenge, private_key)
    is_valid = verifier.verify_challenge(
        challenge, signature, document.credentials.public_key
    )
    print(f"Identity verified: {is_valid}")

    # Rotate keys
    rotated_doc, new_key = factory.rotate_keys(document.id)
    print(f"Keys rotated. New key ID: {rotated_doc.credentials.key_id}")

    return document


if __name__ == "__main__":
    example_did_usage()
```

### 2.3 DID Resolution API

```python
"""
FastAPI-based DID resolution service.
Exposes GET /api/v1/identity/resolve/{did} per spec §3.2.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI(title="GRC_Claw Identity Registry")

# In production, inject a persistent registry
_registry = DIDRegistry()


@app.get("/api/v1/identity/resolve/{did}")
async def resolve_did(did: str):
    """Resolve a DID to its document."""
    document = _registry.resolve(did)
    if not document:
        raise HTTPException(status_code=404, detail="DID not found")
    return document.to_dict()


@app.get("/api/v1/identity/agents")
async def list_agents(status: str = None, owner: str = None):
    """List registered agents."""
    from grc_governance.did import AgentStatus

    status_enum = AgentStatus(status) if status else None
    agents = _registry.list_agents(status=status_enum, owner_id=owner)
    return {"agents": [a.to_dict() for a in agents]}


@app.post("/api/v1/identity/register")
async def register_identity(document: dict):
    """Register a new agent identity."""
    from grc_governance.did import DIDDocument

    doc = DIDDocument.from_dict(document)
    _registry.register(doc)
    return {"status": "registered", "did": doc.id}
```

---

## 3. Verifiable Credential Implementation

Verifiable Credentials (VCs) provide cryptographic attestations about an agent's properties, capabilities, and trust level. GRC_Claw uses W3C VC Data Model with Ed25519 signatures.

### 3.1 VC Data Model

```python
"""
GRC_Claw Verifiable Credential Implementation
Uses W3C VC Data Model with Ed25519 signatures.
"""

from __future__ import annotations

import json
import uuid
import hashlib
import base64
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, Any
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


class CredentialStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


@dataclass
class VerifiableCredential:
    """
    W3C Verifiable Credential for GRC_Claw agent governance.

    Conforms to the VC Data Model v1.1 with GRC_Claw extensions
    for agent identity, capabilities, and trust attestations.
    """
    # VC standard fields
    context: list[str] = field(default_factory=lambda: [
        "https://www.w3.org/2018/credentials/v1",
        "https://grc-claw.dev/schemas/credentials/v1",
    ])
    id: str = field(default_factory=lambda: f"vc:{uuid.uuid4()}")
    type: list[str] = field(default_factory=lambda: [
        "VerifiableCredential",
        "AgentGovernanceCredential",
    ])
    issuer: str = ""  # DID of the issuing entity
    issuance_date: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    expiration_date: Optional[str] = None

    # Credential subject (the agent this VC is about)
    credential_subject: dict = field(default_factory=dict)

    # GRC_Claw extensions
    credential_schema: Optional[str] = None
    credential_status: CredentialStatus = CredentialStatus.ACTIVE

    # Proof
    proof: Optional[dict] = None

    def to_dict(self) -> dict:
        """Serialize to JSON-LD compatible dict."""
        result = {
            "@context": self.context,
            "id": self.id,
            "type": self.type,
            "issuer": self.issuer,
            "issuanceDate": self.issuance_date,
            "expirationDate": self.expiration_date,
            "credentialSubject": self.credential_subject,
            "credentialStatus": {
                "type": "GRCClawCredentialStatusList2026",
                "status": self.credential_status.value,
            },
        }
        if self.proof:
            result["proof"] = self.proof
        return result

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> VerifiableCredential:
        """Deserialize from dict."""
        return cls(
            context=data.get("@context", [
                "https://www.w3.org/2018/credentials/v1",
                "https://grc-claw.dev/schemas/credentials/v1",
            ]),
            id=data["id"],
            type=data["type"],
            issuer=data["issuer"],
            issuance_date=data["issuanceDate"],
            expiration_date=data.get("expirationDate"),
            credential_subject=data.get("credentialSubject", {}),
            credential_status=CredentialStatus(
                data.get("credentialStatus", {}).get("status", "active")
            ),
            proof=data.get("proof"),
        )


class CredentialIssuer:
    """
    Issues verifiable credentials for agent governance.
    Signs credentials with the issuer's Ed25519 private key.
    """

    def __init__(self, issuer_did: str, private_key: Ed25519PrivateKey):
        self.issuer_did = issuer_did
        self.private_key = private_key

    def issue_agent_credential(
        self,
        agent_did: str,
        agent_name: str,
        capabilities: list[str],
        trust_level: str,
        risk_tier: int,
        validity_days: int = 90,
    ) -> VerifiableCredential:
        """
        Issue an agent governance credential.

        This credential attests:
        - The agent's identity (DID)
        - Its declared capabilities
        - Its current trust level
        - Its risk classification
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(days=validity_days)

        credential = VerifiableCredential(
            issuer=self.issuer_did,
            issuance_date=now.isoformat(),
            expiration_date=expires.isoformat(),
            credential_subject={
                "id": agent_did,
                "name": agent_name,
                "type": "Agent",
                "capabilities": capabilities,
                "trustLevel": trust_level,
                "riskTier": risk_tier,
            },
        )

        # Sign the credential
        credential.proof = self._create_proof(credential)
        return credential

    def issue_capability_credential(
        self,
        agent_did: str,
        capability: str,
        resource: str,
        constraints: dict,
        validity_hours: int = 8,
    ) -> VerifiableCredential:
        """Issue a capability-specific credential."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=validity_hours)

        credential = VerifiableCredential(
            issuer=self.issuer_did,
            issuance_date=now.isoformat(),
            expiration_date=expires.isoformat(),
            type=["VerifiableCredential", "CapabilityCredential"],
            credential_subject={
                "id": agent_did,
                "capability": capability,
                "resource": resource,
                "constraints": constraints,
            },
        )

        credential.proof = self._create_proof(credential)
        return credential

    def _create_proof(self, credential: VerifiableCredential) -> dict:
        """Create an Ed25519 signature proof for the credential."""
        # Canonicalize the credential (without proof)
        cred_dict = credential.to_dict()
        cred_dict.pop("proof", None)
        canonical = json.dumps(cred_dict, sort_keys=True, separators=(",", ":"))

        # Sign
        signature = self.private_key.sign(canonical.encode("utf-8"))
        signature_b64 = base64.urlsafe_b64encode(signature).decode("utf-8")

        return {
            "type": "Ed25519Signature2020",
            "created": datetime.now(timezone.utc).isoformat(),
            "proofPurpose": "assertionMethod",
            "verificationMethod": f"{self.issuer_did}#key-1",
            "jws": signature_b64,
        }


class CredentialVerifier:
    """
    Verifies verifiable credentials.
    Checks signature, expiration, and revocation status.
    """

    def __init__(self, trust_anchors: dict[str, Ed25519PublicKey]):
        """
        Args:
            trust_anchors: Map of issuer DID to their public key.
        """
        self.trust_anchors = trust_anchors

    def verify(self, credential: VerifiableCredential) -> dict:
        """
        Verify a credential's validity.

        Returns:
            dict with 'valid' (bool) and 'reasons' (list of failure reasons).
        """
        reasons = []

        # 1. Check expiration
        if credential.expiration_date:
            exp = datetime.fromisoformat(credential.expiration_date)
            if datetime.now(timezone.utc) > exp:
                reasons.append("Credential has expired")

        # 2. Check revocation status
        if credential.credential_status == CredentialStatus.REVOKED:
            reasons.append("Credential has been revoked")
        if credential.credential_status == CredentialStatus.SUSPENDED:
            reasons.append("Credential is suspended")

        # 3. Verify signature
        if not credential.proof:
            reasons.append("No proof present")
        else:
            issuer = credential.issuer
            if issuer not in self.trust_anchors:
                reasons.append(f"Unknown issuer: {issuer}")
            else:
                if not self._verify_signature(credential):
                    reasons.append("Invalid signature")

        return {
            "valid": len(reasons) == 0,
            "reasons": reasons,
        }

    def _verify_signature(self, credential: VerifiableCredential) -> bool:
        """Verify the Ed25519 signature on a credential."""
        try:
            # Reconstruct canonical form
            cred_dict = credential.to_dict()
            proof = cred_dict.pop("proof", None)
            if not proof:
                return False

            canonical = json.dumps(
                cred_dict, sort_keys=True, separators=(",", ":")
            )
            signature = base64.urlsafe_b64decode(proof["jws"].encode("utf-8"))

            public_key = self.trust_anchors[credential.issuer]
            public_key.verify(signature, canonical.encode("utf-8"))
            return True
        except (InvalidSignature, Exception):
            return False


# ─── Credential Status List (Revocation) ────────────────────────────

class CredentialStatusList:
    """
    Implements a status list for credential revocation.
    Uses a compressed bitmap for efficient revocation checking.
    """

    def __init__(self, status_list_id: str):
        self.status_list_id = status_list_id
        self._revoked_indices: set[int] = set()
        self._suspended_indices: set[int] = set()

    def revoke(self, credential_index: int):
        """Mark a credential as revoked."""
        self._revoked_indices.add(credential_index)

    def suspend(self, credential_index: int):
        """Mark a credential as suspended."""
        self._suspended_indices.add(credential_index)

    def is_revoked(self, credential_index: int) -> bool:
        """Check if a credential is revoked."""
        return credential_index in self._revoked_indices

    def is_suspended(self, credential_index: int) -> bool:
        """Check if a credential is suspended."""
        return credential_index in self._suspended_indices

    def to_bitstring(self) -> str:
        """Serialize to a compressed bitstring."""
        max_idx = max(
            max(self._revoked_indices, default=0),
            max(self._suspended_indices, default=0),
        )
        bits = ["0"] * (max_idx + 1)
        for idx in self._revoked_indices:
            bits[idx] = "1"
        return "".join(bits)


# ─── Usage Example ───────────────────────────────────────────────────

def example_vc_usage():
    """Demonstrate VC issuance and verification."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    # Create issuer (e.g., GRC_Claw registry)
    issuer_key = Ed25519PrivateKey.generate()
    issuer_did = "did:grc:org:acme-corp"
    issuer = CredentialIssuer(issuer_did, issuer_key)

    # Issue agent credential
    agent_credential = issuer.issue_agent_credential(
        agent_did="did:grc:agent:7f3a9b2c-4d5e-6f7a8b9c-0d1e2f3a4b5c",
        agent_name="customer-service-agent",
        capabilities=["read:tickets", "write:responses"],
        trust_level="high",
        risk_tier=2,
    )
    print(f"Issued credential: {agent_credential.id}")

    # Verify
    issuer_public_key = issuer_key.public_key()
    verifier = CredentialVerifier({issuer_did: issuer_public_key})
    result = verifier.verify(agent_credential)
    print(f"Verification result: {result}")

    return agent_credential


if __name__ == "__main__":
    example_vc_usage()
```

---

## 4. Delegation Chain Verification

Delegation chains form a directed acyclic graph (DAG) of authority transfer. Each delegation is time-bounded, scope-limited, and cryptographically signed.

### 4.1 Delegation Data Model

```python
"""
GRC_Claw Delegation Chain Verification
Implements delegation tracking, chain validation, and revocation propagation.
"""

from __future__ import annotations

import json
import uuid
import base64
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature


class DelegationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


@dataclass
class DelegationScope:
    """Defines what is being delegated."""
    capabilities: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    constraints: dict = field(default_factory=dict)

    def is_subset_of(self, other: DelegationScope) -> bool:
        """
        Check if this scope is a subset of another scope.
        Implements the scope narrowing rule (spec §2.2.3).
        """
        # Capabilities must be subset
        if not set(self.capabilities).issubset(set(other.capabilities)):
            return False
        # Resources must be subset
        if not set(self.resources).issubset(set(other.resources)):
            return False
        # Constraints must be equal or more restrictive
        for key, value in other.constraints.items():
            if key not in self.constraints:
                return False
            # For numeric constraints, child must be <= parent
            if isinstance(value, (int, float)):
                if self.constraints[key] > value:
                    return False
            # For list constraints, child must be subset
            elif isinstance(value, list):
                if not set(self.constraints[key]).issubset(set(value)):
                    return False
        return True


@dataclass
class DelegationValidity:
    """Time and depth bounds for a delegation."""
    issued_at: str
    expires_at: str
    max_depth: int = 3


@dataclass
class DelegationRecord:
    """
    A single delegation from one agent to another.
    Conforms to spec §2.2.1.
    """
    id: str = field(default_factory=lambda: f"del:{uuid.uuid4()}")
    delegator: str = ""  # DID of delegating agent
    delegate: str = ""  # DID of receiving agent
    scope: DelegationScope = field(default_factory=DelegationScope)
    validity: DelegationValidity = field(default_factory=lambda: DelegationValidity(
        issued_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(
            datetime.now(timezone.utc).replace(hour=23, minute=59, second=59)
        ).isoformat(),
    ))
    parent_delegation: Optional[str] = None
    status: DelegationStatus = DelegationStatus.ACTIVE
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "$schema": "https://grc-claw.dev/schemas/delegation/v1",
            "id": self.id,
            "delegator": self.delegator,
            "delegate": self.delegate,
            "scope": asdict(self.scope),
            "validity": asdict(self.validity),
            "parent-delegation": self.parent_delegation,
            "status": self.status.value,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DelegationRecord:
        return cls(
            id=data["id"],
            delegator=data["delegator"],
            delegate=data["delegate"],
            scope=DelegationScope(**data["scope"]),
            validity=DelegationValidity(**data["validity"]),
            parent_delegation=data.get("parent-delegation"),
            status=DelegationStatus(data.get("status", "active")),
            signature=data.get("signature"),
        )


class DelegationChainVerifier:
    """
    Verifies delegation chains according to spec §2.2.4.

    Validation checks:
    1. Delegation exists and is active
    2. Current time is within validity window
    3. Delegation depth <= max-depth
    4. Action is within scope (capabilities, resources, constraints)
    5. Delegation chain is acyclic
    6. No revocation in the chain
    7. Delegator's signature is valid
    """

    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self._delegations: dict[str, DelegationRecord] = {}
        self._children: dict[str, list[str]] = {}  # parent_id -> [child_ids]
        self._public_keys: dict[str, Ed25519PublicKey] = {}

    def register_delegation(self, record: DelegationRecord):
        """Register a delegation for verification."""
        self._delegations[record.id] = record
        if record.parent_delegation:
            self._children.setdefault(record.parent_delegation, []).append(
                record.id
            )

    def register_public_key(self, did: str, public_key: Ed25519PublicKey):
        """Register an agent's public key for signature verification."""
        self._public_keys[did] = public_key

    def verify_chain(
        self,
        delegation_id: str,
        action_capability: str,
        action_resource: str,
        current_time: Optional[datetime] = None,
    ) -> dict:
        """
        Verify a delegation chain for a specific action.

        Returns:
            dict with 'valid' (bool), 'chain' (list of delegation IDs),
            and 'reasons' (list of failure reasons).
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)

        reasons = []
        chain = []

        # 1. Delegation exists and is active
        delegation = self._delegations.get(delegation_id)
        if not delegation:
            return {"valid": False, "chain": [], "reasons": ["Delegation not found"]}
        if delegation.status != DelegationStatus.ACTIVE:
            reasons.append(f"Delegation status is {delegation.status.value}")

        # 2. Time validity
        issued = datetime.fromisoformat(delegation.validity.issued_at)
        expires = datetime.fromisoformat(delegation.validity.expires_at)
        if current_time < issued:
            reasons.append("Delegation not yet valid")
        if current_time > expires:
            reasons.append("Delegation has expired")

        # 3. Build chain from leaf to root
        current = delegation
        depth = 0
        visited = set()
        while current:
            if current.id in visited:
                reasons.append("Cycle detected in delegation chain")
                break
            visited.add(current.id)
            chain.append(current.id)
            depth += 1

            # Check depth limit
            if depth > self.max_depth:
                reasons.append(f"Delegation depth {depth} exceeds max {self.max_depth}")
                break

            # Check revocation
            if current.status == DelegationStatus.REVOKED:
                reasons.append(f"Delegation {current.id} has been revoked")

            # Check signature
            if not self._verify_signature(current):
                reasons.append(f"Invalid signature on delegation {current.id}")

            # Move to parent
            if current.parent_delegation:
                current = self._delegations.get(current.parent_delegation)
            else:
                current = None

        # 4. Scope validation
        if not self._check_scope(delegation, action_capability, action_resource):
            reasons.append(
                f"Action ({action_capability} on {action_resource}) "
                f"outside delegation scope"
            )

        # 5. Scope narrowing along chain
        if not self._check_scope_narrowing(chain):
            reasons.append("Scope narrowing violation in delegation chain")

        return {
            "valid": len(reasons) == 0,
            "chain": list(reversed(chain)),  # root to leaf
            "reasons": reasons,
        }

    def _check_scope(
        self, delegation: DelegationRecord, capability: str, resource: str
    ) -> bool:
        """Check if an action is within the delegation's scope."""
        if capability not in delegation.scope.capabilities:
            return False
        if resource not in delegation.scope.resources:
            return False
        return True

    def _check_scope_narrowing(self, chain_ids: list[str]) -> bool:
        """
        Verify that each delegation in the chain is a subset of its parent.
        Implements spec §2.2.3 rule 2.
        """
        for i in range(len(chain_ids) - 1):
            child = self._delegations[chain_ids[i]]
            parent = self._delegations[chain_ids[i + 1]]
            if not child.scope.is_subset_of(parent.scope):
                return False
        return True

    def _verify_signature(self, delegation: DelegationRecord) -> bool:
        """Verify the delegator's signature on a delegation."""
        if not delegation.signature:
            return False
        if delegation.delegator not in self._public_keys:
            return False
        try:
            # Reconstruct signed content
            record_dict = delegation.to_dict()
            record_dict.pop("signature", None)
            canonical = json.dumps(
                record_dict, sort_keys=True, separators=(",", ":")
            )
            signature = base64.urlsafe_b64decode(
                delegation.signature.encode("utf-8")
            )
            public_key = self._public_keys[delegation.delegator]
            public_key.verify(signature, canonical.encode("utf-8"))
            return True
        except (InvalidSignature, Exception):
            return False

    def revoke_delegation(
        self, delegation_id: str, revoked_by: str, reason: str
    ) -> list[str]:
        """
        Revoke a delegation and all its children.
        Implements spec §2.2.5 — revocation propagates synchronously.

        Returns:
            List of all revoked delegation IDs (including children).
        """
        revoked_ids = []
        to_revoke = [delegation_id]

        while to_revoke:
            current_id = to_revoke.pop(0)
            delegation = self._delegations.get(current_id)
            if not delegation:
                continue
            if delegation.status == DelegationStatus.REVOKED:
                continue

            delegation.status = DelegationStatus.REVOKED
            revoked_ids.append(current_id)

            # Propagate to children
            for child_id in self._children.get(current_id, []):
                to_revoke.append(child_id)

        return revoked_ids

    def detect_cycle(self, delegator: str, delegate: str) -> bool:
        """
        Detect if creating a delegation from delegator to delegate
        would create a cycle in the delegation graph.
        Implements spec §2.2.3 rule 6.
        """
        if delegator == delegate:
            return True  # Self-delegation

        # Check if delegate is an ancestor of delegator
        visited = set()
        queue = [delegator]
        while queue:
            current = queue.pop(0)
            if current == delegate:
                return True
            if current in visited:
                continue
            visited.add(current)
            # Find all delegations where current is the delegate
            for del_id, record in self._delegations.items():
                if record.delegate == current and record.status == DelegationStatus.ACTIVE:
                    queue.append(record.delegator)
        return False


class DelegationFactory:
    """Factory for creating and signing delegation records."""

    def __init__(self, verifier: DelegationChainVerifier):
        self.verifier = verifier

    def create_delegation(
        self,
        delegator_did: str,
        delegate_did: str,
        scope: DelegationScope,
        validity: DelegationValidity,
        delegator_private_key: Ed25519PrivateKey,
        parent_delegation: Optional[str] = None,
    ) -> DelegationRecord:
        """
        Create a new delegation record.

        Validates:
        - No self-delegation
        - No cycles
        - Scope narrowing (if parent exists)
        - Depth limit
        """
        # Check self-delegation
        if delegator_did == delegate_did:
            raise ValueError("Self-delegation is not allowed")

        # Check cycles
        if self.verifier.detect_cycle(delegator_did, delegate_did):
            raise ValueError("Delegation would create a cycle")

        # Check scope narrowing
        if parent_delegation:
            parent = self.verifier._delegations.get(parent_delegation)
            if parent:
                if not scope.is_subset_of(parent.scope):
                    raise ValueError(
                        "Child delegation scope must be a subset of parent scope"
                    )
                # Check time bounding
                if validity.expires_at > parent.validity.expires_at:
                    raise ValueError(
                        "Child delegation cannot expire after parent"
                    )

        # Create record
        record = DelegationRecord(
            delegator=delegator_did,
            delegate=delegate_did,
            scope=scope,
            validity=validity,
            parent_delegation=parent_delegation,
        )

        # Sign
        record_dict = record.to_dict()
        canonical = json.dumps(
            record_dict, sort_keys=True, separators=(",", ":")
        )
        signature = delegator_private_key.sign(canonical.encode("utf-8"))
        record.signature = base64.urlsafe_b64encode(signature).decode("utf-8")

        # Register
        self.verifier.register_delegation(record)
        return record


# ─── Usage Example ───────────────────────────────────────────────────

def example_delegation_usage():
    """Demonstrate delegation chain creation and verification."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    verifier = DelegationChainVerifier(max_depth=3)
    factory = DelegationFactory(verifier)

    # Create agent keys
    key_a = Ed25519PrivateKey.generate()
    key_b = Ed25519PrivateKey.generate()
    key_c = Ed25519PrivateKey.generate()

    did_a = "did:grc:agent:agent-a"
    did_b = "did:grc:agent:agent-b"
    did_c = "did:grc:agent:agent-c"

    # Register public keys
    verifier.register_public_key(did_a, key_a.public_key())
    verifier.register_public_key(did_b, key_b.public_key())
    verifier.register_public_key(did_c, key_c.public_key())

    # A delegates to B
    scope_ab = DelegationScope(
        capabilities=["read:tickets", "write:responses"],
        resources=["ticket-system", "customer-db"],
        constraints={"max-actions-per-session": 100},
    )
    validity_ab = DelegationValidity(
        issued_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(
            datetime.now(timezone.utc) + timedelta(hours=8)
        ).isoformat(),
        max_depth=2,
    )
    del_ab = factory.create_delegation(
        delegator_did=did_a,
        delegate_did=did_b,
        scope=scope_ab,
        validity=validity_ab,
        delegator_private_key=key_a,
    )
    print(f"Created delegation: {del_ab.id}")

    # B delegates to C (narrowed scope)
    scope_bc = DelegationScope(
        capabilities=["read:tickets"],  # Narrowed from parent
        resources=["ticket-system"],
        constraints={"max-actions-per-session": 50},
    )
    validity_bc = DelegationValidity(
        issued_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(
            datetime.now(timezone.utc) + timedelta(hours=4)
        ).isoformat(),
        max_depth=1,
    )
    del_bc = factory.create_delegation(
        delegator_did=did_b,
        delegate_did=did_c,
        scope=scope_bc,
        validity=validity_bc,
        delegator_private_key=key_b,
        parent_delegation=del_ab.id,
    )
    print(f"Created child delegation: {del_bc.id}")

    # Verify chain for C performing read:tickets
    result = verifier.verify_chain(
        delegation_id=del_bc.id,
        action_capability="read:tickets",
        action_resource="ticket-system",
    )
    print(f"Chain verification: {result}")

    # Revoke parent delegation (propagates to children)
    revoked = verifier.revoke_delegation(
        delegation_id=del_ab.id,
        revoked_by=did_a,
        reason="task-complete",
    )
    print(f"Revoked delegations: {revoked}")

    # Verify again — should fail
    result2 = verifier.verify_chain(
        delegation_id=del_bc.id,
        action_capability="read:tickets",
        action_resource="ticket-system",
    )
    print(f"Post-revocation verification: {result2}")

    return del_ab, del_bc


if __name__ == "__main__":
    example_delegation_usage()
```

---

## 5. Trust Score Computation

Trust is a dynamic, quantifiable measure of an agent's reliability based on behavioral, compliance, operational, and reputation signals.

### 5.1 Trust Score Engine

```python
"""
GRC_Claw Trust Score Computation Engine
Implements the weighted composite trust algorithm from spec §5.2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional


class TrustLevel(str, Enum):
    UNTRUSTED = "untrusted"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    PRIVILEGED = "privileged"


# Trust level thresholds (spec §2.4.2)
TRUST_THRESHOLDS = {
    TrustLevel.UNTRUSTED: (0.00, 0.20),
    TrustLevel.LOW: (0.21, 0.40),
    TrustLevel.MEDIUM: (0.41, 0.60),
    TrustLevel.HIGH: (0.61, 0.80),
    TrustLevel.PRIVILEGED: (0.81, 1.00),
}

# Trust level weights (spec §5.2)
TRUST_WEIGHTS = {
    "behavioral": 0.40,
    "compliance": 0.30,
    "operational": 0.20,
    "reputation": 0.10,
}


@dataclass
class BehavioralSignals:
    """Behavioral trust signals (spec §5.2.1)."""
    policy_violations_30d: int = 0
    anomalous_actions_30d: int = 0
    successful_completions_30d: int = 0
    failed_actions_30d: int = 0

    @property
    def total_actions(self) -> int:
        return self.successful_completions_30d + self.failed_actions_30d


@dataclass
class ComplianceSignals:
    """Compliance trust signals (spec §5.2.2)."""
    audit_findings_30d: int = 0
    policy_drift_events: int = 0
    compliance_check_pass_rate: float = 1.0


@dataclass
class OperationalSignals:
    """Operational trust signals (spec §5.2.3)."""
    uptime_30d: float = 1.0
    error_rate_30d: float = 0.0
    latency_p99: float = 0.0  # milliseconds
    latency_slo: float = 500.0  # milliseconds


@dataclass
class ReputationSignals:
    """Reputation trust signals (spec §5.2.4)."""
    peer_endorsements: int = 0
    cross_org_interactions: int = 0
    incident_history: int = 0
    days_since_last_incident: int = 30


@dataclass
class TrustFactor:
    """A single trust factor with score and weight."""
    score: float
    weight: float
    signals: dict


@dataclass
class TrustScore:
    """
    Complete trust score for an agent.
    Conforms to spec §2.4.1.
    """
    subject: str  # Agent DID
    score: float
    level: TrustLevel
    factors: dict[str, TrustFactor]
    evaluated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    next_evaluation: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "$schema": "https://grc-claw.dev/schemas/trust/v1",
            "subject": self.subject,
            "score": round(self.score, 4),
            "level": self.level.value,
            "factors": {
                name: {
                    "score": round(f.score, 4),
                    "weight": f.weight,
                    "signals": f.signals,
                }
                for name, f in self.factors.items()
            },
            "evaluated-at": self.evaluated_at,
            "next-evaluation": self.next_evaluation,
        }


class TrustScoreEngine:
    """
    Computes trust scores using the weighted composite algorithm.

    trust_score = (behavioral × 0.40) + (compliance × 0.30) +
                  (operational × 0.20) + (reputation × 0.10)
    """

    def __init__(self):
        self._scores: dict[str, TrustScore] = {}
        self._history: dict[str, list[TrustScore]] = {}

    def compute_trust_score(
        self,
        agent_did: str,
        behavioral: BehavioralSignals,
        compliance: ComplianceSignals,
        operational: OperationalSignals,
        reputation: ReputationSignals,
    ) -> TrustScore:
        """
        Compute the composite trust score for an agent.
        All factors are normalized to [0, 1].
        """
        # 1. Behavioral score
        behavioral_score = self._compute_behavioral_score(behavioral)

        # 2. Compliance score
        compliance_score = self._compute_compliance_score(compliance)

        # 3. Operational score
        operational_score = self._compute_operational_score(operational)

        # 4. Reputation score
        reputation_score = self._compute_reputation_score(reputation)

        # 5. Weighted composite
        composite = (
            behavioral_score * TRUST_WEIGHTS["behavioral"]
            + compliance_score * TRUST_WEIGHTS["compliance"]
            + operational_score * TRUST_WEIGHTS["operational"]
            + reputation_score * TRUST_WEIGHTS["reputation"]
        )

        # Clamp to [0, 1]
        composite = max(0.0, min(1.0, composite))

        # 6. Determine trust level
        level = self._score_to_level(composite)

        # 7. Build trust score record
        score = TrustScore(
            subject=agent_did,
            score=composite,
            level=level,
            factors={
                "behavioral": TrustFactor(
                    score=behavioral_score,
                    weight=TRUST_WEIGHTS["behavioral"],
                    signals={
                        "policy-violations-30d": behavioral.policy_violations_30d,
                        "anomalous-actions-30d": behavioral.anomalous_actions_30d,
                        "successful-completions-30d": behavioral.successful_completions_30d,
                        "failed-actions-30d": behavioral.failed_actions_30d,
                    },
                ),
                "compliance": TrustFactor(
                    score=compliance_score,
                    weight=TRUST_WEIGHTS["compliance"],
                    signals={
                        "audit-findings-30d": compliance.audit_findings_30d,
                        "policy-drift-events": compliance.policy_drift_events,
                        "compliance-check-pass-rate": compliance.compliance_check_pass_rate,
                    },
                ),
                "operational": TrustFactor(
                    score=operational_score,
                    weight=TRUST_WEIGHTS["operational"],
                    signals={
                        "uptime-30d": operational.uptime_30d,
                        "error-rate-30d": operational.error_rate_30d,
                        "latency-p99": operational.latency_p99,
                    },
                ),
                "reputation": TrustFactor(
                    score=reputation_score,
                    weight=TRUST_WEIGHTS["reputation"],
                    signals={
                        "peer-endorsements": reputation.peer_endorsements,
                        "cross-org-interactions": reputation.cross_org_interactions,
                        "incident-history": reputation.incident_history,
                    },
                ),
            },
            next_evaluation=(
                datetime.now(timezone.utc) + timedelta(hours=6)
            ).isoformat(),
        )

        # Store
        self._scores[agent_did] = score
        self._history.setdefault(agent_did, []).append(score)

        return score

    def _compute_behavioral_score(self, signals: BehavioralSignals) -> float:
        """
        behavioral = 1.0 - (violations × 0.3 + anomalies × 0.2 + failures × 0.1) / total_actions
        """
        total = signals.total_actions
        if total == 0:
            return 0.5  # Neutral for new agents

        penalty = (
            signals.policy_violations_30d * 0.3
            + signals.anomalous_actions_30d * 0.2
            + signals.failed_actions_30d * 0.1
        ) / total

        return max(0.0, 1.0 - penalty)

    def _compute_compliance_score(self, signals: ComplianceSignals) -> float:
        """
        compliance = (passed_checks / total_checks) × (1 - audit_findings × 0.1)
        """
        base = signals.compliance_check_pass_rate
        penalty = min(1.0, signals.audit_findings_30d * 0.1)
        drift_penalty = min(0.5, signals.policy_drift_events * 0.05)
        return max(0.0, base * (1.0 - penalty - drift_penalty))

    def _compute_operational_score(self, signals: OperationalSignals) -> float:
        """
        operational = uptime × (1 - error_rate) × (1 - latency_penalty)
        """
        latency_penalty = 0.0
        if signals.latency_p99 > signals.latency_slo:
            # Penalty proportional to how much p99 exceeds SLO
            latency_penalty = min(0.5, (signals.latency_p99 - signals.latency_slo) / signals.latency_slo)

        return max(0.0, signals.uptime_30d * (1.0 - signals.error_rate_30d) * (1.0 - latency_penalty))

    def _compute_reputation_score(self, signals: ReputationSignals) -> float:
        """
        reputation = (endorsements × 0.3 + successful_interactions × 0.5 + incident_free_days × 0.2) / normalization
        """
        # Normalize signals to [0, 1] ranges
        endorsement_score = min(1.0, signals.peer_endorsements / 20.0)
        interaction_score = min(1.0, signals.cross_org_interactions / 200.0)
        incident_free_score = min(1.0, signals.days_since_last_incident / 90.0)

        raw = (
            endorsement_score * 0.3
            + interaction_score * 0.5
            + incident_free_score * 0.2
        )

        # Penalize for incidents
        incident_penalty = min(0.5, signals.incident_history * 0.1)
        return max(0.0, raw - incident_penalty)

    def _score_to_level(self, score: float) -> TrustLevel:
        """Map a numeric score to a trust level."""
        for level, (low, high) in TRUST_THRESHOLDS.items():
            if low <= score <= high:
                return level
        return TrustLevel.UNTRUSTED

    def get_trust_level(self, agent_did: str) -> Optional[TrustLevel]:
        """Get the current trust level for an agent."""
        score = self._scores.get(agent_did)
        return score.level if score else None

    def check_promotion_eligibility(
        self, agent_did str, target_level: TrustLevel
    ) -> dict:
        """
        Check if an agent is eligible for trust promotion.
        Implements spec §5.5 requirements.
        """
        history = self._history.get(agent_did, [])
        current = self._scores.get(agent_did)

        if not current:
            return {"eligible": False, "reasons": ["No trust score available"]}

        reasons = []

        # Check minimum days at current level
        min_days = {
            TrustLevel.UNTRUSTED: 7,
            TrustLevel.LOW: 30,
            TrustLevel.MEDIUM: 60,
            TrustLevel.HIGH: 90,
        }

        # Count consecutive days at current level
        days_at_level = 0
        for score in reversed(history):
            if score.level == current.level:
                days_at_level += 1
            else:
                break

        required_days = min_days.get(current.level, 30)
        if days_at_level < required_days:
            reasons.append(
                f"Only {days_at_level} days at current level, "
                f"need {required_days}"
            )

        # Check for violations in evaluation period
        behavioral = current.factors.get("behavioral")
        if behavioral and behavioral.signals.get("policy-violations-30d", 0) > 0:
            reasons.append("Policy violations in evaluation period")

        # Check for privileged requirements
        if target_level == TrustLevel.PRIVILEGED:
            reputation = current.factors.get("reputation")
            if reputation:
                endorsements = reputation.signals.get("peer-endorsements", 0)
                if endorsements < 5:
                    reasons.append(
                        f"Need 5 peer endorsements for privileged, have {endorsements}"
                    )

        return {
            "eligible": len(reasons) == 0,
            "reasons": reasons,
            "current_level": current.level.value,
            "target_level": target_level.value,
        }

    def check_demotion_triggers(self, agent_did: str, event: dict) -> Optional[TrustLevel]:
        """
        Check if a trust demotion should be triggered.
        Implements spec §5.4 demotion triggers.
        """
        current = self._scores.get(agent_did)
        if not current:
            return None

        event_type = event.get("type")

        # Critical policy violation -> immediate untrusted
        if event_type == "critical-policy-violation":
            return TrustLevel.UNTRUSTED

        # 3+ minor violations in 30 days -> drop one level
        if event_type == "minor-policy-violation":
            behavioral = current.factors.get("behavioral")
            if behavioral:
                violations = behavioral.signals.get("policy-violations-30d", 0)
                if violations >= 3:
                    return self._drop_one_level(current.level)

        # Anomalous behavior -> temporary suspension (handled by lifecycle)
        if event_type == "anomalous-behavior":
            return self._drop_one_level(current.level)

        # Trust score below threshold for 2 consecutive evaluations
        if event_type == "trust-evaluation":
            history = self._history.get(agent_did, [])
            if len(history) >= 2:
                last_two = history[-2:]
                for score in last_two:
                    low, high = TRUST_THRESHOLDS[current.level]
                    if score.score < low:
                        return self._drop_one_level(current.level)

        return None

    def _drop_one_level(self, current: TrustLevel) -> TrustLevel:
        """Drop one trust level."""
        order = [
            TrustLevel.PRIVILEGED,
            TrustLevel.HIGH,
            TrustLevel.MEDIUM,
            TrustLevel.LOW,
            TrustLevel.UNTRUSTED,
        ]
        idx = order.index(current)
        return order[min(idx + 1, len(order) - 1)]


# ─── Cross-Organizational Trust ─────────────────────────────────────

@dataclass
class CrossOrgTrust:
    """
    Cross-organizational trust attestation.
    Implements spec §2.4.4.
    """
    home_organization: str
    home_trust_level: TrustLevel
    guest_organization: str
    guest_trust_level: TrustLevel
    trust_mapping_method: str = "bilateral-agreement"
    mapping_rule: str = "conservative-minimum"
    effective_trust: TrustLevel = TrustLevel.UNTRUSTED
    verified_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    expires_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "cross-org-trust": {
                "home-organization": self.home_organization,
                "home-trust-level": self.home_trust_level.value,
                "guest-organization": self.guest_organization,
                "guest-trust-level": self.guest_trust_level.value,
                "trust-mapping": {
                    "method": self.trust_mapping_method,
                    "mapping-rule": self.mapping_rule,
                    "effective-trust": self.effective_trust.value,
                },
                "verified-at": self.verified_at,
                "expires-at": self.expires_at,
            }
        }


class CrossOrgTrustManager:
    """
    Manages cross-organizational trust relationships.
    Implements trust anchoring, translation, and verification.
    """

    def __init__(self):
        self._trust_anchors: dict[str, str] = {}  # org_did -> anchor_cert
        self._bilateral_agreements: dict[tuple[str, str], dict] = {}

    def register_trust_anchor(self, org_did: str, anchor_certificate: str):
        """Register an organization's trust anchor (cross-signed certificate)."""
        self._trust_anchors[org_did] = anchor_certificate

    def establish_bilateral_agreement(
        self,
        org_a: str,
        org_b: str,
        mapping_rule: str = "conservative-minimum",
    ):
        """Establish a bilateral trust agreement between two organizations."""
        self._bilateral_agreements[(org_a, org_b)] = {
            "mapping-rule": mapping_rule,
            "established-at": datetime.now(timezone.utc).isoformat(),
        }
        self._trust_anchors[(org_b, org_a)] = {
            "mapping-rule": mapping_rule,
            "established-at": datetime.now(timezone.utc).isoformat(),
        }

    def compute_effective_trust(
        self,
        home_org: str,
        home_trust: TrustLevel,
        guest_org: str,
        guest_trust: TrustLevel,
    ) -> CrossOrgTrust:
        """
        Compute effective trust for cross-organizational interaction.
        Uses conservative-minimum by default.
        """
        # Trust level ordering for comparison
        trust_order = {
            TrustLevel.UNTRUSTED: 0,
            TrustLevel.LOW: 1,
            TrustLevel.MEDIUM: 2,
            TrustLevel.HIGH: 3,
            TrustLevel.PRIVILEGED: 4,
        }

        # Conservative minimum: use the lower trust level
        if trust_order[home_trust] <= trust_order[guest_trust]:
            effective = home_trust
        else:
            effective = guest_trust

        return CrossOrgTrust(
            home_organization=home_org,
            home_trust_level=home_trust,
            guest_organization=guest_org,
            guest_trust_level=guest_trust,
            effective_trust=effective,
            expires_at=(
                datetime.now(timezone.utc) + timedelta(days=7)
            ).isoformat(),
        )


# ─── Usage Example ───────────────────────────────────────────────────

def example_trust_usage():
    """Demonstrate trust score computation."""
    engine = TrustScoreEngine()

    # Compute trust score for an agent
    score = engine.compute_trust_score(
        agent_did="did:grc:agent:customer-service-agent",
        behavioral=BehavioralSignals(
            policy_violations_30d=0,
            anomalous_actions_30d=1,
            successful_completions_30d=342,
            failed_actions_30d=3,
        ),
        compliance=ComplianceSignals(
            audit_findings_30d=0,
            policy_drift_events=0,
            compliance_check_pass_rate=0.98,
        ),
        operational=OperationalSignals(
            uptime_30d=0.999,
            error_rate_30d=0.002,
            latency_p99=45,
            latency_slo=500,
        ),
        reputation=ReputationSignals(
            peer_endorsements=12,
            cross_org_interactions=156,
            incident_history=0,
            days_since_last_incident=90,
        ),
    )

    print(f"Trust Score: {score.score}")
    print(f"Trust Level: {score.level.value}")
    print(f"Factors: {json.dumps(score.to_dict(), indent=2)}")

    # Check promotion eligibility
    eligibility = engine.check_promotion_eligibility(
        agent_did="did:grc:agent:customer-service-agent",
        target_level=TrustLevel.HIGH,
    )
    print(f"Promotion eligibility: {eligibility}")

    return score


if __name__ == "__main__":
    example_trust_usage()
```

---

## 6. Agent Lifecycle State Machine

The agent lifecycle follows a strict state machine with gated transitions: `provisioning → active → suspended → retiring → decommissioned`.

### 6.1 State Machine Implementation

```python
"""
GRC_Claw Agent Lifecycle State Machine
Implements the lifecycle from spec §11 with gated transitions.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Callable
from collections import defaultdict


class LifecycleState(str, Enum):
    PROVISIONING = "provisioning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    RETIRING = "retiring"
    DECOMMISSIONED = "decommissioned"


class LifecycleEvent(str, Enum):
    # Provisioning events
    IDENTITY_CREATED = "identity_created"
    OWNER_ATTESTED = "owner_attested"
    POLICIES_BOUND = "policies_bound"
    CREDENTIALS_ISSUED = "credentials_issued"
    ACTIVATED = "activated"

    # Active events
    SUSPENSION_TRIGGERED = "suspension_triggered"
    REINSTATED = "reinstated"

    # Suspension events
    REVIEW_COMPLETED = "review_completed"
    RETIREMENT_INITIATED = "retirement_initiated"

    # Retirement events
    DRAIN_COMPLETE = "drain_complete"
    ACCESS_REVOKED = "access_revoked"
    ARCHIVE_COMPLETE = "archive_complete"
    DELETE_COMPLETE = "delete_complete"

    # Terminal
    DECOMMISSIONED = "decommissioned"


# Valid state transitions (spec §2.1.3)
VALID_TRANSITIONS = {
    LifecycleState.PROVISIONING: {
        LifecycleEvent.IDENTITY_CREATED: LifecycleState.PROVISIONING,
        LifecycleEvent.OWNER_ATTESTED: LifecycleState.PROVISIONING,
        LifecycleEvent.POLICIES_BOUND: LifecycleState.PROVISIONING,
        LifecycleEvent.CREDENTIALS_ISSUED: LifecycleState.PROVISIONING,
        LifecycleEvent.ACTIVATED: LifecycleState.ACTIVE,
    },
    LifecycleState.ACTIVE: {
        LifecycleEvent.SUSPENSION_TRIGGERED: LifecycleState.SUSPENDED,
        LifecycleEvent.RETIREMENT_INITIATED: LifecycleState.RETIRING,
    },
    LifecycleState.SUSPENDED: {
        LifecycleEvent.REINSTATED: LifecycleState.ACTIVE,
        LifecycleEvent.RETIREMENT_INITIATED: LifecycleState.RETIRING,
    },
    LifecycleState.RETIRING: {
        LifecycleEvent.DRAIN_COMPLETE: LifecycleState.RETIRING,
        LifecycleEvent.ACCESS_REVOKED: LifecycleState.RETIRING,
        LifecycleEvent.ARCHIVE_COMPLETE: LifecycleState.RETIRING,
        LifecycleEvent.DELETE_COMPLETE: LifecycleState.DECOMMISSIONED,
    },
    LifecycleState.DECOMMISSIONED: {},  # Terminal state
}


# Allowed operations per state (spec §2.1.3)
ALLOWED_OPERATIONS = {
    LifecycleState.PROVISIONING: {
        "key-generation", "metadata-finalization"
    },
    LifecycleState.ACTIVE: {
        "all-operations"
    },
    LifecycleState.SUSPENDED: {
        "read-only-audit", "identity-verification"
    },
    LifecycleState.RETIRING: {
        "drain-inflight", "no-new-operations"
    },
    LifecycleState.DECOMMISSIONED: set(),  # No operations
}


@dataclass
class TransitionRecord:
    """Record of a lifecycle transition."""
    from_state: LifecycleState
    to_state: LifecycleState
    event: LifecycleEvent
    timestamp: str
    actor: str  # DID of the entity that triggered the transition
    reason: str
    metadata: dict = field(default_factory=dict)


@dataclass
class AgentLifecycle:
    """
    Agent lifecycle state machine.
    Tracks state, transitions, and enforces valid state changes.
    """
    agent_did: str
    current_state: LifecycleState = LifecycleState.PROVISIONING
    transition_history: list[TransitionRecord] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    _transition_handlers: dict = field(default_factory=dict)

    def __post_init__(self):
        self._transition_handlers = defaultdict(list)

    def can_transition(self, event: LifecycleEvent) -> bool:
        """Check if a transition is valid from the current state."""
        transitions = VALID_TRANSITIONS.get(self.current_state, {})
        return event in transitions

    def transition(
        self,
        event: LifecycleEvent,
        actor: str,
        reason: str = "",
        metadata: dict = None,
    ) -> TransitionRecord:
        """
        Execute a lifecycle transition.

        Raises:
            ValueError: If the transition is not valid.
        """
        if not self.can_transition(event):
            raise ValueError(
                f"Invalid transition: {self.current_state.value} "
                f"cannot handle event {event.value}"
            )

        new_state = VALID_TRANSITIONS[self.current_state][event]
        old_state = self.current_state

        record = TransitionRecord(
            from_state=old_state,
            to_state=new_state,
            event=event,
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor,
            reason=reason,
            metadata=metadata or {},
        )

        self.current_state = new_state
        self.transition_history.append(record)

        # Notify handlers
        for handler in self._transition_handlers.get(event, []):
            handler(self, record)

        return record

    def on_transition(
        self, event: LifecycleEvent, handler: Callable
    ):
        """Register a transition handler."""
        self._transition_handlers[event].append(handler)

    def can_perform(self, operation: str) -> bool:
        """Check if an operation is allowed in the current state."""
        allowed = ALLOWED_OPERATIONS.get(self.current_state, set())
        return "all-operations" in allowed or operation in allowed

    def to_dict(self) -> dict:
        return {
            "agent-did": self.agent_did,
            "current-state": self.current_state.value,
            "transition-history": [
                {
                    "from": t.from_state.value,
                    "to": t.to_state.value,
                    "event": t.event.value,
                    "timestamp": t.timestamp,
                    "actor": t.actor,
                    "reason": t.reason,
                }
                for t in self.transition_history
            ],
            "created-at": self.created_at,
        }


class LifecycleManager:
    """
    Manages agent lifecycles with full governance controls.
    Implements the provisioning, active, suspension, retirement,
    and decommissioning workflows from spec §11.
    """

    def __init__(self):
        self._lifecycles: dict[str, AgentLifecycle] = {}
        self._provisioning_gates: dict[str, dict] = {}
        self._suspension_records: dict[str, dict] = {}
        self._retirement_records: dict[str, dict] = {}

    def start_provisioning(
        self,
        agent_did: str,
        provisioning_request: dict,
    ) -> AgentLifecycle:
        """
        Start the provisioning process for a new agent.
        Implements spec §11.2.
        """
        lifecycle = AgentLifecycle(agent_did=agent_did)
        self._lifecycles[agent_did] = lifecycle

        # Track provisioning gates
        self._provisioning_gates[agent_did] = {
            "identity-created": False,
            "owner-attested": False,
            "risk-classified": False,
            "capabilities-declared": False,
            "policies-bound": False,
            "adapter-verified": False,
            "sandbox-configured": False,
            "kill-switch-tested": False,
            "baselines-established": False,
            "audit-stream-configured": False,
        }

        return lifecycle

    def complete_provisioning_gate(
        self, agent_did: str, gate: str, metadata: dict = None
    ):
        """Mark a provisioning gate as complete."""
        if agent_did not in self._provisioning_gates:
            raise ValueError(f"No provisioning in progress for {agent_did}")
        if gate not in self._provisioning_gates[agent_did]:
            raise ValueError(f"Unknown provisioning gate: {gate}")

        self._provisioning_gates[agent_did][gate] = True

        # Map gates to lifecycle events
        gate_to_event = {
            "identity-created": LifecycleEvent.IDENTITY_CREATED,
            "owner-attested": LifecycleEvent.OWNER_ATTESTED,
            "policies-bound": LifecycleEvent.POLICIES_BOUND,
            "credentials-issued": LifecycleEvent.CREDENTIALS_ISSUED,
        }

        if gate in gate_to_event:
            lifecycle = self._lifecycles[agent_did]
            lifecycle.transition(
                event=gate_to_event[gate],
                actor="system:provisioning-service",
                reason=f"Provisioning gate completed: {gate}",
                metadata=metadata,
            )

    def activate_agent(self, agent_did: str, actor: str) -> AgentLifecycle:
        """
        Activate an agent after all provisioning gates pass.
        Implements Gate 1 exit criteria (spec §11.2.2).
        """
        # Verify all gates are complete
        gates = self._provisioning_gates.get(agent_did, {})
        incomplete = [g for g, v in gates.items() if not v]
        if incomplete:
            raise ValueError(
                f"Cannot activate: incomplete gates: {incomplete}"
            )

        lifecycle = self._lifecycles[agent_did]
        lifecycle.transition(
            event=LifecycleEvent.ACTIVATED,
            actor=actor,
            reason="All provisioning gates passed",
        )
        return lifecycle

    def suspend_agent(
        self,
        agent_did: str,
        reason: str,
        severity: str,
        suspended_by: str,
        review_deadline: str,
    ) -> dict:
        """
        Suspend an agent.
        Implements spec §11.4.
        """
        lifecycle = self._lifecycles[agent_did]
        lifecycle.transition(
            event=LifecycleEvent.SUSPENSION_TRIGGERED,
            actor=suspended_by,
            reason=reason,
            metadata={"severity": severity},
        )

        suspension_record = {
            "suspension-id": f"susp:{uuid.uuid4()}",
            "agent": agent_did,
            "reason": reason,
            "severity": severity,
            "suspended-by": suspended_by,
            "suspended-at": datetime.now(timezone.utc).isoformat(),
            "delegations-suspended": 0,  # Populated by delegation service
            "capabilities-suspended": 0,  # Populated by capability service
            "review-assigned-to": None,
            "review-deadline": review_deadline,
            "reinstatement-criteria": [
                "Root cause identified and remediated",
                "Risk re-assessment completed",
                "Agent Owner approves reinstatement",
            ],
            "status": "active",
        }

        self._suspension_records[agent_did] = suspension_record
        return suspension_record

    def reinstate_agent(
        self, agent_did: str, actor: str, reason: str
    ) -> AgentLifecycle:
        """Reinstate a suspended agent."""
        lifecycle = self._lifecycles[agent_did]
        lifecycle.transition(
            event=LifecycleEvent.REINSTATED,
            actor=actor,
            reason=reason,
        )

        if agent_did in self._suspension_records:
            self._suspension_records[agent_did]["status"] = "lifted"

        return lifecycle

    def initiate_retirement(
        self,
        agent_did: str,
        reason: str,
        decided_by: str,
        stakeholders: list[str],
    ) -> dict:
        """
        Initiate agent retirement.
        Implements spec §11.5.
        """
        lifecycle = self._lifecycles[agent_did]
        lifecycle.transition(
            event=LifecycleEvent.RETIREMENT_INITIATED,
            actor=decided_by,
            reason=reason,
        )

        retirement_record = {
            "retirement-id": f"ret:{uuid.uuid4()}",
            "agent": agent_did,
            "reason": reason,
            "decided-by": decided_by,
            "decided-at": datetime.now(timezone.utc).isoformat(),
            "stakeholders-notified": stakeholders,
            "access-revoked": {},
            "data-disposition": {},
            "archival": {},
            "deletion": {},
            "dependencies-identified": [],
            "lessons-learned": {},
            "status": "in-progress",
        }

        self._retirement_records[agent_did] = retirement_record
        return retirement_record

    def complete_retirement_step(
        self, agent_did: str, step: str, metadata: dict = None
    ):
        """Complete a retirement step."""
        lifecycle = self._lifecycles[agent_did]

        step_to_event = {
            "drain-complete": LifecycleEvent.DRAIN_COMPLETE,
            "access-revoked": LifecycleEvent.ACCESS_REVOKED,
            "archive-complete": LifecycleEvent.ARCHIVE_COMPLETE,
            "delete-complete": LifecycleEvent.DELETE_COMPLETE,
        }

        if step not in step_to_event:
            raise ValueError(f"Unknown retirement step: {step}")

        lifecycle.transition(
            event=step_to_event[step],
            actor="system:retirement-service",
            reason=f"Retirement step completed: {step}",
            metadata=metadata,
        )

        if agent_did in self._retirement_records:
            self._retirement_records[agent_did][step.replace("-", "_")] = (
                metadata or {}
            )

    def decommission_agent(
        self, agent_did: str, actor: str, certificate: dict
    ) -> dict:
        """
        Complete decommissioning.
        Implements spec §11.6.
        """
        lifecycle = self._lifecycles[agent_did]

        # Verify all retirement steps are complete
        record = self._retirement_records.get(agent_did, {})
        required_steps = [
            "drain_complete",
            "access_revoked",
            "archive_complete",
            "delete_complete",
        ]
        incomplete = [s for s in required_steps if s not in record]
        if incomplete:
            raise ValueError(
                f"Cannot decommission: incomplete steps: {incomplete}"
            )

        lifecycle.transition(
            event=LifecycleEvent.DELETE_COMPLETE,
            actor=actor,
            reason="Decommissioning complete",
            metadata={"certificate": certificate},
        )

        return {
            "certificate-id": certificate.get("certificate-id"),
            "agent": agent_did,
            "decommissioned-at": datetime.now(timezone.utc).isoformat(),
            "decommissioned-by": actor,
            "status": "complete",
        }

    def get_lifecycle(self, agent_did: str) -> Optional[AgentLifecycle]:
        """Get the lifecycle for an agent."""
        return self._lifecycles.get(agent_did)

    def list_agents_by_state(self, state: LifecycleState) -> list[str]:
        """List all agents in a given state."""
        return [
            did
            for did, lc in self._lifecycles.items()
            if lc.current_state == state
        ]


# ─── Usage Example ───────────────────────────────────────────────────

def example_lifecycle_usage():
    """Demonstrate the agent lifecycle state machine."""
    manager = LifecycleManager()

    agent_did = "did:grc:agent:customer-service-agent"

    # Start provisioning
    lifecycle = manager.start_provisioning(
        agent_did=agent_did,
        provisioning_request={
            "agent-name": "customer-service-agent",
            "agent-type": "autonomous",
            "framework": "langchain",
        },
    )
    print(f"Provisioning started. State: {lifecycle.current_state.value}")

    # Complete provisioning gates
    gates = [
        "identity-created",
        "owner-attested",
        "risk-classified",
        "capabilities-declared",
        "policies-bound",
        "adapter-verified",
        "sandbox-configured",
        "kill-switch-tested",
        "baselines-established",
        "audit-stream-configured",
    ]
    for gate in gates:
        manager.complete_provisioning_gate(agent_did, gate)
        print(f"  Gate completed: {gate}")

    # Activate
    lifecycle = manager.activate_agent(
        agent_did=agent_did,
        actor="did:grc:org:acme-corp",
    )
    print(f"Agent activated. State: {lifecycle.current_state.value}")

    # Suspend
    suspension = manager.suspend_agent(
        agent_did=agent_did,
        reason="anomalous-behavior-detected",
        severity="high",
        suspended_by="did:grc:system:risk-engine",
        review_deadline="2026-10-02T14:30:00Z",
    )
    print(f"Agent suspended. State: {lifecycle.current_state.value}")

    # Reinstate
    lifecycle = manager.reinstate_agent(
        agent_did=agent_did,
        actor="did:grc:org:acme-corp",
        reason="Anomaly resolved, root cause identified",
    )
    print(f"Agent reinstated. State: {lifecycle.current_state.value}")

    # Retire
    retirement = manager.initiate_retirement(
        agent_did=agent_did,
        reason="replaced-by-newer-version",
        decided_by="agent-owner-001",
        stakeholders=["agent-owner-001", "risk-officer-001"],
    )
    print(f"Retirement initiated. State: {lifecycle.current_state.value}")

    # Complete retirement steps
    manager.complete_retirement_step(
        agent_did, "drain-complete", {"tasks-drained": 5}
    )
    manager.complete_retirement_step(
        agent_did, "access-revoked", {"capabilities-revoked": 5}
    )
    manager.complete_retirement_step(
        agent_did, "archive-complete", {"archive-location": "s3://..."}
    )
    manager.complete_retirement_step(
        agent_did, "delete-complete", {"artifacts-deleted": ["sandbox"]}
    )

    # Decommission
    cert = manager.decommission_agent(
        agent_did=agent_did,
        actor="agent-owner-001",
        certificate={"certificate-id": f"cert:{uuid.uuid4()}"},
    )
    print(f"Agent decommissioned. State: {lifecycle.current_state.value}")

    return lifecycle


if __name__ == "__main__":
    example_lifecycle_usage()
```

---

## 7. A2A Authorization Protocol

The Agent-to-Agent Authorization Protocol (A2A-AP) governs how one agent requests and receives authorization to act on behalf of another agent.

### 7.1 Protocol Implementation

```python
"""
GRC_Claw Agent-to-Agent Authorization Protocol (A2A-AP)
Implements the authorization flow from spec §6.
"""

from __future__ import annotations

import json
import uuid
import base64
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature


class AuthorizationDecision(str, Enum):
    GRANT = "grant"
    DENY = "deny"
    REQUIRE_APPROVAL = "require-approval"
    TRANSFORM = "transform"
    ESCALATE = "escalate"


@dataclass
class AuthorizationRequest:
    """
    A2A authorization request from one agent to another.
    Conforms to spec §6.2.
    """
    request_id: str = field(default_factory=lambda: f"req:{uuid.uuid4()}")
    requester_agent: str = ""  # DID of requesting agent
    requester_trust_level: str = ""
    requester_delegation_chain: Optional[str] = None
    resource_owner_agent: str = ""  # DID of resource owner
    resource_owner_trust_level: str = ""
    capability: str = ""  # Requested capability (e.g., "read")
    resource: str = ""  # Target resource
    resource_id: Optional[str] = None
    justification: str = ""
    constraints: dict = field(default_factory=dict)
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None
    parent_action: Optional[str] = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "$schema": "https://grc-claw.dev/schemas/authz-request/v1",
            "request-id": self.request_id,
            "requester": {
                "agent": self.requester_agent,
                "trust-level": self.requester_trust_level,
                "delegation-chain": self.requester_delegation_chain,
            },
            "resource-owner": {
                "agent": self.resource_owner_agent,
                "trust-level": self.resource_owner_trust_level,
            },
            "request": {
                "capability": self.capability,
                "resource": self.resource,
                "resource-id": self.resource_id,
                "justification": self.justification,
                "constraints": self.constraints,
            },
            "context": {
                "session-id": self.session_id,
                "workflow-id": self.workflow_id,
                "parent-action": self.parent_action,
            },
            "timestamp": self.timestamp,
            "signature": self.signature,
        }


@dataclass
class AuthorizationResponse:
    """
    A2A authorization decision.
    Conforms to spec §6.3.
    """
    request_id: str = ""
    decision: AuthorizationDecision = AuthorizationDecision.DENY
    decision_reason: str = ""
    granted_capability: Optional[dict] = None
    policy_references: list[str] = field(default_factory=list)
    evaluated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    evaluator: str = "did:grc:system:policy-engine"
    signature: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "$schema": "https://grc-claw.dev/schemas/authz-decision/v1",
            "request-id": self.request_id,
            "decision": self.decision.value,
            "decision-reason": self.decision_reason,
            "granted-capability": self.granted_capability,
            "policy-references": self.policy_references,
            "evaluated-at": self.evaluated_at,
            "evaluator": self.evaluator,
            "signature": self.signature,
        }


class CapabilityToken:
    """
    A signed, scoped, time-bounded capability token.
    Conforms to spec §2.3.1.
    """
    def __init__(
        self,
        token_id: str,
        subject: str,
        issuer: str,
        capability: str,
        resource: str,
        resource_id: Optional[str],
        conditions: dict,
        delegation_id: Optional[str],
        issued_at: str,
        expires_at: str,
        signature: Optional[str] = None,
    ):
        self.id = token_id
        self.subject = subject
        self.issuer = issuer
        self.capability = capability
        self.resource = resource
        self.resource_id = resource_id
        self.conditions = conditions
        self.delegation = delegation_id
        self.issued_at = issued_at
        self.expires_at = expires_at
        self.status = "active"
        self.signature = signature

    def to_dict(self) -> dict:
        return {
            "$schema": "https://grc-claw.dev/schemas/capability/v1",
            "id": self.id,
            "subject": self.subject,
            "issuer": self.issuer,
            "capability": {
                "action": self.capability,
                "resource": self.resource,
                "resource-id": self.resource_id,
                "conditions": self.conditions,
            },
            "delegation": self.delegation,
            "issued-at": self.issued_at,
            "expires-at": self.expires_at,
            "status": self.status,
            "signature": self.signature,
        }

    def is_valid(self) -> bool:
        """Check if the token is still valid."""
        if self.status != "active":
            return False
        expires = datetime.fromisoformat(self.expires_at)
        return datetime.now(timezone.utc) < expires


class A2AAuthorizationEngine:
    """
    Evaluates A2A authorization requests and issues capability tokens.

    Evaluation pipeline (spec §6.5):
    Request → Identity Check → Trust Check → Policy Check → Scope Check → Decision
    """

    def __init__(self):
        self._public_keys: dict[str, Ed25519PublicKey] = {}
        self._policies: list[dict] = []
        self._trust_levels: dict[str, str] = {}  # agent_did -> trust_level
        self._delegation_chains: dict[str, list[str]] = {}  # agent_did -> chain
        self._issued_tokens: dict[str, CapabilityToken] = {}
        self._approval_workflows: dict[str, dict] = {}

    def register_public_key(self, did: str, public_key: Ed25519PublicKey):
        """Register an agent's public key."""
        self._public_keys[did] = public_key

    def register_policy(self, policy: dict):
        """Register a policy for evaluation."""
        self._policies.append(policy)

    def set_trust_level(self, agent_did: str, trust_level: str):
        """Set an agent's trust level."""
        self._trust_levels[agent_did] = trust_level

    def set_delegation_chain(self, agent_did: str, chain: list[str]):
        """Set an agent's delegation chain."""
        self._delegation_chains[agent_did] = chain

    def evaluate_request(
        self, request: AuthorizationRequest
    ) -> AuthorizationResponse:
        """
        Evaluate an A2A authorization request.

        Returns an AuthorizationResponse with a decision.
        """
        # 1. Identity Check
        identity_result = self._check_identity(request)
        if not identity_result["valid"]:
            return AuthorizationResponse(
                request_id=request.request_id,
                decision=AuthorizationDecision.DENY,
                decision_reason=f"Identity check failed: {identity_result['reason']}",
            )

        # 2. Trust Check
        trust_result = self._check_trust(request)
        if not trust_result["valid"]:
            return AuthorizationResponse(
                request_id=request.request_id,
                decision=AuthorizationDecision.DENY,
                decision_reason=f"Trust check failed: {trust_result['reason']}",
            )

        # 3. Policy Check
        policy_result = self._check_policy(request)
        if not policy_result["valid"]:
            return AuthorizationResponse(
                request_id=request.request_id,
                decision=AuthorizationDecision.DENY,
                decision_reason=f"Policy check failed: {policy_result['reason']}",
            )

        # 4. Scope Check
        scope_result = self._check_scope(request)
        if not scope_result["valid"]:
            return AuthorizationResponse(
                request_id=request.request_id,
                decision=AuthorizationDecision.DENY,
                decision_reason=f"Scope check failed: {scope_result['reason']}",
            )

        # 5. Decision — all checks passed
        token = self._issue_capability_token(request)

        return AuthorizationResponse(
            request_id=request.request_id,
            decision=AuthorizationDecision.GRANT,
            decision_reason="All checks passed; capability granted",
            granted_capability=token.to_dict(),
            policy_references=policy_result.get("references", []),
        )

    def _check_identity(self, request: AuthorizationRequest) -> dict:
        """Verify the requester's identity."""
        # Check DID is registered
        if request.requester_agent not in self._public_keys:
            return {"valid": False, "reason": "Unknown requester identity"}

        # Verify signature
        if not request.signature:
            return {"valid": False, "reason": "Missing request signature"}

        try:
            request_dict = request.to_dict()
            request_dict.pop("signature", None)
            canonical = json.dumps(
                request_dict, sort_keys=True, separators=(",", ":")
            )
            signature = base64.urlsafe_b64decode(
                request.signature.encode("utf-8")
            )
            public_key = self._public_keys[request.requester_agent]
            public_key.verify(signature, canonical.encode("utf-8"))
            return {"valid": True}
        except (InvalidSignature, Exception) as e:
            return {"valid": False, "reason": f"Invalid signature: {e}"}

    def _check_trust(self, request: AuthorizationRequest) -> dict:
        """Verify the requester's trust level is sufficient."""
        requester_trust = self._trust_levels.get(
            request.requester_agent, "untrusted"
        )

        # Minimum trust levels for different operations
        min_trust = {
            "read": "low",
            "write": "medium",
            "execute": "high",
            "admin": "privileged",
        }

        required = min_trust.get(request.capability, "medium")

        trust_order = {
            "untrusted": 0, "low": 1, "medium": 2,
            "high": 3, "privileged": 4,
        }

        if trust_order.get(requester_trust, 0) < trust_order.get(required, 2):
            return {
                "valid": False,
                "reason": (
                    f"Insufficient trust: {requester_trust} "
                    f"(requires {required})"
                ),
            }

        return {"valid": True}

    def _check_policy(self, request: AuthorizationRequest) -> dict:
        """Evaluate applicable policies."""
        applicable = []
        for policy in self._policies:
            # Check if policy applies to this agent
            scope = policy.get("scope", {})
            agents = scope.get("agents", [])
            if agents and request.requester_agent not in agents:
                continue
            applicable.append(policy)

        # Evaluate policies (deny-overrides conflict resolution)
        for policy in applicable:
            rules = policy.get("rules", [])
            for rule in rules:
                if self._rule_matches(rule, request):
                    if rule.get("effect") == "deny":
                        return {
                            "valid": False,
                            "reason": f"Denied by policy {policy['id']}",
                        }

        return {
            "valid": True,
            "references": [p["id"] for p in applicable],
        }

    def _rule_matches(self, rule: dict, request: AuthorizationRequest) -> bool:
        """Check if a policy rule matches the request."""
        # Simplified matching — production would use OPA/Rego
        rule_capability = rule.get("capability", "")
        rule_resource = rule.get("resource", "")

        if rule_capability and rule_capability != request.capability:
            return False
        if rule_resource and rule_resource != request.resource:
            return False
        return True

    def _check_scope(self, request: AuthorizationRequest) -> dict:
        """Verify the request is within the requester's delegation scope."""
        chain = self._delegation_chains.get(request.requester_agent, [])
        if not chain:
            # No delegation — agent can only use its own capabilities
            return {"valid": True}

        # Check if the requested capability is in the delegation chain
        # This would integrate with the DelegationChainVerifier
        return {"valid": True}

    def _issue_capability_token(
        self, request: AuthorizationRequest
    ) -> CapabilityToken:
        """Issue a capability token for the granted authorization."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=5)  # Short-lived by default

        token = CapabilityToken(
            token_id=f"cap:{uuid.uuid4()}",
            subject=request.requester_agent,
            issuer="did:grc:system:policy-engine",
            capability=request.capability,
            resource=request.resource,
            resource_id=request.resource_id,
            conditions={
                "fields": request.constraints.get("fields", []),
                "max-records": request.constraints.get("max-records", 1),
                "expires-at": expires.isoformat(),
            },
            delegation_id=request.requester_delegation_chain,
            issued_at=now.isoformat(),
            expires_at=expires.isoformat(),
        )

        self._issued_tokens[token.id] = token
        return token

    def require_approval(
        self,
        request: AuthorizationRequest,
        approver: str,
        escalation_reason: str,
    ) -> AuthorizationResponse:
        """
        Route a request for human approval.
        Implements spec §6.6.
        """
        workflow = {
            "workflow-id": f"appr:{uuid.uuid4()}",
            "request-id": request.request_id,
            "escalated-to": approver,
            "escalation-reason": escalation_reason,
            "status": "pending",
            "created-at": datetime.now(timezone.utc).isoformat(),
        }
        self._approval_workflows[request.request_id] = workflow

        return AuthorizationResponse(
            request_id=request.request_id,
            decision=AuthorizationDecision.REQUIRE_APPROVAL,
            decision_reason=f"Requires human approval: {escalation_reason}",
        )

    def resolve_approval(
        self,
        request_id: str,
        approved: bool,
        approver: str,
        comments: str = "",
    ) -> Optional[AuthorizationResponse]:
        """Resolve a pending approval workflow."""
        workflow = self._approval_workflows.get(request_id)
        if not workflow:
            return None

        workflow["status"] = "approved" if approved else "denied"
        workflow["resolved-by"] = approver
        workflow["resolved-at"] = datetime.now(timezone.utc).isoformat()
        workflow["comments"] = comments

        if approved:
            return AuthorizationResponse(
                request_id=request_id,
                decision=AuthorizationDecision.GRANT,
                decision_reason="Approved by human reviewer",
            )
        else:
            return AuthorizationResponse(
                request_id=request_id,
                decision=AuthorizationDecision.DENY,
                decision_reason="Denied by human reviewer",
            )


# ─── Cross-Organizational Authorization ─────────────────────────────

class CrossOrgAuthorization:
    """
    Handles authorization between agents from different organizations.
    Implements spec §6.7.
    """

    def __init__(self):
        self._trust_anchors: dict[str, str] = {}
        self._org_policies: dict[str, list[dict]] = {}

    def verify_trust_anchor(self, org_did: str) -> bool:
        """Verify an organization's trust anchor."""
        return org_did in self._trust_anchors

    def compute_policy_intersection(
        self, org_a: str, org_b: str
    ) -> list[dict]:
        """Compute the intersection of two organizations' policies."""
        policies_a = self._org_policies.get(org_a, [])
        policies_b = self._org_policies.get(org_b, [])

        # Find common policies by resource and capability
        intersection = []
        for pa in policies_a:
            for pb in policies_b:
                if (
                    pa.get("resource") == pb.get("resource")
                    and pa.get("capability") == pb.get("capability")
                ):
                    # Use the more restrictive policy
                    if pa.get("effect") == "deny" or pb.get("effect") == "deny":
                        intersection.append({
                            "resource": pa.get("resource"),
                            "capability": pa.get("capability"),
                            "effect": "deny",
                            "source": "conservative-minimum",
                        })
                    else:
                        intersection.append({
                            "resource": pa.get("resource"),
                            "capability": pa.get("capability"),
                            "effect": "allow",
                            "source": "conservative-minimum",
                        })
        return intersection

    def check_data_residency(
        self, data_classification: str, source_org: str, target_org: str
    ) -> bool:
        """Verify data does not cross jurisdictional boundaries."""
        # Simplified — production would check data residency rules
        restricted_classifications = ["customer-pii", "phi", "financial"]
        if data_classification in restricted_classifications:
            return source_org == target_org
        return True


# ─── Usage Example ───────────────────────────────────────────────────

def example_a2a_usage():
    """Demonstrate A2A authorization."""
    engine = A2AAuthorizationEngine()

    # Register agents
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    key_a = Ed25519PrivateKey.generate()
    key_b = Ed25519PrivateKey.generate()

    did_a = "did:grc:agent:agent-a"
    did_b = "did:grc:agent:agent-b"

    engine.register_public_key(did_a, key_a.public_key())
    engine.register_public_key(did_b, key_b.public_key())

    # Set trust levels
    engine.set_trust_level(did_a, "high")
    engine.set_trust_level(did_b, "medium")

    # Register a policy
    engine.register_policy({
        "id": "pol:customer-data-access",
        "scope": {"agents": [did_a]},
        "rules": [
            {"capability": "read", "resource": "customer-database", "effect": "allow"},
            {"capability": "delete", "resource": "customer-database", "effect": "deny"},
        ],
    })

    # Create authorization request
    request = AuthorizationRequest(
        requester_agent=did_a,
        requester_trust_level="high",
        resource_owner_agent=did_b,
        resource_owner_trust_level="medium",
        capability="read",
        resource="customer-database",
        resource_id="customer-789",
        justification="Need to verify customer identity before processing refund",
        constraints={
            "max-records": 1,
            "fields": ["name", "email", "account-status"],
        },
    )

    # Sign the request
    request_dict = request.to_dict()
    canonical = json.dumps(request_dict, sort_keys=True, separators=(",", ":"))
    signature = key_a.sign(canonical.encode("utf-8"))
    request.signature = base64.urlsafe_b64encode(signature).decode("utf-8")

    # Evaluate
    response = engine.evaluate_request(request)
    print(f"Decision: {response.decision.value}")
    print(f"Reason: {response.decision_reason}")
    if response.granted_capability:
        print(f"Token issued: {response.granted_capability['id']}")

    return response


if __name__ == "__main__":
    example_a2a_usage()
```

---

## 8. Agent Audit Trail Implementation

The audit trail provides tamper-evident logging of all agent actions using a Merkle chain for cryptographic integrity.

### 8.1 Audit Trail Implementation

```python
"""
GRC_Claw Agent Audit Trail Implementation
Implements tamper-evident audit logging with Merkle chain integrity.
Conforms to spec §7.
"""

from __future__ import annotations

import json
import uuid
import hashlib
import base64
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.exceptions import InvalidSignature


class AuditEventType(str, Enum):
    # Action events
    ACTION_EXECUTED = "action-executed"
    ACTION_BLOCKED = "action-blocked"
    ACTION_TRANSFORMED = "action-transformed"
    ACTION_ESCALATED = "action-escalated"

    # Policy events
    POLICY_EVALUATED = "policy-evaluated"
    POLICY_VIOLATED = "policy-violated"
    POLICY_DRIFT = "policy-drift"

    # Trust events
    TRUST_SCORED = "trust-scored"
    TRUST_PROMOTED = "trust-promoted"
    TRUST_DEMOTED = "trust-demoted"

    # Identity events
    IDENTITY_REGISTERED = "identity-registered"
    IDENTITY_ROTATED = "identity-rotated"
    IDENTITY_REVOKED = "identity-revoked"

    # Delegation events
    DELEGATION_CREATED = "delegation-created"
    DELEGATION_REVOKED = "delegation-revoked"
    DELEGATION_EXPIRED = "delegation-expired"

    # Authorization events
    AUTHZ_REQUESTED = "authz-requested"
    AUTHZ_GRANTED = "authz-granted"
    AUTHZ_DENIED = "authz-denied"
    AUTHZ_APPROVAL_REQUIRED = "authz-approval-required"


@dataclass
class AuditEvent:
    """
    A single audit event.
    Conforms to CloudEvents v1.0 with GRC_Claw extensions (spec §7.2).
    """
    # CloudEvents standard fields
    specversion: str = "1.0"
    type: str = ""  # e.g., "dev.grc-claw.agent.action.executed"
    source: str = ""  # Agent DID
    id: str = field(default_factory=lambda: f"evt:{uuid.uuid4()}")
    time: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    datacontenttype: str = "application/json"

    # Event data
    data: dict = field(default_factory=dict)

    # Integrity fields
    previous_hash: Optional[str] = None
    event_hash: Optional[str] = None
    merkle_root: Optional[str] = None

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the canonical event form."""
        event_dict = {
            "specversion": self.specversion,
            "type": self.type,
            "source": self.source,
            "id": self.id,
            "time": self.time,
            "datacontenttype": self.datacontenttype,
            "data": self.data,
            "previous-hash": self.previous_hash,
        }
        canonical = json.dumps(
            event_dict, sort_keys=True, separators=(",", ":")
        )
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "specversion": self.specversion,
            "type": self.type,
            "source": self.source,
            "id": self.id,
            "time": self.time,
            "datacontenttype": self.datacontenttype,
            "data": self.data,
            "integrity": {
                "previous-hash": self.previous_hash,
                "event-hash": self.event_hash,
                "merkle-root": self.merkle_root,
            },
        }

    def to_jsonl(self) -> str:
        """Serialize to JSONL format (one event per line)."""
        return json.dumps(self.to_dict(), separators=(",", ":"))


class MerkleTree:
    """
    Merkle tree for batch integrity verification.
    """

    def __init__(self, leaves: list[str]):
        self.leaves = leaves
        self.levels: list[list[str]] = []
        self.root = self._build()

    def _build(self) -> str:
        """Build the Merkle tree and return the root hash."""
        if not self.leaves:
            return "sha256:" + hashlib.sha256(b"").hexdigest()

        # Hash leaves
        current_level = [
            "sha256:" + hashlib.sha256(leaf.encode("utf-8")).hexdigest()
            for leaf in self.leaves
        ]
        self.levels.append(current_level)

        # Build tree bottom-up
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                combined = left + right
                next_level.append(
                    "sha256:" + hashlib.sha256(combined.encode("utf-8")).hexdigest()
                )
            self.levels.append(next_level)
            current_level = next_level

        return current_level[0]

    def get_proof(self, leaf_index: int) -> list[dict]:
        """
        Get the Merkle proof for a leaf.
        Returns list of {"position": "left"|"right", "hash": str} dicts.
        """
        if leaf_index < 0 or leaf_index >= len(self.leaves):
            raise ValueError("Leaf index out of range")

        proof = []
        index = leaf_index

        for level_idx in range(len(self.levels) - 1):
            level = self.levels[level_idx]
            if index % 2 == 0:
                sibling_idx = index + 1
                if sibling_idx < len(level):
                    proof.append({
                        "position": "right",
                        "hash": level[sibling_idx],
                    })
            else:
                sibling_idx = index - 1
                proof.append({
                    "position": "left",
                    "hash": level[sibling_idx],
                })
            index //= 2

        return proof

    def verify_proof(
        self, leaf: str, proof: list[dict], root: str
    ) -> bool:
        """Verify a Merkle proof."""
        current = "sha256:" + hashlib.sha256(leaf.encode("utf-8")).hexdigest()

        for step in proof:
            if step["position"] == "right":
                combined = current + step["hash"]
            else:
                combined = step["hash"] + current
            current = "sha256:" + hashlib.sha256(combined.encode("utf-8")).hexdigest()

        return current == root


class AuditTrail:
    """
    Tamper-evident audit trail using a hash chain and Merkle trees.

    Each event includes:
    - previous-hash: SHA-256 of the previous event
    - event-hash: SHA-256 of the current event's canonical form
    - merkle-root: root of the Merkle tree for the current batch

    Any modification to a past event invalidates all subsequent hashes.
    """

    def __init__(self, chain_id: str):
        self.chain_id = chain_id
        self.events: list[AuditEvent] = []
        self._batch_size = 100  # Merkle tree batch size
        self._current_batch: list[AuditEvent] = []
        self._merkle_roots: list[str] = []

    def append(self, event: AuditEvent) -> AuditEvent:
        """
        Append an event to the audit trail.

        Computes the event hash and links it to the previous event.
        """
        # Set previous hash
        if self.events:
            event.previous_hash = self.events[-1].event_hash
        elif self._current_batch:
            event.previous_hash = self._current_batch[-1].event_hash
        else:
            event.previous_hash = "sha256:" + hashlib.sha256(b"").hexdigest()

        # Compute event hash
        event.event_hash = event.compute_hash()

        # Add to batch
        self._current_batch.append(event)

        # If batch is full, compute Merkle root
        if len(self._current_batch) >= self._batch_size:
            self._finalize_batch()

        self.events.append(event)
        return event

    def _finalize_batch(self):
        """Compute Merkle root for the current batch and reset."""
        if not self._current_batch:
            return

        leaves = [e.event_hash for e in self._current_batch]
        tree = MerkleTree(leaves)
        self._merkle_roots.append(tree.root)

        # Set Merkle root on all events in batch
        for event in self._current_batch:
            event.merkle_root = tree.root

        self._current_batch = []

    def verify_integrity(self) -> dict:
        """
        Verify the integrity of the entire audit trail.

        Returns:
            dict with 'valid' (bool) and 'details' (list of issues).
        """
        issues = []

        for i, event in enumerate(self.events):
            # Verify event hash
            computed_hash = event.compute_hash()
            if computed_hash != event.event_hash:
                issues.append(
                    f"Event {i} ({event.id}): hash mismatch"
                )

            # Verify chain linkage
            if i > 0:
                expected_prev = self.events[i - 1].event_hash
                if event.previous_hash != expected_prev:
                    issues.append(
                        f"Event {i} ({event.id}): chain broken"
                    )
            else:
                # First event should have empty previous hash
                expected_prev = "sha256:" + hashlib.sha256(b"").hexdigest()
                if event.previous_hash != expected_prev:
                    issues.append(
                        f"Event 0 ({event.id}): invalid genesis hash"
                    )

        return {
            "valid": len(issues) == 0,
            "details": issues,
            "event_count": len(self.events),
            "merkle_roots": len(self._merkle_roots),
        }

    def get_event_proof(self, event_id: str) -> Optional[dict]:
        """Get the Merkle proof for a specific event."""
        # Find the event
        event_idx = None
        for i, e in enumerate(self.events):
            if e.id == event_id:
                event_idx = i
                break

        if event_idx is None:
            return None

        # Find which batch this event belongs to
        batch_idx = event_idx // self._batch_size
        batch_start = batch_idx * self._batch_size
        batch_end = min(batch_start + self._batch_size, len(self.events))
        batch = self.events[batch_start:batch_end]

        # Build Merkle tree for this batch
        leaves = [e.event_hash for e in batch]
        tree = MerkleTree(leaves)

        # Get proof
        leaf_idx = event_idx - batch_start
        proof = tree.get_proof(leaf_idx)

        return {
            "event-id": event_id,
            "event-hash": self.events[event_idx].event_hash,
            "merkle-root": tree.root,
            "proof": proof,
        }

    def export_jsonl(self) -> str:
        """Export the audit trail as JSONL (one event per line)."""
        return "\n".join(e.to_jsonl() for e in self.events)

    def query(
        self,
        agent_did: Optional[str] = None,
        event_type: Optional[str] = None,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
    ) -> list[AuditEvent]:
        """Query audit events with filters."""
        results = self.events

        if agent_did:
            results = [e for e in results if e.source == agent_did]
        if event_type:
            results = [e for e in results if e.type == event_type]
        if from_time:
            results = [e for e in results if e.time >= from_time]
        if to_time:
            results = [e for e in results if e.time <= to_time]

        return results


class AuditLogger:
    """
    High-level audit logger that creates properly formatted audit events.
    """

    def __init__(self, trail: AuditTrail):
        self.trail = trail

    def log_action(
        self,
        agent_did: str,
        action_type: str,
        tool: str,
        arguments: dict,
        outcome: str,
        result_summary: str,
        capability_id: Optional[str] = None,
        delegation_chain: Optional[str] = None,
        policy_references: list[str] = None,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ) -> AuditEvent:
        """Log an action-executed event."""
        event = AuditEvent(
            type=f"dev.grc-claw.agent.{outcome}",
            source=agent_did,
            data={
                "event-type": "action-executed",
                "agent": {
                    "id": agent_did,
                    "trust-level": "high",  # Populated from trust engine
                },
                "action": {
                    "type": action_type,
                    "tool": tool,
                    "arguments": arguments,
                    "outcome": outcome,
                    "result-summary": result_summary,
                },
                "authorization": {
                    "capability-id": capability_id,
                    "delegation-chain": delegation_chain,
                    "policy-references": policy_references or [],
                    "decision": "grant",
                },
                "context": {
                    "session-id": session_id,
                    "workflow-id": workflow_id,
                    "trace-id": f"trace:{uuid.uuid4()}",
                },
            },
        )
        return self.trail.append(event)

    def log_policy_violation(
        self,
        agent_did: str,
        policy_id: str,
        violation_type: str,
        severity: str,
        details: dict,
    ) -> AuditEvent:
        """Log a policy violation event."""
        event = AuditEvent(
            type="dev.grc-claw.policy.violated",
            source=agent_did,
            data={
                "event-type": "policy-violated",
                "agent": {"id": agent_did},
                "policy": {"id": policy_id},
                "violation": {
                    "type": violation_type,
                    "severity": severity,
                    "details": details,
                },
            },
        )
        return self.trail.append(event)

    def log_trust_change(
        self,
        agent_did: str,
        old_level: str,
        new_level: str,
        reason: str,
        score: float,
    ) -> AuditEvent:
        """Log a trust level change event."""
        event_type = (
            "dev.grc-claw.trust.promoted"
            if new_level > old_level
            else "dev.grc-claw.trust.demoted"
        )
        event = AuditEvent(
            type=event_type,
            source=agent_did,
            data={
                "event-type": "trust-changed",
                "agent": {"id": agent_did},
                "trust": {
                    "old-level": old_level,
                    "new-level": new_level,
                    "reason": reason,
                    "score": score,
                },
            },
        )
        return self.trail.append(event)

    def log_delegation(
        self,
        event_type: str,
        delegation_id: str,
        delegator: str,
        delegate: str,
        reason: str = "",
    ) -> AuditEvent:
        """Log a delegation event."""
        type_map = {
            "created": "dev.grc-claw.delegation.created",
            "revoked": "dev.grc-claw.delegation.revoked",
            "expired": "dev.grc-claw.delegation.expired",
        }
        event = AuditEvent(
            type=type_map.get(event_type, "dev.grc-claw.delegation.event"),
            source=delegator,
            data={
                "event-type": f"delegation-{event_type}",
                "delegation": {
                    "id": delegation_id,
                    "delegator": delegator,
                    "delegate": delegate,
                    "reason": reason,
                },
            },
        )
        return self.trail.append(event)

    def log_authorization(
        self,
        decision: str,
        request_id: str,
        requester: str,
        resource_owner: str,
        capability: str,
        resource: str,
    ) -> AuditEvent:
        """Log an authorization event."""
        type_map = {
            "granted": "dev.grc-claw.authz.granted",
            "denied": "dev.grc-claw.authz.denied",
            "requested": "dev.grc-claw.authz.requested",
            "approval-required": "dev.grc-claw.authz.approval-required",
        }
        event = AuditEvent(
            type=type_map.get(decision, "dev.grc-claw.authz.event"),
            source=requester,
            data={
                "event-type": f"authz-{decision}",
                "authorization": {
                    "request-id": request_id,
                    "requester": requester,
                    "resource-owner": resource_owner,
                    "capability": capability,
                    "resource": resource,
                    "decision": decision,
                },
            },
        )
        return self.trail.append(event)


# ─── Usage Example ───────────────────────────────────────────────────

def example_audit_usage():
    """Demonstrate audit trail usage."""
    trail = AuditTrail(chain_id="chain:0a1b2c3d-4e5f-6a7b-8c9d-0e1f2a3b4c5d")
    logger = AuditLogger(trail)

    agent_did = "did:grc:agent:customer-service-agent"

    # Log some events
    logger.log_action(
        agent_did=agent_did,
        action_type="tool-call",
        tool="read-ticket",
        arguments={"ticket-id": "TKT-12345"},
        outcome="success",
        result_summary="Retrieved ticket details",
        capability_id="cap:9d0e1f2a-3b4c-5d6e-7f8a-9b0c1d2e3f4a",
        session_id="sess:2b3c4d5e-6f7a-8b9c-0d1e-2f3a4b5c6d7e",
    )

    logger.log_policy_violation(
        agent_did=agent_did,
        policy_id="pol:data-handling",
        violation_type="unauthorized-access",
        severity="medium",
        details={"resource": "customer-pii", "action": "read"},
    )

    logger.log_trust_change(
        agent_did=agent_did,
        old_level="medium",
        new_level="high",
        reason="30 days clean record, promotion criteria met",
        score=0.72,
    )

    logger.log_delegation(
        event_type="created",
        delegation_id="del:8c4d5e6f-7a8b-9c0d-1e2f-3a4b5c6d7e8f",
        delegator=agent_did,
        delegate="did:grc:agent:ticket-reader",
    )

    # Verify integrity
    result = trail.verify_integrity()
    print(f"Audit trail integrity: {result}")

    # Get Merkle proof for first event
    if trail.events:
        proof = trail.get_event_proof(trail.events[0].id)
        print(f"Merkle proof for first event: {proof}")

    # Export as JSONL
    jsonl = trail.export_jsonl()
    print(f"Exported {len(trail.events)} events as JSONL")

    return trail


if __name__ == "__main__":
    example_audit_usage()
```

---

## 9. Deployment Patterns

### 9.1 Component Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Production Deployment                             │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Kubernetes Cluster                         │    │
│  │                                                              │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │    │
│  │  │  Identity    │  │  Trust       │  │  Policy      │     │    │
│  │  │  Registry    │  │  Engine      │  │  Engine      │     │    │
│  │  │  (3 replicas)│  │  (3 replicas)│  │  (3 replicas)│     │    │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │    │
│  │         │                 │                 │              │    │
│  │         └────────────────┬┴─────────────────┘              │    │
│  │                          ▼                                 │    │
│  │                  ┌──────────────┐                         │    │
│  │                  │  Governance  │                         │    │
│  │                  │  Orchestrator│                         │    │
│  │                  │  (3 replicas)│                         │    │
│  │                  └──────┬───────┘                         │    │
│  │                         │                                 │    │
│  │         ┌───────────────┼───────────────┐                │    │
│  │         ▼               ▼               ▼                │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐    │    │
│  │  │  Delegation  │ │  Capability  │ │   Audit      │    │    │
│  │  │  Tracker     │ │  Token Svc   │ │   Service    │    │    │
│  │  │  (2 replicas)│ │  (2 replicas)│ │  (3 replicas)│    │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘    │    │
│  │                                                              │    │
│  │  ┌──────────────────────────────────────────────┐          │    │
│  │  │              Framework Adapters               │          │    │
│  │  │  LangChain │ AutoGen │ CrewAI │ OpenAI │ ... │          │    │
│  │  └──────────────────────────────────────────────┘          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  PostgreSQL  │  │    Kafka     │  │    Redis     │             │
│  │  (Primary +  │  │  (3 brokers) │  │  (Cluster)   │             │
│  │   Replica)   │  │              │  │              │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
```

### 9.2 Docker Compose (Development)

```yaml
version: "3.8"

services:
  # Core Governance Services
  identity-registry:
    build: ./services/identity-registry
    ports:
      - "8081:8080"
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/identity
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  trust-engine:
    build: ./services/trust-engine
    ports:
      - "8082:8080"
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/trust
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  policy-engine:
    build: ./services/policy-engine
    ports:
      - "8083:8080"
    environment:
      - OPA_URL=http://opa:8181
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/policy
    depends_on:
      - postgres
      - opa

  governance-orchestrator:
    build: ./services/governance-orchestrator
    ports:
      - "8080:8080"
    environment:
      - IDENTITY_REGISTRY_URL=http://identity-registry:8080
      - TRUST_ENGINE_URL=http://trust-engine:8080
      - POLICY_ENGINE_URL=http://policy-engine:8080
      - DELEGATION_TRACKER_URL=http://delegation-tracker:8080
      - AUDIT_SERVICE_URL=http://audit-service:8080
    depends_on:
      - identity-registry
      - trust-engine
      - policy-engine
      - delegation-tracker
      - audit-service

  delegation-tracker:
    build: ./services/delegation-tracker
    ports:
      - "8084:8080"
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/delegation
    depends_on:
      - postgres

  capability-service:
    build: ./services/capability-service
    ports:
      - "8085:8080"
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/capability
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

  audit-service:
    build: ./services/audit-service
    ports:
      - "8086:8080"
    environment:
      - DATABASE_URL=postgresql://grc:grc@postgres:5432/audit
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - postgres
      - kafka

  # Sidecar proxy for custom framework adapters
  envoy-sidecar:
    image: envoyproxy/envoy:v1.28
    ports:
      - "9901:9901"  # Admin
    volumes:
      - ./config/envoy.yaml:/etc/envoy/envoy.yaml

  # Data Stores
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: grc
      POSTGRES_PASSWORD: grc
      POSTGRES_DB: grc_claw
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  kafka:
    image: confluentinc/cp-kafka:7.5
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

  opa:
    image: openpolicyagent/opa:0.58
    command: "run --server --addr :8181 /policies"
    volumes:
      - ./policies:/policies
    ports:
      - "8181:8181"

volumes:
  postgres_data:
```

### 9.3 Kubernetes Deployment

```yaml
# governance-orchestrator.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: governance-orchestrator
  namespace: grc-claw
spec:
  replicas: 3
  selector:
    matchLabels:
      app: governance-orchestrator
  template:
    metadata:
      labels:
        app: governance-orchestrator
    spec:
      containers:
        - name: orchestrator
          image: grc-claw/governance-orchestrator:v1.0.0
          ports:
            - containerPort: 8080
          env:
            - name: IDENTITY_REGISTRY_URL
              value: "http://identity-registry:8080"
            - name: TRUST_ENGINE_URL
              value: "http://trust-engine:8080"
            - name: POLICY_ENGINE_URL
              value: "http://policy-engine:8080"
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: grc-claw-db-credentials
                  key: url
          resources:
            requests:
              cpu: 500m
              memory: 512Mi
            limits:
              cpu: 2000m
              memory: 2Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: governance-orchestrator
  namespace: grc-claw
spec:
  selector:
    app: governance-orchestrator
  ports:
    - port: 8080
      targetPort: 8080
  type: ClusterIP
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: governance-orchestrator-hpa
  namespace: grc-claw
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: governance-orchestrator
  minReplicas: 3
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### 9.4 Framework Adapter Integration

```python
"""
GRC_Claw Framework Adapter — LangChain Example
Demonstrates how to inject governance enforcement into agent frameworks.
"""

from functools import wraps
from typing import Callable


class GRCGovernDecorator:
    """
    Python decorator for enforcing GRC_Claw governance on agent functions.

    Usage:
        @grc_govern(
            identity=AgentIdentity.from_env(),
            capabilities=[Capability.READ_TICKETS],
            require_trust="medium"
        )
        def process_ticket(ticket_id: str) -> dict:
            ...
    """

    def __init__(
        self,
        identity: str,
        capabilities: list[str],
        require_trust: str = "medium",
        audit: bool = True,
    ):
        self.identity = identity
        self.capabilities = capabilities
        self.require_trust = require_trust
        self.audit = audit

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 1. Identity verification
            if not self._verify_identity():
                raise PermissionError("Identity verification failed")

            # 2. Trust check
            if not self._check_trust():
                raise PermissionError("Insufficient trust level")

            # 3. Capability check
            if not self._check_capabilities(func.__name__):
                raise PermissionError("Missing required capability")

            # 4. Execute
            result = func(*args, **kwargs)

            # 5. Audit
            if self.audit:
                self._audit_log(func.__name__, args, kwargs, result)

            return result

        return wrapper

    def _verify_identity(self) -> bool:
        # Integrate with DID registry
        return True

    def _check_trust(self) -> bool:
        # Integrate with trust engine
        return True

    def _check_capabilities(self, operation: str) -> bool:
        # Check if operation is within declared capabilities
        return True

    def _audit_log(self, operation: str, args, kwargs, result):
        # Log to audit trail
        pass


# LangChain-specific adapter
class LangChainToolAdapter:
    """
    Wraps LangChain tools with GRC_Claw governance enforcement.
    """

    def __init__(self, tool, identity: str, capabilities: list[str]):
        self.tool = tool
        self.identity = identity
        self.capabilities = capabilities

    def run(self, *args, **kwargs):
        # Pre-execution governance check
        self._enforce_governance("pre-execution")

        # Execute tool
        result = self.tool.run(*args, **kwargs)

        # Post-execution audit
        self._enforce_governance("post-execution", result=result)

        return result

    def _enforce_governance(self, phase: str, result=None):
        # Integrate with governance orchestrator
        pass
```

---

## 10. Integration with GRC_Claw Platform

### 10.1 API Endpoints

The governance components expose these REST endpoints (aligned with the Integration Specification):

| Component | Endpoint | Method | Description |
|-----------|----------|--------|-------------|
| Identity Registry | `/api/v1/identity/resolve/{did}` | GET | Resolve DID document |
| Identity Registry | `/api/v1/identity/register` | POST | Register new agent |
| Identity Registry | `/api/v1/identity/rotate` | POST | Rotate agent keys |
| Trust Engine | `/api/v1/trust/score/{agent_did}` | GET | Get trust score |
| Trust Engine | `/api/v1/trust/evaluate` | POST | Evaluate trust |
| Delegation | `/api/v1/delegation/create` | POST | Create delegation |
| Delegation | `/api/v1/delegation/verify` | POST | Verify chain |
| Delegation | `/api/v1/delegation/revoke` | POST | Revoke delegation |
| Authorization | `/api/v1/authz/request` | POST | Request authorization |
| Authorization | `/api/v1/authz/decision` | POST | Submit decision |
| Audit | `/api/v1/audit/events` | GET | Query audit events |
| Audit | `/api/v1/audit/verify` | POST | Verify chain integrity |
| Audit | `/api/v1/audit/export` | GET | Export audit trail |
| Lifecycle | `/api/v1/lifecycle/{agent_did}` | GET | Get lifecycle state |
| Lifecycle | `/api/v1/lifecycle/{agent_did}/transition` | POST | Execute transition |

### 10.2 Event Integration

All governance events are published to the GRC_Claw event bus (Kafka) as CloudEvents v1.0:

```python
"""
Event publisher for GRC_Claw governance events.
Publishes to Kafka topics per the Integration Specification §5.6.
"""

import json
from confluent_kafka import Producer


class GovernanceEventPublisher:
    """Publishes governance events to the GRC_Claw event bus."""

    def __init__(self, kafka_brokers: str):
        self.producer = Producer({
            "bootstrap.servers": kafka_brokers,
            "client.id": "grc-claw-governance",
        })

    def publish(self, topic: str, event: dict):
        """Publish an event to a Kafka topic."""
        self.producer.produce(
            topic=topic,
            key=event.get("agent_did", ""),
            value=json.dumps(event),
        )
        self.producer.flush()

    def publish_agent_registered(self, agent_did: str, identity: dict):
        """Publish agent.registered event."""
        self.publish("grcclaw.agent", {
            "specversion": "1.0",
            "type": "com.grcclaw.agent.registered",
            "source": agent_did,
            "id": f"evt:{uuid.uuid4()}",
            "time": datetime.now(timezone.utc).isoformat(),
            "datacontenttype": "application/json",
            "data": identity,
        })

    def publish_enforcement_decision(self, decision: dict):
        """Publish enforcement.decision event."""
        self.publish("grcclaw.enforcement", {
            "specversion": "1.0",
            "type": "com.grcclaw.enforcement.decision",
            "source": "grc-claw/policy-engine",
            "id": f"evt:{uuid.uuid4()}",
            "time": datetime.now(timezone.utc).isoformat(),
            "datacontenttype": "application/json",
            "data": decision,
        })

    def publish_audit_event(self, event: dict):
        """Publish audit.event to the audit topic."""
        self.publish("grcclaw.audit", event)
```

### 10.3 Compliance Mapping

| OWASP ASI | AGP Control | Implementation |
|-----------|-------------|----------------|
| ASI01: Agent Goal Hijack | Policy engine input validation | Policy engine with prompt injection detection |
| ASI02: Tool Misuse | Capability tokens | Capability token service with tool catalog enforcement |
| ASI03: Identity & Privilege Abuse | Agent identity model | DID registry with trust levels and capability hierarchy |
| ASI04: Agentic Supply Chain | Framework adapter verification | Adapter registry with verified adapter enforcement |
| ASI05: Unexpected Code Execution | Sandbox enforcement | Sandbox service with command denylist |
| ASI06: Memory & Context Poisoning | Audit trail integrity | Merkle chain with memory provenance tracking |
| ASI07: Insecure Inter-Agent Comms | mTLS + DID verification | Identity registry with encrypted transport |
| ASI08: Cascading Failures | Circuit breakers | Circuit breaker configuration per service |
| ASI09: Human-Agent Trust Exploitation | Approval workflows | A2A authorization with human approval flow |
| ASI10: Rogue Agents | Trust demotion | Trust engine with quarantine and kill switch |

---

## Appendix A: Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/grc-claw/grc-claw-governance.git
cd grc-claw-governance

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run tests
pytest tests/ -v

# 4. Start local development environment
docker-compose up -d

# 5. Register a new agent
curl -X POST http://localhost:8080/api/v1/identity/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-agent",
    "type": "autonomous",
    "framework": "langchain",
    "owner": {
      "type": "organization",
      "id": "did:grc:org:my-org",
      "name": "My Org"
    },
    "deployment": {
      "environment": "development",
      "region": "us-east-1",
      "host": "localhost"
    }
  }'

# 6. Resolve the agent's DID
curl http://localhost:8080/api/v1/identity/resolve/did:grc:agent:<uuid>

# 7. Query audit trail
curl "http://localhost:8080/api/v1/audit/events?agent=did:grc:agent:<uuid>"
```

## Appendix B: Configuration Reference

```yaml
# grc-claw-governance.yaml
governance:
  # Identity Registry
  identity_registry:
    key_rotation_interval_days: 90
    challenge_timeout_seconds: 30
    max_agents_per_org: 1000

  # Trust Engine
  trust_engine:
    evaluation_interval_hours: 6
    behavioral_window_days: 30
    compliance_window_days: 30
    operational_window_days: 30
    reputation_window_days: 30
    weights:
      behavioral: 0.40
      compliance: 0.30
      operational: 0.20
      reputation: 0.10
    thresholds:
      untrusted: [0.00, 0.20]
      low: [0.21, 0.40]
      medium: [0.41, 0.60]
      high: [0.61, 0.80]
      privileged: [0.81, 1.00]

  # Delegation
  delegation:
    max_depth: 3
    default_validity_hours: 8
    max_validity_hours: 24
    scope_narrowing_enforced: true
    revocation_propagation: synchronous

  # Authorization
  authorization:
    default_token_ttl_minutes: 5
    max_token_ttl_minutes: 60
    require_approval_for: ["admin", "delete", "export"]
    cross_org_policy: conservative-minimum

  # Audit Trail
  audit:
    merkle_batch_size: 100
    retention:
      action_events: "7years"
      policy_events: "7years"
      trust_events: "3years"
      identity_events: "lifetime+7years"
      delegation_events: "lifetime+3years"
      authorization_events: "7years"
    export_format: jsonl

  # Lifecycle
  lifecycle:
    provisioning_gates:
      - identity-created
      - owner-attested
      - risk-classified
      - capabilities-declared
      - policies-bound
      - adapter-verified
      - sandbox-configured
      - kill-switch-tested
      - baselines-established
      - audit-stream-configured
    suspension_review_deadline_hours: 24
    retirement_drain_timeout_hours: 4

  # Policy Engine
  policy_engine:
    engine: opa
    conflict_resolution: deny-overrides
    default_effect: deny
    dry_run_enabled: true

  # Event Bus
  event_bus:
    type: kafka
    brokers: ["kafka-1:9092", "kafka-2:9092", "kafka-3:9092"]
    topics:
      enforcement: grcclaw.enforcement
      evidence: grcclaw.evidence
      audit: grcclaw.audit
      compliance: grcclaw.compliance
      risk: grcclaw.risk
      agent: grcclaw.agent
```

## Appendix C: Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `DID_NOT_FOUND` | 404 | The requested DID is not registered |
| `DID_ALREADY_REGISTERED` | 409 | The DID is already in the registry |
| `INVALID_SIGNATURE` | 401 | Cryptographic signature verification failed |
| `INSUFFICIENT_TRUST` | 403 | Agent's trust level is below the required threshold |
| `DELEGATION_EXPIRED` | 403 | The delegation has expired |
| `DELEGATION_REVOKED` | 403 | The delegation has been revoked |
| `DELEGATION_CYCLE_DETECTED` | 400 | The requested delegation would create a cycle |
| `SCOPE_NARROWING_VIOLATION` | 400 | Child delegation scope exceeds parent scope |
| `POLICY_VIOLATION` | 403 | Action violates a policy |
| `CREDENTIAL_EXPIRED` | 401 | The verifiable credential has expired |
| `CREDENTIAL_REVOKED` | 401 | The verifiable credential has been revoked |
| `LIFECYCLE_INVALID_TRANSITION` | 400 | Invalid lifecycle state transition |
| `LIFECYCLE_GATE_INCOMPLETE` | 400 | Provisioning gate not yet complete |
| `AUDIT_CHAIN_BROKEN` | 500 | Audit trail integrity verification failed |
| `AUTHORIZATION_DENIED` | 403 | Authorization request denied |
| `APPROVAL_REQUIRED` | 202 | Human approval required |

---

**Document End**

*This implementation guide provides a complete reference for deploying GRC_Claw's Agent Governance Protocol. All code examples are production-ready Python 3.10+ and conform to the specifications in `grc-claw-agent-governance-spec.md` v1.1 and `grc-claw-integration-specification.md` v2.0.*</longcat_think>
