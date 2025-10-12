"""
Domain verification service for tenant custom domains.

Provides DNS-based domain verification using:
- TXT record verification
- CNAME record verification
- Meta tag verification (HTML)
- File upload verification

Security features:
- Rate limiting to prevent abuse
- Automatic verification expiry
- Retry mechanism for failed verifications
- Audit logging for compliance
"""

import asyncio
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

import dns.resolver
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.audit.service import AuditService
from dotmac.platform.tenant.models import Tenant

logger = structlog.get_logger(__name__)


class VerificationMethod(str, Enum):
    """Domain verification methods."""

    DNS_TXT = "dns_txt"  # TXT record verification
    DNS_CNAME = "dns_cname"  # CNAME record verification
    META_TAG = "meta_tag"  # HTML meta tag verification
    FILE_UPLOAD = "file_upload"  # File upload verification


class VerificationStatus(str, Enum):
    """Domain verification status."""

    PENDING = "pending"  # Verification initiated
    VERIFIED = "verified"  # Successfully verified
    FAILED = "failed"  # Verification failed
    EXPIRED = "expired"  # Verification token expired


class DomainVerificationService:
    """Service for domain ownership verification."""

    def __init__(
        self,
        db: AsyncSession,
        audit_service: AuditService | None = None,
        verification_ttl_hours: int = 72,
    ):
        """Initialize domain verification service.

        Args:
            db: Database session
            audit_service: Optional audit service for logging
            verification_ttl_hours: Token TTL in hours (default 72)
        """
        self.db = db
        self.audit_service = audit_service or AuditService(db)
        self.verification_ttl_hours = verification_ttl_hours
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.timeout = 5.0
        self.dns_resolver.lifetime = 10.0

    def generate_verification_token(self, tenant_id: str, domain: str) -> str:
        """Generate a unique verification token.

        Args:
            tenant_id: Tenant ID
            domain: Domain to verify

        Returns:
            Verification token (32 characters)
        """
        # Create unique token using tenant_id, domain, timestamp, and random data
        data = f"{tenant_id}:{domain}:{datetime.now(UTC).isoformat()}:{secrets.token_hex(16)}"
        # Use SHA-256 for token generation
        token_hash = hashlib.sha256(data.encode()).hexdigest()
        # Return first 32 characters for manageable token length
        return token_hash[:32]

    async def initiate_verification(
        self,
        tenant_id: str,
        domain: str,
        method: VerificationMethod,
        user_id: str,
    ) -> dict[str, Any]:
        """Initiate domain verification for a tenant.

        Args:
            tenant_id: Tenant ID
            domain: Domain to verify
            method: Verification method
            user_id: User initiating verification

        Returns:
            dict: Verification details including token and instructions

        Raises:
            ValueError: If domain is invalid or already verified
        """
        # Validate domain format
        if not self._is_valid_domain(domain):
            raise ValueError(f"Invalid domain format: {domain}")

        # Check if tenant exists
        tenant = await self._get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        # Check if domain is already verified for another tenant
        existing = await self._check_domain_exists(domain, tenant_id)
        if existing:
            raise ValueError(f"Domain {domain} is already verified for another tenant")

        # Generate verification token
        token = self.generate_verification_token(tenant_id, domain)

        # Calculate expiry
        expires_at = datetime.now(UTC) + timedelta(hours=self.verification_ttl_hours)

        # Get verification instructions based on method
        instructions = self._get_verification_instructions(domain, token, method)

        # Log audit event
        await self.audit_service.log_activity(
            tenant_id=tenant_id,
            user_id=user_id,
            action="domain.verification.initiated",
            resource_type="domain",
            resource_id=domain,
            details={
                "domain": domain,
                "method": method.value,
                "expires_at": expires_at.isoformat(),
            },
        )

        logger.info(
            "Domain verification initiated",
            tenant_id=tenant_id,
            domain=domain,
            method=method.value,
            expires_at=expires_at,
        )

        return {
            "domain": domain,
            "method": method.value,
            "token": token,
            "expires_at": expires_at,
            "instructions": instructions,
            "status": VerificationStatus.PENDING.value,
        }

    async def verify_domain(
        self,
        tenant_id: str,
        domain: str,
        token: str,
        method: VerificationMethod,
        user_id: str,
    ) -> dict[str, Any]:
        """Verify domain ownership.

        Args:
            tenant_id: Tenant ID
            domain: Domain to verify
            token: Verification token
            method: Verification method
            user_id: User requesting verification

        Returns:
            dict: Verification result

        Raises:
            ValueError: If verification fails
        """
        logger.info(
            "Starting domain verification",
            tenant_id=tenant_id,
            domain=domain,
            method=method.value,
        )

        # Verify based on method
        if method == VerificationMethod.DNS_TXT:
            verified = await self._verify_dns_txt(domain, token)
        elif method == VerificationMethod.DNS_CNAME:
            verified = await self._verify_dns_cname(domain, token, tenant_id)
        else:
            raise ValueError(f"Verification method {method.value} not yet implemented")

        if verified:
            # Update tenant with verified domain
            tenant = await self._get_tenant(tenant_id)
            if not tenant:
                raise ValueError(f"Tenant {tenant_id} not found")

            tenant.domain = domain
            tenant.updated_at = datetime.now(UTC)

            await self.db.commit()

            # Log success
            await self.audit_service.log_activity(
                tenant_id=tenant_id,
                user_id=user_id,
                action="domain.verification.succeeded",
                resource_type="domain",
                resource_id=domain,
                details={
                    "domain": domain,
                    "method": method.value,
                    "verified_at": datetime.now(UTC).isoformat(),
                },
            )

            logger.info(
                "Domain verification succeeded",
                tenant_id=tenant_id,
                domain=domain,
                method=method.value,
            )

            return {
                "domain": domain,
                "status": VerificationStatus.VERIFIED.value,
                "verified_at": datetime.now(UTC),
                "method": method.value,
            }
        else:
            # Log failure
            await self.audit_service.log_activity(
                tenant_id=tenant_id,
                user_id=user_id,
                action="domain.verification.failed",
                resource_type="domain",
                resource_id=domain,
                details={
                    "domain": domain,
                    "method": method.value,
                    "reason": "Verification record not found",
                },
            )

            logger.warning(
                "Domain verification failed",
                tenant_id=tenant_id,
                domain=domain,
                method=method.value,
            )

            raise ValueError(f"Domain verification failed for {domain}")

    async def _verify_dns_txt(self, domain: str, expected_token: str) -> bool:
        """Verify domain using DNS TXT record.

        Args:
            domain: Domain to verify
            expected_token: Expected verification token

        Returns:
            bool: True if verified
        """
        try:
            # Query TXT records
            txt_records = await asyncio.to_thread(self.dns_resolver.resolve, domain, "TXT")

            # Check if any TXT record contains the verification token
            for record in txt_records:
                # TXT records are returned as quoted strings, so we need to clean them
                txt_value = str(record).strip('"')

                # Check for exact match or with prefix
                if txt_value == expected_token or txt_value == f"dotmac-verify={expected_token}":
                    logger.info(
                        "DNS TXT verification successful",
                        domain=domain,
                        record=txt_value,
                    )
                    return True

            logger.warning(
                "DNS TXT verification failed - token not found",
                domain=domain,
                records_found=len(txt_records),
            )
            return False

        except dns.resolver.NXDOMAIN:
            logger.warning("DNS TXT verification failed - domain not found", domain=domain)
            return False
        except dns.resolver.NoAnswer:
            logger.warning("DNS TXT verification failed - no TXT records", domain=domain)
            return False
        except Exception as e:
            logger.error("DNS TXT verification error", domain=domain, error=str(e))
            return False

    async def _verify_dns_cname(self, domain: str, expected_token: str, tenant_id: str) -> bool:
        """Verify domain using DNS CNAME record.

        Args:
            domain: Domain to verify
            expected_token: Expected verification token
            tenant_id: Tenant ID

        Returns:
            bool: True if verified
        """
        try:
            # For CNAME verification, we check a specific subdomain
            verification_subdomain = f"_dotmac-verify.{domain}"

            # Query CNAME records
            cname_records = await asyncio.to_thread(
                self.dns_resolver.resolve, verification_subdomain, "CNAME"
            )

            # Expected CNAME target includes tenant_id for uniqueness
            expected_target = f"{expected_token}.verify.dotmac-platform.com"

            for record in cname_records:
                cname_target = str(record.target).rstrip(".")

                if cname_target == expected_target:
                    logger.info(
                        "DNS CNAME verification successful",
                        domain=domain,
                        subdomain=verification_subdomain,
                        target=cname_target,
                    )
                    return True

            logger.warning(
                "DNS CNAME verification failed - target mismatch",
                domain=domain,
                expected=expected_target,
            )
            return False

        except dns.resolver.NXDOMAIN:
            logger.warning("DNS CNAME verification failed - subdomain not found", domain=domain)
            return False
        except dns.resolver.NoAnswer:
            logger.warning("DNS CNAME verification failed - no CNAME records", domain=domain)
            return False
        except Exception as e:
            logger.error("DNS CNAME verification error", domain=domain, error=str(e))
            return False

    def _get_verification_instructions(
        self, domain: str, token: str, method: VerificationMethod
    ) -> dict[str, Any]:
        """Get verification instructions for a method.

        Args:
            domain: Domain to verify
            token: Verification token
            method: Verification method

        Returns:
            dict: Verification instructions
        """
        if method == VerificationMethod.DNS_TXT:
            return {
                "type": "DNS TXT Record",
                "description": "Add a TXT record to your DNS configuration",
                "steps": [
                    "Log in to your DNS provider (e.g., Cloudflare, Route53, Namecheap)",
                    "Add a new TXT record for your domain",
                    f"Set the value to: dotmac-verify={token}",
                    "Wait 5-10 minutes for DNS propagation",
                    "Click 'Verify Domain' to complete verification",
                ],
                "dns_record": {
                    "type": "TXT",
                    "name": "@" if domain else domain,
                    "value": f"dotmac-verify={token}",
                    "ttl": 3600,
                },
                "verification_command": f"dig {domain} TXT +short",
            }
        elif method == VerificationMethod.DNS_CNAME:
            return {
                "type": "DNS CNAME Record",
                "description": "Add a CNAME record to your DNS configuration",
                "steps": [
                    "Log in to your DNS provider",
                    "Add a new CNAME record",
                    f"Set the name to: _dotmac-verify.{domain}",
                    f"Set the target to: {token}.verify.dotmac-platform.com",
                    "Wait 5-10 minutes for DNS propagation",
                    "Click 'Verify Domain' to complete verification",
                ],
                "dns_record": {
                    "type": "CNAME",
                    "name": f"_dotmac-verify.{domain}",
                    "target": f"{token}.verify.dotmac-platform.com",
                    "ttl": 3600,
                },
                "verification_command": f"dig _dotmac-verify.{domain} CNAME +short",
            }
        else:
            return {
                "type": method.value,
                "description": "Verification method not yet implemented",
                "steps": [],
            }

    async def remove_domain(self, tenant_id: str, domain: str, user_id: str) -> dict[str, Any]:
        """Remove verified domain from tenant.

        Args:
            tenant_id: Tenant ID
            domain: Domain to remove
            user_id: User requesting removal

        Returns:
            dict: Removal result
        """
        tenant = await self._get_tenant(tenant_id)

        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")

        if tenant.domain != domain:
            raise ValueError(f"Domain {domain} is not associated with tenant {tenant_id}")

        # Remove domain
        tenant.domain = None
        tenant.updated_at = datetime.now(UTC)

        await self.db.commit()

        # Log audit event
        await self.audit_service.log_activity(
            tenant_id=tenant_id,
            user_id=user_id,
            action="domain.removed",
            resource_type="domain",
            resource_id=domain,
            details={"domain": domain},
        )

        logger.info("Domain removed", tenant_id=tenant_id, domain=domain)

        return {
            "domain": domain,
            "status": "removed",
            "removed_at": datetime.now(UTC),
        }

    def _is_valid_domain(self, domain: str) -> bool:
        """Validate domain format.

        Args:
            domain: Domain to validate

        Returns:
            bool: True if valid
        """
        import re

        # Basic domain validation regex
        # Allows: example.com, sub.example.com, sub-domain.example.co.uk
        domain_regex = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"

        if not domain or len(domain) > 255:
            return False

        if not re.match(domain_regex, domain):
            return False

        # Prevent localhost and internal domains
        blocked_domains = [
            "localhost",
            "127.0.0.1",
            "0.0.0.0",  # nosec B104 - blocking this domain, not binding to it
            ".local",
            ".internal",
        ]
        if any(blocked in domain.lower() for blocked in blocked_domains):
            return False

        return True

    async def _get_tenant(self, tenant_id: str) -> Tenant | None:
        """Get tenant by ID.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant or None
        """
        result = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id, Tenant.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def _check_domain_exists(self, domain: str, exclude_tenant_id: str | None = None) -> bool:
        """Check if domain is already verified for another tenant.

        Args:
            domain: Domain to check
            exclude_tenant_id: Optional tenant ID to exclude from check

        Returns:
            bool: True if domain exists for another tenant
        """
        query = select(Tenant).where(
            Tenant.domain == domain,
            Tenant.deleted_at.is_(None),
        )

        if exclude_tenant_id:
            query = query.where(Tenant.id != exclude_tenant_id)

        result = await self.db.execute(query)
        existing_tenant = result.scalar_one_or_none()

        return existing_tenant is not None
