"""Partner Multi-Tenant API Router.

Provides endpoints for partners to manage multiple tenant accounts.
"""

from datetime import UTC, datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.auth.core import UserInfo, ensure_uuid, get_current_user
from dotmac.platform.auth.rbac_dependencies import PartnerPermissionChecker
from dotmac.platform.db import get_async_session
from dotmac.platform.partner_management.models import PartnerTenantLink
from dotmac.platform.partner_management.schemas_multitenant import (
    BillingAlertListResponse,
    ConsolidatedBillingSummary,
    CreateTicketRequest,
    CreateTicketResponse,
    InvoiceExportRequest,
    InvoiceExportResponse,
    InvoiceListResponse,
    ManagedTenantDetail,
    ManagedTenantListResponse,
    SLAAlertListResponse,
    SLAReportResponse,
    TicketListResponse,
    UpdateTicketRequest,
    UsageReportResponse,
)
from dotmac.platform.partner_management.multitenant_service import PartnerMultiTenantService
from dotmac.platform.tenant.models import Tenant

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/partner", tags=["Partner Multi-Tenant"])


# ============================================
# Tenant Management Endpoints
# ============================================


@router.get(
    "/tenants",
    response_model=ManagedTenantListResponse,
    dependencies=[Depends(PartnerPermissionChecker(["partner.tenants.list"]))],
)
async def list_managed_tenants(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: str | None = Query(None, description="Filter by tenant status"),
    include_metrics: bool = Query(False, description="Include tenant metrics"),
) -> ManagedTenantListResponse:
    """
    List all managed tenant accounts for the authenticated partner.

    Returns:
        List of managed tenants with optional metrics
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    # Build query for partner's tenant links
    query = (
        select(PartnerTenantLink, Tenant)
        .join(Tenant, PartnerTenantLink.managed_tenant_id == Tenant.id)
        .where(PartnerTenantLink.partner_id == partner_id)
    )

    # Apply filters
    if status:
        query = query.where(Tenant.status == status)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(query)
    rows = result.all()

    # Build response
    from dotmac.platform.partner_management.schemas_multitenant import (
        ManagedTenantMetrics,
        ManagedTenantSummary,
    )

    tenants_list = []
    for link, tenant in rows:
        metrics = None
        if include_metrics:
            service = PartnerMultiTenantService(db)
            metrics_data = await service.get_managed_tenant_metrics(str(tenant.id))
            metrics = ManagedTenantMetrics(
                total_users=metrics_data.get("total_users", 0),
                total_revenue_mtd=metrics_data.get("total_revenue_mtd", 0),
                accounts_receivable=metrics_data.get("accounts_receivable", 0),
                overdue_invoices_count=metrics_data.get("overdue_invoices_count", 0),
                open_tickets_count=metrics_data.get("open_tickets_count", 0),
                sla_compliance_pct=metrics_data.get("sla_compliance_pct"),
            )

        tenant_summary = ManagedTenantSummary(
            tenant_id=tenant.id,
            tenant_name=tenant.name,
            tenant_slug=tenant.slug,
            status=tenant.status.value if hasattr(tenant.status, "value") else str(tenant.status),
            access_role=link.access_role.value,
            relationship_type=link.relationship_type,
            start_date=link.start_date,
            end_date=link.end_date,
            is_active=link.is_active,
            is_expired=link.is_expired,
            metrics=metrics,
        )
        tenants_list.append(tenant_summary)

    logger.info(
        "Partner listed managed tenants",
        partner_id=partner_id,
        count=len(tenants_list),
        total=total,
    )

    return ManagedTenantListResponse(
        tenants=tenants_list,
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/tenants/{tenant_id}",
    response_model=ManagedTenantDetail,
    dependencies=[Depends(PartnerPermissionChecker(["partner.tenants.list"]))],
)
async def get_managed_tenant_detail(
    tenant_id: str,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    include_metrics: bool = Query(False, description="Include tenant metrics"),
) -> ManagedTenantDetail:
    """
    Get detailed information for a specific managed tenant.

    Args:
        tenant_id: Managed tenant ID

    Returns:
        Detailed tenant information including configuration and metrics
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    # Validate access to this tenant
    if tenant_id not in current_user.managed_tenant_ids:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Partner does not have access to this tenant",
        )

    # Query for link and tenant
    result = await db.execute(
        select(PartnerTenantLink, Tenant)
        .join(Tenant, PartnerTenantLink.managed_tenant_id == Tenant.id)
        .where(
            and_(
                PartnerTenantLink.partner_id == partner_id,
                PartnerTenantLink.managed_tenant_id == tenant_id,
            )
        )
    )
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Managed tenant not found",
        )

    link, tenant = row

    # Build metrics if requested
    from dotmac.platform.partner_management.schemas_multitenant import ManagedTenantMetrics

    metrics = None
    if include_metrics:
        service = PartnerMultiTenantService(db)
        metrics_data = await service.get_managed_tenant_metrics(str(tenant.id))
        metrics = ManagedTenantMetrics(
            total_users=metrics_data.get("total_users", 0),
            total_revenue_mtd=metrics_data.get("total_revenue_mtd", 0),
            accounts_receivable=metrics_data.get("accounts_receivable", 0),
            overdue_invoices_count=metrics_data.get("overdue_invoices_count", 0),
            open_tickets_count=metrics_data.get("open_tickets_count", 0),
            sla_compliance_pct=metrics_data.get("sla_compliance_pct"),
        )

    logger.info(
        "Partner viewed managed tenant detail",
        partner_id=partner_id,
        tenant_id=tenant_id,
    )

    return ManagedTenantDetail(
        tenant_id=tenant.id,
        tenant_name=tenant.name,
        tenant_slug=tenant.slug,
        status=tenant.status.value if hasattr(tenant.status, "value") else str(tenant.status),
        access_role=link.access_role.value,
        relationship_type=link.relationship_type,
        start_date=link.start_date,
        end_date=link.end_date,
        is_active=link.is_active,
        is_expired=link.is_expired,
        sla_response_hours=link.sla_response_hours,
        sla_uptime_target=link.sla_uptime_target,
        notify_on_sla_breach=link.notify_on_sla_breach,
        notify_on_billing_threshold=link.notify_on_billing_threshold,
        billing_alert_threshold=link.billing_alert_threshold,
        custom_permissions=link.custom_permissions or {},
        notes=link.notes,
        metadata=link.metadata_ or {},
        metrics=metrics,
    )


# ============================================
# Billing Endpoints
# ============================================


@router.get(
    "/billing/summary",
    response_model=ConsolidatedBillingSummary,
    dependencies=[Depends(PartnerPermissionChecker(["partner.billing.summary.read"]))],
)
async def get_consolidated_billing_summary(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    from_date: datetime | None = Query(None, description="Start date for revenue calculation"),
    status: str | None = Query(None, description="Filter by invoice status (e.g., overdue)"),
) -> ConsolidatedBillingSummary:
    """
    Get consolidated billing summary across all managed tenants.

    Args:
        from_date: Optional start date for revenue calculation
        status: Optional filter by invoice status

    Returns:
        Consolidated billing metrics with per-tenant breakdown
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    from dotmac.platform.partner_management.schemas_multitenant import BillingTenantSummary

    service = PartnerMultiTenantService(db)
    billing_data = await service.get_consolidated_billing_summary(
        managed_tenant_ids=current_user.managed_tenant_ids,
        from_date=from_date,
        status=status,
    )

    logger.info(
        "Partner requested consolidated billing summary",
        partner_id=partner_id,
        managed_tenants_count=len(current_user.managed_tenant_ids),
    )

    # Convert tenant summaries to schema
    tenant_summaries = [
        BillingTenantSummary(
            tenant_id=t["tenant_id"],
            tenant_name=t["tenant_name"],
            total_revenue=t["total_revenue"],
            accounts_receivable=t["accounts_receivable"],
            overdue_amount=t["overdue_amount"],
            overdue_invoices_count=t["overdue_invoices_count"],
            total_invoices_count=t["total_invoices_count"],
            oldest_overdue_days=t.get("oldest_overdue_days"),
        )
        for t in billing_data.get("tenants", [])
    ]

    return ConsolidatedBillingSummary(
        total_revenue=billing_data["total_revenue"],
        total_ar=billing_data["total_ar"],
        total_overdue=billing_data["total_overdue"],
        overdue_invoices_count=billing_data["overdue_invoices_count"],
        tenants_count=billing_data["tenants_count"],
        tenants=tenant_summaries,
        as_of_date=billing_data["as_of_date"],
    )


@router.get(
    "/billing/invoices",
    response_model=InvoiceListResponse,
    dependencies=[Depends(PartnerPermissionChecker(["partner.billing.invoices.read"]))],
)
async def list_invoices(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_id: str | None = Query(None, description="Filter by specific tenant"),
    status: str | None = Query(None, description="Filter by invoice status"),
    from_date: datetime | None = Query(None, description="Filter by invoice date >= from_date"),
    to_date: datetime | None = Query(None, description="Filter by invoice date <= to_date"),
    search: str | None = Query(None, description="Search by invoice number or tenant name"),
) -> InvoiceListResponse:
    """
    List invoices across all managed tenants.

    Returns:
        Paginated list of invoices with filtering options
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    # Validate tenant_id if provided
    if tenant_id and tenant_id not in current_user.managed_tenant_ids:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Partner does not have access to this tenant",
        )

    from dotmac.platform.partner_management.schemas_multitenant import InvoiceListItem

    service = PartnerMultiTenantService(db)
    invoice_data = await service.list_invoices(
        managed_tenant_ids=current_user.managed_tenant_ids,
        tenant_id=tenant_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        search=search,
        offset=offset,
        limit=limit,
    )

    logger.info(
        "Partner listed invoices",
        partner_id=partner_id,
        filters={"tenant_id": tenant_id, "status": status},
    )

    # Convert to response schema
    invoices = [
        InvoiceListItem(
            invoice_id=inv["invoice_id"],
            tenant_id=inv["tenant_id"],
            tenant_name=inv["tenant_name"],
            invoice_number=inv["invoice_number"],
            invoice_date=inv["invoice_date"],
            due_date=inv["due_date"],
            amount=inv["amount"],
            paid_amount=inv["paid_amount"],
            balance=inv["balance"],
            status=inv["status"],
            is_overdue=inv["is_overdue"],
            days_overdue=inv.get("days_overdue"),
        )
        for inv in invoice_data.get("invoices", [])
    ]

    return InvoiceListResponse(
        invoices=invoices,
        total=invoice_data.get("total", 0),
        offset=offset,
        limit=limit,
        filters_applied={
            "tenant_id": tenant_id,
            "status": status,
            "from_date": from_date,
            "to_date": to_date,
            "search": search,
        },
    )


@router.post(
    "/billing/invoices/export",
    response_model=InvoiceExportResponse,
    dependencies=[Depends(PartnerPermissionChecker(["partner.billing.invoices.export"]))],
)
async def export_invoices(
    request: InvoiceExportRequest,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> InvoiceExportResponse:
    """
    Request invoice export (CSV or PDF).

    Returns:
        Export job information with download URL when ready
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    # Validate tenant_ids if provided
    if request.tenant_ids:
        unauthorized = set(request.tenant_ids) - set(current_user.managed_tenant_ids)
        if unauthorized:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail=f"Partner does not have access to tenants: {unauthorized}",
            )

    export_format = request.format.lower().strip()
    if export_format not in {"csv", "pdf"}:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Invalid export format. Use 'csv' or 'pdf'.",
        )

    service = PartnerMultiTenantService(db)
    invoice_data = await service.list_invoices(
        managed_tenant_ids=current_user.managed_tenant_ids,
        tenant_id=request.tenant_ids[0] if request.tenant_ids and len(request.tenant_ids) == 1 else None,
        status=request.status,
        from_date=request.from_date,
        to_date=request.to_date,
        offset=0,
        limit=10000,
    )

    invoices = invoice_data.get("invoices", [])
    if request.tenant_ids and len(request.tenant_ids) > 1:
        allowed = set(request.tenant_ids)
        invoices = [inv for inv in invoices if inv.get("tenant_id") in allowed]
    export_timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    export_id = f"{partner_id}-{export_timestamp}"

    if export_format == "csv":
        import csv
        import io

        csv_buffer = io.StringIO()
        fieldnames = [
            "invoice_id",
            "tenant_id",
            "tenant_name",
            "invoice_number",
            "invoice_date",
            "due_date",
            "amount",
            "paid_amount",
            "balance",
            "status",
            "is_overdue",
            "days_overdue",
        ]
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        for invoice in invoices:
            row = {
                **invoice,
                "invoice_date": invoice.get("invoice_date").isoformat() if invoice.get("invoice_date") else None,
                "due_date": invoice.get("due_date").isoformat() if invoice.get("due_date") else None,
            }
            writer.writerow(row)
        file_bytes = csv_buffer.getvalue().encode("utf-8")
        file_name = f"invoices-{export_id}.csv"
        content_type = "text/csv"
    else:
        from io import BytesIO
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle

        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        table_data = [
            [
                "Invoice #",
                "Tenant",
                "Date",
                "Due",
                "Amount",
                "Paid",
                "Balance",
                "Status",
            ]
        ]
        for invoice in invoices:
            table_data.append(
                [
                    invoice.get("invoice_number", ""),
                    invoice.get("tenant_name", ""),
                    invoice.get("invoice_date").date().isoformat()
                    if invoice.get("invoice_date")
                    else "",
                    invoice.get("due_date").date().isoformat()
                    if invoice.get("due_date")
                    else "",
                    str(invoice.get("amount")),
                    str(invoice.get("paid_amount")),
                    str(invoice.get("balance")),
                    invoice.get("status", ""),
                ]
            )

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#111827")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        doc.build([table])
        file_bytes = pdf_buffer.getvalue()
        file_name = f"invoices-{export_id}.pdf"
        content_type = "application/pdf"

    from dotmac.platform.file_storage.service import get_storage_service

    storage_tenant_id = (
        current_user.effective_tenant_id
        or current_user.tenant_id
        or current_user.active_managed_tenant_id
    )
    if not storage_tenant_id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Tenant context required for invoice export storage.",
        )
    storage_service = get_storage_service()
    file_id = await storage_service.store_file(
        file_data=file_bytes,
        file_name=file_name,
        content_type=content_type,
        path=f"exports/invoices/{partner_id}",
        metadata={
            "export_id": export_id,
            "format": export_format,
            "requested_by": current_user.user_id,
        },
        tenant_id=storage_tenant_id,
    )

    logger.info(
        "Partner requested invoice export",
        partner_id=partner_id,
        export_id=export_id,
        format=request.format,
        file_id=file_id,
    )

    return InvoiceExportResponse(
        export_id=export_id,
        status="pending",
        download_url=f"/api/v1/files/storage/{file_id}/download",
        expires_at=None,
        estimated_completion=None,
    )


# ============================================
# Support/Ticketing Endpoints
# ============================================


@router.get(
    "/support/tickets",
    response_model=TicketListResponse,
    dependencies=[Depends(PartnerPermissionChecker(["partner.support.tickets.list"]))],
)
async def list_tickets(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant_id: str | None = Query(None, description="Filter by specific tenant"),
    status: str | None = Query(None, description="Filter by ticket status"),
    priority: str | None = Query(None, description="Filter by priority"),
) -> TicketListResponse:
    """
    List support tickets across all managed tenants.

    Returns:
        Paginated list of tickets with filtering options
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    # Validate tenant_id if provided
    if tenant_id and tenant_id not in current_user.managed_tenant_ids:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Partner does not have access to this tenant",
        )

    from dotmac.platform.partner_management.schemas_multitenant import TicketListItem

    service = PartnerMultiTenantService(db)
    ticket_data = await service.list_tickets(
        managed_tenant_ids=current_user.managed_tenant_ids,
        tenant_id=tenant_id,
        status=status,
        priority=priority,
        offset=offset,
        limit=limit,
    )

    logger.info(
        "Partner listed tickets",
        partner_id=partner_id,
        filters={"tenant_id": tenant_id, "status": status, "priority": priority},
    )

    # Convert to response schema
    tickets = [
        TicketListItem(
            ticket_id=t["ticket_id"],
            tenant_id=t["tenant_id"],
            tenant_name=t["tenant_name"],
            ticket_number=t["ticket_number"],
            subject=t["subject"],
            status=t["status"],
            priority=t["priority"],
            created_at=t["created_at"],
            updated_at=t["updated_at"],
            assigned_to=t.get("assigned_to"),
            requester_name=t.get("requester_name"),
        )
        for t in ticket_data.get("tickets", [])
    ]

    return TicketListResponse(
        tickets=tickets,
        total=ticket_data.get("total", 0),
        offset=offset,
        limit=limit,
        filters_applied={"tenant_id": tenant_id, "status": status, "priority": priority},
    )


@router.post(
    "/support/tickets",
    response_model=CreateTicketResponse,
    dependencies=[Depends(PartnerPermissionChecker(["partner.support.tickets.create"]))],
)
async def create_ticket(
    request: CreateTicketRequest,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> CreateTicketResponse:
    """
    Create a support ticket on behalf of a managed tenant.

    Requires X-Active-Tenant-Id header to specify which tenant the ticket is for.

    Returns:
        Created ticket information
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    # Require cross-tenant context
    if not current_user.is_cross_tenant_access:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="X-Active-Tenant-Id header required to create ticket for managed tenant",
        )

    active_tenant_id = current_user.active_managed_tenant_id
    if not active_tenant_id:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Active tenant ID not found in context",
        )

    service = PartnerMultiTenantService(db)
    ticket_data = await service.create_ticket(
        tenant_id=active_tenant_id,
        subject=request.subject,
        description=request.description,
        priority=request.priority,
        created_by_user_id=current_user.user_id or str(partner_id),
        category=request.category,
    )

    logger.info(
        "Partner created ticket for managed tenant",
        partner_id=partner_id,
        tenant_id=active_tenant_id,
        ticket_id=ticket_data["ticket_id"],
        subject=request.subject,
    )

    return CreateTicketResponse(
        ticket_id=ticket_data["ticket_id"],
        ticket_number=ticket_data["ticket_number"],
        tenant_id=ticket_data["tenant_id"],
        status=ticket_data["status"],
        created_at=ticket_data["created_at"],
    )


@router.patch(
    "/support/tickets/{ticket_id}",
    dependencies=[Depends(PartnerPermissionChecker(["partner.support.tickets.update"]))],
)
async def update_ticket(
    ticket_id: str,
    request: UpdateTicketRequest,
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
) -> dict:
    """
    Update a support ticket.

    Returns:
        Updated ticket information
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    service = PartnerMultiTenantService(db)
    try:
        result = await service.update_ticket(
            ticket_id=ticket_id,
            status=request.status,
            priority=request.priority,
            assigned_to=request.assigned_to,
            notes=request.notes,
            updated_by=current_user.user_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    logger.info(
        "Partner updated ticket",
        partner_id=partner_id,
        ticket_id=ticket_id,
        updates=request.model_dump(exclude_none=True),
    )

    return result


# ============================================
# Reporting Endpoints
# ============================================


@router.get(
    "/reports/usage",
    response_model=UsageReportResponse,
    dependencies=[Depends(PartnerPermissionChecker(["partner.reports.usage.read"]))],
)
async def get_usage_report(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    from_date: datetime = Query(..., description="Report start date"),
    to_date: datetime = Query(..., description="Report end date"),
    tenant_ids: list[str] | None = Query(None, description="Filter by specific tenants"),
) -> UsageReportResponse:
    """
    Get usage report across managed tenants.

    Args:
        from_date: Report period start
        to_date: Report period end
        tenant_ids: Optional list of tenant IDs to include

    Returns:
        Usage metrics aggregated across tenants
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    # Validate tenant_ids if provided
    if tenant_ids:
        unauthorized = set(tenant_ids) - set(current_user.managed_tenant_ids)
        if unauthorized:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail=f"Partner does not have access to tenants: {unauthorized}",
            )

    from dotmac.platform.partner_management.schemas_multitenant import UsageTenantSummary

    service = PartnerMultiTenantService(db)
    usage_data = await service.get_usage_report(
        managed_tenant_ids=current_user.managed_tenant_ids,
        from_date=from_date,
        to_date=to_date,
        tenant_ids=tenant_ids,
    )

    logger.info(
        "Partner requested usage report",
        partner_id=partner_id,
        period_start=from_date,
        period_end=to_date,
    )

    # Convert to response schema
    tenant_summaries = [
        UsageTenantSummary(
            tenant_id=t["tenant_id"],
            tenant_name=t["tenant_name"],
            total_data_gb=t["total_data_gb"],
            peak_concurrent_users=t["peak_concurrent_users"],
            average_daily_users=t["average_daily_users"],
            total_sessions=t["total_sessions"],
        )
        for t in usage_data.get("tenants", [])
    ]

    return UsageReportResponse(
        period_start=usage_data["period_start"],
        period_end=usage_data["period_end"],
        tenants=tenant_summaries,
        total_data_gb=usage_data["total_data_gb"],
        total_sessions=usage_data["total_sessions"],
    )


@router.get(
    "/reports/sla",
    response_model=SLAReportResponse,
    dependencies=[Depends(PartnerPermissionChecker(["partner.reports.sla.read"]))],
)
async def get_sla_report(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    from_date: datetime = Query(..., description="Report start date"),
    to_date: datetime = Query(..., description="Report end date"),
    tenant_ids: list[str] | None = Query(None, description="Filter by specific tenants"),
) -> SLAReportResponse:
    """
    Get SLA compliance report across managed tenants.

    Args:
        from_date: Report period start
        to_date: Report period end
        tenant_ids: Optional list of tenant IDs to include

    Returns:
        SLA compliance metrics per tenant
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    # Validate tenant_ids if provided
    if tenant_ids:
        unauthorized = set(tenant_ids) - set(current_user.managed_tenant_ids)
        if unauthorized:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail=f"Partner does not have access to tenants: {unauthorized}",
            )

    from dotmac.platform.partner_management.schemas_multitenant import SLATenantSummary

    service = PartnerMultiTenantService(db)
    sla_data = await service.get_sla_report(
        managed_tenant_ids=current_user.managed_tenant_ids,
        from_date=from_date,
        to_date=to_date,
        tenant_ids=tenant_ids,
        partner_id=partner_id,
    )

    logger.info(
        "Partner requested SLA report",
        partner_id=partner_id,
        period_start=from_date,
        period_end=to_date,
    )

    # Convert to response schema
    tenant_summaries = [
        SLATenantSummary(
            tenant_id=t["tenant_id"],
            tenant_name=t["tenant_name"],
            uptime_pct=t["uptime_pct"],
            average_response_hours=t["average_response_hours"],
            sla_target_uptime=t.get("sla_target_uptime"),
            sla_target_response_hours=t.get("sla_target_response_hours"),
            is_compliant=t["is_compliant"],
            breach_count=t["breach_count"],
        )
        for t in sla_data.get("tenants", [])
    ]

    return SLAReportResponse(
        period_start=sla_data["period_start"],
        period_end=sla_data["period_end"],
        tenants=tenant_summaries,
        overall_compliance_pct=sla_data["overall_compliance_pct"],
    )


# ============================================
# Alert Endpoints
# ============================================


@router.get(
    "/alerts/sla",
    response_model=SLAAlertListResponse,
    dependencies=[Depends(PartnerPermissionChecker(["partner.alerts.sla.read"]))],
)
async def get_sla_alerts(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    tenant_id: str | None = Query(None, description="Filter by specific tenant"),
    acknowledged: bool | None = Query(None, description="Filter by acknowledged status"),
) -> SLAAlertListResponse:
    """
    Get SLA breach alerts for managed tenants.

    Returns:
        List of SLA alerts with acknowledgment status
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    # Validate tenant_id if provided
    if tenant_id and tenant_id not in current_user.managed_tenant_ids:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Partner does not have access to this tenant",
        )

    from dotmac.platform.partner_management.schemas_multitenant import SLAAlert

    service = PartnerMultiTenantService(db)
    alert_data = await service.get_sla_alerts(
        managed_tenant_ids=current_user.managed_tenant_ids,
        tenant_id=tenant_id,
        acknowledged=acknowledged,
    )

    logger.info(
        "Partner requested SLA alerts",
        partner_id=partner_id,
        filters={"tenant_id": tenant_id, "acknowledged": acknowledged},
    )

    # Convert to response schema
    alerts = [
        SLAAlert(
            alert_id=a["alert_id"],
            tenant_id=a["tenant_id"],
            tenant_name=a["tenant_name"],
            alert_type=a["alert_type"],
            severity=a["severity"],
            message=a["message"],
            detected_at=a["detected_at"],
            acknowledged=a["acknowledged"],
            acknowledged_at=a.get("acknowledged_at"),
        )
        for a in alert_data.get("alerts", [])
    ]

    return SLAAlertListResponse(
        alerts=alerts,
        total=alert_data.get("total", 0),
        unacknowledged_count=alert_data.get("unacknowledged_count", 0),
    )


@router.get(
    "/alerts/billing",
    response_model=BillingAlertListResponse,
    dependencies=[Depends(PartnerPermissionChecker(["partner.alerts.billing.read"]))],
)
async def get_billing_alerts(
    current_user: Annotated[UserInfo, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_async_session)],
    tenant_id: str | None = Query(None, description="Filter by specific tenant"),
    acknowledged: bool | None = Query(None, description="Filter by acknowledged status"),
) -> BillingAlertListResponse:
    """
    Get billing threshold alerts for managed tenants.

    Returns:
        List of billing alerts with acknowledgment status
    """
    if not current_user.partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a partner",
        )

    partner_id = current_user.partner_uuid
    if not partner_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Invalid partner identifier",
        )

    # Validate tenant_id if provided
    if tenant_id and tenant_id not in current_user.managed_tenant_ids:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="Partner does not have access to this tenant",
        )

    from dotmac.platform.partner_management.schemas_multitenant import BillingAlert

    service = PartnerMultiTenantService(db)
    alert_data = await service.get_billing_alerts(
        managed_tenant_ids=current_user.managed_tenant_ids,
        tenant_id=tenant_id,
        acknowledged=acknowledged,
        partner_id=partner_id,
    )

    logger.info(
        "Partner requested billing alerts",
        partner_id=partner_id,
        filters={"tenant_id": tenant_id, "acknowledged": acknowledged},
    )

    # Convert to response schema
    alerts = [
        BillingAlert(
            alert_id=a["alert_id"],
            tenant_id=a["tenant_id"],
            tenant_name=a["tenant_name"],
            alert_type=a["alert_type"],
            current_amount=a["current_amount"],
            threshold_amount=a["threshold_amount"],
            severity=a["severity"],
            message=a["message"],
            detected_at=a["detected_at"],
            acknowledged=a["acknowledged"],
        )
        for a in alert_data.get("alerts", [])
    ]

    return BillingAlertListResponse(
        alerts=alerts,
        total=alert_data.get("total", 0),
        unacknowledged_count=alert_data.get("unacknowledged_count", 0),
    )
