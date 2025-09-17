"""
Plugin certification and code review system.
Manages plugin certification lifecycle with automated and manual review processes.
"""

import asyncio

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from dotmac.platform.core.decorators import standard_exception_handler
from dotmac.platform.core import BusinessRuleError
from dotmac.platform.core.enhanced.exceptions import ValidationError
from dotmac.security.audit import get_audit_logger
from dotmac.platform.plugins.security.audit_monitor import UnifiedAuditMonitor

from .marketplace_validation_pipeline import (

    CertificationLevel,
    PluginSubmission,
    ValidationStatus,
)
from dotmac.platform.observability.unified_logging import get_logger


logger = get_logger("plugins.certification")
audit_logger = get_audit_logger()

class ReviewStatus(Enum):
    """Code review status enumeration."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_REVIEW = "in_review"
    REVIEW_COMPLETE = "review_complete"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"

class ReviewerLevel(Enum):
    """Reviewer authorization levels."""

    JUNIOR = "junior"  # Basic code review
    SENIOR = "senior"  # Standard certification review
    SECURITY_EXPERT = "security_expert"  # Premium/Enterprise security review
    COMPLIANCE_OFFICER = "compliance_officer"  # Compliance validation

@dataclass
class ReviewCriteria:
    """Code review criteria definition."""

    criteria_id: str
    name: str
    description: str
    category: str  # "security", "performance", "quality", "compliance"
    weight: float = 1.0  # Scoring weight
    required_for_levels: list[CertificationLevel] = field(default_factory=list)
    reviewer_levels: list[ReviewerLevel] = field(default_factory=list)

@dataclass
class ReviewComment:
    """Individual review comment."""

    comment_id: str = field(default_factory=lambda: str(uuid4()))
    reviewer_id: str = ""
    criteria_id: Optional[str] = None
    line_number: Optional[int] = None
    file_path: Optional[str] = None

    # Comment details
    comment_type: str = "general"  # "general", "issue", "suggestion", "blocker"
    severity: str = "info"  # "info", "warning", "error", "critical"
    title: str = ""
    description: str = ""

    # Resolution
    resolved: bool = False
    resolution_notes: str = ""

    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

@dataclass
class CodeReview:
    """Complete code review record."""

    review_id: str = field(default_factory=lambda: str(uuid4()))
    submission_id: str = ""
    reviewer_id: str = ""
    reviewer_level: ReviewerLevel = ReviewerLevel.JUNIOR

    # Review details
    certification_level: CertificationLevel = CertificationLevel.BASIC
    assigned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Status and results
    status: ReviewStatus = ReviewStatus.PENDING
    overall_score: float = 0.0
    criteria_scores: dict[str, float] = field(default_factory=dict)

    # Comments and feedback
    comments: list[ReviewComment] = field(default_factory=list)
    summary: str = ""
    recommendation: str = ""  # "approve", "reject", "request_changes"

    # Time tracking
    estimated_hours: float = 0.0
    actual_hours: float = 0.0

@dataclass
class PluginCertificate:
    """Plugin certification certificate."""

    certificate_id: str = field(default_factory=lambda: str(uuid4()))
    plugin_id: str = ""
    submission_id: str = ""

    # Certification details
    certification_level: CertificationLevel = CertificationLevel.BASIC
    version: str = ""
    issuer: str = "DotMac Platform"

    # Validity
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=365)
    )
    revoked: bool = False
    revoked_at: Optional[datetime] = None
    revocation_reason: str = ""

    # Metadata
    security_score: float = 0.0
    compliance_validated: bool = False
    manual_review_completed: bool = False

    # Associated reviews
    review_ids: list[str] = field(default_factory=list)

    # Permissions granted
    granted_permissions: list[str] = field(default_factory=list)
    restrictions: list[str] = field(default_factory=list)

class PluginCertificationSystem:
    """
    Comprehensive plugin certification and code review system.
    """

    def __init__(self, audit_monitor: Optional[UnifiedAuditMonitor] = None):
        self.audit_monitor = audit_monitor  # Optional audit monitor

        # Review criteria by category
        self.review_criteria = self._initialize_review_criteria()

        # Active reviews and certificates
        self._active_reviews: dict[str, CodeReview] = {}
        self._certificates: dict[str, PluginCertificate] = {}
        self._reviewer_queue: asyncio.Queue = asyncio.Queue()

        # Configuration
        self.max_review_days = {
            CertificationLevel.BASIC: 2,
            CertificationLevel.STANDARD: 5,
            CertificationLevel.PREMIUM: 10,
            CertificationLevel.ENTERPRISE: 15,
        }

    def _initialize_review_criteria(self) -> dict[str, list[ReviewCriteria]]:
        """Initialize review criteria by category."""
        return {
            "security": [
                ReviewCriteria(
                    "sec_001",
                    "Input Validation",
                    "Proper input validation and sanitization",
                    "security",
                    weight=2.0,
                    required_for_levels=[
                        CertificationLevel.STANDARD,
                        CertificationLevel.PREMIUM,
                        CertificationLevel.ENTERPRISE,
                    ],
                    reviewer_levels=[ReviewerLevel.SENIOR, ReviewerLevel.SECURITY_EXPERT],
                ),
                ReviewCriteria(
                    "sec_002",
                    "Authentication & Authorization",
                    "Proper authentication and authorization implementation",
                    "security",
                    weight=2.5,
                    required_for_levels=[CertificationLevel.PREMIUM, CertificationLevel.ENTERPRISE],
                    reviewer_levels=[ReviewerLevel.SECURITY_EXPERT],
                ),
                ReviewCriteria(
                    "sec_003",
                    "Data Encryption",
                    "Sensitive data encryption at rest and in transit",
                    "security",
                    weight=2.0,
                    required_for_levels=[CertificationLevel.PREMIUM, CertificationLevel.ENTERPRISE],
                    reviewer_levels=[ReviewerLevel.SECURITY_EXPERT],
                ),
                ReviewCriteria(
                    "sec_004",
                    "SQL Injection Prevention",
                    "Protection against SQL injection attacks",
                    "security",
                    weight=2.5,
                    required_for_levels=[
                        CertificationLevel.STANDARD,
                        CertificationLevel.PREMIUM,
                        CertificationLevel.ENTERPRISE,
                    ],
                    reviewer_levels=[ReviewerLevel.SENIOR, ReviewerLevel.SECURITY_EXPERT],
                ),
            ],
            "performance": [
                ReviewCriteria(
                    "perf_001",
                    "Resource Usage",
                    "Efficient memory and CPU usage",
                    "performance",
                    weight=1.5,
                    required_for_levels=[
                        CertificationLevel.STANDARD,
                        CertificationLevel.PREMIUM,
                        CertificationLevel.ENTERPRISE,
                    ],
                    reviewer_levels=[ReviewerLevel.SENIOR, ReviewerLevel.SECURITY_EXPERT],
                ),
                ReviewCriteria(
                    "perf_002",
                    "Async/Await Usage",
                    "Proper async/await implementation for I/O operations",
                    "performance",
                    weight=1.0,
                    required_for_levels=[CertificationLevel.PREMIUM, CertificationLevel.ENTERPRISE],
                    reviewer_levels=[ReviewerLevel.SENIOR],
                ),
                ReviewCriteria(
                    "perf_003",
                    "Database Query Optimization",
                    "Efficient database query patterns",
                    "performance",
                    weight=1.5,
                    required_for_levels=[CertificationLevel.PREMIUM, CertificationLevel.ENTERPRISE],
                    reviewer_levels=[ReviewerLevel.SENIOR],
                ),
            ],
            "quality": [
                ReviewCriteria(
                    "qual_001",
                    "Code Structure",
                    "Clean, maintainable code structure",
                    "quality",
                    weight=1.0,
                    required_for_levels=[
                        CertificationLevel.STANDARD,
                        CertificationLevel.PREMIUM,
                        CertificationLevel.ENTERPRISE,
                    ],
                    reviewer_levels=[ReviewerLevel.JUNIOR, ReviewerLevel.SENIOR],
                ),
                ReviewCriteria(
                    "qual_002",
                    "Error Handling",
                    "Comprehensive error handling and recovery",
                    "quality",
                    weight=1.5,
                    required_for_levels=[
                        CertificationLevel.STANDARD,
                        CertificationLevel.PREMIUM,
                        CertificationLevel.ENTERPRISE,
                    ],
                    reviewer_levels=[ReviewerLevel.SENIOR],
                ),
                ReviewCriteria(
                    "qual_003",
                    "Documentation",
                    "Adequate code documentation and comments",
                    "quality",
                    weight=1.0,
                    required_for_levels=[
                        CertificationLevel.STANDARD,
                        CertificationLevel.PREMIUM,
                        CertificationLevel.ENTERPRISE,
                    ],
                    reviewer_levels=[ReviewerLevel.JUNIOR, ReviewerLevel.SENIOR],
                ),
                ReviewCriteria(
                    "qual_004",
                    "Testing Coverage",
                    "Adequate unit and integration test coverage",
                    "quality",
                    weight=1.5,
                    required_for_levels=[CertificationLevel.PREMIUM, CertificationLevel.ENTERPRISE],
                    reviewer_levels=[ReviewerLevel.SENIOR],
                ),
            ],
            "compliance": [
                ReviewCriteria(
                    "comp_001",
                    "Data Privacy Compliance",
                    "GDPR/CCPA compliance for data handling",
                    "compliance",
                    weight=3.0,
                    required_for_levels=[CertificationLevel.ENTERPRISE],
                    reviewer_levels=[ReviewerLevel.COMPLIANCE_OFFICER],
                ),
                ReviewCriteria(
                    "comp_002",
                    "Audit Logging",
                    "Comprehensive audit logging implementation",
                    "compliance",
                    weight=2.0,
                    required_for_levels=[CertificationLevel.ENTERPRISE],
                    reviewer_levels=[
                        ReviewerLevel.COMPLIANCE_OFFICER,
                        ReviewerLevel.SECURITY_EXPERT,
                    ],
                ),
                ReviewCriteria(
                    "comp_003",
                    "Multi-tenant Isolation",
                    "Proper tenant data isolation",
                    "compliance",
                    weight=2.5,
                    required_for_levels=[CertificationLevel.ENTERPRISE],
                    reviewer_levels=[
                        ReviewerLevel.COMPLIANCE_OFFICER,
                        ReviewerLevel.SECURITY_EXPERT,
                    ],
                ),
            ],
        }

    @standard_exception_handler
    async def create_review_assignment(
        self, submission: PluginSubmission, reviewer_id: str, reviewer_level: ReviewerLevel
    ) -> str:
        """Create code review assignment."""

        # Validate reviewer level for certification level
        self._validate_reviewer_authorization(submission.requested_certification, reviewer_level)

        # Create review record
        review = CodeReview(
            submission_id=submission.submission_id,
            reviewer_id=reviewer_id,
            reviewer_level=reviewer_level,
            certification_level=submission.requested_certification,
            estimated_hours=self._estimate_review_hours(submission.requested_certification),
        )

        # Store review
        self._active_reviews[review.review_id] = review

        # Update submission status
        submission.status = ValidationStatus.MANUAL_REVIEW

        audit_logger.info(
            "Code review assigned",
            extra={
                "review_id": review.review_id,
                "submission_id": submission.submission_id,
                "plugin_name": submission.plugin_name,
                "reviewer_id": reviewer_id,
                "reviewer_level": reviewer_level.value,
                "certification_level": submission.requested_certification.value,
            },
        )

        return review.review_id

    def _validate_reviewer_authorization(
        self, certification_level: CertificationLevel, reviewer_level: ReviewerLevel
    ) -> None:
        """Validate reviewer is authorized for certification level."""

        authorization_matrix = {
            CertificationLevel.BASIC: [
                ReviewerLevel.JUNIOR,
                ReviewerLevel.SENIOR,
                ReviewerLevel.SECURITY_EXPERT,
            ],
            CertificationLevel.STANDARD: [ReviewerLevel.SENIOR, ReviewerLevel.SECURITY_EXPERT],
            CertificationLevel.PREMIUM: [ReviewerLevel.SECURITY_EXPERT],
            CertificationLevel.ENTERPRISE: [
                ReviewerLevel.SECURITY_EXPERT,
                ReviewerLevel.COMPLIANCE_OFFICER,
            ],
        }

        if reviewer_level not in authorization_matrix.get(certification_level, []):
            raise BusinessRuleError(
                f"Reviewer level {reviewer_level.value} not authorized for {certification_level.value} certification"
            )

    def _estimate_review_hours(self, certification_level: CertificationLevel) -> float:
        """Estimate review hours based on certification level."""
        estimates = {
            CertificationLevel.BASIC: 2.0,
            CertificationLevel.STANDARD: 8.0,
            CertificationLevel.PREMIUM: 16.0,
            CertificationLevel.ENTERPRISE: 24.0,
        }
        return estimates.get(certification_level, 4.0)

    @standard_exception_handler
    async def start_review(self, review_id: str) -> None:
        """Start code review process."""

        if review_id not in self._active_reviews:
            raise ValidationError(f"Review not found: {review_id}")

        review = self._active_reviews[review_id]

        if review.status != ReviewStatus.PENDING:
            raise BusinessRuleError(f"Review not in pending status: {review.status}")

        # Update review status
        review.status = ReviewStatus.IN_REVIEW
        review.started_at = datetime.now(timezone.utc)

        audit_logger.info(
            "Code review started",
            extra={
                "review_id": review_id,
                "reviewer_id": review.reviewer_id,
                "submission_id": review.submission_id,
            },
        )

    @standard_exception_handler
    async def submit_review_comment(
        self,
        review_id: str,
        comment: ReviewComment,
    ) -> str:
        """Submit review comment."""

        if review_id not in self._active_reviews:
            raise ValidationError(f"Review not found: {review_id}")

        review = self._active_reviews[review_id]

        if review.status not in [ReviewStatus.IN_REVIEW, ReviewStatus.ASSIGNED]:
            raise BusinessRuleError(f"Cannot add comments to review in status: {review.status}")

        # Add comment to review
        review.comments.append(comment)

        audit_logger.info(
            "Review comment added",
            extra={
                "review_id": review_id,
                "comment_id": comment.comment_id,
                "comment_type": comment.comment_type,
                "severity": comment.severity,
                "reviewer_id": review.reviewer_id,
            },
        )

        return comment.comment_id

    @standard_exception_handler
    async def complete_review(
        self,
        review_id: str,
        overall_score: float,
        criteria_scores: dict[str, float],
        summary: str,
        recommendation: str,
    ) -> None:
        """Complete code review with final assessment."""

        if review_id not in self._active_reviews:
            raise ValidationError(f"Review not found: {review_id}")

        review = self._active_reviews[review_id]

        if review.status != ReviewStatus.IN_REVIEW:
            raise BusinessRuleError(f"Review not in progress: {review.status}")

        # Validate scores
        if not (0.0 <= overall_score <= 10.0):
            raise ValidationError("Overall score must be between 0.0 and 10.0")

        if recommendation not in ["approve", "reject", "request_changes"]:
            raise ValidationError(
                "Recommendation must be 'approve', 'reject', or 'request_changes'"
            )

        # Update review
        review.status = ReviewStatus.REVIEW_COMPLETE
        review.completed_at = datetime.now(timezone.utc)
        review.overall_score = overall_score
        review.criteria_scores = criteria_scores
        review.summary = summary
        review.recommendation = recommendation

        # Calculate actual hours (simplified - would use time tracking in production)
        if review.started_at:
            hours = (review.completed_at - review.started_at).total_seconds() / 3600
            review.actual_hours = hours

        audit_logger.info(
            "Code review completed",
            extra={
                "review_id": review_id,
                "reviewer_id": review.reviewer_id,
                "overall_score": overall_score,
                "recommendation": recommendation,
                "actual_hours": review.actual_hours,
                "comment_count": len(review.comments),
            },
        )

        # Process recommendation
        await self._process_review_recommendation(review)

    async def _process_review_recommendation(self, review: CodeReview) -> None:
        """Process review recommendation and update submission status."""

        if review.recommendation == "approve":
            # Create certificate if all reviews approve
            await self._check_certification_eligibility(review.submission_id)

        elif review.recommendation == "request_changes":
            review.status = ReviewStatus.CHANGES_REQUESTED
            # Notification would be sent to plugin author

        elif review.recommendation == "reject":
            review.status = ReviewStatus.REJECTED
            # Update submission status and notify author

    async def _check_certification_eligibility(self, submission_id: str) -> None:
        """Check if submission is eligible for certification."""

        # Get all reviews for submission
        submission_reviews = [
            review
            for review in self._active_reviews.values()
            if review.submission_id == submission_id
        ]

        # Check if all required reviews are complete and approved
        all_approved = all(
            review.recommendation == "approve" and review.status == ReviewStatus.REVIEW_COMPLETE
            for review in submission_reviews
        )

        if all_approved and submission_reviews:
            await self._issue_certificate(submission_id, submission_reviews)

    @standard_exception_handler
    async def issue_certificate(
        self,
        submission: PluginSubmission,
        reviews: list[CodeReview],
        issuer_id: str,
    ) -> str:
        """Issue plugin certificate."""

        # Calculate security score from reviews
        security_score = self._calculate_security_score(reviews)

        # Determine granted permissions
        granted_permissions = self._determine_granted_permissions(submission, reviews)

        # Create certificate
        certificate = PluginCertificate(
            plugin_id=submission.plugin_id,
            submission_id=submission.submission_id,
            certification_level=submission.requested_certification,
            version=submission.version,
            security_score=security_score,
            compliance_validated=self._check_compliance_validation(reviews),
            manual_review_completed=True,
            review_ids=[review.review_id for review in reviews],
            granted_permissions=granted_permissions,
        )

        # Store certificate
        self._certificates[certificate.certificate_id] = certificate

        # Update submission status
        submission.status = ValidationStatus.APPROVED

        audit_logger.info(
            "Plugin certificate issued",
            extra={
                "certificate_id": certificate.certificate_id,
                "plugin_id": submission.plugin_id,
                "plugin_name": submission.plugin_name,
                "certification_level": certificate.certification_level.value,
                "security_score": security_score,
                "issuer_id": issuer_id,
            },
        )

        return certificate.certificate_id

    async def _issue_certificate(self, submission_id: str, reviews: list[CodeReview]) -> None:
        """Internal certificate issuance."""
        # Implementation would get submission and issue certificate
        pass

    def _calculate_security_score(self, reviews: list[CodeReview]) -> float:
        """Calculate overall security score from reviews."""
        if not reviews:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for review in reviews:
            # Weight by reviewer level
            weight_multiplier = {
                ReviewerLevel.JUNIOR: 1.0,
                ReviewerLevel.SENIOR: 1.5,
                ReviewerLevel.SECURITY_EXPERT: 2.0,
                ReviewerLevel.COMPLIANCE_OFFICER: 1.8,
            }

            weight = weight_multiplier.get(review.reviewer_level, 1.0)
            total_score += review.overall_score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.0

    def _determine_granted_permissions(
        self, submission: PluginSubmission, reviews: list[CodeReview]
    ) -> list[str]:
        """Determine permissions to grant based on review results."""
        base_permissions = {
            CertificationLevel.BASIC: ["filesystem:read_temp", "api:read_basic"],
            CertificationLevel.STANDARD: [
                "filesystem:read",
                "api:read",
                "api:write",
                "network:http",
            ],
            CertificationLevel.PREMIUM: ["filesystem:write", "database:read", "database:write"],
            CertificationLevel.ENTERPRISE: [
                "tenant_data:read",
                "tenant_data:write",
                "audit_logs:write",
            ],
        }

        permissions = base_permissions.get(submission.requested_certification, [])

        # Additional permissions based on review scores
        avg_score = self._calculate_security_score(reviews)
        if avg_score >= 9.0:
            permissions.extend(["premium:access"])

        return permissions

    def _check_compliance_validation(self, reviews: list[CodeReview]) -> bool:
        """Check if compliance validation was performed."""
        return any(review.reviewer_level == ReviewerLevel.COMPLIANCE_OFFICER for review in reviews)

    @standard_exception_handler
    async def revoke_certificate(
        self,
        certificate_id: str,
        reason: str,
        revoker_id: str,
    ) -> None:
        """Revoke plugin certificate."""

        if certificate_id not in self._certificates:
            raise ValidationError(f"Certificate not found: {certificate_id}")

        certificate = self._certificates[certificate_id]

        if certificate.revoked:
            raise BusinessRuleError("Certificate already revoked")

        # Revoke certificate
        certificate.revoked = True
        certificate.revoked_at = datetime.now(timezone.utc)
        certificate.revocation_reason = reason

        audit_logger.warning(
            "Plugin certificate revoked",
            extra={
                "certificate_id": certificate_id,
                "plugin_id": certificate.plugin_id,
                "reason": reason,
                "revoker_id": revoker_id,
            },
        )

    # Query methods

    def get_review(self, review_id: str) -> Optional[CodeReview]:
        """Get review by ID."""
        return self._active_reviews.get(review_id)

    def get_reviews_by_reviewer(self, reviewer_id: str) -> list[CodeReview]:
        """Get reviews assigned to reviewer."""
        return [
            review for review in self._active_reviews.values() if review.reviewer_id == reviewer_id
        ]

    def get_certificate(self, certificate_id: str) -> Optional[PluginCertificate]:
        """Get certificate by ID."""
        return self._certificates.get(certificate_id)

    def get_plugin_certificates(self, plugin_id: str) -> list[PluginCertificate]:
        """Get all certificates for a plugin."""
        return [cert for cert in self._certificates.values() if cert.plugin_id == plugin_id]

    def get_active_certificate(self, plugin_id: str) -> Optional[PluginCertificate]:
        """Get active (non-revoked) certificate for plugin."""
        certificates = self.get_plugin_certificates(plugin_id)
        active_certs = [cert for cert in certificates if not cert.revoked]

        # Return most recent active certificate
        return max(active_certs, key=lambda c: c.issued_at) if active_certs else None

    def get_expiring_certificates(self, days_ahead: int = 30) -> list[PluginCertificate]:
        """Get certificates expiring within specified days."""
        cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)

        return [
            cert
            for cert in self._certificates.values()
            if not cert.revoked and cert.valid_until <= cutoff_date
        ]

# Factory function for dependency injection
def create_certification_system(
    audit_monitor: Optional[UnifiedAuditMonitor] = None,
) -> PluginCertificationSystem:
    """Create plugin certification system."""
    return PluginCertificationSystem(audit_monitor)

__all__ = [
    "ReviewStatus",
    "ReviewerLevel",
    "ReviewCriteria",
    "ReviewComment",
    "CodeReview",
    "PluginCertificate",
    "PluginCertificationSystem",
    "create_certification_system",
]
