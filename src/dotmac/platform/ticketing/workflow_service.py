"""
Ticketing Workflow Service

Provides workflow-compatible methods for ticketing operations.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..auth.core import UserInfo
from .models import TicketActorType, TicketPriority, TicketType
from .schemas import TicketCreate
from .service import TicketService

logger = logging.getLogger(__name__)


class TicketingService:
    """
    Ticketing service for workflow integration.

    Provides ticket creation and installation scheduling for workflows.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ticket(
        self,
        title: str,
        description: str,
        tenant_id: str,
        priority: str = "normal",
        assigned_team: str | None = None,
        ticket_type: str | None = None,
        service_address: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a support ticket for a tenant.

        Args:
            title: Ticket subject/title
            description: Detailed description of the issue or request
            tenant_id: Tenant ID for multi-tenant isolation
            priority: Priority level ("low", "normal", "high", "urgent")
            assigned_team: Team to assign ticket to (optional, used as metadata)
            ticket_type: Type of ticket (e.g., "technical_support", "installation_request")
            service_address: Service location address (for field operations)
        """
        logger.info(
            "Creating ticket for tenant %s, priority %s, type %s",
            tenant_id,
            priority,
            ticket_type,
        )

        # Map priority string to enum
        priority_map = {
            "low": TicketPriority.LOW,
            "normal": TicketPriority.NORMAL,
            "high": TicketPriority.HIGH,
            "urgent": TicketPriority.URGENT,
        }
        priority_enum = priority_map.get(priority.lower(), TicketPriority.NORMAL)

        # Map ticket_type string to enum (if provided)
        ticket_type_enum = None
        if ticket_type:
            type_map = {
                "general_inquiry": TicketType.GENERAL_INQUIRY,
                "billing_issue": TicketType.BILLING_ISSUE,
                "technical_support": TicketType.TECHNICAL_SUPPORT,
                "installation_request": TicketType.INSTALLATION_REQUEST,
                "outage_report": TicketType.OUTAGE_REPORT,
                "service_upgrade": TicketType.SERVICE_UPGRADE,
                "service_downgrade": TicketType.SERVICE_DOWNGRADE,
                "cancellation_request": TicketType.CANCELLATION_REQUEST,
                "equipment_issue": TicketType.EQUIPMENT_ISSUE,
                "speed_issue": TicketType.SPEED_ISSUE,
                "network_issue": TicketType.NETWORK_ISSUE,
                "connectivity_issue": TicketType.CONNECTIVITY_ISSUE,
            }
            ticket_type_enum = type_map.get(ticket_type.lower())

        # Build metadata
        metadata: dict[str, Any] = {}
        if assigned_team:
            metadata["assigned_team"] = assigned_team
            metadata["routing"] = {"team": assigned_team}

        try:
            system_user = UserInfo(
                user_id=None,
                email="system@workflow",
                tenant_id=tenant_id,
                roles=["system"],
                is_authenticated=True,
            )

            ticket_service = TicketService(self.db)

            ticket_data = TicketCreate(
                subject=title,
                message=description,
                target_type=TicketActorType.PLATFORM,
                priority=priority_enum,
                tenant_id=tenant_id,
                metadata=metadata,
                attachments=[],
                ticket_type=ticket_type_enum,
                service_address=service_address,
            )

            ticket = await ticket_service.create_ticket(
                data=ticket_data, current_user=system_user, tenant_id=tenant_id
            )

            await self.db.flush()
            await self.db.commit()

            logger.info(
                "Ticket created successfully: %s (ID: %s) for tenant %s",
                ticket.ticket_number,
                ticket.id,
                tenant_id,
            )

            return {
                "ticket_id": str(ticket.id),
                "ticket_number": ticket.ticket_number,
                "title": ticket.subject,
                "description": description,
                "priority": priority_enum.value,
                "ticket_type": ticket_type_enum.value if ticket_type_enum else None,
                "status": ticket.status.value,
                "assigned_team": assigned_team,
                "service_address": service_address,
                "origin_type": ticket.origin_type.value,
                "target_type": ticket.target_type.value,
                "created_at": ticket.created_at.isoformat(),
                "sla_due_date": ticket.sla_due_date.isoformat() if ticket.sla_due_date else None,
                "context": ticket.context,
            }

        except ValueError as e:
            logger.error("Validation error creating ticket: %s", e)
            raise

        except Exception as e:
            logger.error("Error creating ticket: %s", e, exc_info=True)
            raise RuntimeError(f"Failed to create ticket: {e}") from e
    async def schedule_installation(
        self,
        tenant_id: str,
        installation_address: str,
        technician_id: int | str | None = None,
        scheduled_date: str | None = None,
        priority: str = "normal",
        notes: str | None = None,
    ) -> dict[str, Any]:
        """
        Schedule an installation appointment for a tenant.

        This method creates an installation ticket with scheduled date/time
        and optionally assigns it to a specific field technician.
        """
        from datetime import timedelta

        logger.info(
            "Scheduling installation for tenant %s at %s",
            tenant_id,
            installation_address,
        )

        # Parse or generate scheduled date
        if scheduled_date:
            try:
                scheduled_dt = datetime.fromisoformat(scheduled_date.replace("Z", "+00:00"))
            except (ValueError, AttributeError) as e:
                raise ValueError(f"Invalid scheduled_date format: {scheduled_date}") from e
        else:
            scheduled_dt = datetime.now(UTC) + timedelta(days=3)
            scheduled_dt = scheduled_dt.replace(hour=10, minute=0, second=0, microsecond=0)

        if not technician_id:
            from sqlalchemy import select
            from ..user_management.models import User

            tech_stmt = (
                select(User)
                .where(
                    User.tenant_id == tenant_id,
                    User.is_active == True,  # noqa: E712
                )
                .limit(1)
            )

            result = await self.db.execute(tech_stmt)
            technician = result.scalar_one_or_none()

            if technician:
                technician_id = str(technician.id)
                logger.info("Auto-assigned technician: %s", technician.email)
            else:
                technician_id = "unassigned"
                logger.warning("No technician found, marked as unassigned")

        description = f"""Installation Request

Tenant ID: {tenant_id}
Installation Address: {installation_address}
Scheduled Date: {scheduled_dt.strftime('%Y-%m-%d %H:%M %Z')}
Assigned Technician: {technician_id}

{notes or 'No additional notes'}
"""

        return await self.create_ticket(
            title="Installation Request",
            description=description,
            tenant_id=tenant_id,
            priority=priority,
            ticket_type="installation_request",
            service_address=installation_address,
        )
