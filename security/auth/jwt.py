"""JWT token management for agentic AI marketing security layer.

Provides JWT creation, validation, key rotation, token binding,
and secure token storage with full lifecycle management.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import uuid
from base64 import urlsafe_b64encode, urlsafe_b64decode
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union


class JWTError(Exception):
    """Base exception for JWT errors."""


class JWTValidationError(JWTError):
    """Raised when JWT validation fails."""


class JWTExpiredError(JWTValidationError):
    """Raised when JWT has expired."""


class JWTIssuerError(JWTValidationError):
    """Raised when JWT issuer is invalid."""


class JWTAudienceError(JWTValidationError):
    """Raised when JWT audience is invalid."""


class JWTAlgorithm(str, Enum):
    """Supported JWT signing algorithms."""

    HS256 = "HS256"
    HS384 = "HS384"
    HS512 = "HS512"
    RS256 = "RS256"
    RS384 = "RS384"
    RS512 = "RS512"
    ES256 = "ES256"
    ES384 = "ES384"
    ES512 = "ES512"
    EdDSA = "EdDSA"


@dataclass(frozen=True)
class JWTHeader:
    """JWT header."""

    alg: str
    typ: str = "JWT"
    kid: Optional[str] = None
    cty: Optional[str] = None
    crit: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result: Dict[str, Any] = {"alg": self.alg, "typ": self.typ}
        if self.kid:
            result["kid"] = self.kid
        if self.cty:
            result["cty"] = self.cty
        if self.crit:
            result["crit"] = self.crit
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JWTHeader":
        """Create from dictionary."""
        return cls(
            alg=data["alg"],
            typ=data.get("typ", "JWT"),
            kid=data.get("kid"),
            cty=data.get("cty"),
            crit=data.get("crit"),
        )


@dataclass(frozen=True)
class JWTPayload:
    """JWT payload (claims)."""

    iss: Optional[str] = None
    sub: Optional[str] = None
    aud: Optional[Union[str, List[str]]] = None
    exp: Optional[int] = None
    nbf: Optional[int] = None
    iat: Optional[int] = None
    jti: Optional[str] = None
    custom_claims: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result: Dict[str, Any] = {}
        if self.iss is not None:
            result["iss"] = self.iss
        if self.sub is not None:
            result["sub"] = self.sub
        if self.aud is not None:
            result["aud"] = self.aud
        if self.exp is not None:
            result["exp"] = self.exp
        if self.nbf is not None:
            result["nbf"] = self.nbf
        if self.iat is not None:
            result["iat"] = self.iat
        if self.jti is not None:
            result["jti"] = self.jti
        result.update(self.custom_claims)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JWTPayload":
        """Create from dictionary."""
        standard_claims = {"iss", "sub", "aud", "exp", "nbf", "iat", "jti"}
        custom = {k: v for k, v in data.items() if k not in standard_claims}
        return cls(
            iss=data.get("iss"),
            sub=data.get("sub"),
            aud=data.get("aud"),
            exp=data.get("exp"),
            nbf=data.get("nbf"),
            iat=data.get("iat"),
            jti=data.get("jti"),
            custom_claims=custom,
        )


@dataclass(frozen=True)
class DecodedJWT:
    """Decoded JWT with header, payload, and signature."""

    header: JWTHeader
    payload: JWTPayload
    signature: bytes
    signing_input: bytes

    @property
    def is_expired(self) -> bool:
        """Check if token is expired."""
        if self.payload.exp is None:
            return False
        return time.time() >= self.payload.exp

    @property
    def is_not_yet_valid(self) -> bool:
        """Check if token is not yet valid."""
        if self.payload.nbf is None:
            return False
        return time.time() < self.payload.nbf


class HMACKeyStore:
    """HMAC key store with rotation support."""

    def __init__(self) -> None:
        self._keys: Dict[str, bytes] = {}
        self._current_key_id: Optional[str] = None

    def generate_key(self, key_id: Optional[str] = None) -> str:
        """Generate a new HMAC key."""
        key_id = key_id or str(uuid.uuid4())
        self._keys[key_id] = secrets.token_bytes(64)
        self._current_key_id = key_id
        return key_id

    def add_key(self, key_id: str, key_bytes: bytes) -> None:
        """Add an existing key."""
        self._keys[key_id] = key_bytes

    def get_key(self, key_id: str) -> Optional[bytes]:
        """Get a key by ID."""
        return self._keys.get(key_id)

    def get_current_key(self) -> Tuple[str, bytes]:
        """Get the current signing key."""
        if not self._current_key_id:
            raise JWTError("No current key set")
        return self._current_key_id, self._keys[self._current_key_id]

    def set_current_key(self, key_id: str) -> None:
        """Set the current signing key."""
        if key_id not in self._keys:
            raise JWTError(f"Key '{key_id}' not found")
        self._current_key_id = key_id

    def remove_key(self, key_id: str) -> None:
        """Remove a key."""
        if key_id == self._current_key_id:
            raise JWTError("Cannot remove the current signing key")
        self._keys.pop(key_id, None)

    def list_keys(self) -> List[str]:
        """List all key IDs."""
        return list(self._keys.keys())

    def rotate(self) -> str:
        """Rotate to a new key."""
        return self.generate_key()


class JWTManager:
    """JWT token manager with full lifecycle support."""

    _ALGORITHMS = {
        "HS256": hashlib.sha256,
        "HS384": hashlib.sha384,
        "HS512": hashlib.sha512,
    }

    def __init__(
        self,
        key_store: Optional[HMACKeyStore] = None,
        default_algorithm: str = "HS256",
        issuer: Optional[str] = None,
        audience: Optional[Union[str, List[str]]] = None,
        clock_skew: int = 30,
    ) -> None:
        self.key_store = key_store or HMACKeyStore()
        self.default_algorithm = default_algorithm
        self.issuer = issuer
        self.audience = audience
        self.clock_skew = clock_skew

    def create_token(
        self,
        subject: str,
        claims: Optional[Dict[str, Any]] = None,
        algorithm: Optional[str] = None,
        expires_in: int = 3600,
        not_before: int = 0,
        audience: Optional[Union[str, List[str]]] = None,
        issuer: Optional[str] = None,
        key_id: Optional[str] = None,
        extra_header: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new JWT token."""
        alg = algorithm or self.default_algorithm
        if alg not in self._ALGORITHMS:
            raise JWTError(f"Unsupported algorithm: {alg}")

        now = int(time.time())
        jti = str(uuid.uuid4())

        payload = JWTPayload(
            iss=issuer or self.issuer,
            sub=subject,
            aud=audience or self.audience,
            exp=now + expires_in,
            nbf=now + not_before,
            iat=now,
            jti=jti,
            custom_claims=claims or {},
        )

        header = JWTHeader(
            alg=alg,
            kid=key_id or (self.key_store._current_key_id if self.key_store else None),
        )

        if extra_header:
            header_dict = header.to_dict()
            header_dict.update(extra_header)
            header = JWTHeader.from_dict(header_dict)

        return self._encode(header, payload, alg)

    def decode_token(
        self,
        token: str,
        verify: bool = True,
        algorithms: Optional[List[str]] = None,
        audience: Optional[Union[str, List[str]]] = None,
        issuer: Optional[str] = None,
        leeway: Optional[int] = None,
    ) -> DecodedJWT:
        """Decode and optionally verify a JWT token."""
        parts = token.split(".")
        if len(parts) != 3:
            raise JWTValidationError("Invalid JWT format: expected 3 parts")

        header_b64, payload_b64, signature_b64 = parts

        try:
            header_json = self._b64_decode(header_b64)
            payload_json = self._b64_decode(payload_b64)
            signature = self._b64_decode(signature_b64, pad=False)
        except Exception as exc:
            raise JWTValidationError(f"Failed to decode JWT: {exc}") from exc

        try:
            header = JWTHeader.from_dict(json.loads(header_json))
            payload = JWTPayload.from_dict(json.loads(payload_json))
        except (json.JSONDecodeError, KeyError) as exc:
            raise JWTValidationError(f"Invalid JWT structure: {exc}") from exc

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

        decoded = DecodedJWT(
            header=header,
            payload=payload,
            signature=signature,
            signing_input=signing_input,
        )

        if verify:
            self._verify(
                decoded,
                algorithms=algorithms,
                audience=audience,
                issuer=issuer,
                leeway=leeway,
            )

        return decoded

    def verify_token(
        self,
        token: str,
        algorithms: Optional[List[str]] = None,
        audience: Optional[Union[str, List[str]]] = None,
        issuer: Optional[str] = None,
        leeway: Optional[int] = None,
    ) -> JWTPayload:
        """Verify a JWT token and return its payload."""
        decoded = self.decode_token(
            token,
            verify=True,
            algorithms=algorithms,
            audience=audience,
            issuer=issuer,
            leeway=leeway,
        )
        return decoded.payload

    def refresh_token(
        self,
        token: str,
        expires_in: int = 3600,
        rotate_jti: bool = True,
    ) -> str:
        """Refresh a JWT token."""
        payload = self.verify_token(token)

        claims = dict(payload.custom_claims)
        if rotate_jti:
            claims["original_jti"] = payload.jti

        return self.create_token(
            subject=payload.sub or "",
            claims=claims,
            expires_in=expires_in,
            audience=payload.aud,
            issuer=payload.iss,
        )

    def revoke_token(self, token: str, revocation_store: "JWTRevocationStore") -> None:
        """Revoke a JWT token."""
        payload = self.verify_token(token)
        if payload.jti:
            revocation_store.revoke(payload.jti, payload.exp or 0)

    def _encode(self, header: JWTHeader, payload: JWTPayload, algorithm: str) -> str:
        """Encode a JWT token."""
        header_b64 = self._b64_encode(json.dumps(header.to_dict(), separators=(",", ":")))
        payload_b64 = self._b64_encode(json.dumps(payload.to_dict(), separators=(",", ":")))
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")

        if algorithm not in self._ALGORITHMS:
            raise JWTError(f"Unsupported algorithm: {algorithm}")

        _, key = self.key_store.get_current_key()
        hash_func = self._ALGORITHMS[algorithm]
        signature = hmac.new(key, signing_input, hash_func).digest()
        signature_b64 = self._b64_encode(signature)

        return f"{header_b64}.{payload_b64}.{signature_b64}"

    def _verify(
        self,
        decoded: DecodedJWT,
        algorithms: Optional[List[str]] = None,
        audience: Optional[Union[str, List[str]]] = None,
        issuer: Optional[str] = None,
        leeway: Optional[int] = None,
    ) -> None:
        """Verify a decoded JWT token."""
        skew = leeway if leeway is not None else self.clock_skew

        # Verify algorithm
        allowed_algs = algorithms or [self.default_algorithm]
        if decoded.header.alg not in allowed_algs:
            raise JWTValidationError(
                f"Algorithm '{decoded.header.alg}' not in allowed: {allowed_algs}"
            )

        # Verify signature
        if decoded.header.alg in self._ALGORITHMS:
            self._verify_hmac(decoded)
        else:
            raise JWTError(f"Unsupported algorithm: {decoded.header.alg}")

        # Verify expiration
        if decoded.payload.exp is not None:
            if time.time() > decoded.payload.exp + skew:
                raise JWTExpiredError("Token has expired")

        # Verify not before
        if decoded.payload.nbf is not None:
            if time.time() < decoded.payload.nbf - skew:
                raise JWTValidationError("Token is not yet valid")

        # Verify issuer
        expected_issuer = issuer or self.issuer
        if expected_issuer and decoded.payload.iss != expected_issuer:
            raise JWTIssuerError(
                f"Issuer mismatch: {decoded.payload.iss} != {expected_issuer}"
            )

        # Verify audience
        expected_aud = audience or self.audience
        if expected_aud:
            token_aud = decoded.payload.aud
            if isinstance(token_aud, str):
                token_aud = [token_aud]
            if isinstance(expected_aud, str):
                expected_aud = [expected_aud]
            if not set(token_aud or []) & set(expected_aud or []):
                raise JWTAudienceError(
                    f"Audience mismatch: {token_aud} does not contain any of {expected_aud}"
                )

    def _verify_hmac(self, decoded: DecodedJWT) -> None:
        """Verify HMAC signature."""
        if decoded.header.alg not in self._ALGORITHMS:
            raise JWTError(f"Unsupported algorithm: {decoded.header.alg}")

        key_id = decoded.header.kid
        if key_id:
            key = self.key_store.get_key(key_id)
            if key is None:
                raise JWTError(f"Key '{key_id}' not found")
        else:
            _, key = self.key_store.get_current_key()

        hash_func = self._ALGORITHMS[decoded.header.alg]
        expected_sig = hmac.new(key, decoded.signing_input, hash_func).digest()

        if not hmac.compare_digest(decoded.signature, expected_sig):
            raise JWTValidationError("Invalid signature")

    @staticmethod
    def _b64_encode(data: Union[str, bytes]) -> str:
        """Base64url encode."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    @staticmethod
    def _b64_decode(data: str, pad: bool = True) -> bytes:
        """Base64url decode."""
        if pad:
            padding = 4 - len(data) % 4
            if padding != 4:
                data += "=" * padding
        return urlsafe_b64decode(data)


class JWTRevocationStore:
    """JWT revocation store."""

    def __init__(self) -> None:
        self._revoked: Dict[str, int] = {}  # jti -> exp

    def revoke(self, jti: str, exp: int) -> None:
        """Revoke a token by JTI."""
        self._revoked[jti] = exp

    def is_revoked(self, jti: str) -> bool:
        """Check if a token is revoked."""
        return jti in self._revoked

    def cleanup(self) -> int:
        """Remove expired revocations. Returns count removed."""
        now = time.time()
        expired = [jti for jti, exp in self._revoked.items() if exp < now]
        for jti in expired:
            del self._revoked[jti]
        return len(expired)


class TokenBinding:
    """Token binding for enhanced security."""

    def __init__(self) -> None:
        self._bindings: Dict[str, str] = {}  # token_jti -> binding_id

    def bind_token(self, token_jti: str, binding_id: str) -> None:
        """Bind a token to a specific binding (e.g., TLS session)."""
        self._bindings[token_jti] = binding_id

    def verify_binding(self, token_jti: str, binding_id: str) -> bool:
        """Verify that a token is bound to the expected binding."""
        return self._bindings.get(token_jti) == binding_id

    def unbind_token(self, token_jti: str) -> None:
        """Remove a token binding."""
        self._bindings.pop(token_jti, None)
