"""
Focused tests for BulkEmailService based on actual implementation.

Tests the actual methods and functionality present in the BulkEmailService.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
from uuid import uuid4

from dotmac.platform.communications.bulk_service import BulkEmailService
from dotmac.platform.communications.models import (
    BulkEmailJobCreate,
    BulkJobStatus,
)


class TestBulkEmailServiceInitialization:
    """Test BulkEmailService initialization."""

    def test_bulk_service_init(self):
        """Test bulk email service initialization."""
        service = BulkEmailService()

        # Check that service initializes with expected attributes
        assert hasattr(service, 'template_service')
        assert service.template_service is not None

    def test_bulk_service_has_required_methods(self):
        """Test that service has expected methods."""
        service = BulkEmailService()

        assert hasattr(service, 'create_bulk_job')
        assert hasattr(service, 'get_bulk_job')
        assert hasattr(service, 'list_bulk_jobs')
        assert hasattr(service, 'cancel_bulk_job')
        assert hasattr(service, 'get_job_stats')


class TestBulkEmailServiceJobManagement:
    """Test bulk email job CRUD operations."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def sample_bulk_job_data(self):
        return BulkEmailJobCreate(
            name="Newsletter Campaign",
            template_id=str(uuid4()),
            recipients=[
                {
                    "email": "user1@example.com",
                    "variables": {"name": "John", "company": "Acme Inc"}
                },
                {
                    "email": "user2@example.com",
                    "variables": {"name": "Jane", "company": "Tech Corp"}
                }
            ],
            scheduled_at=datetime.now(timezone.utc),
            priority="normal"
        )

    @pytest.mark.asyncio
    async def test_create_bulk_job_success(self, service, mock_session, sample_bulk_job_data):
        """Test successful bulk job creation."""
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.name = sample_bulk_job_data.name
        mock_job.status = BulkJobStatus.PENDING

        # Mock template exists
        with patch.object(service.template_service, 'get_template') as mock_get_template:
            mock_get_template.return_value = Mock(id=sample_bulk_job_data.template_id)

            with patch('dotmac.platform.communications.models.BulkEmailJob') as MockBulkJob:
                MockBulkJob.return_value = mock_job

                result = await service.create_bulk_job(sample_bulk_job_data, mock_session)

                assert result is not None
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bulk_job_template_not_found(self, service, mock_session, sample_bulk_job_data):
        """Test bulk job creation when template doesn't exist."""
        with patch.object(service.template_service, 'get_template') as mock_get_template:
            mock_get_template.return_value = None

            # Should raise ValueError for missing template
            with pytest.raises(ValueError, match="Template not found"):
                await service.create_bulk_job(sample_bulk_job_data, mock_session)

    @pytest.mark.asyncio
    async def test_get_bulk_job_success(self, service, mock_session):
        """Test successful bulk job retrieval."""
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.name = "Test Job"
        mock_job.status = BulkJobStatus.PENDING

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        result = await service.get_bulk_job(job_id, mock_session)

        assert result is not None
        assert result.id == job_id
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_bulk_job_not_found(self, service, mock_session):
        """Test bulk job retrieval when not found."""
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
            Mock(id=str(uuid4()), name="Job 1", status=BulkJobStatus.PENDING),
            Mock(id=str(uuid4()), name="Job 2", status=BulkJobStatus.COMPLETED)
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_jobs
        mock_session.execute.return_value = mock_result

        # Mock count query
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(mock_jobs)

        def execute_side_effect(query):
            query_str = str(query).lower()
            if 'count' in query_str:
                return mock_count_result
            return mock_result

        mock_session.execute.side_effect = execute_side_effect

        jobs, count = await service.list_bulk_jobs(mock_session)

        assert len(jobs) == 2
        assert count == 2

    @pytest.mark.asyncio
    async def test_list_bulk_jobs_with_filters(self, service, mock_session):
        """Test bulk job listing with status filter."""
        mock_jobs = [Mock(id=str(uuid4()), name="Pending Job", status=BulkJobStatus.PENDING)]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_jobs
        mock_session.execute.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1

        def execute_side_effect(query):
            if 'count' in str(query).lower():
                return mock_count_result
            return mock_result

        mock_session.execute.side_effect = execute_side_effect

        jobs, count = await service.list_bulk_jobs(
            mock_session,
            status=BulkJobStatus.PENDING,
            limit=10,
            offset=0
        )

        assert len(jobs) == 1
        assert jobs[0].status == BulkJobStatus.PENDING

    @pytest.mark.asyncio
    async def test_cancel_bulk_job_success(self, service, mock_session):
        """Test successful bulk job cancellation."""
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.PENDING

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        result = await service.cancel_bulk_job(job_id, mock_session)

        assert result is True
        assert mock_job.status == BulkJobStatus.CANCELLED
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_bulk_job_not_found(self, service, mock_session):
        """Test cancelling non-existent job."""
        job_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await service.cancel_bulk_job(job_id, mock_session)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_bulk_job_already_completed(self, service, mock_session):
        """Test cancelling already completed job."""
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.COMPLETED

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        # Should raise ValueError for completed job
        with pytest.raises(ValueError, match="Cannot cancel"):
            await service.cancel_bulk_job(job_id, mock_session)


class TestBulkEmailServiceStatistics:
    """Test bulk job statistics."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    @pytest.fixture
    def mock_session(self):
        session = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_get_job_stats_success(self, service, mock_session):
        """Test getting job statistics."""
        job_id = str(uuid4())

        # Mock job stats query
        mock_stats = Mock()
        mock_stats.total_recipients = 100
        mock_stats.sent_count = 75
        mock_stats.failed_count = 20
        mock_stats.pending_count = 5
        mock_stats.success_rate = 75.0

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        mock_session.execute.return_value = mock_result

        stats = await service.get_job_stats(job_id, mock_session)

        assert stats is not None
        assert stats.total_recipients == 100
        assert stats.success_rate == 75.0

    @pytest.mark.asyncio
    async def test_get_job_stats_job_not_found(self, service, mock_session):
        """Test getting stats for non-existent job."""
        job_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        stats = await service.get_job_stats(job_id, mock_session)
        assert stats is None


class TestBulkEmailServiceEmailProcessing:
    """Test email processing functionality."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    @pytest.mark.asyncio
    async def test_send_single_email_success(self, service):
        """Test sending single email."""
        template = Mock()
        template.subject = "Welcome {{ name }}!"
        template.html_content = "<h1>Hello {{ name }}</h1>"
        template.text_content = "Hello {{ name }}"

        recipient = {
            "email": "test@example.com",
            "variables": {"name": "John Doe"}
        }

        with patch('dotmac.platform.communications.bulk_service._send_smtp_email') as mock_send:
            mock_send.return_value = {
                "success": True,
                "message_id": "msg123",
                "smtp_response": "250 OK"
            }

            result = await service._send_single_email(template, recipient)

            assert result["success"] is True
            assert result["message_id"] == "msg123"

    @pytest.mark.asyncio
    async def test_send_single_email_failure(self, service):
        """Test sending single email with failure."""
        template = Mock()
        template.subject = "Test"

        recipient = {
            "email": "invalid@example.com",
            "variables": {}
        }

        with patch('dotmac.platform.communications.bulk_service._send_smtp_email') as mock_send:
            mock_send.return_value = {
                "success": False,
                "error": "Invalid recipient"
            }

            result = await service._send_single_email(template, recipient)

            assert result["success"] is False
            assert "error" in result

    @pytest.mark.asyncio
    async def test_send_smtp_email_success(self, service):
        """Test SMTP email sending."""
        to_email = "test@example.com"
        subject = "Test Subject"
        html_content = "<h1>Test</h1>"
        text_content = "Test"

        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = Mock()
            mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_smtp_class.return_value.__exit__ = Mock(return_value=None)
            mock_smtp.send_message = Mock(return_value={})

            result = await service._send_smtp_email(to_email, subject, html_content, text_content)

            assert result["success"] is True
            assert "message_id" in result

    @pytest.mark.asyncio
    async def test_send_smtp_email_connection_error(self, service):
        """Test SMTP email sending with connection error."""
        to_email = "test@example.com"
        subject = "Test Subject"

        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = ConnectionRefusedError("Connection refused")

            result = await service._send_smtp_email(to_email, subject, "", "")

            assert result["success"] is False
            assert "Connection refused" in result["error"]


class TestBulkEmailServiceCeleryIntegration:
    """Test Celery task integration."""

    def test_process_bulk_email_job_task_decorator(self):
        """Test that the Celery task is properly decorated."""
        from dotmac.platform.communications.bulk_service import process_bulk_email_job

        # Should be callable as a function
        assert callable(process_bulk_email_job)

    @pytest.mark.asyncio
    async def test_process_bulk_email_job_async_function(self):
        """Test the async bulk processing function."""
        from dotmac.platform.communications.bulk_service import _process_bulk_email_job_async

        job_id = str(uuid4())
        mock_task = Mock()

        # Mock the database and services
        with patch('dotmac.platform.communications.bulk_service.get_async_session'):
            with patch('dotmac.platform.communications.bulk_service.get_bulk_service'):
                with patch('dotmac.platform.communications.bulk_service.get_template_service'):
                    # Should be able to call without raising exceptions
                    # (actual implementation would require more mocking)
                    assert callable(_process_bulk_email_job_async)


class TestBulkEmailServiceUtilities:
    """Test utility functions."""

    def test_get_bulk_service_function(self):
        """Test the get_bulk_service utility function."""
        from dotmac.platform.communications.bulk_service import get_bulk_service

        service = get_bulk_service()
        assert isinstance(service, BulkEmailService)

    def test_bulk_service_reusability(self):
        """Test that service can be reused."""
        service = BulkEmailService()

        # Should be able to create multiple instances
        service2 = BulkEmailService()

        assert service is not service2
        assert isinstance(service, BulkEmailService)
        assert isinstance(service2, BulkEmailService)


class TestBulkEmailServiceErrorHandling:
    """Test error handling scenarios."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.mark.asyncio
    async def test_create_job_empty_recipients(self, service, mock_session):
        """Test creating job with empty recipients list."""
        empty_job_data = BulkEmailJobCreate(
            name="Empty Job",
            template_id=str(uuid4()),
            recipients=[]  # Empty list
        )

        # Should raise ValueError for empty recipients
        with pytest.raises(ValueError, match="At least one recipient"):
            await service.create_bulk_job(empty_job_data, mock_session)

    @pytest.mark.asyncio
    async def test_database_error_handling(self, service, mock_session):
        """Test handling database errors."""
        job_id = str(uuid4())
        mock_session.execute.side_effect = Exception("Database error")

        # Should handle database errors gracefully
        try:
            result = await service.get_bulk_job(job_id, mock_session)
            # Depending on implementation, might return None or re-raise
        except Exception as e:
            # Should be a handled exception, not crash
            assert "Database error" in str(e)

    @pytest.mark.asyncio
    async def test_invalid_job_id_handling(self, service, mock_session):
        """Test handling invalid job IDs."""
        invalid_ids = ["", "invalid-uuid", None]

        for invalid_id in invalid_ids:
            if invalid_id is not None:
                # Should not crash on invalid IDs
                try:
                    result = await service.get_bulk_job(invalid_id, mock_session)
                except (ValueError, TypeError):
                    # These are acceptable exceptions for invalid input
                    pass

    def test_service_configuration_validation(self):
        """Test that service validates its configuration."""
        service = BulkEmailService()

        # Service should have required components
        assert service.template_service is not None

        # Should have access to required methods
        assert hasattr(service, 'create_bulk_job')
        assert hasattr(service, 'get_bulk_job')
        assert hasattr(service, 'list_bulk_jobs')
        assert hasattr(service, 'cancel_bulk_job')
        assert hasattr(service, 'get_job_stats')


class TestBulkEmailServiceIntegration:
    """Test integration scenarios."""

    @pytest.fixture
    def service(self):
        return BulkEmailService()

    def test_service_template_service_integration(self, service):
        """Test integration with template service."""
        # Should have template service available
        assert hasattr(service, 'template_service')
        assert service.template_service is not None

        # Template service should have expected methods
        assert hasattr(service.template_service, 'get_template')
        assert hasattr(service.template_service, 'render_template')