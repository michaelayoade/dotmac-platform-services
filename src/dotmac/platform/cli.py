#!/usr/bin/env python
"""
CLI management commands for DotMac Platform Services.
"""

import click
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import select

from dotmac.platform.db import init_db, get_session
from dotmac.platform.auth.jwt_service import JWTService
# from dotmac.platform.secrets.manager import SecretsManager
SecretsManager = None  # Placeholder for removed secrets module


@click.group()
def cli():
    """DotMac Platform Services CLI."""
    pass


@cli.command()
def init_database():
    """Initialize the database with required schemas."""
    click.echo("Initializing database...")
    asyncio.run(init_db())
    click.echo("Database initialized successfully!")


@cli.command()
@click.option("--email", prompt=True, help="Admin user email")
@click.option("--password", prompt=True, hide_input=True, help="Admin user password")
def create_admin(email: str, password: str):
    """Create an admin user."""
    async def _create_admin():
        from dotmac.platform.auth.models import User
        from dotmac.platform.auth.utils import hash_password

        async with get_session() as session:
            # Check if user exists
            existing = await session.execute(
                select(User).where(User.email == email)
            )
            if existing.scalar():
                click.echo(f"User with email {email} already exists!")
                return

            # Create admin user
            user = User(
                email=email,
                password_hash=hash_password(password),
                is_admin=True,
                is_active=True,
            )
            session.add(user)
            await session.commit()
            click.echo(f"Admin user {email} created successfully!")

    asyncio.run(_create_admin())


@cli.command()
def generate_jwt_keys():
    """Generate JWT signing keys."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.backends import default_backend

    click.echo("Generating RSA key pair for JWT signing...")

    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    # Get public key
    public_key = private_key.public_key()

    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    # Save keys
    Path("jwt_private.pem").write_bytes(private_pem)
    Path("jwt_public.pem").write_bytes(public_pem)

    click.echo("Keys saved to jwt_private.pem and jwt_public.pem")


@cli.command()
@click.option("--path", required=True, help="Secret path")
@click.option("--value", required=True, help="Secret value")
@click.option("--provider", default="vault", help="Secret provider (vault/env)")
def set_secret(path: str, value: str, provider: str):
    """Set a secret in the secrets manager."""
    async def _set_secret():
        manager = SecretsManager(provider=provider)
        await manager.set_secret(path, {"value": value})
        click.echo(f"Secret set at path: {path}")

    asyncio.run(_set_secret())


@cli.command()
@click.option("--path", required=True, help="Secret path")
@click.option("--provider", default="vault", help="Secret provider (vault/env)")
def get_secret(path: str, provider: str):
    """Get a secret from the secrets manager."""
    async def _get_secret():
        manager = SecretsManager(provider=provider)
        secret = await manager.get_secret(path)
        click.echo(f"Secret at {path}: {secret}")

    asyncio.run(_get_secret())


@cli.command()
def run_migrations():
    """Run database migrations."""
    import subprocess

    click.echo("Running database migrations...")
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        click.echo("Migrations completed successfully!")
        click.echo(result.stdout)
    else:
        click.echo("Migration failed!")
        click.echo(result.stderr)
        sys.exit(1)


@cli.command()
@click.option("--test", is_flag=True, help="Run in test mode")
def check_services(test: bool):
    """Check connectivity to all required services."""
    async def _check_services():
        results = {}

        # Check database
        try:
            async with get_session() as session:
                await session.execute("SELECT 1")
            results["database"] = "✓ Connected"
        except Exception as e:
            results["database"] = f"✗ Failed: {e}"

        # Check Redis
        try:
            import aioredis
            redis = await aioredis.create_redis_pool('redis://localhost')
            await redis.ping()
            redis.close()
            await redis.wait_closed()
            results["redis"] = "✓ Connected"
        except Exception as e:
            results["redis"] = f"✗ Failed: {e}"

        # Check Vault/OpenBao
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8200/v1/sys/health")
                if response.status_code in [200, 429, 501, 503]:
                    results["vault"] = "✓ Available"
                else:
                    results["vault"] = f"✗ Status: {response.status_code}"
        except Exception as e:
            results["vault"] = f"✗ Failed: {e}"

        # Print results
        click.echo("\nService Status:")
        click.echo("-" * 40)
        for service, status in results.items():
            click.echo(f"{service:15} {status}")

    asyncio.run(_check_services())


@cli.command()
@click.option("--days", default=30, help="Number of days to keep")
def cleanup_sessions(days: int):
    """Clean up expired sessions."""
    async def _cleanup():
        from datetime import datetime, timedelta

        async with get_session() as session:
            cutoff = datetime.utcnow() - timedelta(days=days)
            result = await session.execute(
                "DELETE FROM auth.sessions WHERE created_at < :cutoff",
                {"cutoff": cutoff}
            )
            await session.commit()
            click.echo(f"Deleted {result.rowcount} expired sessions")

    asyncio.run(_cleanup())


@cli.command()
@click.option("--format", default="json", help="Export format (json/csv)")
def export_audit_logs(format: str):
    """Export audit logs."""
    async def _export():
        async with get_session() as session:
            result = await session.execute(
                "SELECT * FROM audit.audit_log ORDER BY event_timestamp DESC"
            )
            logs = result.fetchall()

            if format == "json":
                import json
                output = json.dumps([dict(log) for log in logs], default=str, indent=2)
                Path("audit_logs.json").write_text(output)
                click.echo(f"Exported {len(logs)} logs to audit_logs.json")
            elif format == "csv":
                import csv
                with open("audit_logs.csv", "w", newline="") as f:
                    if logs:
                        writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                        writer.writeheader()
                        writer.writerows([dict(log) for log in logs])
                click.echo(f"Exported {len(logs)} logs to audit_logs.csv")

    asyncio.run(_export())


if __name__ == "__main__":
    cli()
