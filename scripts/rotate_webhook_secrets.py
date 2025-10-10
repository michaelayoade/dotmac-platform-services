#!/usr/bin/env python3
"""
Webhook Secret Rotation Script.

Automates rotation of webhook signing secrets for security compliance.
Supports grace period for seamless transition.
"""

import argparse
import asyncio
import secrets
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import structlog

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotmac.platform.db import get_async_session
from dotmac.platform.webhooks.models import WebhookSubscription

logger = structlog.get_logger(__name__)


class WebhookSecretRotator:
    """Handles webhook secret rotation with grace period support."""

    def __init__(self, dry_run: bool = False, grace_period_days: int = 7):
        self.dry_run = dry_run
        self.grace_period_days = grace_period_days
        self.rotated_count = 0
        self.failed_count = 0
        self.skipped_count = 0

    def generate_secret(self) -> str:
        """Generate cryptographically secure webhook secret."""
        return secrets.token_urlsafe(32)

    async def rotate_webhook(
        self,
        webhook: WebhookSubscription,
        db,
        force: bool = False
    ) -> dict[str, str | None]:
        """Rotate secret for a single webhook.

        Returns:
            dict with old_secret, new_secret, and status
        """
        old_secret = webhook.secret
        new_secret = self.generate_secret()

        result = {
            "webhook_id": str(webhook.id),
            "url": webhook.url,
            "old_secret": old_secret,
            "new_secret": new_secret,
            "rotated_at": datetime.now(UTC).isoformat(),
            "grace_period_until": (
                datetime.now(UTC) + timedelta(days=self.grace_period_days)
            ).isoformat(),
        }

        if self.dry_run:
            logger.info(
                "DRY RUN: Would rotate webhook secret",
                webhook_id=webhook.id,
                url=webhook.url,
            )
            self.skipped_count += 1
            return result

        try:
            # Update webhook with new secret
            webhook.secret = new_secret

            # Store old secret in metadata for grace period
            if not webhook.custom_metadata:
                webhook.custom_metadata = {}

            webhook.custom_metadata["old_secret"] = old_secret
            webhook.custom_metadata["secret_rotated_at"] = datetime.now(UTC).isoformat()
            webhook.custom_metadata["old_secret_expires_at"] = (
                datetime.now(UTC) + timedelta(days=self.grace_period_days)
            ).isoformat()

            await db.commit()
            await db.refresh(webhook)

            logger.info(
                "Webhook secret rotated",
                webhook_id=webhook.id,
                url=webhook.url,
                grace_period_days=self.grace_period_days,
            )

            self.rotated_count += 1
            return result

        except Exception as e:
            logger.error(
                "Failed to rotate webhook secret",
                webhook_id=webhook.id,
                error=str(e),
            )
            self.failed_count += 1
            result["error"] = str(e)
            return result

    async def rotate_all_webhooks(
        self,
        db,
        tenant_id: str | None = None,
        age_days: int | None = None,
    ) -> list[dict]:
        """Rotate secrets for all webhooks matching criteria."""
        from sqlalchemy import select

        query = select(WebhookSubscription)

        # Filter by tenant if specified
        if tenant_id:
            query = query.where(WebhookSubscription.tenant_id == tenant_id)

        # Filter by age if specified
        if age_days:
            cutoff_date = datetime.now(UTC) - timedelta(days=age_days)
            query = query.where(WebhookSubscription.created_at < cutoff_date)

        result = await db.execute(query)
        webhooks = result.scalars().all()

        logger.info(
            "Starting webhook secret rotation",
            total_webhooks=len(webhooks),
            dry_run=self.dry_run,
        )

        results = []
        for webhook in webhooks:
            rotation_result = await self.rotate_webhook(webhook, db)
            results.append(rotation_result)

        return results

    async def rotate_single_webhook(
        self,
        webhook_id: str,
        db,
    ) -> dict:
        """Rotate secret for a single webhook by ID."""
        from sqlalchemy import select

        result = await db.execute(
            select(WebhookSubscription).where(WebhookSubscription.id == UUID(webhook_id))
        )
        webhook = result.scalar_one_or_none()

        if not webhook:
            raise ValueError(f"Webhook {webhook_id} not found")

        return await self.rotate_webhook(webhook, db)

    async def cleanup_old_secrets(self, db) -> int:
        """Remove old secrets that are past grace period."""
        from sqlalchemy import select

        query = select(WebhookSubscription)
        result = await db.execute(query)
        webhooks = result.scalars().all()

        cleaned_count = 0

        for webhook in webhooks:
            if not webhook.custom_metadata or "old_secret" not in webhook.custom_metadata:
                continue

            expires_at_str = webhook.custom_metadata.get("old_secret_expires_at")
            if not expires_at_str:
                continue

            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))

            if datetime.now(UTC) > expires_at:
                # Grace period expired, remove old secret
                if self.dry_run:
                    logger.info(
                        "DRY RUN: Would clean up old secret",
                        webhook_id=webhook.id,
                    )
                else:
                    webhook.custom_metadata.pop("old_secret", None)
                    webhook.custom_metadata.pop("secret_rotated_at", None)
                    webhook.custom_metadata.pop("old_secret_expires_at", None)

                    await db.commit()

                    logger.info(
                        "Cleaned up expired old secret",
                        webhook_id=webhook.id,
                    )

                cleaned_count += 1

        return cleaned_count

    def print_summary(self) -> None:
        """Print rotation summary."""
        print("\n" + "="*60)
        print("WEBHOOK SECRET ROTATION SUMMARY")
        print("="*60)
        print(f"Rotated: {self.rotated_count}")
        print(f"Failed: {self.failed_count}")
        print(f"Skipped (dry run): {self.skipped_count}")
        print(f"Grace Period: {self.grace_period_days} days")
        print("="*60 + "\n")


async def send_rotation_notification(
    webhook: WebhookSubscription,
    rotation_result: dict,
    email_service,
) -> None:
    """Send email notification to webhook owner about secret rotation."""
    # This would integrate with EmailService to notify the webhook owner
    # For now, just log it
    logger.info(
        "Would send rotation notification",
        webhook_id=webhook.id,
        url=webhook.url,
        grace_period_until=rotation_result["grace_period_until"],
    )


async def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Rotate webhook signing secrets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run - see what would be rotated
  %(prog)s --dry-run

  # Rotate all webhooks older than 90 days
  %(prog)s --age-days 90

  # Rotate specific webhook
  %(prog)s --webhook-id 123e4567-e89b-12d3-a456-426614174000

  # Rotate all webhooks for a tenant
  %(prog)s --tenant-id tenant-uuid

  # Force rotation with custom grace period
  %(prog)s --force --grace-period-days 14

  # Clean up old secrets past grace period
  %(prog)s --cleanup
        """,
    )

    parser.add_argument(
        "--webhook-id",
        type=str,
        help="Rotate secret for specific webhook (UUID)",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        help="Rotate all webhooks for specific tenant",
    )
    parser.add_argument(
        "--age-days",
        type=int,
        help="Only rotate webhooks older than N days",
    )
    parser.add_argument(
        "--grace-period-days",
        type=int,
        default=7,
        help="Grace period for old secret (default: 7 days)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be rotated without making changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rotation even if recently rotated",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove old secrets past grace period",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send email notifications to webhook owners",
    )

    args = parser.parse_args()

    rotator = WebhookSecretRotator(
        dry_run=args.dry_run,
        grace_period_days=args.grace_period_days,
    )

    # Get database session
    async for db in get_async_session():
        try:
            if args.cleanup:
                # Cleanup mode
                cleaned = await rotator.cleanup_old_secrets(db)
                print(f"\nCleaned up {cleaned} expired old secrets\n")
                return 0

            elif args.webhook_id:
                # Single webhook rotation
                result = await rotator.rotate_single_webhook(args.webhook_id, db)
                print("\nWebhook Secret Rotated:")
                print(f"  Webhook ID: {result['webhook_id']}")
                print(f"  URL: {result['url']}")
                print(f"  New Secret: {result['new_secret'][:8]}...")
                print(f"  Grace Period Until: {result['grace_period_until']}")
                print()

            else:
                # Bulk rotation
                results = await rotator.rotate_all_webhooks(
                    db,
                    tenant_id=args.tenant_id,
                    age_days=args.age_days,
                )

                # Print results
                if results:
                    print("\nRotation Results:")
                    for result in results:
                        print(f"  [{result['webhook_id']}] {result['url']}")

            rotator.print_summary()

            # Exit code
            if rotator.failed_count > 0:
                return 1
            return 0

        except Exception as e:
            logger.error("Rotation failed", error=str(e))
            print(f"\nERROR: {str(e)}\n")
            return 1
        finally:
            break  # Exit after first session


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
