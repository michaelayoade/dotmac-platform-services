"""
Tests for task system components.
"""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from dotmac.platform.tasks import (
    BackgroundOperation,
    BackgroundOperationsManager,
    BackgroundOperationsMiddleware,
    IdempotencyKey,
    MemoryStorage,
    OperationStatus,
    SagaStep,
    SagaStepStatus,
    SagaWorkflow,
    add_background_operations_middleware,
    get_idempotency_key,
    is_idempotent_request,
    set_operation_result,
)


class TestOperationStatus:
    """Test OperationStatus enum."""

    def test_operation_status_values(self):
        """Test all operation status values are defined."""
        assert OperationStatus.PENDING == "pending"
        assert OperationStatus.RUNNING == "running"
        assert OperationStatus.COMPLETED == "completed"
        assert OperationStatus.FAILED == "failed"
        assert OperationStatus.CANCELLED == "cancelled"


class TestSagaStepStatus:
    """Test SagaStepStatus enum."""

    def test_saga_step_status_values(self):
        """Test all saga step status values are defined."""
        assert SagaStepStatus.PENDING == "pending"
        assert SagaStepStatus.RUNNING == "running"
        assert SagaStepStatus.COMPLETED == "completed"
        assert SagaStepStatus.FAILED == "failed"
        assert SagaStepStatus.COMPENSATING == "compensating"
        assert SagaStepStatus.COMPENSATED == "compensated"


class TestIdempotencyKey:
    """Test IdempotencyKey dataclass."""

    def test_idempotency_key_creation(self):
        """Test creating an idempotency key."""
        now = datetime.utcnow()
        key = IdempotencyKey(key="test-key-123", operation_id="op-456", created_at=now)

        assert key.key == "test-key-123"
        assert key.operation_id == "op-456"
        assert key.created_at == now


class TestSagaStep:
    """Test SagaStep dataclass."""

    def test_saga_step_creation(self):
        """Test creating a saga step."""
        action = Mock(return_value="action_result")
        compensate = Mock(return_value="compensate_result")

        step = SagaStep(id="step-1", name="Test Step", action=action, compensate=compensate)

        assert step.id == "step-1"
        assert step.name == "Test Step"
        assert step.action == action
        assert step.compensate == compensate
        assert step.status == SagaStepStatus.PENDING
        assert step.result is None
        assert step.error is None

    def test_saga_step_without_compensate(self):
        """Test creating a saga step without compensate function."""
        action = Mock()

        step = SagaStep(id="step-2", name="No Compensate Step", action=action)

        assert step.compensate is None


class TestSagaWorkflow:
    """Test SagaWorkflow dataclass."""

    def test_saga_workflow_creation(self):
        """Test creating a saga workflow."""
        steps = [
            SagaStep(id="s1", name="Step 1", action=Mock()),
            SagaStep(id="s2", name="Step 2", action=Mock()),
        ]

        workflow = SagaWorkflow(id="workflow-1", name="Test Workflow", steps=steps)

        assert workflow.id == "workflow-1"
        assert workflow.name == "Test Workflow"
        assert len(workflow.steps) == 2
        assert workflow.current_step == 0
        assert workflow.status == OperationStatus.PENDING


class TestBackgroundOperation:
    """Test BackgroundOperation dataclass."""

    def test_background_operation_creation(self):
        """Test creating a background operation."""
        now = datetime.utcnow()

        operation = BackgroundOperation(
            id="op-1", name="Test Operation", status=OperationStatus.PENDING, created_at=now
        )

        assert operation.id == "op-1"
        assert operation.name == "Test Operation"
        assert operation.status == OperationStatus.PENDING
        assert operation.created_at == now
        assert operation.started_at is None
        assert operation.completed_at is None
        assert operation.result is None
        assert operation.error is None


class TestMemoryStorage:
    """Test MemoryStorage class."""

    def test_memory_storage_initialization(self):
        """Test memory storage initialization."""
        storage = MemoryStorage()

        assert storage.operations == {}
        assert storage.sagas == {}
        assert storage.idempotency_keys == {}

    def test_store_and_get_operation(self):
        """Test storing and retrieving operations."""
        storage = MemoryStorage()
        operation = BackgroundOperation(
            id="op-1", name="Test", status=OperationStatus.PENDING, created_at=datetime.utcnow()
        )

        storage.store_operation(operation)
        retrieved = storage.get_operation("op-1")

        assert retrieved == operation
        assert storage.get_operation("non-existent") is None

    def test_store_and_get_saga(self):
        """Test storing and retrieving sagas."""
        storage = MemoryStorage()
        saga = SagaWorkflow(id="saga-1", name="Test Saga", steps=[])

        storage.store_saga(saga)
        retrieved = storage.get_saga("saga-1")

        assert retrieved == saga
        assert storage.get_saga("non-existent") is None


class TestBackgroundOperationsManager:
    """Test BackgroundOperationsManager class."""

    def test_manager_initialization(self):
        """Test manager initialization with default storage."""
        manager = BackgroundOperationsManager()
        assert isinstance(manager.storage, MemoryStorage)

    def test_manager_with_custom_storage(self):
        """Test manager initialization with custom storage."""
        custom_storage = MemoryStorage()
        manager = BackgroundOperationsManager(storage=custom_storage)
        assert manager.storage == custom_storage

    @patch("dotmac.platform.tasks.uuid.uuid4")
    @patch("dotmac.platform.tasks.datetime")
    def test_start_operation(self, mock_datetime, mock_uuid):
        """Test starting a background operation."""
        mock_uuid.return_value = "generated-uuid"
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        manager = BackgroundOperationsManager()

        # Start operation with auto-generated ID
        operation = manager.start_operation("Test Operation")

        assert operation.id == "generated-uuid"
        assert operation.name == "Test Operation"
        assert operation.status == OperationStatus.PENDING
        assert operation.created_at == mock_now

        # Verify operation was stored
        stored = manager.storage.get_operation("generated-uuid")
        assert stored == operation

    def test_start_operation_with_custom_id(self):
        """Test starting operation with custom ID."""
        manager = BackgroundOperationsManager()

        operation = manager.start_operation("Test Op", operation_id="custom-id")

        assert operation.id == "custom-id"
        assert operation.name == "Test Op"

    @patch("dotmac.platform.tasks.datetime")
    def test_complete_operation(self, mock_datetime):
        """Test completing a background operation."""
        mock_now = datetime(2024, 1, 1, 13, 0, 0)
        mock_datetime.utcnow.return_value = mock_now

        manager = BackgroundOperationsManager()

        # Start an operation
        manager.start_operation("Test", operation_id="op-1")

        # Complete it
        manager.complete_operation("op-1", result={"data": "result"})

        # Verify updates
        updated = manager.storage.get_operation("op-1")
        assert updated.status == OperationStatus.COMPLETED
        assert updated.completed_at == mock_now
        assert updated.result == {"data": "result"}

    def test_complete_nonexistent_operation(self):
        """Test completing a non-existent operation does nothing."""
        manager = BackgroundOperationsManager()

        # Should not raise, just do nothing
        manager.complete_operation("non-existent", result="data")

    @patch("dotmac.platform.tasks.datetime")
    def test_fail_operation(self, mock_datetime):
        """Test failing a background operation."""
        mock_now = datetime(2024, 1, 1, 13, 30, 0)
        mock_datetime.utcnow.return_value = mock_now

        manager = BackgroundOperationsManager()

        # Start an operation
        manager.start_operation("Test", operation_id="op-1")

        # Fail it
        manager.fail_operation("op-1", error="Something went wrong")

        # Verify updates
        updated = manager.storage.get_operation("op-1")
        assert updated.status == OperationStatus.FAILED
        assert updated.completed_at == mock_now
        assert updated.error == "Something went wrong"

    def test_fail_nonexistent_operation(self):
        """Test failing a non-existent operation does nothing."""
        manager = BackgroundOperationsManager()

        # Should not raise, just do nothing
        manager.fail_operation("non-existent", error="error")


class TestBackgroundOperationsMiddleware:
    """Test BackgroundOperationsMiddleware class."""

    def test_middleware_initialization(self):
        """Test middleware initialization."""
        app = Mock()
        manager = BackgroundOperationsManager()

        middleware = BackgroundOperationsMiddleware(app, manager)

        assert middleware.app == app
        assert middleware.manager == manager

    def test_middleware_with_default_manager(self):
        """Test middleware creates default manager if not provided."""
        app = Mock()

        middleware = BackgroundOperationsMiddleware(app)

        assert isinstance(middleware.manager, BackgroundOperationsManager)

    @pytest.mark.asyncio
    async def test_middleware_call(self):
        """Test middleware call passes through to app."""
        app = Mock()
        app.return_value = None

        middleware = BackgroundOperationsMiddleware(app)

        scope = {"type": "http"}
        receive = Mock()
        send = Mock()

        await middleware(scope, receive, send)

        app.assert_called_once_with(scope, receive, send)


class TestHelperFunctions:
    """Test helper functions."""

    def test_add_background_operations_middleware(self):
        """Test adding background operations middleware."""
        app = Mock()
        manager = BackgroundOperationsManager()

        result = add_background_operations_middleware(app, manager)

        assert isinstance(result, BackgroundOperationsMiddleware)
        assert result.app == app
        assert result.manager == manager

    def test_get_idempotency_key(self):
        """Test getting idempotency key from request data."""
        request_data = {"idempotency_key": "key-123", "other": "data"}

        key = get_idempotency_key(request_data)

        assert key == "key-123"

    def test_get_idempotency_key_missing(self):
        """Test getting idempotency key when not present."""
        request_data = {"other": "data"}

        key = get_idempotency_key(request_data)

        assert key is None

    def test_is_idempotent_request(self):
        """Test checking if request is idempotent."""
        # Request with idempotency key
        request_with_key = {"idempotency_key": "key-123"}
        assert is_idempotent_request(request_with_key) is True

        # Request without idempotency key
        request_without_key = {"data": "value"}
        assert is_idempotent_request(request_without_key) is False

    @patch("dotmac.platform.tasks.logger")
    def test_set_operation_result(self, mock_logger):
        """Test setting operation result (logs only)."""
        set_operation_result("op-123", {"result": "data"})

        mock_logger.info.assert_called_once_with(
            "Setting result for operation op-123: {'result': 'data'}"
        )
