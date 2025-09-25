"""
Fixed tests for BulkEmailService with proper async mocking.

This test file properly handles:
- Async session mocking
- Pydantic model validation
- Complete mock object attributes
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch, MagicMock, PropertyMock
from uuid import uuid4
import json

from dotmac.platform.communications.bulk_service import BulkEmailService
from dotmac.platform.communications.models import (
    BulkEmailJobCreate,
    BulkEmailJobResponse,
    BulkJobStatus,
    RecipientData,
    EmailTemplate,
    BulkEmailJob,
)


@pytest.fixture
def mock_async_session():
    """Create a properly configured async session mock."""
    session = AsyncMock()

    # Configure async context manager
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)

    # Configure execute to return a result mock
    result_mock = AsyncMock()
    result_mock.scalar_one_or_none = AsyncMock()
    result_mock.scalars = AsyncMock()
    session.execute = AsyncMock(return_value=result_mock)

    # Configure transaction methods
    session.add = Mock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()

    return session


@pytest.fixture
def mock_template():
    """Create a mock email template."""
    template = Mock(spec=EmailTemplate)
    template.id = str(uuid4())
    template.name = "Test Template"
    template.subject = "Test Subject"
    template.body = "Test Body {{ name }}"
    template.is_active = True
    return template


@pytest.fixture
def bulk_service():
    """Create BulkEmailService instance."""
    return BulkEmailService()


@pytest.fixture
def sample_job_data():
    """Create sample bulk job creation data."""
    return BulkEmailJobCreate(
        name="Test Campaign",
        template_id=str(uuid4()),
        recipients=[
            RecipientData(email="user1@example.com", name="User 1"),
            RecipientData(email="user2@example.com", name="User 2"),
            RecipientData(email="user3@example.com", name="User 3", custom_data={"role": "admin"}),
        ],
        scheduled_at=None,
        priority="normal"
    )


class TestBulkEmailServiceInitialization:
    """Test BulkEmailService initialization."""

    def test_service_initialization(self):
        """Test bulk email service initializes correctly."""
        service = BulkEmailService()

        # Check SMTP configuration is a dictionary
        assert isinstance(service.smtp_config, dict)
        assert 'host' in service.smtp_config
        assert 'port' in service.smtp_config
        assert 'username' in service.smtp_config
        assert 'password' in service.smtp_config
        assert 'use_tls' in service.smtp_config

        # Check template service exists
        assert service.template_service is not None

    @patch('dotmac.platform.communications.bulk_service.settings')
    def test_service_with_custom_settings(self, mock_settings):
        """Test service initialization with custom SMTP settings."""
        # Configure mock settings
        mock_smtp = Mock()
        mock_smtp.host = 'custom-smtp.example.com'
        mock_smtp.port = 2525
        mock_smtp.username = 'custom_user'
        mock_smtp.password = 'custom_pass'
        mock_smtp.use_tls = False
        mock_settings.smtp = mock_smtp

        service = BulkEmailService()

        # Verify custom settings are used
        assert service.smtp_config['host'] == 'custom-smtp.example.com'
        assert service.smtp_config['port'] == 2525
        assert service.smtp_config['username'] == 'custom_user'
        assert service.smtp_config['password'] == 'custom_pass'
        assert service.smtp_config['use_tls'] is False


class TestBulkEmailJobCreation:
    """Test bulk email job creation with proper mocking."""

    @pytest.mark.asyncio
    async def test_create_bulk_job_success(self, bulk_service, mock_async_session, sample_job_data, mock_template):
        """Test successful bulk email job creation."""
        job_id = str(uuid4())
        created_at = datetime.now(timezone.utc)

        # Configure session to return template
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = mock_template

        # Create a properly configured mock job that will be returned after DB operations
        mock_job = Mock(spec=BulkEmailJob)
        mock_job.id = job_id
        mock_job.name = sample_job_data.name
        mock_job.template_id = sample_job_data.template_id
        mock_job.status = BulkJobStatus.QUEUED
        mock_job.total_recipients = len(sample_job_data.recipients)
        mock_job.sent_count = 0
        mock_job.failed_count = 0
        mock_job.error_message = None
        mock_job.scheduled_at = sample_job_data.scheduled_at
        mock_job.started_at = None
        mock_job.completed_at = None
        mock_job.created_at = created_at
        mock_job.recipients_data = json.dumps([
            {'email': r.email, 'name': r.name, 'custom_data': r.custom_data or {}}
            for r in sample_job_data.recipients
        ])

        # Configure refresh to populate the mock job
        def refresh_side_effect(obj):
            """Side effect to simulate SQLAlchemy refresh."""
            if hasattr(obj, '__class__') and obj.__class__.__name__ == 'BulkEmailJob':
                # Copy mock attributes to the actual object
                for attr in ['id', 'status', 'total_recipients', 'sent_count',
                           'failed_count', 'created_at', 'started_at', 'completed_at']:
                    setattr(obj, attr, getattr(mock_job, attr))

        mock_async_session.refresh.side_effect = refresh_side_effect

        # Patch BulkEmailJob to return our configured mock
        with patch('dotmac.platform.communications.bulk_service.BulkEmailJob') as MockJob:
            # Create instance that will be used
            job_instance = Mock(spec=BulkEmailJob)
            MockJob.return_value = job_instance

            # Set initial attributes
            job_instance.id = None  # Will be set after insert
            job_instance.name = sample_job_data.name
            job_instance.template_id = sample_job_data.template_id
            job_instance.status = BulkJobStatus.QUEUED
            job_instance.total_recipients = len(sample_job_data.recipients)
            job_instance.sent_count = 0
            job_instance.failed_count = 0
            job_instance.error_message = None
            job_instance.scheduled_at = sample_job_data.scheduled_at
            job_instance.started_at = None
            job_instance.completed_at = None
            job_instance.created_at = None  # Will be set after insert

            # Configure refresh to update the job instance
            async def mock_refresh(obj):
                if obj == job_instance:
                    obj.id = job_id
                    obj.created_at = created_at
                    obj.status = BulkJobStatus.QUEUED

            mock_async_session.refresh = AsyncMock(side_effect=mock_refresh)

            # Call the service method
            result = await bulk_service.create_bulk_job(sample_job_data, mock_async_session)

            # Verify the result
            assert isinstance(result, BulkEmailJobResponse)
            assert result.id == job_id
            assert result.name == sample_job_data.name
            assert result.template_id == sample_job_data.template_id
            assert result.status == BulkJobStatus.QUEUED
            assert result.total_recipients == len(sample_job_data.recipients)
            assert result.sent_count == 0
            assert result.failed_count == 0

            # Verify database operations were called
            mock_async_session.add.assert_called_once()
            mock_async_session.commit.assert_called_once()
            mock_async_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bulk_job_template_not_found(self, bulk_service, mock_async_session, sample_job_data):
        """Test bulk job creation with non-existent template."""
        # Configure session to return no template
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = None

        # Should raise ValueError
        with pytest.raises(ValueError, match="Template .* not found or inactive"):
            await bulk_service.create_bulk_job(sample_job_data, mock_async_session)

        # Verify no commit was called
        mock_async_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_bulk_job_with_scheduled_time(self, bulk_service, mock_async_session, sample_job_data, mock_template):
        """Test creating a scheduled bulk email job."""
        scheduled_time = datetime.now(timezone.utc).replace(hour=10, minute=0, second=0)
        sample_job_data.scheduled_at = scheduled_time

        # Configure session
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = mock_template

        # Create mock job
        job_instance = Mock(spec=BulkEmailJob)
        job_instance.id = str(uuid4())
        job_instance.name = sample_job_data.name
        job_instance.template_id = sample_job_data.template_id
        job_instance.status = BulkJobStatus.QUEUED
        job_instance.total_recipients = len(sample_job_data.recipients)
        job_instance.sent_count = 0
        job_instance.failed_count = 0
        job_instance.scheduled_at = scheduled_time
        job_instance.created_at = datetime.now(timezone.utc)

        async def mock_refresh(obj):
            # Copy attributes from job_instance to obj
            for attr in dir(job_instance):
                if not attr.startswith('_'):
                    try:
                        setattr(obj, attr, getattr(job_instance, attr))
                    except:
                        pass

        mock_async_session.refresh = AsyncMock(side_effect=mock_refresh)

        with patch('dotmac.platform.communications.bulk_service.BulkEmailJob', return_value=job_instance):
            result = await bulk_service.create_bulk_job(sample_job_data, mock_async_session)

            assert result.scheduled_at == scheduled_time
            assert result.status == BulkJobStatus.QUEUED


class TestBulkEmailJobManagement:
    """Test bulk email job management operations."""

    @pytest.mark.asyncio
    async def test_get_bulk_job_found(self, bulk_service, mock_async_session):
        """Test retrieving an existing bulk job."""
        job_id = str(uuid4())

        # Create mock job
        mock_job = Mock(spec=BulkEmailJob)
        mock_job.id = job_id
        mock_job.name = "Test Job"
        mock_job.status = BulkJobStatus.PROCESSING
        mock_job.total_recipients = 100
        mock_job.sent_count = 50
        mock_job.failed_count = 5
        mock_job.template_id = str(uuid4())
        mock_job.created_at = datetime.now(timezone.utc)

        # Configure session to return the job
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = mock_job

        result = await bulk_service.get_bulk_job(job_id, mock_async_session)

        assert isinstance(result, BulkEmailJobResponse)
        assert result.id == job_id
        assert result.name == "Test Job"
        assert result.status == BulkJobStatus.PROCESSING
        assert result.sent_count == 50

    @pytest.mark.asyncio
    async def test_get_bulk_job_not_found(self, bulk_service, mock_async_session):
        """Test retrieving a non-existent bulk job."""
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = None

        result = await bulk_service.get_bulk_job(str(uuid4()), mock_async_session)
        assert result is None

    @pytest.mark.asyncio
    async def test_list_bulk_jobs(self, bulk_service, mock_async_session):
        """Test listing bulk email jobs."""
        # Create mock jobs
        jobs = [
            Mock(
                id=str(uuid4()),
                name=f"Job {i}",
                status=BulkJobStatus.QUEUED if i % 2 == 0 else BulkJobStatus.COMPLETED,
                total_recipients=100,
                sent_count=100 if i % 2 == 1 else 0,
                failed_count=0,
                template_id=str(uuid4()),
                created_at=datetime.now(timezone.utc)
            )
            for i in range(3)
        ]

        # Configure session
        scalars_mock = AsyncMock()
        scalars_mock.all.return_value = jobs
        mock_async_session.execute.return_value.scalars.return_value = scalars_mock

        result = await bulk_service.list_bulk_jobs(mock_async_session)

        assert len(result) == 3
        assert all(isinstance(job, BulkEmailJobResponse) for job in result)

    @pytest.mark.asyncio
    async def test_cancel_bulk_job(self, bulk_service, mock_async_session):
        """Test cancelling a bulk email job."""
        job_id = str(uuid4())

        # Create mock job
        mock_job = Mock(spec=BulkEmailJob)
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.QUEUED
        mock_job.name = "Test Job"
        mock_job.total_recipients = 100
        mock_job.sent_count = 0
        mock_job.failed_count = 0
        mock_job.template_id = str(uuid4())
        mock_job.created_at = datetime.now(timezone.utc)

        # Configure session
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = mock_job

        result = await bulk_service.cancel_bulk_job(job_id, mock_async_session)

        # Verify status was updated
        assert mock_job.status == BulkJobStatus.CANCELLED
        mock_async_session.commit.assert_called_once()

        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_bulk_job_already_completed(self, bulk_service, mock_async_session):
        """Test cancelling an already completed job."""
        job_id = str(uuid4())

        # Create completed job
        mock_job = Mock(spec=BulkEmailJob)
        mock_job.id = job_id
        mock_job.status = BulkJobStatus.COMPLETED

        mock_async_session.execute.return_value.scalar_one_or_none.return_value = mock_job

        result = await bulk_service.cancel_bulk_job(job_id, mock_async_session)

        # Should return False and not change status
        assert result is False
        assert mock_job.status == BulkJobStatus.COMPLETED
        mock_async_session.commit.assert_not_called()