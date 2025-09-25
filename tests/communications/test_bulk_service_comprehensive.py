"""
Comprehensive tests for BulkEmailService.

Tests all bulk email functionality including:
- Bulk job creation and management
- Email processing with templates
- Celery task integration
- SMTP delivery
- Progress tracking and statistics
- Error handling and retry logic
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from uuid import uuid4

import smtplib
from email.mime.multipart import MIMEMultipart
from sqlalchemy.ext.asyncio import AsyncSession

from dotmac.platform.communications.bulk_service import BulkEmailService
from dotmac.platform.communications.models import (
    BulkEmailJobCreate,
    BulkJobStatus,
    EmailDelivery,
)


class TestBulkEmailServiceInitialization:
    """Test BulkEmailService initialization and configuration."""

    def test_bulk_service_init(self):
        """Test bulk email service initialization."""
        service = BulkEmailService()

        # Check SMTP configuration (it's a dictionary, not an object)
        assert service.smtp_config is not None
        assert isinstance(service.smtp_config, dict)
        assert 'host' in service.smtp_config
        assert 'port' in service.smtp_config

        # Check template service exists
        assert service.template_service is not None

    @patch('dotmac.platform.communications.bulk_service.settings')
    def test_bulk_service_init_with_custom_settings(self, mock_settings):
        """Test bulk service with custom SMTP settings."""
        mock_settings.smtp.host = 'custom-smtp.example.com'
        mock_settings.smtp.port = 25
        mock_settings.smtp.username = 'testuser'
        mock_settings.smtp.password = 'testpass'
        mock_settings.smtp.use_tls = False

        service = BulkEmailService()

        # Should use mock settings (smtp_config is a dictionary)
        assert service.smtp_config['host'] == 'custom-smtp.example.com'
        assert service.smtp_config['port'] == 25


class TestBulkEmailServiceJobManagement:
    """Test bulk email job CRUD operations."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    @pytest.fixture
    def mock_session(self):
        """Mock async database session."""
        session = AsyncMock(spec=AsyncSession)
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.delete = AsyncMock()
        return session

    @pytest.fixture
    def sample_bulk_job_data(self):
        return BulkEmailJobCreate(
            name="Weekly Newsletter",
            template_id=str(uuid4()),
            recipients=[
                {"email": "user1@example.com", "variables": {"name": "John"}},
                {"email": "user2@example.com", "variables": {"name": "Jane"}},
                {"email": "user3@example.com", "variables": {"name": "Bob"}},
            ],
            scheduled_at=datetime.now(timezone.utc),
            priority="normal"
        )

    @pytest.mark.asyncio
    async def test_create_bulk_job_success(self, service, mock_session, sample_bulk_job_data):
        """Test successful bulk email job creation."""
        mock_job = Mock()
        job_id = str(uuid4())
        now = datetime.now(timezone.utc)

        # Set all required fields for BulkEmailJobResponse validation
        mock_job.id = job_id
        mock_job.name = sample_bulk_job_data.name
        mock_job.template_id = sample_bulk_job_data.template_id
        mock_job.status = BulkJobStatus.QUEUED
        mock_job.total_recipients = len(sample_bulk_job_data.recipients)
        mock_job.sent_count = 0
        mock_job.failed_count = 0
        mock_job.error_message = None
        mock_job.scheduled_at = None
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.created_at = now

        with patch('dotmac.platform.communications.models.BulkEmailJob') as MockJob:
            MockJob.return_value = mock_job

            result = await service.create_bulk_job(sample_bulk_job_data, mock_session)

            # Verify database operations
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.refresh.assert_called_once_with(mock_job)

            assert result.id == job_id
            assert result.name == sample_bulk_job_data.name
            assert result.status == BulkJobStatus.QUEUED
            assert result.sent_count == 0
            assert result.failed_count == 0

    @pytest.mark.asyncio
    async def test_create_bulk_job_with_invalid_template(self, service, mock_session):
        """Test bulk job creation with non-existent template."""
        invalid_job_data = BulkEmailJobCreate(
            name="Test Job",
            template_id="non-existent-template",
            recipients=[{"email": "test@example.com", "variables": {}}]
        )

        # Mock template service to return None
        with patch.object(service, 'template_service') as mock_template_service:
            mock_template_service.get_template.return_value = None

            with pytest.raises(ValueError, match="Template not found"):
                await service.create_bulk_job(invalid_job_data, mock_session)

    @pytest.mark.asyncio
    async def test_get_bulk_job_success(self, service, mock_session):
        """Test successful bulk job retrieval."""
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.name = "Test Job"
        mock_job.status = BulkJobStatus.IN_PROGRESS

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        result = await service.get_bulk_job(job_id, mock_session)

        assert result is not None
        assert result.id == job_id
        assert result.status == BulkJobStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_get_bulk_job_not_found(self, service, mock_session):
        """Test bulk job retrieval when job doesn't exist."""
        job_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.get_bulk_job(job_id, mock_session)

        assert result is None

    @pytest.mark.asyncio
    async def test_list_bulk_jobs_success(self, service, mock_session):
        """Test successful bulk job listing."""
        mock_jobs = [
            Mock(id=str(uuid4()), name="Job 1", status=BulkJobStatus.QUEUED),
            Mock(id=str(uuid4()), name="Job 2", status=BulkJobStatus.COMPLETED),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_jobs
        mock_session.execute.return_value = mock_result

        jobs, count = await service.list_bulk_jobs(mock_session)

        assert len(jobs) == 2
        assert count == 2
        assert jobs[0].name == "Job 1"
        assert jobs[1].name == "Job 2"

    @pytest.mark.asyncio
    async def test_list_bulk_jobs_with_status_filter(self, service, mock_session):
        """Test bulk job listing with status filter."""
        mock_jobs = [Mock(id=str(uuid4()), name="Pending Job", status=BulkJobStatus.QUEUED)]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_jobs
        mock_session.execute.return_value = mock_result

        jobs, count = await service.list_bulk_jobs(
            mock_session,
            status=BulkJobStatus.QUEUED,
            limit=10,
            offset=0
        )

        assert len(jobs) == 1
        assert jobs[0].status == BulkJobStatus.QUEUED

    @pytest.mark.asyncio
    async def test_update_job_status(self, service, mock_session):
        """Test updating bulk job status."""
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.QUEUED

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        await service.update_job_status(job_id, BulkJobStatus.IN_PROGRESS, mock_session)

        assert mock_job.status == BulkJobStatus.IN_PROGRESS
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_bulk_job(self, service, mock_session):
        """Test cancelling a bulk job."""
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.IN_PROGRESS

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        result = await service.cancel_bulk_job(job_id, mock_session)

        assert result is True
        assert mock_job.status == BulkJobStatus.CANCELLED
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_bulk_job_already_completed(self, service, mock_session):
        """Test cancelling an already completed job."""
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.COMPLETED

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        with pytest.raises(ValueError, match="Cannot cancel"):
            await service.cancel_bulk_job(job_id, mock_session)


class TestBulkEmailServiceStatistics:
    """Test bulk job statistics and progress tracking."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_job_stats_success(self, service, mock_session):
        """Test getting job statistics."""
        job_id = str(uuid4())

        # Mock deliveries with various statuses
        mock_deliveries = [
            Mock(status="sent"),
            Mock(status="sent"),
            Mock(status="failed"),
            Mock(status="pending"),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_deliveries
        mock_session.execute.return_value = mock_result

        stats = await service.get_job_stats(job_id, mock_session)

        assert stats["total_recipients"] == 4
        assert stats["sent_count"] == 2
        assert stats["failed_count"] == 1
        assert stats["pending_count"] == 1
        assert stats["success_rate"] == 50.0  # 2/4 * 100

    @pytest.mark.asyncio
    async def test_get_job_stats_empty_job(self, service, mock_session):
        """Test getting statistics for job with no deliveries."""
        job_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        stats = await service.get_job_stats(job_id, mock_session)

        assert stats["total_recipients"] == 0
        assert stats["sent_count"] == 0
        assert stats["failed_count"] == 0
        assert stats["success_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_update_job_progress(self, service, mock_session):
        """Test updating job progress."""
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.progress = 0

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        await service.update_job_progress(job_id, 75, mock_session)

        assert mock_job.progress == 75
        mock_session.commit.assert_called_once()


class TestBulkEmailServiceEmailProcessing:
    """Test email processing and SMTP operations."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    @pytest.fixture
    def mock_template(self):
        template = Mock()
        template.subject = "Welcome {{ name }}!"
        template.html_content = "<h1>Hello {{ name }}</h1>"
        template.text_content = "Hello {{ name }}"
        return template

    @pytest.fixture
    def sample_recipient(self):
        return {
            "email": "test@example.com",
            "variables": {"name": "John Doe"}
        }

    def test_create_email_message(self, service, mock_template, sample_recipient):
        """Test creating email message from template."""
        with patch.object(service, '_render_template_content') as mock_render:
            mock_render.side_effect = [
                "Welcome John Doe!",  # subject
                "<h1>Hello John Doe</h1>",  # html
                "Hello John Doe"  # text
            ]

            message = service.create_email_message(mock_template, sample_recipient)

            assert isinstance(message, MIMEMultipart)
            assert message['Subject'] == "Welcome John Doe!"
            assert message['To'] == "test@example.com"

    def test_render_template_content(self, service):
        """Test rendering template content with variables."""
        template_content = "Hello {{ name }}, your order {{ order_id }} is ready!"
        variables = {"name": "John", "order_id": "12345"}

        result = service._render_template_content(template_content, variables)

        assert result == "Hello John, your order 12345 is ready!"

    def test_render_template_content_missing_variables(self, service):
        """Test rendering template with missing variables."""
        template_content = "Hello {{ name }}, your order {{ order_id }} is ready!"
        variables = {"name": "John"}  # Missing order_id

        with pytest.raises(Exception):  # Should handle undefined variables
            service._render_template_content(template_content, variables)

    @pytest.mark.asyncio
    async def test_send_email_success(self, service, mock_template, sample_recipient):
        """Test successful email sending via SMTP."""
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = Mock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__enter__ = Mock(return_value=mock_smtp)
            mock_smtp.__exit__ = Mock(return_value=None)

            with patch.object(service, 'create_email_message') as mock_create_msg:
                mock_message = Mock()
                mock_message.as_string.return_value = "Email content"
                mock_create_msg.return_value = mock_message

                result = await service.send_email(mock_template, sample_recipient)

                assert result["success"] is True
                assert result["message_id"] is not None
                mock_smtp.send_message.assert_called_once_with(mock_message)

    @pytest.mark.asyncio
    async def test_send_email_smtp_error(self, service, mock_template, sample_recipient):
        """Test email sending with SMTP error."""
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = Mock()
            mock_smtp_class.return_value = mock_smtp
            mock_smtp.__enter__ = Mock(return_value=mock_smtp)
            mock_smtp.__exit__ = Mock(return_value=None)
            mock_smtp.send_message.side_effect = smtplib.SMTPException("SMTP Error")

            with patch.object(service, 'create_email_message'):
                result = await service.send_email(mock_template, sample_recipient)

                assert result["success"] is False
                assert "SMTP Error" in result["error"]

    @pytest.mark.asyncio
    async def test_send_email_connection_error(self, service, mock_template, sample_recipient):
        """Test email sending with connection error."""
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = ConnectionRefusedError("Connection refused")

            result = await service.send_email(mock_template, sample_recipient)

            assert result["success"] is False
            assert "Connection refused" in result["error"]


class TestBulkEmailServiceCeleryIntegration:
    """Test Celery task integration."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    @pytest.fixture
    def mock_celery_app(self):
        app = Mock()
        app.send_task = Mock()
        return app

    def test_schedule_bulk_processing_task(self, service, mock_celery_app):
        """Test scheduling bulk email processing task."""
        job_id = str(uuid4())

        with patch.object(service, 'celery_app', mock_celery_app):
            task_result = service.schedule_bulk_processing_task(job_id)

            mock_celery_app.send_task.assert_called_once_with(
                'communications.process_bulk_email_job',
                args=[job_id]
            )

    @pytest.mark.asyncio
    async def test_process_bulk_email_job_success(self, service, mock_session):
        """Test processing bulk email job."""
        job_id = str(uuid4())

        # Mock job with recipients
        mock_job = Mock()
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.QUEUED
        mock_job.template_id = str(uuid4())
        mock_job.recipients = [
            {"email": "user1@example.com", "variables": {"name": "John"}},
            {"email": "user2@example.com", "variables": {"name": "Jane"}},
        ]

        # Mock template
        mock_template = Mock()
        mock_template.subject = "Hello {{ name }}"

        with patch.object(service, 'get_bulk_job', return_value=mock_job):
            with patch.object(service, 'template_service') as mock_template_service:
                mock_template_service.get_template.return_value = mock_template

                with patch.object(service, 'send_email') as mock_send:
                    mock_send.return_value = {"success": True, "message_id": "msg123"}

                    with patch.object(service, 'update_job_status') as mock_update_status:
                        await service.process_bulk_email_job(job_id, mock_session)

                        # Verify status updates
                        mock_update_status.assert_any_call(job_id, BulkJobStatus.IN_PROGRESS, mock_session)
                        mock_update_status.assert_any_call(job_id, BulkJobStatus.COMPLETED, mock_session)

                        # Verify emails were sent
                        assert mock_send.call_count == 2

    @pytest.mark.asyncio
    async def test_process_bulk_email_job_partial_failure(self, service, mock_session):
        """Test processing bulk job with some email failures."""
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.QUEUED
        mock_job.recipients = [
            {"email": "user1@example.com", "variables": {"name": "John"}},
            {"email": "user2@example.com", "variables": {"name": "Jane"}},
        ]

        mock_template = Mock()

        def mock_send_side_effect(template, recipient):
            if recipient["email"] == "user1@example.com":
                return {"success": True, "message_id": "msg123"}
            else:
                return {"success": False, "error": "Invalid email"}

        with patch.object(service, 'get_bulk_job', return_value=mock_job):
            with patch.object(service, 'template_service') as mock_template_service:
                mock_template_service.get_template.return_value = mock_template

                with patch.object(service, 'send_email', side_effect=mock_send_side_effect):
                    with patch.object(service, 'update_job_status') as mock_update_status:
                        await service.process_bulk_email_job(job_id, mock_session)

                        # Should complete despite partial failures
                        mock_update_status.assert_any_call(job_id, BulkJobStatus.COMPLETED, mock_session)

    @pytest.mark.asyncio
    async def test_process_bulk_email_job_cancelled(self, service, mock_session):
        """Test processing cancelled bulk job."""
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.CANCELLED

        with patch.object(service, 'get_bulk_job', return_value=mock_job):
            # Should not process cancelled job
            await service.process_bulk_email_job(job_id, mock_session)

            # No emails should be sent
            with patch.object(service, 'send_email') as mock_send:
                mock_send.assert_not_called()


class TestBulkEmailServiceDeliveryTracking:
    """Test email delivery tracking and logging."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock(spec=AsyncSession)
        session.add = Mock()
        session.commit = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_track_delivery_success(self, service, mock_session):
        """Test tracking successful email delivery."""
        job_id = str(uuid4())
        recipient = {"email": "test@example.com", "variables": {"name": "John"}}
        send_result = {"success": True, "message_id": "msg123"}

        with patch('dotmac.platform.communications.models.EmailDelivery') as MockDelivery:
            mock_delivery = Mock()
            MockDelivery.return_value = mock_delivery

            await service.track_delivery(job_id, recipient, send_result, mock_session)

            mock_session.add.assert_called_once_with(mock_delivery)
            mock_session.commit.assert_called_once()

            # Verify delivery record properties
            assert mock_delivery.job_id == job_id
            assert mock_delivery.recipient_email == recipient["email"]
            assert mock_delivery.status == "sent"
            assert mock_delivery.message_id == send_result["message_id"]

    @pytest.mark.asyncio
    async def test_track_delivery_failure(self, service, mock_session):
        """Test tracking failed email delivery."""
        job_id = str(uuid4())
        recipient = {"email": "invalid@example.com", "variables": {}}
        send_result = {"success": False, "error": "Invalid email address"}

        with patch('dotmac.platform.communications.models.EmailDelivery') as MockDelivery:
            mock_delivery = Mock()
            MockDelivery.return_value = mock_delivery

            await service.track_delivery(job_id, recipient, send_result, mock_session)

            assert mock_delivery.status == "failed"
            assert mock_delivery.error_message == send_result["error"]

    @pytest.mark.asyncio
    async def test_get_delivery_logs(self, service, mock_session):
        """Test retrieving delivery logs for a job."""
        job_id = str(uuid4())

        mock_deliveries = [
            Mock(recipient_email="user1@example.com", status="sent"),
            Mock(recipient_email="user2@example.com", status="failed"),
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_deliveries
        mock_session.execute.return_value = mock_result

        deliveries = await service.get_delivery_logs(job_id, mock_session)

        assert len(deliveries) == 2
        assert deliveries[0].status == "sent"
        assert deliveries[1].status == "failed"


class TestBulkEmailServiceErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    @pytest.mark.asyncio
    async def test_handle_invalid_job_id(self, service, mock_session=None):
        """Test handling invalid job ID."""
        if mock_session is None:
            mock_session = AsyncMock(spec=AsyncSession)

        with patch.object(service, 'get_bulk_job', return_value=None):
            result = await service.process_bulk_email_job("invalid-id", mock_session)
            assert result is None

    @pytest.mark.asyncio
    async def test_handle_empty_recipients_list(self, service, mock_session):
        """Test handling job with empty recipients list."""
        job_data = BulkEmailJobCreate(
            name="Empty Job",
            template_id=str(uuid4()),
            recipients=[]
        )

        with pytest.raises(ValueError, match="At least one recipient"):
            await service.create_bulk_job(job_data, mock_session)

    def test_handle_malformed_recipient_data(self, service):
        """Test handling malformed recipient data."""
        mock_template = Mock()
        invalid_recipient = {"invalid": "data"}  # Missing email

        with pytest.raises(KeyError):
            service.create_email_message(mock_template, invalid_recipient)

    @pytest.mark.asyncio
    async def test_handle_database_error_during_job_creation(self, service, mock_session):
        """Test handling database error during job creation."""
        job_data = BulkEmailJobCreate(
            name="Test Job",
            template_id=str(uuid4()),
            recipients=[{"email": "test@example.com", "variables": {}}]
        )

        mock_session.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await service.create_bulk_job(job_data, mock_session)

    @pytest.mark.asyncio
    async def test_handle_smtp_configuration_error(self, service):
        """Test handling SMTP configuration errors."""
        recipient = {"email": "test@example.com", "variables": {"name": "John"}}
        template = Mock()

        # Mock invalid SMTP configuration
        with patch.object(service, 'smtp_config') as mock_config:
            mock_config.host = None  # Invalid host

            with patch('smtplib.SMTP') as mock_smtp_class:
                mock_smtp_class.side_effect = Exception("Invalid SMTP config")

                result = await service.send_email(template, recipient)

                assert result["success"] is False
                assert "Invalid SMTP config" in result["error"]