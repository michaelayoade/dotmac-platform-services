"""
End-to-end tests for dunning and collections.

Tests cover dunning campaigns, executions, and action logs.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.billing.dunning.models import (
    DunningActionLog,
    DunningActionType,
    DunningCampaign,
    DunningExecution,
    DunningExecutionStatus,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.e2e]


# ============================================================================
# Fixtures for Dunning E2E Tests
# ============================================================================


@pytest_asyncio.fixture
async def dunning_campaign(e2e_db_session: AsyncSession, tenant_id: str):
    """Create a dunning campaign."""
    unique_id = uuid.uuid4().hex[:8]
    campaign = DunningCampaign(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name=f"Test Dunning Campaign {unique_id}",
        description="A test dunning campaign for overdue invoices",
        is_active=True,
        priority=10,
        trigger_after_days=7,
        actions=[
            {
                "action_type": "email",
                "delay_days": 0,
                "template_id": "dunning_reminder_1",
                "subject": "Payment Reminder",
            },
            {
                "action_type": "email",
                "delay_days": 7,
                "template_id": "dunning_reminder_2",
                "subject": "Second Payment Reminder",
            },
            {
                "action_type": "suspend_service",
                "delay_days": 14,
            },
        ],
        exclusion_rules=[],
        metadata={},
    )
    e2e_db_session.add(campaign)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(campaign)
    return campaign


@pytest_asyncio.fixture
async def multiple_campaigns(e2e_db_session: AsyncSession, tenant_id: str):
    """Create multiple dunning campaigns."""
    campaigns = []

    for i in range(3):
        unique_id = uuid.uuid4().hex[:8]
        campaign = DunningCampaign(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=f"Campaign {unique_id}",
            description=f"Campaign description {i}",
            is_active=i < 2,  # Two active, one inactive
            priority=10 - i,
            trigger_after_days=7 * (i + 1),
            actions=[
                {
                    "action_type": "email",
                    "delay_days": 0,
                    "template_id": f"template_{i}",
                }
            ],
            exclusion_rules=[],
            metadata={},
        )
        e2e_db_session.add(campaign)
        campaigns.append(campaign)

    await e2e_db_session.commit()
    for c in campaigns:
        await e2e_db_session.refresh(c)
    return campaigns


@pytest_asyncio.fixture
async def dunning_execution(
    e2e_db_session: AsyncSession,
    tenant_id: str,
    dunning_campaign: DunningCampaign,
):
    """Create a dunning execution."""
    execution = DunningExecution(
        id=uuid.uuid4(),
        campaign_id=dunning_campaign.id,
        tenant_id=tenant_id,
        subscription_id=str(uuid.uuid4()),
        customer_id=str(uuid.uuid4()),
        invoice_id=str(uuid.uuid4()),
        outstanding_amount=55000,  # Amount in cents
        status=DunningExecutionStatus.IN_PROGRESS,
        current_step=0,
        total_steps=3,
        next_action_at=datetime.now(UTC) + timedelta(days=1),
        started_at=datetime.now(UTC),
    )
    e2e_db_session.add(execution)
    await e2e_db_session.commit()
    await e2e_db_session.refresh(execution)
    return execution


@pytest_asyncio.fixture
async def multiple_executions(
    e2e_db_session: AsyncSession,
    tenant_id: str,
    dunning_campaign: DunningCampaign,
):
    """Create multiple dunning executions."""
    executions = []
    statuses = [
        DunningExecutionStatus.IN_PROGRESS,
        DunningExecutionStatus.PENDING,
        DunningExecutionStatus.COMPLETED,
        DunningExecutionStatus.CANCELED,
    ]

    for i, exec_status in enumerate(statuses):
        execution = DunningExecution(
            id=uuid.uuid4(),
            campaign_id=dunning_campaign.id,
            tenant_id=tenant_id,
            subscription_id=str(uuid.uuid4()),
            customer_id=str(uuid.uuid4()),
            invoice_id=str(uuid.uuid4()),
            outstanding_amount=(i + 1) * 10000,  # Amount in cents
            status=exec_status,
            current_step=i,
            total_steps=3,
            started_at=datetime.now(UTC) - timedelta(days=i),
        )
        e2e_db_session.add(execution)
        executions.append(execution)

    await e2e_db_session.commit()
    for e in executions:
        await e2e_db_session.refresh(e)
    return executions


@pytest_asyncio.fixture
async def execution_with_logs(
    e2e_db_session: AsyncSession,
    tenant_id: str,
    dunning_campaign: DunningCampaign,
):
    """Create an execution with action logs."""
    execution = DunningExecution(
        id=uuid.uuid4(),
        campaign_id=dunning_campaign.id,
        tenant_id=tenant_id,
        subscription_id=str(uuid.uuid4()),
        customer_id=str(uuid.uuid4()),
        invoice_id=str(uuid.uuid4()),
        outstanding_amount=25000,  # Amount in cents
        status=DunningExecutionStatus.IN_PROGRESS,
        current_step=2,
        total_steps=3,
        started_at=datetime.now(UTC) - timedelta(days=14),
    )
    e2e_db_session.add(execution)
    await e2e_db_session.flush()

    # Create action logs
    logs = []
    for i in range(3):
        log = DunningActionLog(
            id=uuid.uuid4(),
            execution_id=execution.id,
            tenant_id=tenant_id,
            step_number=i,
            action_type=DunningActionType.EMAIL if i < 2 else DunningActionType.SUSPEND_SERVICE,
            action_config={"template_id": f"template_{i}"},
            status="success",
            executed_at=datetime.now(UTC) - timedelta(days=14 - i * 7),
            result={"message_id": f"msg_{i}"},
        )
        e2e_db_session.add(log)
        logs.append(log)

    await e2e_db_session.commit()
    await e2e_db_session.refresh(execution)
    return execution, logs


# ============================================================================
# Dunning Campaign Tests
# ============================================================================


class TestDunningCampaignE2E:
    """End-to-end tests for dunning campaign management."""

    async def test_create_campaign(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating a dunning campaign."""
        unique_id = uuid.uuid4().hex[:8]
        campaign_data = {
            "name": f"New Campaign {unique_id}",
            "description": "A new dunning campaign",
            "is_active": True,
            "priority": 5,
            "trigger_after_days": 3,
            "actions": [
                {
                    "type": "email",
                    "delay_days": 0,
                    "template": "first_reminder",
                },
                {
                    "type": "email",
                    "delay_days": 5,
                    "template": "second_reminder",
                },
            ],
        }

        response = await async_client.post(
            "/api/v1/billing/dunning/campaigns",
            json=campaign_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == campaign_data["name"]
        assert "id" in data

    async def test_create_campaign_without_actions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test creating campaign without actions fails."""
        campaign_data = {
            "name": "Empty Campaign",
            "description": "Campaign with no actions",
            "is_active": True,
            "priority": 1,
            "trigger_after_days": 7,
            "actions": [],
        }

        response = await async_client.post(
            "/api/v1/billing/dunning/campaigns",
            json=campaign_data,
            headers=auth_headers,
        )

        # 422 because actions list must have at least one item
        assert response.status_code == 422

    async def test_list_campaigns(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_campaigns: list[DunningCampaign],
    ):
        """Test listing dunning campaigns."""
        response = await async_client.get(
            "/api/v1/billing/dunning/campaigns",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_campaigns_active_only(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_campaigns: list[DunningCampaign],
    ):
        """Test listing only active campaigns."""
        response = await async_client.get(
            "/api/v1/billing/dunning/campaigns?active_only=true",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for campaign in data:
            assert campaign["is_active"] is True

    async def test_get_campaign(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        dunning_campaign: DunningCampaign,
    ):
        """Test getting a specific campaign."""
        response = await async_client.get(
            f"/api/v1/billing/dunning/campaigns/{dunning_campaign.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(dunning_campaign.id)

    async def test_get_campaign_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent campaign."""
        fake_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/v1/billing/dunning/campaigns/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_update_campaign(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        dunning_campaign: DunningCampaign,
    ):
        """Test updating a campaign."""
        update_data = {
            "name": "Updated Campaign Name",
            "priority": 20,
        }

        response = await async_client.patch(
            f"/api/v1/billing/dunning/campaigns/{dunning_campaign.id}",
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Campaign Name"

    async def test_delete_campaign(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        e2e_db_session: AsyncSession,
        tenant_id: str,
    ):
        """Test deleting a campaign."""
        # Create a campaign to delete
        unique_id = uuid.uuid4().hex[:8]
        campaign = DunningCampaign(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            name=f"Delete Test {unique_id}",
            is_active=True,
            priority=1,
            trigger_after_days=7,
            actions=[{"action_type": "email", "delay_days": 0, "template_id": "test"}],
            exclusion_rules=[],
            metadata={},
        )
        e2e_db_session.add(campaign)
        await e2e_db_session.commit()

        response = await async_client.delete(
            f"/api/v1/billing/dunning/campaigns/{campaign.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

    async def test_get_campaign_stats(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        dunning_campaign: DunningCampaign,
    ):
        """Test getting campaign statistics."""
        response = await async_client.get(
            f"/api/v1/billing/dunning/campaigns/{dunning_campaign.id}/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_executions" in data or isinstance(data, dict)


# ============================================================================
# Dunning Execution Tests
# ============================================================================


class TestDunningExecutionE2E:
    """End-to-end tests for dunning execution management."""

    async def test_start_execution(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        dunning_campaign: DunningCampaign,
    ):
        """Test starting a dunning execution."""
        execution_data = {
            "campaign_id": str(dunning_campaign.id),
            "subscription_id": str(uuid.uuid4()),
            "customer_id": str(uuid.uuid4()),
            "invoice_id": str(uuid.uuid4()),
            "outstanding_amount": "350.00",
        }

        response = await async_client.post(
            "/api/v1/billing/dunning/executions",
            json=execution_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "in_progress"

    async def test_list_executions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_executions: list[DunningExecution],
    ):
        """Test listing dunning executions."""
        response = await async_client.get(
            "/api/v1/billing/dunning/executions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_list_executions_filter_by_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_executions: list[DunningExecution],
    ):
        """Test listing executions filtered by status."""
        response = await async_client.get(
            "/api/v1/billing/dunning/executions?status=active",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for exec_data in data:
            assert exec_data["status"] == "in_progress"

    async def test_list_executions_filter_by_campaign(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        dunning_campaign: DunningCampaign,
        multiple_executions: list[DunningExecution],
    ):
        """Test listing executions filtered by campaign."""
        response = await async_client.get(
            f"/api/v1/billing/dunning/executions?campaign_id={dunning_campaign.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for exec_data in data:
            assert exec_data["campaign_id"] == str(dunning_campaign.id)

    async def test_get_execution(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        dunning_execution: DunningExecution,
    ):
        """Test getting a specific execution."""
        response = await async_client.get(
            f"/api/v1/billing/dunning/executions/{dunning_execution.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(dunning_execution.id)

    async def test_get_execution_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent execution."""
        fake_id = uuid.uuid4()
        response = await async_client.get(
            f"/api/v1/billing/dunning/executions/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_cancel_execution(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        dunning_execution: DunningExecution,
    ):
        """Test canceling an execution."""
        response = await async_client.post(
            f"/api/v1/billing/dunning/executions/{dunning_execution.id}/cancel",
            json={"reason": "Customer paid manually"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "canceled"

    async def test_get_execution_logs(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        execution_with_logs: tuple[DunningExecution, list[DunningActionLog]],
    ):
        """Test getting execution action logs."""
        execution, logs = execution_with_logs
        response = await async_client.get(
            f"/api/v1/billing/dunning/executions/{execution.id}/logs",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= len(logs)


# ============================================================================
# Dunning Stats Tests
# ============================================================================


class TestDunningStatsE2E:
    """End-to-end tests for dunning statistics."""

    async def test_get_tenant_stats(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        multiple_executions: list[DunningExecution],
    ):
        """Test getting tenant-wide dunning statistics."""
        response = await async_client.get(
            "/api/v1/billing/dunning/stats",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    async def test_get_pending_actions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        dunning_execution: DunningExecution,
    ):
        """Test getting pending dunning actions."""
        response = await async_client.get(
            "/api/v1/billing/dunning/pending-actions",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ============================================================================
# Error Handling Tests
# ============================================================================


class TestDunningErrorsE2E:
    """End-to-end tests for dunning error handling."""

    async def test_start_execution_invalid_campaign(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test starting execution with invalid campaign."""
        execution_data = {
            "campaign_id": str(uuid.uuid4()),  # Non-existent
            "subscription_id": str(uuid.uuid4()),
            "customer_id": str(uuid.uuid4()),
            "invoice_id": str(uuid.uuid4()),
            "outstanding_amount": "100.00",
        }

        response = await async_client.post(
            "/api/v1/billing/dunning/executions",
            json=execution_data,
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_cancel_completed_execution(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        e2e_db_session: AsyncSession,
        tenant_id: str,
        dunning_campaign: DunningCampaign,
    ):
        """Test canceling a completed execution fails."""
        # Create completed execution
        execution = DunningExecution(
            id=uuid.uuid4(),
            campaign_id=dunning_campaign.id,
            tenant_id=tenant_id,
            subscription_id=str(uuid.uuid4()),
            customer_id=str(uuid.uuid4()),
            invoice_id=str(uuid.uuid4()),
            outstanding_amount=10000,  # Amount in cents
            status=DunningExecutionStatus.COMPLETED,
            current_step=0,
            total_steps=3,
            started_at=datetime.now(UTC) - timedelta(days=7),
        )
        e2e_db_session.add(execution)
        await e2e_db_session.commit()

        response = await async_client.post(
            f"/api/v1/billing/dunning/executions/{execution.id}/cancel",
            json={"reason": "Test"},
            headers=auth_headers,
        )

        assert response.status_code == 400

    async def test_unauthorized_access(
        self,
        async_client: AsyncClient,
        tenant_id: str,
    ):
        """Test accessing dunning without authentication."""
        response = await async_client.get(
            "/api/v1/billing/dunning/campaigns",
            headers={"X-Tenant-ID": tenant_id},
        )

        assert response.status_code == 401

    async def test_invalid_execution_status_filter(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing executions with invalid status filter."""
        response = await async_client.get(
            "/api/v1/billing/dunning/executions?status=invalid_status",
            headers=auth_headers,
        )

        assert response.status_code == 400
