"""
Partner Multi-Tenant Service.

Provides service methods for partner multi-tenant API endpoints,
querying across billing, ticketing, and tenant modules.
"""

from datetime import UTC, datetime, timedelta, date
from decimal import Decimal
from typing import Any, cast
from uuid import UUID

import structlog
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.partner_management.models import PartnerTenantLink
from dotmac.platform.tenant.models import Tenant

logger = structlog.get_logger(__name__)


class PartnerMultiTenantService:
    """Service for partner multi-tenant operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_managed_tenant_metrics(
        self,
        tenant_id: str,
    ) -> dict[str, Any]:
        """
        Calculate metrics for a specific managed tenant.

        Args:
            tenant_id: The tenant ID to get metrics for

        Returns:
            Dictionary with tenant metrics
        """
        from dotmac.platform.ticketing.models import Ticket, TicketStatus

        # Get open tickets count
        tickets_query = select(func.count(Ticket.id)).where(
            and_(
                Ticket.tenant_id == tenant_id,
                Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.WAITING]),
            )
        )
        tickets_result = await self.session.execute(tickets_query)
        open_tickets_count = tickets_result.scalar() or 0

        # Get billing metrics
        billing_metrics = await self._get_tenant_billing_metrics(tenant_id)

        # Get user count
        user_count = await self._get_tenant_user_count(tenant_id)

        # Calculate SLA compliance
        sla_compliance = await self._calculate_sla_compliance(tenant_id)

        return {
            "total_users": user_count,
            "total_revenue_mtd": billing_metrics.get("revenue_mtd", Decimal("0.00")),
            "accounts_receivable": billing_metrics.get("accounts_receivable", Decimal("0.00")),
            "overdue_invoices_count": billing_metrics.get("overdue_count", 0),
            "open_tickets_count": open_tickets_count,
            "sla_compliance_pct": sla_compliance,
        }

    async def _get_tenant_billing_metrics(
        self,
        tenant_id: str,
        from_date: datetime | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """Get billing metrics for a tenant from the billing module."""
        try:
            from dotmac.platform.billing.core.entities import InvoiceEntity

            # Get current month start
            now = datetime.now(UTC)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            revenue_start = from_date or month_start

            # Query invoices for this tenant
            stmt = select(InvoiceEntity).where(InvoiceEntity.tenant_id == tenant_id)
            result = await self.session.execute(stmt)
            invoices = result.scalars().all()

            revenue_mtd = Decimal("0.00")
            accounts_receivable = Decimal("0.00")
            overdue_count = 0
            total_invoices_count = 0
            oldest_overdue_days = None

            status_filter = status.lower() if status else None

            for invoice in invoices:
                inv_status = self._normalize_invoice_status(invoice)
                if status_filter and inv_status != status_filter:
                    continue
                total_invoices_count += 1
                # Revenue: paid invoices since requested start
                if invoice.paid_at and invoice.paid_at >= revenue_start:
                    revenue_mtd += Decimal(invoice.total_amount) / 100  # Convert from cents

                # AR: unpaid invoices
                if inv_status in ("open", "pending") and invoice.remaining_balance > 0:
                    accounts_receivable += Decimal(invoice.remaining_balance) / 100

                # Overdue: past due date and unpaid
                if invoice.due_date and invoice.due_date < now and inv_status not in ("paid", "void"):
                    overdue_count += 1
                    overdue_days = (now - invoice.due_date).days
                    if overdue_days is not None:
                        if oldest_overdue_days is None or overdue_days > oldest_overdue_days:
                            oldest_overdue_days = overdue_days

            return {
                "revenue_mtd": revenue_mtd,
                "accounts_receivable": accounts_receivable,
                "overdue_count": overdue_count,
                "total_invoices_count": total_invoices_count,
                "oldest_overdue_days": oldest_overdue_days,
            }
        except ImportError:
            logger.debug("Billing module not available for metrics")
            return {
                "revenue_mtd": Decimal("0.00"),
                "accounts_receivable": Decimal("0.00"),
                "overdue_count": 0,
                "total_invoices_count": 0,
                "oldest_overdue_days": None,
            }
        except Exception as e:
            logger.warning("Failed to get billing metrics", tenant_id=tenant_id, error=str(e))
            return {
                "revenue_mtd": Decimal("0.00"),
                "accounts_receivable": Decimal("0.00"),
                "overdue_count": 0,
                "total_invoices_count": 0,
                "oldest_overdue_days": None,
            }

    async def _get_tenant_user_count(self, tenant_id: str) -> int:
        """Get active user count for a tenant."""
        try:
            from dotmac.platform.user_management.models import User

            result = await self.session.execute(
                select(func.count(User.id)).where(
                    and_(
                        User.tenant_id == tenant_id,
                        User.is_active.is_(True),
                        User.deleted_at.is_(None),
                    )
                )
            )
            return result.scalar() or 0
        except ImportError:
            logger.debug("User management module not available")
            return 0
        except Exception as e:
            logger.warning("Failed to get user count", tenant_id=tenant_id, error=str(e))
            return 0

    async def _calculate_sla_compliance(self, tenant_id: str) -> Decimal | None:
        """Calculate SLA compliance percentage for a tenant."""
        try:
            from dotmac.platform.ticketing.models import Ticket

            # Get tickets from the last 30 days
            thirty_days_ago = datetime.now(UTC) - timedelta(days=30)

            result = await self.session.execute(
                select(
                    func.count(Ticket.id).label("total"),
                    func.sum(case((Ticket.sla_breached.is_(False), 1), else_=0)).label("met"),
                ).where(
                    and_(
                        Ticket.tenant_id == tenant_id,
                        Ticket.created_at >= thirty_days_ago,
                    )
                )
            )
            row = result.first()

            if row and row.total and row.total > 0:
                compliance = (row.met or 0) / row.total * 100
                return Decimal(str(round(compliance, 2)))

            return None
        except Exception as e:
            logger.warning("Failed to calculate SLA compliance", tenant_id=tenant_id, error=str(e))
            return None

    async def get_consolidated_billing_summary(
        self,
        managed_tenant_ids: list[str],
        from_date: datetime | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        """
        Get consolidated billing summary across all managed tenants.

        Args:
            managed_tenant_ids: List of tenant IDs the partner manages
            from_date: Optional start date for revenue calculation

        Returns:
            Consolidated billing summary
        """
        total_revenue = Decimal("0.00")
        total_ar = Decimal("0.00")
        total_overdue = Decimal("0.00")
        overdue_invoices_count = 0
        tenant_summaries = []

        for tenant_id in managed_tenant_ids:
            tenant = await self._get_tenant(tenant_id)
            if not tenant:
                continue

            metrics = await self._get_tenant_billing_metrics(
                tenant_id,
                from_date=from_date,
                status=status,
            )
            overdue_amount = await self._get_tenant_overdue_amount(
                tenant_id,
                status=status,
            )

            tenant_summary = {
                "tenant_id": str(tenant.id),
                "tenant_name": tenant.name,
                "total_revenue": metrics.get("revenue_mtd", Decimal("0.00")),
                "accounts_receivable": metrics.get("accounts_receivable", Decimal("0.00")),
                "overdue_amount": overdue_amount,
                "overdue_invoices_count": metrics.get("overdue_count", 0),
                "total_invoices_count": metrics.get("total_invoices_count", 0),
                "oldest_overdue_days": metrics.get("oldest_overdue_days"),
            }
            tenant_summaries.append(tenant_summary)

            total_revenue += tenant_summary["total_revenue"]
            total_ar += tenant_summary["accounts_receivable"]
            total_overdue += overdue_amount
            overdue_invoices_count += tenant_summary["overdue_invoices_count"]

        return {
            "total_revenue": total_revenue,
            "total_ar": total_ar,
            "total_overdue": total_overdue,
            "overdue_invoices_count": overdue_invoices_count,
            "tenants_count": len(managed_tenant_ids),
            "tenants": tenant_summaries,
            "as_of_date": datetime.now(UTC),
        }

    async def _get_tenant(self, tenant_id: str) -> Tenant | None:
        """Get tenant by ID."""
        result = await self.session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def _get_tenant_overdue_amount(
        self,
        tenant_id: str,
        status: str | None = None,
    ) -> Decimal:
        """Get total overdue amount for a tenant."""
        try:
            from dotmac.platform.billing.core.entities import InvoiceEntity

            stmt = select(InvoiceEntity).where(InvoiceEntity.tenant_id == tenant_id)
            result = await self.session.execute(stmt)
            invoices = result.scalars().all()

            now = datetime.now(UTC)
            overdue_total = Decimal("0.00")
            status_filter = status.lower() if status else None

            for invoice in invoices:
                inv_status = self._normalize_invoice_status(invoice)
                if status_filter and inv_status != status_filter:
                    continue
                if invoice.due_date and invoice.due_date < now and inv_status not in ("paid", "void"):
                    overdue_total += Decimal(invoice.remaining_balance) / 100

            return overdue_total
        except Exception as e:
            logger.warning("Failed to get overdue amount", tenant_id=tenant_id, error=str(e))
            return Decimal("0.00")

    async def list_invoices(
        self,
        managed_tenant_ids: list[str],
        tenant_id: str | None = None,
        status: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        search: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        List invoices across managed tenants.

        Returns:
            Paginated invoice list with metadata
        """
        try:
            from dotmac.platform.billing.core.entities import InvoiceEntity

            # Filter tenant IDs
            target_tenants = [tenant_id] if tenant_id else managed_tenant_ids
            status_filter = status.lower() if status else None

            all_invoices = []
            normalized_search = search.strip().lower() if search else None

            for tid in target_tenants:
                stmt = select(InvoiceEntity).where(InvoiceEntity.tenant_id == tid)
                result = await self.session.execute(stmt)
                invoices = result.scalars().all()
                tenant = await self._get_tenant(tid)
                tenant_name = tenant.name if tenant else "Unknown"

                for inv in invoices:
                    inv_status = self._normalize_invoice_status(inv)
                    invoice_date = (
                        inv.issue_date
                        or getattr(inv, "created_at", None)
                        or datetime.now(UTC)
                    )

                    # Apply filters
                    if status_filter and inv_status != status_filter:
                        continue
                    if from_date and invoice_date and invoice_date < from_date:
                        continue
                    if to_date and invoice_date and invoice_date > to_date:
                        continue
                    if normalized_search:
                        search_target = f"{inv.invoice_number or ''} {tenant_name}".lower()
                        if normalized_search not in search_target:
                            continue

                    now = datetime.now(UTC)
                    is_overdue = (
                        inv.due_date is not None
                        and inv.due_date < now
                        and inv_status not in ("paid", "void")
                    )
                    days_overdue = None
                    if is_overdue and inv.due_date:
                        days_overdue = (now - inv.due_date).days

                    all_invoices.append({
                        "invoice_id": inv.invoice_id,
                        "tenant_id": tid,
                        "tenant_name": tenant_name,
                        "invoice_number": inv.invoice_number or "",
                        "invoice_date": invoice_date,
                        "due_date": inv.due_date,
                        "amount": Decimal(inv.total_amount) / 100,
                        "paid_amount": Decimal(inv.total_amount - inv.remaining_balance) / 100,
                        "balance": Decimal(inv.remaining_balance) / 100,
                        "status": inv_status,
                        "is_overdue": is_overdue,
                        "days_overdue": days_overdue,
                    })

            # Sort by invoice date descending
            def _invoice_sort_key(invoice: dict[str, Any]) -> datetime:
                value = cast(datetime | None, invoice.get("invoice_date"))
                return self._safe_sort_datetime(value)

            all_invoices.sort(key=_invoice_sort_key, reverse=True)

            # Apply pagination
            total = len(all_invoices)
            paginated = all_invoices[offset:offset + limit]

            return {
                "invoices": paginated,
                "total": total,
                "offset": offset,
                "limit": limit,
            }
        except ImportError:
            logger.debug("Billing module not available")
            return {"invoices": [], "total": 0, "offset": offset, "limit": limit}
        except Exception as e:
            logger.error("Failed to list invoices", error=str(e))
            return {"invoices": [], "total": 0, "offset": offset, "limit": limit}

    async def list_tickets(
        self,
        managed_tenant_ids: list[str],
        tenant_id: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        List support tickets across managed tenants.

        Returns:
            Paginated ticket list with metadata
        """
        from dotmac.platform.ticketing.models import Ticket, TicketStatus, TicketPriority

        # Build query
        query = select(Ticket).where(
            Ticket.tenant_id.in_(managed_tenant_ids if not tenant_id else [tenant_id])
        )

        # Apply filters
        if status:
            try:
                status_enum = TicketStatus(status)
                query = query.where(Ticket.status == status_enum)
            except ValueError:
                pass

        if priority:
            try:
                priority_enum = TicketPriority(priority)
                query = query.where(Ticket.priority == priority_enum)
            except ValueError:
                pass

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Ticket.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(query)
        tickets = result.scalars().all()

        # Build response
        ticket_list = []
        for ticket in tickets:
            tenant = await self._get_tenant(ticket.tenant_id)
            tenant_name = tenant.name if tenant else "Unknown"

            ticket_list.append({
                "ticket_id": str(ticket.id),
                "tenant_id": ticket.tenant_id,
                "tenant_name": tenant_name,
                "ticket_number": ticket.ticket_number,
                "subject": ticket.subject,
                "status": ticket.status.value,
                "priority": ticket.priority.value,
                "created_at": ticket.created_at,
                "updated_at": ticket.updated_at or ticket.created_at,
                "assigned_to": str(ticket.assigned_to_user_id) if ticket.assigned_to_user_id else None,
                "requester_name": None,  # Would require user lookup
            })

        return {
            "tickets": ticket_list,
            "total": total,
            "offset": offset,
            "limit": limit,
        }

    async def create_ticket(
        self,
        tenant_id: str,
        subject: str,
        description: str,
        priority: str,
        created_by_user_id: str,
        category: str | None = None,
    ) -> dict[str, Any]:
        """
        Create a support ticket for a managed tenant.

        Returns:
            Created ticket information
        """
        import uuid
        from dotmac.platform.ticketing.models import (
            Ticket,
            TicketMessage,
            TicketActorType,
            TicketPriority,
            TicketStatus,
        )

        try:
            priority_enum = TicketPriority(priority)
        except ValueError:
            priority_enum = TicketPriority.NORMAL

        ticket_number = f"TKT-{uuid.uuid4().hex[:8].upper()}"

        ticket = Ticket(
            ticket_number=ticket_number,
            subject=subject,
            status=TicketStatus.OPEN,
            priority=priority_enum,
            origin_type=TicketActorType.PARTNER,
            target_type=TicketActorType.TENANT,
            tenant_id=tenant_id,
            context={"category": category} if category else {},
            created_by=created_by_user_id,
        )

        # Add initial message
        initial_message = TicketMessage(
            ticket=ticket,
            sender_type=TicketActorType.PARTNER,
            tenant_id=tenant_id,
            body=description,
            created_by=created_by_user_id,
        )
        ticket.messages.append(initial_message)

        self.session.add(ticket)
        await self.session.commit()
        await self.session.refresh(ticket)

        logger.info(
            "Partner created ticket for managed tenant",
            ticket_id=str(ticket.id),
            ticket_number=ticket_number,
            tenant_id=tenant_id,
        )

        return {
            "ticket_id": str(ticket.id),
            "ticket_number": ticket_number,
            "tenant_id": tenant_id,
            "status": ticket.status.value,
            "created_at": ticket.created_at,
        }

    async def update_ticket(
        self,
        ticket_id: str,
        status: str | None = None,
        priority: str | None = None,
        assigned_to: str | None = None,
        notes: str | None = None,
        updated_by: str | None = None,
    ) -> dict[str, Any]:
        """
        Update a support ticket.

        Returns:
            Updated ticket information
        """
        from dotmac.platform.ticketing.models import Ticket, TicketPriority, TicketStatus

        result = await self.session.execute(
            select(Ticket).where(Ticket.id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")

        if status:
            try:
                ticket.status = TicketStatus(status)
            except ValueError:
                pass

        if priority:
            try:
                ticket.priority = TicketPriority(priority)
            except ValueError:
                pass

        if assigned_to is not None:
            ticket.assigned_to_user_id = UUID(assigned_to) if assigned_to else None

        if notes:
            # Add notes to context
            existing_notes = ticket.context.get("partner_notes", [])
            existing_notes.append({
                "note": notes,
                "added_at": datetime.now(UTC).isoformat(),
                "added_by": updated_by,
            })
            ticket.context["partner_notes"] = existing_notes

        if updated_by:
            ticket.updated_by = updated_by

        await self.session.commit()

        logger.info(
            "Partner updated ticket",
            ticket_id=ticket_id,
            status=ticket.status.value,
        )

        return {
            "ticket_id": str(ticket.id),
            "status": "updated",
            "updated_at": datetime.now(UTC),
        }

    async def get_usage_report(
        self,
        managed_tenant_ids: list[str],
        from_date: datetime,
        to_date: datetime,
        tenant_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate usage report across managed tenants.

        Returns:
            Usage report with per-tenant breakdown
        """
        target_tenants = tenant_ids if tenant_ids else managed_tenant_ids

        tenant_summaries = []
        total_data_gb = Decimal("0.00")
        total_sessions = 0

        for tenant_id in target_tenants:
            tenant = await self._get_tenant(tenant_id)
            if not tenant:
                continue

            # Get usage metrics (would query analytics/observability module)
            usage = await self._get_tenant_usage(tenant_id, from_date, to_date)

            summary = {
                "tenant_id": str(tenant.id),
                "tenant_name": tenant.name,
                "total_data_gb": usage.get("data_gb", Decimal("0.00")),
                "peak_concurrent_users": usage.get("peak_users", 0),
                "average_daily_users": usage.get("avg_daily_users", 0),
                "total_sessions": usage.get("sessions", 0),
            }
            tenant_summaries.append(summary)

            total_data_gb += summary["total_data_gb"]
            total_sessions += summary["total_sessions"]

        return {
            "period_start": from_date,
            "period_end": to_date,
            "tenants": tenant_summaries,
            "total_data_gb": total_data_gb,
            "total_sessions": total_sessions,
        }

    async def _get_tenant_usage(
        self,
        tenant_id: str,
        from_date: datetime,
        to_date: datetime,
    ) -> dict[str, Any]:
        """Get usage metrics for a tenant (placeholder for analytics integration)."""
        data_gb = Decimal("0.00")
        sessions = 0
        peak_users = 0
        avg_daily_users = 0

        try:
            from dotmac.platform.billing.usage.service import UsageBillingService

            usage_service = UsageBillingService(self.session)
            usage_stats = await usage_service.get_usage_summary(
                tenant_id,
                period_start=from_date,
                period_end=to_date,
            )

            data_usage_types = {"data_transfer", "bandwidth_gb", "overage_gb"}
            for key, summary in usage_stats.by_type.items():
                if key in data_usage_types:
                    data_gb += Decimal(summary.total_quantity)
        except ImportError:
            logger.debug("Usage billing module not available", tenant_id=tenant_id)
        except Exception as e:
            logger.warning("Failed to get usage billing stats", tenant_id=tenant_id, error=str(e))

        try:
            session_metrics = await self._get_tenant_session_metrics(
                tenant_id,
                from_date,
                to_date,
            )
            sessions = session_metrics.get("sessions", 0)
            peak_users = session_metrics.get("peak_users", 0)
            avg_daily_users = session_metrics.get("avg_daily_users", 0)
        except Exception as e:
            logger.warning("Failed to get session metrics", tenant_id=tenant_id, error=str(e))

        return {
            "data_gb": data_gb,
            "peak_users": peak_users,
            "avg_daily_users": avg_daily_users,
            "sessions": sessions,
        }

    async def get_sla_report(
        self,
        managed_tenant_ids: list[str],
        from_date: datetime,
        to_date: datetime,
        tenant_ids: list[str] | None = None,
        partner_id: str | UUID | None = None,
    ) -> dict[str, Any]:
        """
        Generate SLA compliance report across managed tenants.

        Returns:
            SLA report with per-tenant breakdown
        """
        from dotmac.platform.ticketing.models import Ticket

        target_tenants = tenant_ids if tenant_ids else managed_tenant_ids

        tenant_summaries = []
        total_compliant = 0
        total_tenants = 0

        for tenant_id in target_tenants:
            tenant = await self._get_tenant(tenant_id)
            link = await self._get_tenant_link(tenant_id, partner_id=partner_id)

            if not tenant:
                continue

            # Get SLA metrics
            result = await self.session.execute(
                select(
                    func.count(Ticket.id).label("total"),
                    func.sum(case((Ticket.sla_breached.is_(True), 1), else_=0)).label("breached"),
                    func.avg(Ticket.resolution_time_minutes).label("avg_resolution"),
                ).where(
                    and_(
                        Ticket.tenant_id == tenant_id,
                        Ticket.created_at >= from_date,
                        Ticket.created_at <= to_date,
                    )
                )
            )
            row = result.one()

            total_tickets = row.total or 0
            breached = row.breached or 0
            uptime_pct = link.sla_uptime_target if link and link.sla_uptime_target else Decimal("100.00")

            if total_tickets > 0:
                compliance_pct = ((total_tickets - breached) / total_tickets) * 100
            else:
                compliance_pct = 100.0

            avg_response_hours = Decimal("0.00")
            if row.avg_resolution:
                avg_response_hours = Decimal(str(row.avg_resolution / 60))

            sla_target_uptime = link.sla_uptime_target if link else None
            sla_target_response = link.sla_response_hours if link else None

            is_compliant = (
                breached == 0
                and (sla_target_uptime is None or uptime_pct >= sla_target_uptime)
            )

            summary = {
                "tenant_id": str(tenant.id),
                "tenant_name": tenant.name,
                "uptime_pct": uptime_pct,
                "average_response_hours": avg_response_hours,
                "sla_target_uptime": sla_target_uptime,
                "sla_target_response_hours": sla_target_response,
                "is_compliant": is_compliant,
                "breach_count": breached,
            }
            tenant_summaries.append(summary)

            if is_compliant:
                total_compliant += 1
            total_tenants += 1

        overall_compliance = Decimal("100.00")
        if total_tenants > 0:
            overall_compliance = Decimal(str(round(total_compliant / total_tenants * 100, 2)))

        return {
            "period_start": from_date,
            "period_end": to_date,
            "tenants": tenant_summaries,
            "overall_compliance_pct": overall_compliance,
        }

    async def _get_tenant_link(
        self,
        tenant_id: str,
        partner_id: str | UUID | None = None,
    ) -> PartnerTenantLink | None:
        """Get partner-tenant link for SLA config."""
        criteria = [PartnerTenantLink.managed_tenant_id == tenant_id]
        partner_uuid: UUID | None = None
        if isinstance(partner_id, UUID):
            partner_uuid = partner_id
        elif isinstance(partner_id, str):
            try:
                partner_uuid = UUID(partner_id)
            except ValueError:
                partner_uuid = None
        if partner_uuid:
            criteria.append(PartnerTenantLink.partner_id == partner_uuid)
        result = await self.session.execute(
            select(PartnerTenantLink).where(
                and_(*criteria)
            )
        )
        return result.scalar_one_or_none()

    async def get_sla_alerts(
        self,
        managed_tenant_ids: list[str],
        tenant_id: str | None = None,
        acknowledged: bool | None = None,
    ) -> dict[str, Any]:
        """
        Get SLA breach alerts for managed tenants.

        Returns:
            List of SLA alerts
        """
        from dotmac.platform.ticketing.models import Ticket

        target_tenants = [tenant_id] if tenant_id else managed_tenant_ids

        # Query tickets with SLA breaches
        query = select(Ticket).where(
            and_(
                Ticket.tenant_id.in_(target_tenants),
                Ticket.sla_breached.is_(True),
            )
        ).order_by(Ticket.created_at.desc())

        result = await self.session.execute(query)
        breached_tickets = result.scalars().all()

        alerts = []
        unacknowledged = 0

        for ticket in breached_tickets:
            tenant = await self._get_tenant(ticket.tenant_id)
            tenant_name = tenant.name if tenant else "Unknown"

            # Check if acknowledged in context
            is_acknowledged = ticket.context.get("sla_breach_acknowledged", False)

            if acknowledged is not None and is_acknowledged != acknowledged:
                continue

            alert = {
                "alert_id": f"sla-{ticket.id}",
                "tenant_id": ticket.tenant_id,
                "tenant_name": tenant_name,
                "alert_type": "response_time_breach",
                "severity": "high" if ticket.priority.value == "urgent" else "medium",
                "message": f"SLA breached for ticket {ticket.ticket_number}: {ticket.subject}",
                "detected_at": ticket.sla_due_date or ticket.created_at,
                "acknowledged": is_acknowledged,
                "acknowledged_at": ticket.context.get("sla_breach_acknowledged_at"),
            }
            alerts.append(alert)

            if not is_acknowledged:
                unacknowledged += 1

        return {
            "alerts": alerts,
            "total": len(alerts),
            "unacknowledged_count": unacknowledged,
        }

    async def get_billing_alerts(
        self,
        managed_tenant_ids: list[str],
        tenant_id: str | None = None,
        acknowledged: bool | None = None,
        partner_id: str | UUID | None = None,
    ) -> dict[str, Any]:
        """
        Get billing threshold alerts for managed tenants.

        Returns:
            List of billing alerts
        """
        target_tenants = [tenant_id] if tenant_id else managed_tenant_ids

        alerts = []
        unacknowledged = 0

        for tid in target_tenants:
            tenant = await self._get_tenant(tid)
            link = await self._get_tenant_link(tid, partner_id=partner_id)

            if not tenant or not link:
                continue

            # Skip if no threshold configured
            if not link.billing_alert_threshold:
                continue

            metrics = await self._get_tenant_billing_metrics(tid)
            ar = metrics.get("accounts_receivable", Decimal("0.00"))

            # Check if AR exceeds threshold
            if ar >= link.billing_alert_threshold:
                is_acknowledged = False  # Would be stored in alerts table

                if acknowledged is not None and is_acknowledged != acknowledged:
                    continue

                alert = {
                    "alert_id": f"billing-ar-{tid}",
                    "tenant_id": str(tenant.id),
                    "tenant_name": tenant.name,
                    "alert_type": "ar_threshold",
                    "current_amount": ar,
                    "threshold_amount": link.billing_alert_threshold,
                    "severity": "high" if ar > link.billing_alert_threshold * 2 else "medium",
                    "message": f"Accounts receivable ({ar}) exceeds threshold ({link.billing_alert_threshold})",
                    "detected_at": datetime.now(UTC),
                    "acknowledged": is_acknowledged,
                }
                alerts.append(alert)

                if not is_acknowledged:
                    unacknowledged += 1

        return {
            "alerts": alerts,
            "total": len(alerts),
            "unacknowledged_count": unacknowledged,
        }

    @staticmethod
    def _normalize_invoice_status(invoice: Any) -> str:
        """Normalize invoice status to a lowercase string for comparisons."""
        status = getattr(invoice, "status", None)
        if status is not None and hasattr(status, "value"):
            return str(status.value).lower()
        if status is None:
            return ""
        return str(status).lower()

    @staticmethod
    def _safe_sort_datetime(value: Any) -> datetime:
        """Return a timezone-aware datetime for sorting."""
        if isinstance(value, datetime):
            return value.replace(tzinfo=UTC) if value.tzinfo is None else value
        if isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
            except ValueError:
                return datetime.min.replace(tzinfo=UTC)
        return datetime.min.replace(tzinfo=UTC)

    @staticmethod
    def _coerce_event_timestamp(value: Any) -> datetime | None:
        """Coerce an event timestamp to a datetime when possible."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None

    async def _get_tenant_session_metrics(
        self,
        tenant_id: str,
        from_date: datetime,
        to_date: datetime,
    ) -> dict[str, int]:
        """Summarize session/user activity from analytics events."""
        from dotmac.platform.analytics.service import get_analytics_service

        analytics = get_analytics_service(tenant_id=tenant_id, service_name="analytics")
        events = await analytics.query_events(
            start_date=from_date,
            end_date=to_date,
            limit=10000,
        )

        session_ids: set[str] = set()
        daily_users: dict[date, set[str]] = {}

        for event in events:
            session_id = event.get("session_id") or event.get("properties", {}).get("session_id")
            if session_id:
                session_ids.add(str(session_id))

            user_id = event.get("user_id") or event.get("properties", {}).get("user_id")
            timestamp = self._coerce_event_timestamp(event.get("timestamp"))
            if user_id and timestamp:
                day = timestamp.date()
                daily_users.setdefault(day, set()).add(str(user_id))

        total_sessions = len(session_ids)
        peak_users = max((len(users) for users in daily_users.values()), default=0)

        days_span = (to_date.date() - from_date.date()).days + 1
        if days_span <= 0:
            days_span = 1
        total_daily_users = sum(len(users) for users in daily_users.values())
        avg_daily_users = int(round(total_daily_users / days_span))

        return {
            "sessions": total_sessions,
            "peak_users": peak_users,
            "avg_daily_users": avg_daily_users,
        }


__all__ = ["PartnerMultiTenantService"]
