"""Authentication security tests for GRC_Claw.

Tests JWT token lifecycle, OAuth2/OIDC flows, SPIFFE identity
verification, and token binding to ensure robust authentication
security across the platform.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
import uuid
from base64 import urlsafe_b64encode, urlsafe_b64decode
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from auth.jwt import (
    HMACKeyStore,
    JWTAlgorithm,
    JWTError,
    JWTExpiredError,
    JWTAudienceError,
    JWTIssuerError,
    JWTManager,
    JWTPayload,
    JWTRevocationStore,
    JWTValidationError,
    TokenBinding,
)
from auth.oauth2 import (
    GrantType,
    OAuth2Client,
    OAuth2Error,
    OIDCConfiguration,
    PKCEPair,
    TokenSet,
    generate_pkce_pair,
)
from auth.spiffe import (
    SPIFFEID,
    SPIFFEIDError,
    SPIFFEIDParser,
    SPIFFEIDScheme,
    SPIFFEMutualTLS,
    SPIFFEPolicyEngine,
    SPIFFEError,
    SPIFFEFetcher,
    SVID,
    SVIDValidationError,
    SVIDValidator,
    TrustDomainError,
    X509SVID,
)


# ===========================================================================
# JWT Token Creation Tests
# ===========================================================================


class TestJWTTokenCreation:
    """Tests for JWT token creation and encoding."""

    def test_create_token_returns_valid_jwt(
        self, jwt_manager: JWTManager, sample_user_id: str
    ) -> None:
        """Verify that create_token returns a properly formatted JWT."""
        token = jwt_manager.create_token(
            subject=sample_user_id,
            claims={"role": "admin"},
            expires_in=3600,
        )
        parts = token.split(".")
        assert len(parts) == 3, "JWT must have exactly 3 parts"

    def test_create_token_contains_expected_claims(
        self, jwt_manager: JWTManager, sample_user_id: str
    ) -> None:
        """Verify that created tokens contain the expected claims."""
        token = jwt_manager.create_token(
            subject=sample_user_id,
            claims={"role": "admin", "email": "test@example.com"},
            expires_in=3600,
        )
        payload = jwt_manager.decode_token(token, verify=False)
        assert payload.sub == sample_user_id
        assert payload.custom_claims["role"] == "admin"
        assert payload.custom_claims["email"] == "test@example.com"
        assert payload.iss == "https://test.grc-claw.local"
        assert payload.aud == "test-api"

    def test_create_token_sets_expiration(
        self, jwt_manager: JWTManager, sample_user_id: str
    ) -> None:
        """Verify that tokens have correct expiration time."""
        expires_in = 1800
        before = int(time.time())
        token = jwt_manager.create_token(
            subject=sample_user_id,
            expires_in=expires_in,
        )
        after = int(time.time())
        payload = jwt_manager.decode_token(token, verify=False)
        assert payload.exp is not None
        assert before + expires_in <= payload.exp <= after + expires_in

    def test_create_token_generates_unique_jti(
        self, jwt_manager: JWTManager, sample_user_id: str
    ) -> None:
        """Verify that each token gets a unique JTI."""
        tokens = [
            jwt_manager.create_token(subject=sample_user_id, expires_in=3600)
            for _ in range(10)
        ]
        jtis = set()
        for token in tokens:
            payload = jwt_manager.decode_token(token, verify=False)
            assert payload.jti is not None
            jtis.add(payload.jti)
        assert len(jtis) == 10, "All JTIs must be unique"

    def test_create_token_with_custom_claims(
        self, jwt_manager: JWTManager, sample_user_id: str
    ) -> None:
        """Verify that custom claims are preserved in the token."""
        custom = {
            "department": "engineering",
            "clearance": "top-secret",
            "project_ids": ["proj-1", "proj-2"],
        }
        token = jwt_manager.create_token(
            subject=sample_user_id,
            claims=custom,
            expires_in=3600,
        )
        payload = jwt_manager.decode_token(token, verify=False)
        assert payload.custom_claims["department"] == "engineering"
        assert payload.custom_claims["clearance"] == "top-secret"
        assert payload.custom_claims["project_ids"] == ["proj-1", "proj-2"]

    def test_create_token_with_different_algorithms(
        self, jwt_key_store: HMACKeyStore, sample_user_id: str
    ) -> None:
        """Verify token creation with different HMAC algorithms."""
        for alg in ["HS256", "HS384", "HS512"]:
            manager = JWTManager(
                key_store=jwt_key_store,
                default_algorithm=alg,
                clock_skew=0,
            )
            token = manager.create_token(
                subject=sample_user_id,
                algorithm=alg,
                expires_in=3600,
            )
            payload = manager.verify_token(token, algorithms=[alg])
            assert payload.sub == sample_user_id

    def test_create_token_rejects_unsupported_algorithm(
        self, jwt_manager: JWTManager, sample_user_id: str
    ) -> None:
        """Verify that unsupported algorithms are rejected."""
        with pytest.raises(JWTError, match="Unsupported algorithm"):
            jwt_manager.create_token(
                subject=sample_user_id,
                algorithm="none",
                expires_in=3600,
            )

    def test_create_token_with_extra_header(
        self, jwt_manager: JWTManager, sample_user_id: str
    ) -> None:
        """Verify that extra header fields are included."""
        token = jwt_manager.create_token(
            subject=sample_user_id,
            expires_in=3600,
            extra_header={"kid": "custom-key-id", "cty": "JWT"},
        )
        decoded = jwt_manager.decode_token(token, verify=False)
        assert decoded.header.kid == "custom-key-id"
        assert decoded.header.cty == "JWT"


# ===========================================================================
# JWT Token Verification Tests
# ===========================================================================


class TestJWTTokenVerification:
    """Tests for JWT token verification and validation."""

    def test_verify_valid_token(
        self, jwt_manager: JWTManager, jwt_token: str, sample_user_id: str
    ) -> None:
        """Verify that a valid token passes verification."""
        payload = jwt_manager.verify_token(jwt_token)
        assert payload.sub == sample_user_id

    def test_verify_expired_token_raises_error(
        self, jwt_manager: JWTManager, expired_jwt_token: str
    ) -> None:
        """Verify that expired tokens are rejected."""
        with pytest.raises(JWTExpiredError):
            jwt_manager.verify_token(expired_jwt_token)

    def test_verify_token_with_wrong_issuer(
        self, jwt_manager: JWTManager, jwt_token: str
    ) -> None:
        """Verify that tokens with wrong issuer are rejected."""
        with pytest.raises(JWTIssuerError):
            jwt_manager.verify_token(jwt_token, issuer="https://evil.local")

    def test_verify_token_with_wrong_audience(
        self, jwt_manager: JWTManager, jwt_token: str
    ) -> None:
        """Verify that tokens with wrong audience are rejected."""
        with pytest.raises(JWTAudienceError):
            jwt_manager.verify_token(jwt_token, audience="wrong-api")

    def test_verify_token_with_disallowed_algorithm(
        self, jwt_manager: JWTManager, jwt_token: str
    ) -> None:
        """Verify that tokens with disallowed algorithms are rejected."""
        with pytest.raises(JWTValidationError):
            jwt_manager.verify_token(jwt_token, algorithms=["HS512"])

    def test_verify_tampered_token_fails(
        self, jwt_manager: JWTManager, jwt_token: str
    ) -> None:
        """Verify that tampered tokens fail signature verification."""
        parts = jwt_token.split(".")
        # Tamper with the payload
        payload_data = json.loads(urlsafe_b64decode(parts[1] + "=="))
        payload_data["role"] = "super-admin"
        tampered_payload = urlsafe_b64encode(
            json.dumps(payload_data).encode()
        ).rstrip(b"=").decode()
        tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"
        with pytest.raises(JWTValidationError, match="Invalid signature"):
            jwt_manager.verify_token(tampered_token)

    def test_verify_token_with_leeway(
        self, jwt_manager: JWTManager, sample_user_id: str
    ) -> None:
        """Verify that leeway allows slightly expired tokens."""
        # Create a token that expired 10 seconds ago
        token = jwt_manager.create_token(
            subject=sample_user_id,
            expires_in=-10,
        )
        # Should fail without leeway
        with pytest.raises(JWTExpiredError):
            jwt_manager.verify_token(token)
        # Should pass with sufficient leeway
        payload = jwt_manager.verify_token(token, leeway=30)
        assert payload.sub == sample_user_id

    def test_verify_malformed_token_raises_error(
        self, jwt_manager: JWTManager
    ) -> None:
        """Verify that malformed tokens are rejected."""
        with pytest.raises(JWTValidationError):
            jwt_manager.verify_token("not.a.valid.jwt")
        with pytest.raises(JWTValidationError):
            jwt_manager.verify_token("only-two-parts")
        with pytest.raises(JWTValidationError):
            jwt_manager.verify_token("")

    def test_verify_token_with_not_before(
        self, jwt_manager: JWTManager, sample_user_id: str
    ) -> None:
        """Verify that not-yet-valid tokens are rejected."""
        future_token = jwt_manager.create_token(
            subject=sample_user_id,
            not_before=3600,  # Valid 1 hour from now
            expires_in=7200,
        )
        with pytest.raises(JWTValidationError, match="not yet valid"):
            jwt_manager.verify_token(future_token)


# ===========================================================================
# JWT Key Management Tests
# ===========================================================================


class TestJWTKeyManagement:
    """Tests for JWT key store and rotation."""

    def test_key_store_generates_unique_keys(self) -> None:
        """Verify that key store generates unique keys."""
        store = HMACKeyStore()
        key_id_1 = store.generate_key()
        key_id_2 = store.generate_key()
        assert key_id_1 != key_id_2
        key_1 = store.get_key(key_id_1)
        key_2 = store.get_key(key_id_2)
        assert key_1 != key_2

    def test_key_store_rotation(self) -> None:
        """Verify that key rotation works correctly."""
        store = HMACKeyStore()
        old_key_id = store.generate_key()
        old_key = store.get_key(old_key_id)
        new_key_id = store.rotate()
        new_key = store.get_key(new_key_id)
        assert new_key_id != old_key_id
        assert new_key != old_key
        # Old key should still be available
        assert store.get_key(old_key_id) == old_key

    def test_key_store_cannot_remove_current_key(self) -> None:
        """Verify that the current signing key cannot be removed."""
        store = HMACKeyStore()
        key_id = store.generate_key()
        with pytest.raises(JWTError, match="Cannot remove the current"):
            store.remove_key(key_id)

    def test_key_store_set_current_key(self) -> None:
        """Verify that the current key can be switched."""
        store = HMACKeyStore()
        key_id_1 = store.generate_key()
        key_id_2 = store.generate_key()
        store.set_current_key(key_id_1)
        current_id, _ = store.get_current_key()
        assert current_id == key_id_1

    def test_key_store_set_nonexistent_key_raises(self) -> None:
        """Verify that setting a non-existent key raises an error."""
        store = HMACKeyStore()
        with pytest.raises(JWTError, match="not found"):
            store.set_current_key("nonexistent-key")

    def test_key_store_add_existing_key(self) -> None:
        """Verify that existing keys can be added to the store."""
        store = HMACKeyStore()
        key_bytes = secrets.token_bytes(64)
        store.add_key("imported-key", key_bytes)
        assert store.get_key("imported-key") == key_bytes

    def test_key_store_list_keys(self) -> None:
        """Verify that all key IDs are listed."""
        store = HMACKeyStore()
        ids = [store.generate_key() for _ in range(3)]
        assert set(store.list_keys()) == set(ids)


# ===========================================================================
# JWT Token Refresh Tests
# ===========================================================================


class TestJWTTokenRefresh:
    """Tests for JWT token refresh and revocation."""

    def test_refresh_token_creates_new_token(
        self, jwt_manager: JWTManager, jwt_token: str, sample_user_id: str
    ) -> None:
        """Verify that refresh creates a new valid token."""
        new_token = jwt_manager.refresh_token(jwt_token)
        assert new_token != jwt_token
        payload = jwt_manager.verify_token(new_token)
        assert payload.sub == sample_user_id

    def test_refresh_token_rotates_jti(
        self, jwt_manager: JWTManager, jwt_token: str
    ) -> None:
        """Verify that refresh rotates the JTI by default."""
        old_payload = jwt_manager.decode_token(jwt_token, verify=False)
        new_token = jwt_manager.refresh_token(jwt_token, rotate_jti=True)
        new_payload = jwt_manager.decode_token(new_token, verify=False)
        assert new_payload.jti != old_payload.jti
        assert new_payload.custom_claims.get("original_jti") == old_payload.jti

    def test_refresh_token_without_jti_rotation(
        self, jwt_manager: JWTManager, jwt_token: str
    ) -> None:
        """Verify that refresh can preserve JTI."""
        old_payload = jwt_manager.decode_token(jwt_token, verify=False)
        new_token = jwt_manager.refresh_token(jwt_token, rotate_jti=False)
        new_payload = jwt_manager.decode_token(new_token, verify=False)
        assert new_payload.jti != old_payload.jti  # Still new JTI from create_token
        assert "original_jti" not in new_payload.custom_claims

    def test_revoke_token_adds_to_revocation_store(
        self, jwt_manager: JWTManager, jwt_token: str, jwt_revocation_store: JWTRevocationStore
    ) -> None:
        """Verify that revocation adds the token JTI to the store."""
        jwt_manager.revoke_token(jwt_token, jwt_revocation_store)
        payload = jwt_manager.decode_token(jwt_token, verify=False)
        assert jwt_revocation_store.is_revoked(payload.jti)

    def test_revocation_store_cleanup(self) -> None:
        """Verify that expired revocations are cleaned up."""
        store = JWTRevocationStore()
        store.revoke("jti-1", int(time.time()) - 100)  # Expired
        store.revoke("jti-2", int(time.time()) + 1000)  # Not expired
        removed = store.cleanup()
        assert removed == 1
        assert not store.is_revoked("jti-1")
        assert store.is_revoked("jti-2")


# ===========================================================================
# Token Binding Tests
# ===========================================================================


class TestTokenBinding:
    """Tests for token binding security."""

    def test_bind_token_to_session(self) -> None:
        """Verify that tokens can be bound to sessions."""
        binding = TokenBinding()
        binding.bind_token("jti-123", "session-abc")
        assert binding.verify_binding("jti-123", "session-abc")

    def test_verify_binding_fails_for_wrong_session(self) -> None:
        """Verify that binding verification fails for wrong session."""
        binding = TokenBinding()
        binding.bind_token("jti-123", "session-abc")
        assert not binding.verify_binding("jti-123", "session-xyz")

    def test_unbind_token(self) -> None:
        """Verify that tokens can be unbound."""
        binding = TokenBinding()
        binding.bind_token("jti-123", "session-abc")
        binding.unbind_token("jti-123")
        assert not binding.verify_binding("jti-123", "session-abc")

    def test_verify_unbound_token_returns_false(self) -> None:
        """Verify that unbound tokens return False."""
        binding = TokenBinding()
        assert not binding.verify_binding("nonexistent-jti", "session-abc")


# ===========================================================================
# OAuth2/OIDC Tests
# ===========================================================================


class TestOAuth2Security:
    """Tests for OAuth2/OIDC authentication security."""

    def test_pkce_pair_generation(self) -> None:
        """Verify that PKCE pairs are generated correctly."""
        pair = generate_pkce_pair()
        assert len(pair.code_verifier) >= 43
        assert pair.code_challenge_method == "S256"
        # Verify challenge is SHA256 of verifier
        expected = urlsafe_b64encode(
            hashlib.sha256(pair.code_verifier.encode()).digest()
        ).rstrip(b"=").decode()
        assert pair.code_challenge == expected

    def test_pkce_pairs_are_unique(self) -> None:
        """Verify that each PKCE pair is unique."""
        pairs = [generate_pkce_pair() for _ in range(10)]
        verifiers = {p.code_verifier for p in pairs}
        challenges = {p.code_challenge for p in pairs}
        assert len(verifiers) == 10
        assert len(challenges) == 10

    def test_oauth2_client_initialization(self) -> None:
        """Verify OAuth2 client initialization."""
        client = OAuth2Client(
            client_id="test-client",
            client_secret="test-secret",
            redirect_uri="https://app.test.local/callback",
        )
        assert client.client_id == "test-client"
        assert client.client_secret == "test-secret"
        assert client.redirect_uri == "https://app.test.local/callback"

    def test_build_authorization_url_contains_required_params(
        self, oauth2_config: OIDCConfiguration
    ) -> None:
        """Verify authorization URL contains all required parameters."""
        client = OAuth2Client(
            client_id="test-client",
            redirect_uri="https://app.test.local/callback",
        )
        client._config = oauth2_config
        url = client.build_authorization_url(
            state="test-state-123",
            scope=["openid", "profile"],
        )
        assert "response_type=code" in url
        assert "client_id=test-client" in url
        assert "state=test-state-123" in url
        assert "redirect_uri=" in url
        assert "scope=openid+profile" in url or "scope=openid%20profile" in url

    def test_build_authorization_url_includes_pkce(
        self, oauth2_config: OIDCConfiguration, pkce_pair: PKCEPair
    ) -> None:
        """Verify that PKCE parameters are included in authorization URL."""
        client = OAuth2Client(client_id="test-client")
        client._config = oauth2_config
        url = client.build_authorization_url(
            state="test-state",
            pkce_pair=pkce_pair,
        )
        assert f"code_challenge={pkce_pair.code_challenge}" in url
        assert "code_challenge_method=S256" in url

    def test_build_authorization_url_without_config_raises(self) -> None:
        """Verify that building URL without config raises an error."""
        client = OAuth2Client(client_id="test-client")
        with pytest.raises(OAuth2Error, match="OIDC configuration not loaded"):
            client.build_authorization_url(state="test-state")

    def test_token_set_expiration_check(self) -> None:
        """Verify TokenSet expiration detection."""
        token = TokenSet(
            access_token="test-token",
            token_type="Bearer",
            expires_in=3600,
            obtained_at=time.time() - 3601,  # Obtained 3601 seconds ago
        )
        assert token.is_expired

    def test_token_set_not_expired(self) -> None:
        """Verify TokenSet reports not expired for fresh tokens."""
        token = TokenSet(
            access_token="test-token",
            token_type="Bearer",
            expires_in=3600,
            obtained_at=time.time(),
        )
        assert not token.is_expired

    def test_token_set_scopes_parsing(self) -> None:
        """Verify that scopes are correctly parsed."""
        token = TokenSet(
            access_token="test-token",
            token_type="Bearer",
            expires_in=3600,
            scope="openid profile email",
        )
        assert token.scopes == ["openid", "profile", "email"]

    def test_grant_type_enum_values(self) -> None:
        """Verify OAuth2 grant type enum values."""
        assert GrantType.AUTHORIZATION_CODE.value == "authorization_code"
        assert GrantType.CLIENT_CREDENTIALS.value == "client_credentials"
        assert GrantType.REFRESH_TOKEN.value == "refresh_token"
        assert GrantType.DEVICE_CODE.value == "urn:ietf:params:oauth:grant-type:device_code"


# ===========================================================================
# SPIFFE Identity Tests
# ===========================================================================


class TestSPIFFEIdentity:
    """Tests for SPIFFE identity management and validation."""

    def test_parse_valid_spiffe_id(self) -> None:
        """Verify parsing of valid SPIFFE IDs."""
        spiffe_id = SPIFFEIDParser.parse("spiffe://test.local/ns/default/sa/test-sa")
        assert spiffe_id.scheme == "spiffe"
        assert spiffe_id.trust_domain == "test.local"
        assert spiffe_id.path == "/ns/default/sa/test-sa"

    def test_parse_invalid_spiffe_id_raises(self) -> None:
        """Verify that invalid SPIFFE IDs are rejected."""
        with pytest.raises(SPIFFEIDError):
            SPIFFEIDParser.parse("https://test.local/ns/default/sa/test-sa")
        with pytest.raises(SPIFFEIDError):
            SPIFFEIDParser.parse("spiffe:///no-trust-domain")
        with pytest.raises(SPIFFEIDError):
            SPIFFEIDParser.parse("")

    def test_build_spiffe_id(self) -> None:
        """Verify building SPIFFE IDs from components."""
        spiffe_id = SPIFFEIDParser.build("test.local", "/ns/default/sa/test-sa")
        assert spiffe_id.trust_domain == "test.local"
        assert spiffe_id.path == "/ns/default/sa/test-sa"
        assert str(spiffe_id) == "spiffe://test.local/ns/default/sa/test-sa"

    def test_build_spiffe_id_adds_leading_slash(self) -> None:
        """Verify that build adds leading slash to path if missing."""
        spiffe_id = SPIFFEIDParser.build("test.local", "ns/default/sa/test-sa")
        assert spiffe_id.path == "/ns/default/sa/test-sa"

    def test_spiffe_id_wildcard_detection(self) -> None:
        """Verify wildcard detection in SPIFFE IDs."""
        wildcard_id = SPIFFEIDParser.parse("spiffe://test.local/ns/*/sa/test-sa")
        assert wildcard_id.is_wildcard
        non_wildcard_id = SPIFFEIDParser.parse("spiffe://test.local/ns/default/sa/test-sa")
        assert not non_wildcard_id.is_wildcard

    def test_spiffe_id_matching(self) -> None:
        """Verify SPIFFE ID pattern matching."""
        spiffe_id = SPIFFEIDParser.parse("spiffe://test.local/ns/default/sa/test-sa")
        # Exact match
        exact = SPIFFEIDParser.parse("spiffe://test.local/ns/default/sa/test-sa")
        assert spiffe_id.matches(exact)
        # Wildcard match
        wildcard = SPIFFEIDParser.parse("spiffe://test.local/ns/*/sa/test-sa")
        assert spiffe_id.matches(wildcard)
        # Prefix wildcard match
        prefix = SPIFFEIDParser.parse("spiffe://test.local/ns/default/*")
        assert spiffe_id.matches(prefix)
        # No match - different trust domain
        different = SPIFFEIDParser.parse("spiffe://other.local/ns/default/sa/test-sa")
        assert not spiffe_id.matches(different)

    def test_svid_validator_validates_trust_domain(self) -> None:
        """Verify SVID validator checks trust domain."""
        validator = SVIDValidator(trust_domain="test.local")
        spiffe_id = SPIFFEIDParser.parse("spiffe://test.local/ns/default/sa/test-sa")
        # Should not raise
        validator.validate_spiffe_id(spiffe_id)

    def test_svid_validator_rejects_wrong_trust_domain(self) -> None:
        """Verify SVID validator rejects wrong trust domain."""
        validator = SVIDValidator(trust_domain="test.local")
        spiffe_id = SPIFFEIDParser.parse("spiffe://evil.local/ns/default/sa/test-sa")
        with pytest.raises(TrustDomainError):
            validator.validate_spiffe_id(spiffe_id)

    def test_svid_validator_allowed_spiffe_ids(self) -> None:
        """Verify SVID validator enforces allowed SPIFFE IDs."""
        validator = SVIDValidator(
            trust_domain="test.local",
            allowed_spiffe_ids={"spiffe://test.local/ns/default/sa/test-sa"},
        )
        allowed_id = SPIFFEIDParser.parse("spiffe://test.local/ns/default/sa/test-sa")
        # Should not raise
        validator.validate_spiffe_id(allowed_id)

        disallowed_id = SPIFFEIDParser.parse("spiffe://test.local/ns/other/sa/other-sa")
        with pytest.raises(SVIDValidationError):
            validator.validate_spiffe_id(disallowed_id)

    def test_svid_validator_certificate_expiry(self) -> None:
        """Verify certificate expiry validation."""
        validator = SVIDValidator(trust_domain="test.local")
        now = time.time()
        # Valid certificate
        validator.validate_certificate_expiry(now - 100, now + 1000)
        # Not yet valid
        with pytest.raises(SVIDValidationError, match="not yet valid"):
            validator.validate_certificate_expiry(now + 100, now + 1000)
        # Expired
        with pytest.raises(SVIDValidationError, match="expired"):
            validator.validate_certificate_expiry(now - 1000, now - 100)

    def test_spiffe_policy_engine_authorize(self) -> None:
        """Verify SPIFFE policy engine authorization."""
        engine = SPIFFEPolicyEngine(trust_domain="test.local")
        engine.add_policy(
            "spiffe://test.local/ns/default/sa/test-sa",
            {"read:data", "write:data"},
        )
        spiffe_id = SPIFFEIDParser.parse("spiffe://test.local/ns/default/sa/test-sa")
        assert engine.authorize(spiffe_id, "read:data")
        assert engine.authorize(spiffe_id, "write:data")
        assert not engine.authorize(spiffe_id, "delete:data")

    def test_spiffe_policy_engine_rejects_wrong_trust_domain(self) -> None:
        """Verify policy engine rejects wrong trust domain."""
        engine = SPIFFEPolicyEngine(trust_domain="test.local")
        spiffe_id = SPIFFEIDParser.parse("spiffe://evil.local/ns/default/sa/test-sa")
        with pytest.raises(TrustDomainError):
            engine.authorize(spiffe_id, "read:data")

    def test_spiffe_id_scheme_enum(self) -> None:
        """Verify SPIFFE ID scheme enum."""
        assert SPIFFEIDScheme.SPIFFE.value == "spiffe"


# ===========================================================================
# Authentication Security Edge Cases
# ===========================================================================


class TestAuthenticationEdgeCases:
    """Tests for authentication security edge cases."""

    def test_jwt_algorithm_confusion_attack_prevention(
        self, jwt_manager: JWTManager, jwt_token: str
    ) -> None:
        """Verify that algorithm confusion attacks are prevented."""
        # Try to verify with a different algorithm
        with pytest.raises(JWTValidationError):
            jwt_manager.verify_token(jwt_token, algorithms=["HS512"])

    def test_jwt_none_algorithm_rejected(
        self, jwt_manager: JWTManager, sample_user_id: str
    ) -> None:
        """Verify that 'none' algorithm is rejected."""
        with pytest.raises(JWTError, match="Unsupported algorithm"):
            jwt_manager.create_token(
                subject=sample_user_id,
                algorithm="none",
            )

    def test_jwt_with_empty_key_fails(self) -> None:
        """Verify that JWT operations fail gracefully with empty key."""
        store = HMACKeyStore()
        store.generate_key()
        # Replace key with empty bytes
        store._keys[store._current_key_id] = b""
        manager = JWTManager(key_store=store, clock_skew=0)
        token = manager.create_token(subject="test", expires_in=3600)
        # Verification should fail due to invalid signature
        with pytest.raises(JWTValidationError):
            manager.verify_token(token)

    def test_concurrent_token_creation_unique_jtis(
        self, jwt_manager: JWTManager
    ) -> None:
        """Verify that concurrent token creation produces unique JTIs."""
        import concurrent.futures

        def create_token(i: int) -> str:
            return jwt_manager.create_token(
                subject=f"user-{i}",
                expires_in=3600,
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            tokens = list(executor.map(create_token, range(50)))

        jtis = set()
        for token in tokens:
            payload = jwt_manager.decode_token(token, verify=False)
            jtis.add(payload.jti)
        assert len(jtis) == 50, "All JTIs must be unique even under concurrency"

    def test_token_binding_prevents_replay(self) -> None:
        """Verify that token binding prevents token replay attacks."""
        binding = TokenBinding()
        binding.bind_token("jti-123", "session-abc")
        # Token used from different session should fail
        assert not binding.verify_binding("jti-123", "session-xyz")
        # Token used from correct session should pass
        assert binding.verify_binding("jti-123", "session-abc")
