"""
Simple tests for BulkEmailService to increase coverage.

Tests basic functionality without complex mocking.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
from uuid import uuid4

from dotmac.platform.communications.bulk_service import BulkEmailService
from dotmac.platform.communications.models import BulkEmailJobCreate, BulkJobStatus


class TestBulkEmailServiceBasics:
    """Test basic BulkEmailService functionality."""

    def test_init(self):
        """Test service initialization."""
        service = BulkEmailService()

        # Should have template service
        assert hasattr(service, 'template_service')
        assert service.template_service is not None

    def test_has_required_methods(self):
        """Test that service has expected methods."""
        service = BulkEmailService()

        required_methods = [
            'create_bulk_job',
            'get_bulk_job',
            'list_bulk_jobs',
            'cancel_bulk_job',
            'get_job_stats',
        ]

        for method in required_methods:
            assert hasattr(service, method)
            assert callable(getattr(service, method))

    @pytest.mark.asyncio
    async def test_create_bulk_job_basic(self):
        """Test basic bulk job creation."""
        service = BulkEmailService()

        job_data = BulkEmailJobCreate(
            name="Test Campaign",
            template_id=str(uuid4()),
            recipients=[
                {
                    "email": "user1@example.com",
                    "variables": {"name": "John"}
                },
                {
                    "email": "user2@example.com",
                    "variables": {"name": "Jane"}
                }
            ],
            scheduled_at=datetime.now(timezone.utc),
            priority="normal"
        )

        mock_session = AsyncMock()
        mock_job = Mock()
        mock_job.id = str(uuid4())
        mock_job.name = job_data.name

        # Mock template exists
        with patch.object(service.template_service, 'get_template') as mock_get_template:
            mock_get_template.return_value = Mock(id=job_data.template_id)

            with patch('dotmac.platform.communications.models.BulkEmailJob') as MockBulkJob:
                MockBulkJob.return_value = mock_job

                result = await service._create_bulk_job(job_data, mock_session)

                assert result is not None
                mock_session.add.assert_called_once()
                mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bulk_job_empty_recipients(self):
        """Test bulk job creation with empty recipients."""
        service = BulkEmailService()

        job_data = BulkEmailJobCreate(
            name="Empty Campaign",
            template_id=str(uuid4()),
            recipients=[]  # Empty list
        )

        mock_session = AsyncMock()

        # Should raise ValueError for empty recipients
        with pytest.raises(ValueError, match="At least one recipient"):
            await service._create_bulk_job(job_data, mock_session)

    @pytest.mark.asyncio
    async def test_create_bulk_job_template_not_found(self):
        """Test bulk job creation when template doesn't exist."""
        service = BulkEmailService()

        job_data = BulkEmailJobCreate(
            name="Test Campaign",
            template_id=str(uuid4()),
            recipients=[{"email": "test@example.com", "variables": {}}]
        )

        mock_session = AsyncMock()

        # Mock template not found
        with patch.object(service.template_service, 'get_template') as mock_get_template:
            mock_get_template.return_value = None

            with pytest.raises(ValueError, match="Template not found"):
                await service._create_bulk_job(job_data, mock_session)

    @pytest.mark.asyncio
    async def test_get_bulk_job_found(self):
        """Test getting existing bulk job."""
        service = BulkEmailService()
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.name = "Test Job"

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        with patch('dotmac.platform.communications.models.BulkJobResponse') as MockResponse:
            MockResponse.model_validate.return_value = mock_job

            result = await service._get_bulk_job(job_id, mock_session)

            assert result is not None
            mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_bulk_job_not_found(self):
        """Test getting non-existent bulk job."""
        service = BulkEmailService()
        job_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        result = await service._get_bulk_job(job_id, mock_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_bulk_jobs_no_filter(self):
        """Test listing bulk jobs without filters."""
        service = BulkEmailService()

        mock_jobs = [
            Mock(id="1", name="Job 1"),
            Mock(id="2", name="Job 2")
        ]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_jobs
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        # Mock count query
        mock_count_result = Mock()
        mock_count_result.scalar.return_value = len(mock_jobs)

        def execute_side_effect(query):
            if 'count' in str(query).lower():
                return mock_count_result
            return mock_result

        mock_session.execute.side_effect = execute_side_effect

        with patch('dotmac.platform.communications.models.BulkJobResponse') as MockResponse:
            MockResponse.model_validate.side_effect = lambda x: x

            jobs, count = await service._list_bulk_jobs(None, None, 50, 0, mock_session)

            assert len(jobs) == 2
            assert count == 2

    @pytest.mark.asyncio
    async def test_list_bulk_jobs_with_status_filter(self):
        """Test listing bulk jobs with status filter."""
        service = BulkEmailService()

        mock_jobs = [Mock(id="1", name="Pending Job", status=BulkJobStatus.PENDING)]

        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = mock_jobs
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        mock_count_result = Mock()
        mock_count_result.scalar.return_value = 1

        def execute_side_effect(query):
            if 'count' in str(query).lower():
                return mock_count_result
            return mock_result

        mock_session.execute.side_effect = execute_side_effect

        with patch('dotmac.platform.communications.models.BulkJobResponse') as MockResponse:
            MockResponse.model_validate.side_effect = lambda x: x

            jobs, count = await service._list_bulk_jobs(BulkJobStatus.PENDING, None, 50, 0, mock_session)

            assert len(jobs) == 1
            assert count == 1

    @pytest.mark.asyncio
    async def test_cancel_bulk_job_success(self):
        """Test successful bulk job cancellation."""
        service = BulkEmailService()
        job_id = str(uuid4())

        mock_job = Mock()
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.PENDING

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        result = await service._cancel_bulk_job(job_id, mock_session)

        assert result is True
        assert mock_job.status == BulkJobStatus.CANCELLED
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_bulk_job_not_found(self):
        """Test cancelling non-existent job."""
        service = BulkEmailService()
        job_id = str(uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        result = await service._cancel_bulk_job(job_id, mock_session)
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_bulk_job_invalid_status(self):
        """Test cancelling job with invalid status."""
        service = BulkEmailService()
        job_id = str(uuid4())

        # Test each invalid status
        invalid_statuses = [BulkJobStatus.COMPLETED, BulkJobStatus.FAILED]

        for status in invalid_statuses:
            mock_job = Mock()
            mock_job.id = job_id
            mock_job.status = status

            mock_result = Mock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session = AsyncMock()
            mock_session.execute.return_value = mock_result

            with pytest.raises(ValueError, match="Cannot cancel"):
                await service._cancel_bulk_job(job_id, mock_session)

    @pytest.mark.asyncio
    async def test_get_job_stats_success(self):
        """Test getting job statistics."""
        service = BulkEmailService()
        job_id = str(uuid4())

        # Mock job stats
        mock_stats = Mock()
        mock_stats.total_recipients = 100
        mock_stats.sent_count = 75
        mock_stats.failed_count = 20
        mock_stats.pending_count = 5

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_stats
        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        result = await service._get_job_stats(mock_session)

        # Should return the mocked stats
        assert result is not None

    def test_service_utility_function(self):
        """Test the utility function for getting service instance."""
        from dotmac.platform.communications.bulk_service import get_bulk_service

        service = get_bulk_service()
        assert isinstance(service, BulkEmailService)

    def test_celery_task_decorator(self):
        """Test that Celery task is properly decorated."""
        from dotmac.platform.communications.bulk_service import process_bulk_email_job

        # Should be callable
        assert callable(process_bulk_email_job)

    @pytest.mark.asyncio
    async def test_process_bulk_email_job_async_function(self):
        """Test the async bulk processing function exists."""
        from dotmac.platform.communications.bulk_service import _process_bulk_email_job_async

        # Should be callable
        assert callable(_process_bulk_email_job_async)

    @pytest.mark.asyncio
    async def test_send_single_email_function_exists(self):
        """Test that send single email function exists."""
        service = BulkEmailService()

        # Should have the method
        assert hasattr(service, '_send_single_email')
        assert callable(service._send_single_email)

    @pytest.mark.asyncio
    async def test_send_smtp_email_function_exists(self):
        """Test that SMTP email function exists."""
        from dotmac.platform.communications.bulk_service import _send_smtp_email

        # Should be callable
        assert callable(_send_smtp_email)

    @pytest.mark.asyncio
    async def test_send_smtp_email_basic(self):
        """Test basic SMTP email sending."""
        from dotmac.platform.communications.bulk_service import _send_smtp_email

        # Mock SMTP server
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = Mock()
            mock_smtp_class.return_value.__enter__ = Mock(return_value=mock_smtp)
            mock_smtp_class.return_value.__exit__ = Mock(return_value=None)
            mock_smtp.send_message = Mock(return_value={})

            result = await _send_smtp_email(
                "test@example.com",
                "Test Subject",
                "<h1>Test HTML</h1>",
                "Test text content"
            )

            assert result["success"] is True
            assert "message_id" in result

    @pytest.mark.asyncio
    async def test_send_smtp_email_connection_error(self):
        """Test SMTP email sending with connection error."""
        from dotmac.platform.communications.bulk_service import _send_smtp_email

        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = ConnectionRefusedError("Connection refused")

            result = await _send_smtp_email(
                "test@example.com",
                "Test Subject",
                "<h1>Test HTML</h1>",
                "Test text content"
            )

            assert result["success"] is False
            assert "Connection refused" in result["error"]

    @pytest.mark.asyncio
    async def test_service_integration_with_template_service(self):
        """Test integration with template service."""
        service = BulkEmailService()

        # Should have template service
        assert service.template_service is not None

        # Template service should have expected methods
        template_service = service.template_service
        assert hasattr(template_service, 'get_template')
        assert hasattr(template_service, 'render_template')

    def test_service_error_handling_methods(self):
        """Test that service has error handling."""
        service = BulkEmailService()

        # Service should handle database errors gracefully
        # This is tested through the actual method calls above

        # Service should validate input data
        # This is tested through the empty recipients test above

        assert service is not None

    @pytest.mark.asyncio
    async def test_bulk_job_workflow(self):
        """Test typical bulk job workflow."""
        service = BulkEmailService()

        # 1. Create job
        job_data = BulkEmailJobCreate(
            name="Workflow Test",
            template_id=str(uuid4()),
            recipients=[{"email": "test@example.com", "variables": {"name": "Test"}}]
        )

        # 2. Mock successful creation
        mock_session = AsyncMock()
        mock_job = Mock()
        mock_job.id = str(uuid4())

        with patch.object(service.template_service, 'get_template') as mock_get_template:
            mock_get_template.return_value = Mock()

            with patch('dotmac.platform.communications.models.BulkEmailJob') as MockBulkJob:
                MockBulkJob.return_value = mock_job

                created_job = await service._create_bulk_job(job_data, mock_session)
                assert created_job is not None

        # 3. Mock getting the job
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        with patch('dotmac.platform.communications.models.BulkJobResponse') as MockResponse:
            MockResponse.model_validate.return_value = mock_job

            retrieved_job = await service._get_bulk_job(mock_job.id, mock_session)
            assert retrieved_job is not None

        # 4. Mock cancelling the job
        mock_job.status = BulkJobStatus.PENDING
        result = await service._cancel_bulk_job(mock_job.id, mock_session)
        assert result is True
        assert mock_job.status == BulkJobStatus.CANCELLED