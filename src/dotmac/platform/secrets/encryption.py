from pydantic import BaseModel, ConfigDict, Field

"""
Field-Level Encryption Module

Extracted from encryption.py for better organization.
Provides field-level encryption decorators and utilities for Pydantic models.
"""

import base64
import json
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, TypeVar

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

try:
    from pydantic import field_validator

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

try:
    from cryptography.fernet import Fernet

    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False


# Import DataClassification from the main module
class DataClassification(str, Enum):
    """Data classification levels for encryption policies"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class EncryptionAlgorithm(str, Enum):
    """Encryption algorithms enum for tests/imports."""

    AES_256_GCM = "AES-256-GCM"
    CHACHA20_POLY1305 = "ChaCha20-Poly1305"
    AES_256_CBC = "AES-256-CBC"
    FERNET = "Fernet"


from datetime import UTC

UTC = UTC  # Replacement for the imported UTC

T = TypeVar("T", bound=BaseModel)


class EncryptedField(BaseModel):
    """Represents an encrypted field with metadata"""

    encrypted_data: str = Field(..., description="Base64 encoded encrypted data")
    key_id: str = Field(..., description="Encryption key identifier")
    algorithm: str = Field(..., description="Encryption algorithm used")
    iv: str | None = Field(None, description="Initialization vector if used")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    model_config = ConfigDict()

    @field_validator("encrypted_data")
    def validate_encrypted_data(cls, v):
        """Validate encrypted data is base64 encoded"""
        try:
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("encrypted_data must be valid base64")


def encrypted_field(
    classification: DataClassification = DataClassification.CONFIDENTIAL, **kwargs
) -> Any:
    """
    Create an encrypted field descriptor for Pydantic models.

    Args:
        classification: Data classification level
        **kwargs: Additional Field arguments

    Returns:
        Pydantic Field configured for encryption
    """
    if not PYDANTIC_AVAILABLE:
        raise ImportError("Pydantic not available for encrypted fields")

    # Store encryption metadata in field info
    kwargs.setdefault("description", f"Encrypted field (classification: {classification.value})")
    kwargs["json_schema_extra"] = {
        "encrypted": True,
        "classification": classification.value,
    }

    return Field(**kwargs)


class FieldEncryption:
    """Field-level encryption utilities"""

    def __init__(self, encryption_service) -> None:
        """Init   operation."""
        self.encryption_service = encryption_service

    def encrypt_model_fields(
        self, model: BaseModel, field_classifications: dict[str, DataClassification]
    ) -> BaseModel:
        """
        Encrypt specified fields in a Pydantic model.

        Args:
            model: Pydantic model instance
            field_classifications: Mapping of field names to classification levels

        Returns:
            Model with encrypted fields
        """
        if not PYDANTIC_AVAILABLE:
            raise ImportError("Pydantic not available")

        model_dict = model.model_dump() if hasattr(model, "dict") else model.model_dump()

        for field_name, classification in field_classifications.items():
            if field_name in model_dict and model_dict[field_name] is not None:
                # Convert value to string for encryption
                field_value = model_dict[field_name]
                if not isinstance(field_value, str):
                    field_value = json.dumps(field_value)

                # Encrypt the field
                encrypted_field = self.encryption_service.encrypt(field_value, classification)
                model_dict[field_name] = (
                    encrypted_field.model_dump()
                    if hasattr(encrypted_field, "dict")
                    else encrypted_field.model_dump()
                )
        # Create new model instance with encrypted fields
        return type(model)(**model_dict)

    def decrypt_model_fields(
        self,
        model: BaseModel,
        field_names: list[str],
        target_types: dict[str, type] | None = None,
    ) -> BaseModel:
        """
        Decrypt specified fields in a Pydantic model.

        Args:
            model: Pydantic model instance with encrypted fields
            field_names: List of field names to decrypt
            target_types: Optional mapping of field names to target types

        Returns:
            Model with decrypted fields
        """
        if not PYDANTIC_AVAILABLE:
            raise ImportError("Pydantic not available")

        model_dict = model.model_dump() if hasattr(model, "dict") else model.model_dump()
        target_types = target_types or {}

        for field_name in field_names:
            if field_name in model_dict and model_dict[field_name] is not None:
                encrypted_data = model_dict[field_name]

                # Handle both EncryptedField objects and raw encrypted data
                if isinstance(encrypted_data, dict):
                    encrypted_field = EncryptedField(**encrypted_data)
                else:
                    encrypted_field = encrypted_data

                # Decrypt the field
                decrypted_value = self.encryption_service.decrypt(encrypted_field)

                # Convert back to target type if specified
                if field_name in target_types:
                    target_type = target_types[field_name]
                    if target_type is not str:
                        try:
                            decrypted_value = json.loads(decrypted_value)
                        except (json.JSONDecodeError, TypeError):
                            pass  # Keep as string if JSON decode fails

                model_dict[field_name] = decrypted_value

        # Create new model instance with decrypted fields
        return type(model)(**model_dict)

    def get_encrypted_fields(self, model: BaseModel) -> list[str]:
        """
        Get list of field names that are encrypted in a model.

        Args:
            model: Pydantic model instance

        Returns:
            List of encrypted field names
        """
        if not PYDANTIC_AVAILABLE:
            return []

        encrypted_fields = []
        model_dict = model.model_dump() if hasattr(model, "dict") else model.model_dump()

        for field_name, field_value in model_dict.items():
            if isinstance(field_value, dict):
                # Check if it looks like an EncryptedField
                if all(key in field_value for key in ["encrypted_data", "key_id", "algorithm"]):
                    encrypted_fields.append(field_name)
            elif hasattr(field_value, "encrypted_data"):
                encrypted_fields.append(field_name)

        return encrypted_fields


# ---------------------------------------------------------------------------
# Simple secret encryption helpers used by tests
# ---------------------------------------------------------------------------

def generate_encryption_key() -> str:
    """Generate a symmetric encryption key for Fernet (urlsafe base64)."""
    if not CRYPTOGRAPHY_AVAILABLE:
        # Fallback to pseudo key for environments without cryptography
        return base64.urlsafe_b64encode(b"fallback-secret-key-32bytes!!!!").decode()
    return Fernet.generate_key().decode()


def encrypt_secret(value: str, key: str) -> str:
    """Encrypt a secret string using Fernet. Returns base64 string."""
    if not CRYPTOGRAPHY_AVAILABLE:
        # Lightweight fallback: reversible base64 with prefix
        return "b64:" + base64.urlsafe_b64encode(value.encode()).decode()
    f = Fernet(key.encode() if not isinstance(key, bytes) else key)
    return f.encrypt(value.encode()).decode()


def decrypt_secret(token: str, key: str) -> str:
    """Decrypt a secret string using Fernet or fallback decoding."""
    if token.startswith("b64:"):
        return base64.urlsafe_b64decode(token[4:].encode()).decode()
    if not CRYPTOGRAPHY_AVAILABLE:
        # If cryptography is unavailable and token has no fallback prefix, best-effort
        try:
            return base64.urlsafe_b64decode(token.encode()).decode()
        except Exception:
            return token
    f = Fernet(key.encode() if not isinstance(key, bytes) else key)
    return f.decrypt(token.encode()).decode()


class SymmetricEncryptionService:
    """
    Simple symmetric encryption service using Fernet if available,
    with a deterministic key derivation from a provided secret.
    """

    def __init__(self, secret: str) -> None:
        self.secret = secret or "dotmac-default-secret"
        self._fernet = None

        if CRYPTOGRAPHY_AVAILABLE:
            self._fernet = self._create_fernet(self.secret)

    def _create_fernet(self, secret: str):
        import hashlib
        from base64 import urlsafe_b64encode

        # If the provided key already looks like a Fernet key (44 chars base64), try to use it
        try:
            if len(secret) == 44:
                return Fernet(secret.encode())
        except Exception:
            pass

        # Derive a stable 32-byte key from the secret
        key_bytes = hashlib.sha256(secret.encode("utf-8")).digest()
        fernet_key = urlsafe_b64encode(key_bytes)
        return Fernet(fernet_key)

    def encrypt(self, plaintext: str, classification: DataClassification) -> EncryptedField:
        if not isinstance(plaintext, str):
            raise TypeError("plaintext must be a string")

        if self._fernet:
            token = self._fernet.encrypt(plaintext.encode("utf-8"))
            enc = base64.b64encode(token).decode("utf-8")
            return EncryptedField(
                encrypted_data=enc,
                key_id="default",
                algorithm="fernet",
                iv=None,
            )

        # Fallback: reversible base64 wrapper (not secure; for environments without cryptography)
        token = base64.b64encode(plaintext.encode("utf-8")).decode("utf-8")
        return EncryptedField(
            encrypted_data=token,
            key_id="default",
            algorithm="base64",
            iv=None,
        )

    def decrypt(self, encrypted: EncryptedField | dict[str, Any]) -> str:
        if isinstance(encrypted, dict):
            encrypted = EncryptedField(**encrypted)

        data = encrypted.encrypted_data
        raw = base64.b64decode(data)

        if self._fernet and encrypted.algorithm == "fernet":
            plaintext = self._fernet.decrypt(raw).decode("utf-8")
            return plaintext

        # Fallback base64
        try:
            return base64.b64decode(encrypted.encrypted_data).decode("utf-8")
        except Exception as e:
            raise ValueError(f"Unable to decrypt data: {e}")


class SecureDataModel(BaseModel):
    """Base model with encryption capabilities"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def with_encryption(
        cls,
        encryption_service,
        classification: DataClassification = DataClassification.CONFIDENTIAL,
    ):
        """
        Create a model class with automatic field encryption.

        Args:
            encryption_service: Encryption service instance
            classification: Default classification for encrypted fields

        Returns:
            Model class with encryption support
        """

        class EncryptedModel(cls):
            """Class for EncryptedModel operations."""

            _encryption_service = encryption_service
            _classification = classification

            def encrypt_sensitive_fields(self, field_names: list[str]) -> "EncryptedModel":
                """Encrypt specified fields in this model instance"""
                field_classifications = dict.fromkeys(field_names, self._classification)
                field_encryptor = FieldEncryption(self._encryption_service)
                return field_encryptor.encrypt_model_fields(self, field_classifications)

            def decrypt_fields(self, field_names: list[str]) -> "EncryptedModel":
                """Decrypt specified fields in this model instance"""
                field_encryptor = FieldEncryption(self._encryption_service)
                return field_encryptor.decrypt_model_fields(self, field_names)

            def get_encrypted_fields(self) -> list[str]:
                """Get list of encrypted fields in this model"""
                field_encryptor = FieldEncryption(self._encryption_service)
                return field_encryptor.get_encrypted_fields(self)

        return EncryptedModel


def encrypt_sensitive_data(
    classification: DataClassification = DataClassification.CONFIDENTIAL,
    fields: list[str] | None = None,
):
    """
    Decorator for automatically encrypting sensitive fields in Pydantic models.

    Args:
        classification: Data classification level for encryption
        fields: List of field names to encrypt (if None, encrypts all fields marked as encrypted)

    Returns:
        Decorator function
    """

    def decorator(cls):
        """Decorator operation."""
        if not issubclass(cls, BaseModel):
            raise TypeError("encrypt_sensitive_data can only be used on Pydantic models")
        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, **kwargs) -> None:
            """New Init operation."""
            # Initialize normally first
            original_init(self, **kwargs)

            # Get encryption service from kwargs or class attribute
            encryption_service = kwargs.pop("_encryption_service", None)
            if not encryption_service and hasattr(cls, "_encryption_service"):
                encryption_service = cls._encryption_service

            if encryption_service:
                # Determine fields to encrypt
                target_fields = fields
                if not target_fields:
                    # Auto-detect fields marked for encryption
                    target_fields = []
                    for field_name, field_info in cls.model_fields.items():
                        if hasattr(field_info, "json_schema_extra"):
                            extra = field_info.json_schema_extra or {}
                            if extra.get("encrypted", False):
                                target_fields.append(field_name)

                if target_fields:
                    # Encrypt the specified fields
                    field_classifications = dict.fromkeys(target_fields, classification)
                    field_encryptor = FieldEncryption(encryption_service)
                    encrypted_model = field_encryptor.encrypt_model_fields(
                        self, field_classifications
                    )
                    # Update self with encrypted data
                    for field_name in target_fields:
                        if hasattr(encrypted_model, field_name):
                            setattr(self, field_name, getattr(encrypted_model, field_name))

        cls.__init__ = new_init
        return cls

    return decorator


def selective_encryption(field_mapping: dict[str, DataClassification]):
    """
    Decorator for encrypting specific fields with different classification levels.

    Args:
        field_mapping: Dictionary mapping field names to classification levels

    Returns:
        Decorator function
    """

    def decorator(cls):
        """Decorator operation."""
        if not issubclass(cls, BaseModel):
            raise TypeError("selective_encryption can only be used on Pydantic models")

        original_init = cls.__init__

        @wraps(original_init)
        def new_init(self, **kwargs) -> None:
            """New Init operation."""
            # Initialize normally first
            original_init(self, **kwargs)

            # Get encryption service
            encryption_service = kwargs.pop("_encryption_service", None)
            if not encryption_service and hasattr(cls, "_encryption_service"):
                encryption_service = cls._encryption_service

            if encryption_service:
                # Encrypt mapped fields
                field_encryptor = FieldEncryption(encryption_service)
                encrypted_model = field_encryptor.encrypt_model_fields(self, field_mapping)
                # Update self with encrypted data
                for field_name in field_mapping:
                    if hasattr(encrypted_model, field_name):
                        setattr(self, field_name, getattr(encrypted_model, field_name))

        cls.__init__ = new_init
        return cls

    return decorator


__all__ = [
    "EncryptedField",
    "FieldEncryption",
    "SymmetricEncryptionService",
    "DataClassification",
    "SecureDataModel",
    "encrypt_sensitive_data",
    "encrypted_field",
    "selective_encryption",
]
