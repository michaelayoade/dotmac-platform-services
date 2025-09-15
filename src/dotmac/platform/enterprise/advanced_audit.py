"""
Advanced audit logging with enhanced security features.
"""

from typing import Any, Optional

import structlog

from ..audit import AuditEvent, AuditEventType, AuditLogger, AuditSeverity

logger = structlog.get_logger(__name__)


class AdvancedAuditLogger(AuditLogger):
    """Enhanced audit logger with enterprise security features."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enable_encryption = kwargs.get("enable_encryption", True)
        self.enable_integrity_checks = kwargs.get("enable_integrity_checks", True)
        self.retention_policy_days = kwargs.get("retention_policy_days", 2555)  # 7 years default

    async def log_compliance_event(
        self,
        event_type: str,
        compliance_framework: str,
        description: str,
        evidence: dict[str, Any],
        actor_id: Optional[str] = None,
        **kwargs,
    ) -> AuditEvent:
        """
        Log compliance-related security event.

        Args:
            event_type: Type of compliance event
            compliance_framework: Relevant compliance framework (SOC2, GDPR, etc.)
            description: Event description
            evidence: Supporting evidence/documentation
            actor_id: ID of the actor involved

        Returns:
            Created audit event
        """
        return await self.log_event(
            event_type=AuditEventType.SECURITY_POLICY_VIOLATION,
            message=f"Compliance event: {description}",
            actor_id=actor_id,
            severity=AuditSeverity.HIGH,
            custom_attributes={
                "compliance_framework": compliance_framework,
                "event_type": event_type,
                "evidence": evidence,
            },
            **kwargs,
        )

    async def log_privacy_event(
        self,
        event_type: str,
        data_subject_id: str,
        data_categories: list[str],
        lawful_basis: str,
        retention_period: Optional[str] = None,
        **kwargs,
    ) -> AuditEvent:
        """
        Log privacy-related events for GDPR compliance.

        Args:
            event_type: Type of privacy event (access, rectification, erasure, etc.)
            data_subject_id: ID of the data subject
            data_categories: Categories of personal data involved
            lawful_basis: Legal basis for processing
            retention_period: Data retention period

        Returns:
            Created audit event
        """
        return await self.log_event(
            event_type=AuditEventType.DATA_READ if "access" in event_type else AuditEventType.DATA_UPDATE,
            message=f"Privacy event: {event_type} for data subject {data_subject_id}",
            severity=AuditSeverity.HIGH,
            custom_attributes={
                "privacy_event": True,
                "event_type": event_type,
                "data_subject_id": data_subject_id,
                "data_categories": data_categories,
                "lawful_basis": lawful_basis,
                "retention_period": retention_period,
            },
            **kwargs,
        )

    async def log_security_incident(
        self,
        incident_type: str,
        severity: str,
        affected_systems: list[str],
        attack_vectors: list[str],
        mitigation_actions: list[str],
        **kwargs,
    ) -> AuditEvent:
        """
        Log security incident with detailed forensic information.

        Args:
            incident_type: Type of security incident
            severity: Incident severity level
            affected_systems: List of affected systems/components
            attack_vectors: Identified attack vectors
            mitigation_actions: Actions taken to mitigate

        Returns:
            Created audit event
        """
        # Map severity to audit severity
        severity_mapping = {
            "low": AuditSeverity.LOW,
            "medium": AuditSeverity.MEDIUM,
            "high": AuditSeverity.HIGH,
            "critical": AuditSeverity.CRITICAL,
        }

        return await self.log_event(
            event_type=AuditEventType.SECURITY_INTRUSION_DETECTED,
            message=f"Security incident: {incident_type}",
            severity=severity_mapping.get(severity.lower(), AuditSeverity.HIGH),
            custom_attributes={
                "security_incident": True,
                "incident_type": incident_type,
                "severity": severity,
                "affected_systems": affected_systems,
                "attack_vectors": attack_vectors,
                "mitigation_actions": mitigation_actions,
                "requires_notification": severity.lower() in ["high", "critical"],
            },
            **kwargs,
        )

    async def log_privileged_access(
        self,
        user_id: str,
        privilege_type: str,
        target_resource: str,
        justification: str,
        approval_required: bool = True,
        **kwargs,
    ) -> AuditEvent:
        """
        Log privileged access events for enhanced monitoring.

        Args:
            user_id: User requesting/using privileges
            privilege_type: Type of privilege (admin, root, service_account)
            target_resource: Resource being accessed
            justification: Business justification for access
            approval_required: Whether approval was required

        Returns:
            Created audit event
        """
        return await self.log_event(
            event_type=AuditEventType.AUTHZ_PERMISSION_GRANTED,
            message=f"Privileged access: {privilege_type} to {target_resource}",
            actor_id=user_id,
            resource_id=target_resource,
            severity=AuditSeverity.HIGH,
            custom_attributes={
                "privileged_access": True,
                "privilege_type": privilege_type,
                "justification": justification,
                "approval_required": approval_required,
                "monitoring_required": True,
            },
            **kwargs,
        )

    async def generate_forensic_report(
        self, incident_id: str, start_time: str, end_time: str, include_evidence: bool = True
    ) -> dict[str, Any]:
        """
        Generate forensic report for security incident.

        Args:
            incident_id: Security incident identifier
            start_time: Investigation start time
            end_time: Investigation end time
            include_evidence: Whether to include evidence files

        Returns:
            Forensic report data
        """
        logger.info("Generating forensic report", incident_id=incident_id, start_time=start_time, end_time=end_time)

        # Query related audit events
        events = await self.query_events(start_time=start_time, end_time=end_time, limit=10000)

        # Filter events related to incident
        incident_events = [
            event for event in events if incident_id in str(event.custom_attributes.get("incident_id", ""))
        ]

        report = {
            "incident_id": incident_id,
            "report_period": {
                "start": start_time,
                "end": end_time,
            },
            "summary": {
                "total_events": len(incident_events),
                "affected_users": set(),
                "affected_resources": set(),
                "event_types": set(),
            },
            "timeline": [],
            "evidence": [],
            "recommendations": [],
        }

        # Analyze events
        for event in incident_events:
            if event.actor:
                report["summary"]["affected_users"].add(event.actor.actor_id)
            if event.resource:
                report["summary"]["affected_resources"].add(event.resource.resource_id)
            report["summary"]["event_types"].add(event.event_type.value)

            report["timeline"].append(
                {
                    "timestamp": event.timestamp,
                    "event_type": event.event_type.value,
                    "message": event.message,
                    "severity": event.severity.value,
                }
            )

        # Convert sets to lists for JSON serialization
        report["summary"]["affected_users"] = list(report["summary"]["affected_users"])
        report["summary"]["affected_resources"] = list(report["summary"]["affected_resources"])
        report["summary"]["event_types"] = list(report["summary"]["event_types"])

        # Sort timeline by timestamp
        report["timeline"].sort(key=lambda x: x["timestamp"])

        logger.info("Forensic report generated", incident_id=incident_id, event_count=len(incident_events))
        return report
