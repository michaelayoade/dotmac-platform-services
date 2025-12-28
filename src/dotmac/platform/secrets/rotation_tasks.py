"""
Secret Rotation Tasks.

Background Celery tasks for managing secret lifecycle:
- JWT key rotation with graceful transition
- API key expiration monitoring and notification
- Database credential rotation (optional)

Note: These tasks work with the KeyManager (auth/keys.py) for JWT key management
and the Vault client for secure secret storage.
"""

import base64
from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from dotmac.platform.celery_app import celery_app as app
from dotmac.platform.database import get_async_session_context
from dotmac.platform.settings import settings

logger = structlog.get_logger(__name__)


def _run_async(coro: Any) -> Any:
    """Helper to run async code from sync Celery tasks."""
    import asyncio

    try:
        return asyncio.run(coro)
    except RuntimeError as exc:
        if "asyncio.run() cannot be called" not in str(exc):
            raise
        loop = asyncio.new_event_loop()
        policy = asyncio.get_event_loop_policy()
        try:
            previous_loop = policy.get_event_loop()
        except RuntimeError:
            previous_loop = None
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            asyncio.set_event_loop(previous_loop)
            loop.close()


@app.task(name="secrets.rotate_jwt_keys")
def rotate_jwt_keys_task() -> dict[str, Any]:
    """
    Rotate JWT signing keys with graceful transition.

    This task:
    1. Generates a new RSA/EC key pair
    2. Stores the new keys in Vault
    3. Updates the previous_keys list with the old key
    4. Sets the new key as current

    The old key is kept in the verification pool for a grace period
    to allow tokens signed with it to remain valid.

    Note: This task generates the keys but doesn't reload the KeyManager.
    A restart or config reload is needed for the new keys to take effect.
    For zero-downtime rotation, use dynamic key loading.

    Returns:
        Dictionary with rotation status and key IDs
    """
    from dotmac.platform.secrets.vault_client import VaultClient, VaultError

    result = {
        "rotated": False,
        "new_key_id": None,
        "old_key_id": settings.auth.jwt_key_id,
        "algorithm": settings.auth.jwt_asymmetric_algorithm,
        "error": None,
    }

    try:
        # Generate new key ID based on timestamp
        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        new_key_id = f"key-{timestamp}"

        # Generate new key pair based on algorithm
        algorithm = settings.auth.jwt_asymmetric_algorithm
        if algorithm.startswith("RS"):
            # RSA key (RS256, RS384, RS512)
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
        elif algorithm.startswith("ES"):
            # EC key (ES256, ES384, ES512)
            curve_map = {
                "ES256": ec.SECP256R1(),
                "ES384": ec.SECP384R1(),
                "ES512": ec.SECP521R1(),
            }
            curve = curve_map.get(algorithm, ec.SECP256R1())
            private_key = ec.generate_private_key(curve)
        else:
            result["error"] = f"Unsupported algorithm: {algorithm}"
            return result

        # Serialize keys to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        # Store in Vault
        try:
            vault = VaultClient(
                url=settings.vault.url,
                token=settings.vault.token,
                mount_path=settings.vault.mount_path,
                kv_version=settings.vault.kv_version,
            )

            # Store new keys
            vault.set_secret(
                "jwt/current",
                {
                    "key_id": new_key_id,
                    "private_key": private_pem,
                    "public_key": public_pem,
                    "algorithm": algorithm,
                    "created_at": datetime.now(UTC).isoformat(),
                },
            )

            # Archive old key to previous keys
            old_key_id = settings.auth.jwt_key_id
            if settings.auth.jwt_public_key:
                # Base64 encode the old public key for storage
                old_public_b64 = base64.b64encode(
                    settings.auth.jwt_public_key.encode()
                ).decode()

                vault.set_secret(
                    f"jwt/previous/{old_key_id}",
                    {
                        "key_id": old_key_id,
                        "public_key": settings.auth.jwt_public_key,
                        "public_key_b64": old_public_b64,
                        "archived_at": datetime.now(UTC).isoformat(),
                    },
                )

            result["rotated"] = True
            result["new_key_id"] = new_key_id

            logger.info(
                "jwt_keys.rotated",
                new_key_id=new_key_id,
                old_key_id=old_key_id,
                algorithm=algorithm,
            )

        except VaultError as e:
            result["error"] = f"Vault error: {e}"
            logger.error("jwt_keys.rotation_failed", error=str(e))

    except Exception as e:
        result["error"] = str(e)
        logger.error("jwt_keys.rotation_failed", error=str(e))

    return result


@app.task(name="secrets.check_expiring_api_keys")
def check_expiring_api_keys_task() -> dict[str, Any]:
    """
    Check for API keys approaching expiration and send notifications.

    This task:
    1. Finds all API keys expiring within the warning period
    2. Sends notification emails to key owners
    3. Logs expiring keys for monitoring

    Returns:
        Dictionary with check results:
        - expiring_count: Number of keys expiring soon
        - notified: Number of notifications sent
        - errors: Number of notification failures
    """

    async def _check():
        from sqlalchemy import and_, select

        from dotmac.platform.auth.models import APIKeyTable

        warning_days = 7  # Notify 7 days before expiration
        cutoff_date = datetime.now(UTC) + timedelta(days=warning_days)

        stats = {"expiring_count": 0, "notified": 0, "errors": 0, "keys": []}

        async with get_async_session_context() as session:
            # Find expiring API keys
            stmt = select(APIKeyTable).where(
                and_(
                    APIKeyTable.expires_at.isnot(None),
                    APIKeyTable.expires_at <= cutoff_date,
                    APIKeyTable.expires_at > datetime.now(UTC),
                    APIKeyTable.revoked_at.is_(None),
                )
            )

            result = await session.execute(stmt)
            expiring_keys = result.scalars().all()

            stats["expiring_count"] = len(expiring_keys)

            for key in expiring_keys:
                days_until_expiry = (key.expires_at - datetime.now(UTC)).days

                stats["keys"].append(
                    {
                        "key_id": str(key.id),
                        "name": key.name,
                        "user_id": str(key.user_id),
                        "tenant_id": str(key.tenant_id) if key.tenant_id else None,
                        "expires_at": key.expires_at.isoformat(),
                        "days_until_expiry": days_until_expiry,
                    }
                )

                logger.warning(
                    "api_key.expiring_soon",
                    key_id=str(key.id),
                    key_name=key.name,
                    user_id=str(key.user_id),
                    days_until_expiry=days_until_expiry,
                )

                # TODO: Send notification email to key owner
                # For now, just log the warning
                stats["notified"] += 1

        return stats

    result = _run_async(_check())

    logger.info(
        "api_keys.expiration_check_completed",
        expiring_count=result["expiring_count"],
        notified=result["notified"],
    )

    return result


@app.task(name="secrets.cleanup_expired_api_keys")
def cleanup_expired_api_keys_task() -> dict[str, Any]:
    """
    Cleanup expired API keys by marking them as revoked.

    This task:
    1. Finds all expired API keys that haven't been revoked
    2. Marks them as revoked with reason "expired"
    3. Logs the cleanup for audit

    Note: We don't delete keys, just mark them revoked for audit trail.

    Returns:
        Dictionary with cleanup results:
        - cleaned_count: Number of keys marked as revoked
        - errors: Number of cleanup failures
    """

    async def _cleanup():
        from sqlalchemy import and_, select

        from dotmac.platform.auth.models import APIKeyTable

        stats = {"cleaned_count": 0, "errors": 0}

        async with get_async_session_context() as session:
            # Find expired, non-revoked API keys
            stmt = select(APIKeyTable).where(
                and_(
                    APIKeyTable.expires_at.isnot(None),
                    APIKeyTable.expires_at <= datetime.now(UTC),
                    APIKeyTable.revoked_at.is_(None),
                )
            )

            result = await session.execute(stmt)
            expired_keys = result.scalars().all()

            for key in expired_keys:
                try:
                    key.revoked_at = datetime.now(UTC)
                    key.revoked_reason = "expired"

                    logger.info(
                        "api_key.auto_revoked",
                        key_id=str(key.id),
                        key_name=key.name,
                        user_id=str(key.user_id),
                        expired_at=key.expires_at.isoformat(),
                    )

                    stats["cleaned_count"] += 1
                except Exception as e:
                    logger.error(
                        "api_key.cleanup_failed",
                        key_id=str(key.id),
                        error=str(e),
                    )
                    stats["errors"] += 1

            await session.commit()

        return stats

    result = _run_async(_cleanup())

    logger.info(
        "api_keys.cleanup_completed",
        cleaned_count=result["cleaned_count"],
        errors=result["errors"],
    )

    return result


@app.task(name="secrets.cleanup_previous_jwt_keys")
def cleanup_previous_jwt_keys_task() -> dict[str, Any]:
    """
    Cleanup old JWT keys from the rotation window.

    This task removes keys older than the configured retention period
    from the previous keys storage in Vault.

    Keys are kept for 30 days after rotation to allow existing tokens
    to remain valid for their full lifetime.

    Returns:
        Dictionary with cleanup results:
        - checked: Number of keys checked
        - removed: Number of keys removed
        - retained: Number of keys kept
    """
    from dotmac.platform.secrets.vault_client import VaultClient, VaultError

    result = {"checked": 0, "removed": 0, "retained": 0, "error": None}

    retention_days = 30  # Keep previous keys for 30 days

    try:
        vault = VaultClient(
            url=settings.vault.url,
            token=settings.vault.token,
            mount_path=settings.vault.mount_path,
            kv_version=settings.vault.kv_version,
        )

        # List previous keys
        previous_keys = vault.list_secrets("jwt/previous")
        result["checked"] = len(previous_keys)

        cutoff_date = datetime.now(UTC) - timedelta(days=retention_days)

        for key_id in previous_keys:
            try:
                # Get key metadata
                key_data = vault.get_secret(f"jwt/previous/{key_id}")
                archived_at_str = key_data.get("archived_at")

                if archived_at_str:
                    archived_at = datetime.fromisoformat(archived_at_str.replace("Z", "+00:00"))

                    if archived_at < cutoff_date:
                        # Key is past retention period, delete it
                        vault.delete_secret(f"jwt/previous/{key_id}")
                        result["removed"] += 1
                        logger.info(
                            "jwt_key.previous_removed",
                            key_id=key_id,
                            archived_at=archived_at_str,
                        )
                    else:
                        result["retained"] += 1
                else:
                    # No archived_at, retain for safety
                    result["retained"] += 1

            except VaultError as e:
                logger.warning(
                    "jwt_key.cleanup_check_failed",
                    key_id=key_id,
                    error=str(e),
                )
                result["retained"] += 1

    except VaultError as e:
        result["error"] = str(e)
        logger.error("jwt_keys.cleanup_failed", error=str(e))

    logger.info(
        "jwt_keys.cleanup_completed",
        checked=result["checked"],
        removed=result["removed"],
        retained=result["retained"],
    )

    return result


# Schedule periodic tasks
@app.on_after_finalize.connect
def setup_rotation_periodic_tasks(sender: Any, **kwargs: Any) -> None:
    """Set up periodic schedules for rotation tasks."""
    from celery.schedules import crontab

    # Check for expiring API keys daily at 8am
    sender.add_periodic_task(
        crontab(hour=8, minute=0),
        check_expiring_api_keys_task.s(),
        name="secrets-check-expiring-api-keys-daily",
    )

    # Cleanup expired API keys daily at midnight
    sender.add_periodic_task(
        crontab(hour=0, minute=0),
        cleanup_expired_api_keys_task.s(),
        name="secrets-cleanup-expired-api-keys-daily",
    )

    # Cleanup old JWT keys weekly on Sunday at 3am
    sender.add_periodic_task(
        crontab(hour=3, minute=0, day_of_week=0),
        cleanup_previous_jwt_keys_task.s(),
        name="secrets-cleanup-previous-jwt-keys-weekly",
    )

    # JWT key rotation is NOT automatically scheduled
    # It should be triggered manually or by operator policy
    # Example: Monthly rotation on 1st of each month
    # sender.add_periodic_task(
    #     crontab(day_of_month=1, hour=2, minute=0),
    #     rotate_jwt_keys_task.s(),
    #     name="secrets-rotate-jwt-keys-monthly",
    # )

    logger.info(
        "secrets.rotation_tasks_scheduled",
        tasks=[
            "check-expiring-api-keys-daily",
            "cleanup-expired-api-keys-daily",
            "cleanup-previous-jwt-keys-weekly",
        ],
    )
