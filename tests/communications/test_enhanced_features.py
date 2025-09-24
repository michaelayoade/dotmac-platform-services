"""
Comprehensive tests for enhanced communications features.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from dotmac.platform.communications import (
    get_template_service,
    get_bulk_service,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    TemplatePreviewRequest,
    BulkEmailJobCreate,
    RecipientData,
)
from dotmac.platform.communications.models import (
    EmailTemplate,
    BulkEmailJob,
    EmailDelivery,
    BulkJobStatus,
)


@pytest.fixture
async def sample_template_data():
    """Sample template data for testing."""
    return EmailTemplateCreate(
        name="Welcome Email",
        description="Welcome new users",
        subject_template="Welcome to {{company_name}}, {{user_name}}!",
        html_template="""
        <html>
        <body>
            <h1>Welcome {{user_name}}!</h1>
            <p>Thank you for joining {{company_name}}.</p>
            <p>Your email: {{user_email}}</p>
        </body>
        </html>
        """,
        text_template="Welcome {{user_name}}! Thank you for joining {{company_name}}. Your email: {{user_email}}",
        category="onboarding",
    )


class TestTemplateService:
    """Test the enhanced template service."""

    async def test_create_template(self, async_session, sample_template_data):
        """Test creating an email template."""
        template_service = get_template_service()

        template = await template_service.create_template(sample_template_data, async_session)

        assert template.id is not None
        assert template.name == "Welcome Email"
        assert template.category == "onboarding"
        assert template.is_active is True
        assert "{{user_name}}" in template.subject_template
        assert "user_name" in template.variables["all_variables"]

    async def test_create_template_with_syntax_error(self, async_session):
        """Test creating template with invalid Jinja2 syntax."""
        template_service = get_template_service()

        invalid_template = EmailTemplateCreate(
            name="Invalid Template",
            subject_template="Welcome {{user_name",  # Missing closing brace
            html_template="<p>Hello {{user_name}}</p>",
        )

        with pytest.raises(ValueError, match="Syntax error"):
            await template_service.create_template(invalid_template, async_session)

    async def test_get_template(self, async_session, sample_template_data):
        """Test retrieving a template."""
        template_service = get_template_service()

        # Create template
        created = await template_service.create_template(sample_template_data, async_session)

        # Retrieve template
        retrieved = await template_service.get_template(created.id, async_session)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    async def test_get_nonexistent_template(self, async_session):
        """Test retrieving a nonexistent template."""
        template_service = get_template_service()

        template = await template_service.get_template("nonexistent", async_session)
        assert template is None

    async def test_list_templates(self, async_session):
        """Test listing templates with filtering."""
        template_service = get_template_service()

        # Create test templates
        template1 = EmailTemplateCreate(
            name="Marketing Email 1",
            subject_template="Special Offer!",
            html_template="<p>Check out our offer!</p>",
            category="marketing",
        )
        template2 = EmailTemplateCreate(
            name="Transactional Email 1",
            subject_template="Your Order Confirmation",
            html_template="<p>Order confirmed</p>",
            category="transactional",
        )

        await template_service.create_template(template1, async_session)
        await template_service.create_template(template2, async_session)

        # Test listing all templates
        all_templates = await template_service.list_templates(session=async_session)
        assert len(all_templates) >= 2

        # Test filtering by category
        marketing_templates = await template_service.list_templates(
            category="marketing", session=async_session
        )
        assert len(marketing_templates) == 1
        assert marketing_templates[0].category == "marketing"

    async def test_update_template(self, async_session, sample_template_data):
        """Test updating a template."""
        template_service = get_template_service()

        # Create template
        created = await template_service.create_template(sample_template_data, async_session)

        # Update template
        update_data = EmailTemplateUpdate(
            name="Updated Welcome Email",
            subject_template="Welcome to our platform, {{user_name}}!",
            category="updated_onboarding",
        )

        updated = await template_service.update_template(created.id, update_data, async_session)

        assert updated is not None
        assert updated.name == "Updated Welcome Email"
        assert updated.category == "updated_onboarding"
        assert "Welcome to our platform" in updated.subject_template

    async def test_delete_template(self, async_session, sample_template_data):
        """Test soft deleting a template."""
        template_service = get_template_service()

        # Create template
        created = await template_service.create_template(sample_template_data, async_session)
        assert created.is_active is True

        # Delete template
        success = await template_service.delete_template(created.id, async_session)
        assert success is True

        # Verify template is deactivated
        result = await async_session.execute(
            select(EmailTemplate).where(EmailTemplate.id == created.id)
        )
        template = result.scalar_one()
        assert template.is_active is False

    async def test_preview_template(self, async_session, sample_template_data):
        """Test template preview with sample data."""
        template_service = get_template_service()

        # Create template
        created = await template_service.create_template(sample_template_data, async_session)

        # Preview template
        preview_data = TemplatePreviewRequest(
            template_data={
                "user_name": "John Doe",
                "company_name": "ACME Corp",
                "user_email": "john@example.com",
            }
        )

        preview = await template_service.preview_template(created.id, preview_data, async_session)

        assert preview is not None
        assert "Welcome to ACME Corp, John Doe!" in preview.subject
        assert "John Doe" in preview.html_content
        assert "john@example.com" in preview.html_content
        assert len(preview.variables_used) > 0
        assert len(preview.missing_variables) == 0

    async def test_preview_template_missing_variables(self, async_session, sample_template_data):
        """Test template preview with missing variables."""
        template_service = get_template_service()

        # Create template
        created = await template_service.create_template(sample_template_data, async_session)

        # Preview with incomplete data
        preview_data = TemplatePreviewRequest(
            template_data={
                "user_name": "John Doe",
                # Missing company_name and user_email
            }
        )

        with pytest.raises(ValueError, match="Template rendering failed"):
            await template_service.preview_template(created.id, preview_data, async_session)


class TestBulkEmailService:
    """Test the bulk email service."""

    async def test_create_bulk_job(self, async_session, sample_template_data):
        """Test creating a bulk email job."""
        template_service = get_template_service()
        bulk_service = get_bulk_service()

        # Create template first
        template = await template_service.create_template(sample_template_data, async_session)

        # Create bulk job
        recipients = [
            RecipientData(
                email="user1@example.com",
                name="User One",
                custom_data={"department": "engineering"}
            ),
            RecipientData(
                email="user2@example.com",
                name="User Two",
                custom_data={"department": "marketing"}
            ),
        ]

        job_data = BulkEmailJobCreate(
            name="Welcome Campaign",
            template_id=template.id,
            recipients=recipients,
            template_data={"company_name": "ACME Corp"},
        )

        with patch('dotmac.platform.communications.bulk_service.process_bulk_email_job') as mock_task:
            job = await bulk_service.create_bulk_job(job_data, async_session)

        assert job.id is not None
        assert job.name == "Welcome Campaign"
        assert job.template_id == template.id
        assert job.total_recipients == 2
        assert job.status == BulkJobStatus.QUEUED
        assert job.sent_count == 0
        assert job.failed_count == 0

    async def test_create_bulk_job_invalid_template(self, async_session):
        """Test creating bulk job with invalid template."""
        bulk_service = get_bulk_service()

        recipients = [RecipientData(email="test@example.com")]
        job_data = BulkEmailJobCreate(
            name="Test Campaign",
            template_id="nonexistent",
            recipients=recipients,
        )

        with pytest.raises(ValueError, match="Template nonexistent not found"):
            await bulk_service.create_bulk_job(job_data, async_session)

    async def test_create_bulk_job_duplicate_recipients(self):
        """Test bulk job creation with duplicate recipients."""
        recipients = [
            RecipientData(email="duplicate@example.com"),
            RecipientData(email="duplicate@example.com"),  # Duplicate
        ]

        with pytest.raises(ValueError, match="Duplicate email addresses"):
            BulkEmailJobCreate(
                name="Test Campaign",
                template_id="template1",
                recipients=recipients,
            )

    async def test_get_bulk_job(self, async_session, sample_template_data):
        """Test retrieving a bulk job."""
        template_service = get_template_service()
        bulk_service = get_bulk_service()

        # Create template and job
        template = await template_service.create_template(sample_template_data, async_session)
        recipients = [RecipientData(email="test@example.com")]
        job_data = BulkEmailJobCreate(
            name="Test Campaign",
            template_id=template.id,
            recipients=recipients,
        )

        with patch('dotmac.platform.communications.bulk_service.process_bulk_email_job'):
            created_job = await bulk_service.create_bulk_job(job_data, async_session)

        # Retrieve job
        retrieved_job = await bulk_service.get_bulk_job(created_job.id, async_session)

        assert retrieved_job is not None
        assert retrieved_job.id == created_job.id
        assert retrieved_job.name == created_job.name

    async def test_list_bulk_jobs(self, async_session, sample_template_data):
        """Test listing bulk jobs with filtering."""
        template_service = get_template_service()
        bulk_service = get_bulk_service()

        # Create template
        template = await template_service.create_template(sample_template_data, async_session)
        recipients = [RecipientData(email="test@example.com")]

        # Create multiple jobs
        job_data1 = BulkEmailJobCreate(
            name="Campaign 1",
            template_id=template.id,
            recipients=recipients,
        )
        job_data2 = BulkEmailJobCreate(
            name="Campaign 2",
            template_id=template.id,
            recipients=recipients,
        )

        with patch('dotmac.platform.communications.bulk_service.process_bulk_email_job'):
            await bulk_service.create_bulk_job(job_data1, async_session)
            await bulk_service.create_bulk_job(job_data2, async_session)

        # List all jobs
        jobs = await bulk_service.list_bulk_jobs(session=async_session)
        assert len(jobs) >= 2

        # List by status
        queued_jobs = await bulk_service.list_bulk_jobs(
            status=BulkJobStatus.QUEUED, session=async_session
        )
        assert len(queued_jobs) >= 2

    async def test_cancel_bulk_job(self, async_session, sample_template_data):
        """Test cancelling a bulk job."""
        template_service = get_template_service()
        bulk_service = get_bulk_service()

        # Create template and job
        template = await template_service.create_template(sample_template_data, async_session)
        recipients = [RecipientData(email="test@example.com")]
        job_data = BulkEmailJobCreate(
            name="Test Campaign",
            template_id=template.id,
            recipients=recipients,
        )

        with patch('dotmac.platform.communications.bulk_service.process_bulk_email_job'):
            job = await bulk_service.create_bulk_job(job_data, async_session)

        # Cancel job
        success = await bulk_service.cancel_bulk_job(job.id, async_session)
        assert success is True

        # Verify job is cancelled
        cancelled_job = await bulk_service.get_bulk_job(job.id, async_session)
        assert cancelled_job.status == BulkJobStatus.CANCELLED

    async def test_get_job_stats(self, async_session, sample_template_data):
        """Test getting bulk job statistics."""
        template_service = get_template_service()
        bulk_service = get_bulk_service()

        # Create template and jobs
        template = await template_service.create_template(sample_template_data, async_session)
        recipients = [RecipientData(email="test@example.com")]
        job_data = BulkEmailJobCreate(
            name="Test Campaign",
            template_id=template.id,
            recipients=recipients,
        )

        with patch('dotmac.platform.communications.bulk_service.process_bulk_email_job'):
            await bulk_service.create_bulk_job(job_data, async_session)

        # Get stats
        stats = await bulk_service.get_job_stats(async_session)

        assert stats.total_jobs >= 1
        assert stats.active_jobs >= 0
        assert stats.success_rate >= 0


@pytest.fixture
async def async_session(db_session):
    """Provide async session for testing."""
    return db_session


# Mock fixtures
@pytest.fixture(autouse=True)
def mock_celery_task():
    """Mock Celery task processing."""
    with patch('dotmac.platform.communications.bulk_service.process_bulk_email_job') as mock_task:
        mock_task.delay = AsyncMock()
        mock_task.apply_async = AsyncMock()
        yield mock_task


class TestBulkEmailProcessing:
    """Test bulk email processing logic."""

    async def test_bulk_email_task_processing(self, async_session, sample_template_data):
        """Test the bulk email processing task."""
        from dotmac.platform.communications.bulk_service import _process_bulk_email_job_async

        template_service = get_template_service()

        # Create template
        template = await template_service.create_template(sample_template_data, async_session)

        # Create bulk job manually
        bulk_job = BulkEmailJob(
            name="Test Processing",
            template_id=template.id,
            recipients=[
                {"email": "user1@example.com", "name": "User 1", "custom_data": {}},
                {"email": "user2@example.com", "name": "User 2", "custom_data": {}},
            ],
            template_data={"company_name": "ACME Corp"},
            total_recipients=2,
            status=BulkJobStatus.QUEUED,
        )

        async_session.add(bulk_job)
        await async_session.commit()
        await async_session.refresh(bulk_job)

        # Mock the task instance
        mock_task = AsyncMock()
        mock_task.update_state = AsyncMock()

        # Process the job
        with patch('dotmac.platform.communications.bulk_service._send_single_email') as mock_send:
            mock_send.return_value = "delivery_123"

            await _process_bulk_email_job_async(bulk_job.id, mock_task)

        # Verify job was processed
        await async_session.refresh(bulk_job)
        assert bulk_job.status == BulkJobStatus.COMPLETED
        assert bulk_job.sent_count == 2
        assert bulk_job.failed_count == 0
        assert bulk_job.started_at is not None
        assert bulk_job.completed_at is not None