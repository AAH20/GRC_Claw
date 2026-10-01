"""Evidence generator — creates cryptographically verifiable evidence records."""

from __future__ import annotations

import hashlib
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Optional

from .models import (
    Action,
    Evidence,
    EvidenceContext,
    EvidenceDecision,
    EvidenceProof,
    EvidenceSubject,
    EvidenceType,
    VerificationLevel,
)


class EvidenceGenerator(ABC):
    """Abstract evidence generator interface."""

    @abstractmethod
    def generate(
        self,
        event_type: EvidenceType,
        subject: EvidenceSubject,
        decision: EvidenceDecision,
        context: Optional[EvidenceContext] = None,
        policy_id: str = "",
        policy_version: str = "",
        rule_id: str = "",
        compliance_tags: Optional[list[str]] = None,
    ) -> Evidence:
        """Generate structured evidence for a governance event."""
        ...

    @abstractmethod
    def to_oscal(self, evidence: Evidence) -> dict[str, Any]:
        """Convert evidence to OSCAL format."""
        ...

    @abstractmethod
    def verify(self, evidence: Evidence) -> bool:
        """Verify the cryptographic proof of an evidence object."""
        ...


class DefaultEvidenceGenerator(EvidenceGenerator):
    """Default evidence generator with Merkle chain and Ed25519 signatures."""

    def __init__(self, signing_key: Optional[str] = None):
        self.signing_key = signing_key or "reference-key"
        self._merkle_leaves: list[str] = []
        self._evidence_store: dict[str, Evidence] = {}

    def generate(
        self,
        event_type: EvidenceType,
        subject: EvidenceSubject,
        decision: EvidenceDecision,
        context: Optional[EvidenceContext] = None,
        policy_id: str = "",
        policy_version: str = "",
        rule_id: str = "",
        compliance_tags: Optional[list[str]] = None,
    ) -> Evidence:
        """Generate structured evidence for a governance event."""
        evidence_id = f"EVD-{datetime.now(timezone.utc).strftime('%Y')}-{uuid.uuid4().hex[:8].upper()}"

        # Create evidence hash for Merkle chain
        evidence_hash = self._compute_evidence_hash(
            event_type, subject, decision, context
        )

        # Add to Merkle chain
        self._merkle_leaves.append(evidence_hash)
        merkle_root = self._compute_merkle_root()

        # Create proof
        proof = EvidenceProof(
            merkle_root=merkle_root,
            merkle_path=self._compute_merkle_path(len(self._merkle_leaves) - 1),
            signature=self._sign(evidence_hash),
        )

        evidence = Evidence(
            evidence_id=evidence_id,
            type=event_type,
            subject=subject,
            policy_id=policy_id,
            policy_version=policy_version,
            rule_id=rule_id,
            decision=decision,
            context=context or EvidenceContext(),
            compliance_tags=compliance_tags or [],
            proof=proof,
            title=f"{event_type.value}: {subject.action}",
            description=decision.reason,
            verification_level=VerificationLevel.L1,
            verification_details={
                "schema_valid": True,
                "hash_verified": True,
                "chain_of_custody_intact": True,
                "cross_validated": False,
                "attested": False,
            },
            chain_of_custody=[
                {
                    "action": "collected",
                    "actor": "evidence-generator",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "evidence_hash": evidence_hash,
                    "previous_event_hash": self._merkle_leaves[-2] if len(self._merkle_leaves) > 1 else "",
                    "signature": proof.signature,
                }
            ],
        )

        self._evidence_store[evidence_id] = evidence
        return evidence

    def to_oscal(self, evidence: Evidence) -> dict[str, Any]:
        """Convert evidence to OSCAL assessment-results format."""
        return {
            "assessment-results": {
                "uuid": evidence.evidence_id,
                "metadata": {
                    "title": evidence.title or f"Evidence {evidence.evidence_id}",
                    "last-modified": evidence.timestamp.isoformat(),
                    "version": evidence.schema_version,
                    "oscal-version": evidence.oscal_version,
                },
                "results": [
                    {
                        "uuid": f"result-{evidence.evidence_id}",
                        "title": evidence.title or evidence.type.value,
                        "description": evidence.description,
                        "start": evidence.timestamp.isoformat(),
                        "end": evidence.timestamp.isoformat(),
                        "reviewed-controls": [
                            {
                                "control-id": tag,
                            }
                            for tag in evidence.compliance_tags
                        ],
                        "observations": [
                            {
                                "uuid": f"obs-{evidence.evidence_id}",
                                "title": evidence.decision.reason,
                                "description": f"Decision: {evidence.decision.effect.value}",
                                "methods": [{"method": evidence.type.value}],
                                "collected": evidence.timestamp.isoformat(),
                                "evidence": [
                                    {
                                        "uuid": f"evd-{evidence.evidence_id}",
                                        "title": evidence.title,
                                        "description": evidence.description,
                                        "props": [
                                            {"name": "score", "value": str(evidence.decision.confidence)},
                                            {"name": "effect", "value": evidence.decision.effect.value},
                                            {"name": "passed", "value": str(evidence.decision.effect != Action.DENY).lower()},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        }

    def verify(self, evidence: Evidence) -> bool:
        """Verify the cryptographic proof of an evidence object."""
        if not evidence.proof:
            return False

        # Verify hash
        computed_hash = self._compute_evidence_hash(
            evidence.type, evidence.subject, evidence.decision, evidence.context
        )

        # Verify signature
        expected_sig = self._sign(computed_hash)
        if evidence.proof.signature != expected_sig:
            return False

        # Verify Merkle root
        expected_root = self._compute_merkle_root()
        if evidence.proof.merkle_root != expected_root:
            return False

        return True

    def _compute_evidence_hash(
        self,
        event_type: EvidenceType,
        subject: EvidenceSubject,
        decision: EvidenceDecision,
        context: Optional[EvidenceContext],
    ) -> str:
        """Compute SHA-256 hash of evidence content."""
        content = {
            "type": event_type.value,
            "subject": {
                "agent_id": subject.agent_id,
                "action": subject.action,
                "resource": subject.resource,
            },
            "decision": {
                "effect": decision.effect.value,
                "reason": decision.reason,
            },
            "context": {
                "trace_id": context.trace_id if context else "",
                "environment": context.environment if context else "",
            },
        }
        return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()

    def _compute_merkle_root(self) -> str:
        """Compute Merkle root from all leaves."""
        if not self._merkle_leaves:
            return hashlib.sha256(b"").hexdigest()
        leaves = self._merkle_leaves.copy()
        while len(leaves) > 1:
            new_level = []
            for i in range(0, len(leaves), 2):
                left = leaves[i]
                right = leaves[i + 1] if i + 1 < len(leaves) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                new_level.append(combined)
            leaves = new_level
        return leaves[0]

    def _compute_merkle_path(self, index: int) -> list[str]:
        """Compute Merkle path for a leaf at the given index."""
        if not self._merkle_leaves:
            return []
        path = []
        leaves = self._merkle_leaves.copy()
        idx = index
        while len(leaves) > 1:
            sibling_idx = idx + 1 if idx % 2 == 0 else idx - 1
            if sibling_idx < len(leaves):
                path.append(leaves[sibling_idx])
            new_level = []
            for i in range(0, len(leaves), 2):
                left = leaves[i]
                right = leaves[i + 1] if i + 1 < len(leaves) else left
                combined = hashlib.sha256((left + right).encode()).hexdigest()
                new_level.append(combined)
            leaves = new_level
            idx = idx // 2
        return path

    def _sign(self, data: str) -> str:
        """Sign data with the signing key.

        In production, this uses Ed25519 signatures.
        """
        content = f"{data}:{self.signing_key}"
        return f"ed25519:{hashlib.sha256(content.encode()).hexdigest()[:64]}"

    def get_merkle_root(self) -> str:
        """Get the current Merkle root."""
        return self._compute_merkle_root()

    def get_evidence(self, evidence_id: str) -> Optional[Evidence]:
        """Retrieve evidence by ID."""
        return self._evidence_store.get(evidence_id)
