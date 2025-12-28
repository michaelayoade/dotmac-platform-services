"""
Key Management for JWKS/OIDC support.

This module provides:
- Asymmetric key loading from PEM (RSA/EC)
- JWK Set generation for /.well-known/jwks.json
- Key rotation support with previous key fallback
- Dual-stack verification (asymmetric + HS256 fallback)
"""

import base64
import hashlib
from typing import Any

import structlog
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

logger = structlog.get_logger(__name__)


class KeyManager:
    """Manages asymmetric keys for JWT signing and JWKS endpoint.

    Supports:
    - RSA (RS256, RS384, RS512)
    - ECDSA (ES256, ES384, ES512)
    - Key rotation with previous key fallback
    - Graceful degradation to HS256
    """

    def __init__(self) -> None:
        """Initialize key manager from settings."""
        from ..settings import settings

        self.current_key_id: str = settings.auth.jwt_key_id
        self.algorithm: str = settings.auth.jwt_asymmetric_algorithm
        self.private_key: Any | None = None
        self.public_key: Any | None = None
        self.previous_keys: dict[str, Any] = {}  # kid -> public_key

        # Load current keys if configured
        if settings.auth.jwt_private_key:
            self._load_private_key(settings.auth.jwt_private_key)

        if settings.auth.jwt_public_key:
            self._load_public_key(settings.auth.jwt_public_key)
        elif self.private_key:
            # Derive public key from private key
            self.public_key = self.private_key.public_key()

        # Load previous keys for rotation window
        if settings.auth.jwt_previous_public_keys:
            self._load_previous_keys(settings.auth.jwt_previous_public_keys)

        logger.info(
            "key_manager.initialized",
            has_private_key=self.private_key is not None,
            has_public_key=self.public_key is not None,
            current_kid=self.current_key_id,
            previous_key_count=len(self.previous_keys),
            algorithm=self.algorithm,
        )

    def _load_private_key(self, pem_data: str) -> None:
        """Load private key from PEM string."""
        try:
            # Handle escaped newlines from env vars
            pem_data = pem_data.replace("\\n", "\n")
            pem_bytes = pem_data.encode()

            self.private_key = serialization.load_pem_private_key(
                pem_bytes,
                password=None,
            )
            logger.debug("key_manager.private_key_loaded")
        except Exception as e:
            logger.error("key_manager.private_key_load_failed", error=str(e))
            self.private_key = None

    def _load_public_key(self, pem_data: str) -> None:
        """Load public key from PEM string."""
        try:
            pem_data = pem_data.replace("\\n", "\n")
            pem_bytes = pem_data.encode()

            self.public_key = serialization.load_pem_public_key(pem_bytes)
            logger.debug("key_manager.public_key_loaded")
        except Exception as e:
            logger.error("key_manager.public_key_load_failed", error=str(e))
            self.public_key = None

    def _load_previous_keys(self, keys_string: str) -> None:
        """Load previous public keys from comma-separated format.

        Format: kid1:base64_pem,kid2:base64_pem,...
        """
        if not keys_string.strip():
            return

        for entry in keys_string.split(","):
            entry = entry.strip()
            if ":" not in entry:
                continue

            kid, b64_pem = entry.split(":", 1)
            try:
                pem_data = base64.b64decode(b64_pem).decode()
                pem_data = pem_data.replace("\\n", "\n")
                pem_bytes = pem_data.encode()

                public_key = serialization.load_pem_public_key(pem_bytes)
                self.previous_keys[kid] = public_key
                logger.debug("key_manager.previous_key_loaded", kid=kid)
            except Exception as e:
                logger.warning(
                    "key_manager.previous_key_load_failed",
                    kid=kid,
                    error=str(e),
                )

    def get_jwks(self) -> dict[str, list[dict[str, Any]]]:
        """Return JWK Set for /.well-known/jwks.json endpoint.

        Includes current key and all previous keys in rotation window.
        """
        keys: list[dict[str, Any]] = []

        # Add current public key
        if self.public_key:
            jwk = self._public_key_to_jwk(self.public_key, self.current_key_id)
            if jwk:
                keys.append(jwk)

        # Add previous keys for rotation window
        for kid, public_key in self.previous_keys.items():
            jwk = self._public_key_to_jwk(public_key, kid)
            if jwk:
                keys.append(jwk)

        return {"keys": keys}

    def _public_key_to_jwk(self, public_key: Any, kid: str) -> dict[str, Any] | None:
        """Convert a public key to JWK format."""
        try:
            if isinstance(public_key, rsa.RSAPublicKey):
                return self._rsa_to_jwk(public_key, kid)
            elif isinstance(public_key, ec.EllipticCurvePublicKey):
                return self._ec_to_jwk(public_key, kid)
            else:
                logger.warning("key_manager.unsupported_key_type", key_type=type(public_key))
                return None
        except Exception as e:
            logger.error("key_manager.jwk_conversion_failed", kid=kid, error=str(e))
            return None

    def _rsa_to_jwk(self, public_key: rsa.RSAPublicKey, kid: str) -> dict[str, Any]:
        """Convert RSA public key to JWK."""
        numbers = public_key.public_numbers()

        # Convert to base64url encoding
        def to_base64url(n: int, length: int) -> str:
            data = n.to_bytes(length, byteorder="big")
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        key_size = public_key.key_size // 8

        return {
            "kty": "RSA",
            "kid": kid,
            "use": "sig",
            "alg": self.algorithm,
            "n": to_base64url(numbers.n, key_size),
            "e": to_base64url(numbers.e, 3),  # e is typically 65537 (3 bytes)
        }

    def _ec_to_jwk(self, public_key: ec.EllipticCurvePublicKey, kid: str) -> dict[str, Any]:
        """Convert EC public key to JWK."""
        numbers = public_key.public_numbers()
        curve = public_key.curve

        # Map curve to JWK curve name
        curve_name_map = {
            "secp256r1": "P-256",
            "secp384r1": "P-384",
            "secp521r1": "P-521",
        }
        crv = curve_name_map.get(curve.name, curve.name)

        # Determine coordinate size based on curve
        coord_size_map = {
            "P-256": 32,
            "P-384": 48,
            "P-521": 66,
        }
        coord_size = coord_size_map.get(crv, 32)

        def to_base64url(n: int, length: int) -> str:
            data = n.to_bytes(length, byteorder="big")
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

        return {
            "kty": "EC",
            "kid": kid,
            "use": "sig",
            "alg": self.algorithm,
            "crv": crv,
            "x": to_base64url(numbers.x, coord_size),
            "y": to_base64url(numbers.y, coord_size),
        }

    def get_signing_key(self) -> tuple[Any, str]:
        """Return (private_key, kid) for token signing.

        Raises:
            ValueError: If no private key is configured
        """
        if not self.private_key:
            raise ValueError("No private key configured for asymmetric signing")
        return self.private_key, self.current_key_id

    def get_key_by_kid(self, kid: str) -> Any | None:
        """Lookup public key by kid for verification.

        Supports rotation fallback to previous keys.
        """
        if kid == self.current_key_id and self.public_key:
            return self.public_key
        return self.previous_keys.get(kid)

    def get_all_verification_keys(self) -> list[tuple[str, Any]]:
        """Return all valid keys for verification (current + previous).

        Returns list of (kid, public_key) tuples.
        """
        keys: list[tuple[str, Any]] = []

        if self.public_key:
            keys.append((self.current_key_id, self.public_key))

        for kid, public_key in self.previous_keys.items():
            keys.append((kid, public_key))

        return keys

    @property
    def is_asymmetric_available(self) -> bool:
        """Check if asymmetric signing/verification is available."""
        return self.public_key is not None

    @property
    def is_signing_available(self) -> bool:
        """Check if asymmetric signing is available."""
        return self.private_key is not None


# Singleton instance
_key_manager: KeyManager | None = None


def get_key_manager() -> KeyManager:
    """Get or create the singleton KeyManager instance."""
    global _key_manager
    if _key_manager is None:
        _key_manager = KeyManager()
    return _key_manager


def reset_key_manager() -> None:
    """Reset the singleton instance (for testing)."""
    global _key_manager
    _key_manager = None
