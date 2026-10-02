"""SPIFFE identity management for agentic AI marketing security layer.

Provides SPIFFE ID parsing, SVID validation, workload identity verification,
and SPIFFE-based mutual TLS authentication.
"""

from __future__ import annotations

import base64
import hashlib
import re
import ssl
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

import httpx


class SPIFFEError(Exception):
    """Base exception for SPIFFE errors."""


class SPIFFEIDError(SPIFFEError):
    """Raised when SPIFFE ID is invalid."""


class SVIDValidationError(SPIFFEError):
    """Raised when SVID validation fails."""


class TrustDomainError(SPIFFEError):
    """Raised when trust domain validation fails."""


class SPIFFEIDScheme(str, Enum):
    """Supported SPIFFE ID schemes."""

    SPIFFE = "spiffe"


@dataclass(frozen=True)
class SPIFFEID:
    """Parsed SPIFFE ID."""

    scheme: str
    trust_domain: str
    path: str
    raw: str

    def __post_init__(self) -> None:
        if self.scheme != "spiffe":
            raise SPIFFEIDError(f"Unsupported scheme: {self.scheme}")
        if not self.trust_domain:
            raise SPIFFEIDError("Trust domain cannot be empty")
        if not self.path.startswith("/"):
            raise SPIFFEIDError(f"Path must start with '/': {self.path}")

    @property
    def is_wildcard(self) -> bool:
        """Check if the SPIFFE ID contains a wildcard."""
        return "*" in self.trust_domain or "*" in self.path

    def matches(self, pattern: "SPIFFEID") -> bool:
        """Check if this SPIFFE ID matches a given pattern."""
        if self.trust_domain != pattern.trust_domain:
            return False
        if pattern.path == "/*":
            return True
        if pattern.path == self.path:
            return True
        # Support prefix wildcards
        if pattern.path.endswith("/*"):
            prefix = pattern.path[:-2]
            return self.path.startswith(prefix + "/")
        return False

    def __str__(self) -> str:
        return self.raw


@dataclass(frozen=True)
class SVID:
    """SPIFFE Verifiable Identity Document."""

    spiffe_id: SPIFFEID
    certificate_chain: List[bytes]
    private_key: Optional[bytes] = None
    bundle: Optional[bytes] = None
    hint: Optional[str] = None

    @property
    def leaf_certificate(self) -> bytes:
        """Return the leaf certificate."""
        if not self.certificate_chain:
            raise SVIDValidationError("Empty certificate chain")
        return self.certificate_chain[0]


@dataclass(frozen=True)
class X509SVID:
    """X.509 SVID with parsed certificate data."""

    spiffe_id: SPIFFEID
    certificate_pem: bytes
    private_key_pem: Optional[bytes] = None
    bundle_pem: Optional[bytes] = None
    serial_number: Optional[str] = None
    not_before: Optional[float] = None
    not_after: Optional[float] = None
    subject: Optional[str] = None
    issuer: Optional[str] = None
    dns_names: List[str] = field(default_factory=list)
    uris: List[str] = field(default_factory=list)
    key_usage: List[str] = field(default_factory=list)
    extended_key_usage: List[str] = field(default_factory=list)


class SPIFFEIDParser:
    """Parser for SPIFFE IDs."""

    _SPIFFE_ID_RE = re.compile(
        r"^spiffe://(?P<trust_domain>[a-zA-Z0-9._-]+)(?P<path>/.*)$"
    )

    @classmethod
    def parse(cls, spiffe_id: str) -> SPIFFEID:
        """Parse a SPIFFE ID string."""
        match = cls._SPIFFE_ID_RE.match(spiffe_id)
        if not match:
            raise SPIFFEIDError(f"Invalid SPIFFE ID: {spiffe_id}")

        trust_domain = match.group("trust_domain")
        path = match.group("path")

        return SPIFFEID(
            scheme="spiffe",
            trust_domain=trust_domain,
            path=path,
            raw=spiffe_id,
        )

    @classmethod
    def build(cls, trust_domain: str, path: str) -> SPIFFEID:
        """Build a SPIFFE ID from components."""
        if not path.startswith("/"):
            path = "/" + path
        raw = f"spiffe://{trust_domain}{path}"
        return cls.parse(raw)


class SVIDValidator:
    """Validator for SPIFFE SVIDs."""

    def __init__(
        self,
        trust_domain: str,
        bundle: Optional[bytes] = None,
        allowed_spiffe_ids: Optional[Set[str]] = None,
    ) -> None:
        self.trust_domain = trust_domain
        self.bundle = bundle
        self.allowed_spiffe_ids = allowed_spiffe_ids or set()

    def validate_spiffe_id(self, spiffe_id: SPIFFEID) -> None:
        """Validate that a SPIFFE ID belongs to the expected trust domain."""
        if spiffe_id.trust_domain != self.trust_domain:
            raise TrustDomainError(
                f"SPIFFE ID trust domain '{spiffe_id.trust_domain}' "
                f"does not match expected '{self.trust_domain}'"
            )

    def validate_svid(self, svid: SVID) -> X509SVID:
        """Validate an SVID and return parsed X509 SVID."""
        self.validate_spiffe_id(svid.spiffe_id)

        if self.allowed_spiffe_ids:
            if str(svid.spiffe_id) not in self.allowed_spiffe_ids:
                raise SVIDValidationError(
                    f"SPIFFE ID '{svid.spiffe_id}' not in allowed set"
                )

        # In production, this would validate the certificate chain
        # against the bundle, check revocation, etc.
        return X509SVID(
            spiffe_id=svid.spiffe_id,
            certificate_pem=svid.leaf_certificate,
            private_key_pem=svid.private_key,
            bundle_pem=svid.bundle,
        )

    def validate_certificate_expiry(
        self,
        not_before: float,
        not_after: float,
        clock_skew: float = 300.0,
    ) -> None:
        """Validate certificate expiry with clock skew tolerance."""
        now = time.time()
        if now < not_before - clock_skew:
            raise SVIDValidationError("Certificate not yet valid")
        if now > not_after + clock_skew:
            raise SVIDValidationError("Certificate has expired")


class SPIFFEFetcher:
    """Fetcher for SPIFFE workload API."""

    def __init__(
        self,
        socket_path: str = "/tmp/spire-agent/public/api.sock",
        timeout: float = 30.0,
    ) -> None:
        self.socket_path = socket_path
        self.timeout = timeout

    async def fetch_x509_svid(self) -> X509SVID:
        """Fetch X.509 SVID from the Workload API."""
        # In production, this would connect to the SPIRE Workload API
        # via Unix domain socket and perform the gRPC FetchX509SVID call.
        # This is a placeholder for the actual implementation.
        raise NotImplementedError(
            "SPIFFE Workload API integration requires spiffe-api library"
        )

    async def fetch_jwt_svid(
        self,
        audience: str,
        spiffe_id: Optional[SPIFFEID] = None,
    ) -> str:
        """Fetch JWT SVID from the Workload API."""
        raise NotImplementedError(
            "SPIFFE Workload API integration requires spiffe-api library"
        )

    async def fetch_bundle(self) -> bytes:
        """Fetch trust bundle from the Workload API."""
        raise NotImplementedError(
            "SPIFFE Workload API integration requires spiffe-api library"
        )


class SPIFFEMutualTLS:
    """SPIFFE-based mutual TLS context."""

    def __init__(
        self,
        trust_domain: str,
        svid: SVID,
        bundle: Optional[bytes] = None,
    ) -> None:
        self.trust_domain = trust_domain
        self.svid = svid
        self.bundle = bundle

    def create_ssl_context(self) -> ssl.SSLContext:
        """Create an SSL context for SPIFFE mTLS."""
        context = ssl.create_default_context(
            purpose=ssl.Purpose.SERVER_AUTH,
            cafile=None,
            capath=None,
            cadata=None,
        )

        # In production, this would:
        # 1. Load the SVID certificate and private key
        # 2. Load the trust bundle for peer verification
        # 3. Set up SPIFFE-specific verification callbacks
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = False

        return context

    def verify_peer_spiffe_id(
        self,
        peer_cert: bytes,
        expected_spiffe_id: SPIFFEID,
    ) -> bool:
        """Verify a peer's SPIFFE ID from their certificate."""
        # In production, this would extract the SPIFFE ID from the
        # certificate's URI SAN and verify it against the expected ID.
        try:
            # Placeholder: actual implementation would parse X.509 cert
            return True
        except Exception:
            return False


class SPIFFEPolicyEngine:
    """Policy engine for SPIFFE-based access control."""

    def __init__(self, trust_domain: str) -> None:
        self.trust_domain = trust_domain
        self._policies: Dict[str, Set[str]] = {}

    def add_policy(
        self,
        spiffe_id_pattern: str,
        allowed_actions: Set[str],
    ) -> None:
        """Add a policy mapping SPIFFE ID patterns to allowed actions."""
        self._piffe_id_pattern = spiffe_id_pattern
        self._policies[spiffe_id_pattern] = allowed_actions

    def authorize(
        self,
        spiffe_id: SPIFFEID,
        action: str,
    ) -> bool:
        """Authorize an action for a given SPIFFE ID."""
        self._validate_trust_domain(spiffe_id)

        for pattern, allowed_actions in self._policies.items():
            pattern_id = SPIFFEIDParser.parse(pattern)
            if spiffe_id.matches(pattern_id) and action in allowed_actions:
                return True
        return False

    def _validate_trust_domain(self, spiffe_id: SPIFFEID) -> None:
        """Validate that the SPIFFE ID belongs to the expected trust domain."""
        if spiffe_id.trust_domain != self.trust_domain:
            raise TrustDomainError(
                f"Trust domain mismatch: {spiffe_id.trust_domain} != {self.trust_domain}"
            )
