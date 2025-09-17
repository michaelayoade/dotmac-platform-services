"""
DotMac Tasks - Background Operations and Workflow Management

Simple task management for background operations, sagas, and workflows.
This is a minimal implementation for backward compatibility.
"""

import asyncio
import importlib
import inspect

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Optional

from .config import TaskConfig

from dotmac.platform.observability.unified_logging import get_logger
try:
    from .celery_app import app as celery_app

    CELERY_AVAILABLE = True
except Exception:  # pragma: no cover - celery optional in tests
    celery_app = None
    CELERY_AVAILABLE = False

logger = get_logger(__name__)

class OperationStatus(str, Enum):
    """Status of a background operation."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SagaStepStatus(str, Enum):
    """Status of a saga step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"

@dataclass
class IdempotencyKey:
    """Idempotency key for operations."""

    key: str
    operation_id: str
    created_at: datetime

@dataclass
class SagaStep:
    """A step in a saga workflow."""

    id: str
    name: str
    action: Callable[..., Any]
    compensate: Callable[..., Any] | None = None
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Any = None
    error: str | None = None

@dataclass
class SagaWorkflow:
    """Saga workflow definition."""

    id: str
    name: str
    steps: list[SagaStep]
    current_step: int = 0
    status: OperationStatus = OperationStatus.PENDING

@dataclass
class BackgroundOperation:
    """Background operation."""

    id: str
    name: str
    status: OperationStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    result: Any = None
    error: str | None = None

class MemoryStorage:
    """In-memory storage for operations."""

    def __init__(self) -> None:
        self.operations: dict[str, BackgroundOperation] = {}
        self.sagas: dict[str, SagaWorkflow] = {}
        self.idempotency_keys: dict[str, IdempotencyKey] = {}

    def get_operation(self, operation_id: str) -> BackgroundOperation | None:
        return self.operations.get(operation_id)

    def store_operation(self, operation: BackgroundOperation) -> None:
        self.operations[operation.id] = operation

    def get_saga(self, saga_id: str) -> SagaWorkflow | None:
        return self.sagas.get(saga_id)

    def store_saga(self, saga: SagaWorkflow) -> None:
        self.sagas[saga.id] = saga

class BackgroundOperationsManager:
    """Manager for background operations."""

    def __init__(self, storage: MemoryStorage | None = None) -> None:
        self.storage = storage or MemoryStorage()

    def mark_running(self, operation_id: str) -> None:
        """Mark an operation as running and capture the start timestamp."""
        operation = self.storage.get_operation(operation_id)
        if not operation:
            return
        operation.status = OperationStatus.RUNNING
        operation.started_at = datetime.utcnow()
        self.storage.store_operation(operation)

    def start_operation(self, name: str, operation_id: str | None = None) -> BackgroundOperation:
        """Start a background operation."""
        operation = BackgroundOperation(
            id=operation_id or str(uuid.uuid4()),
            name=name,
            status=OperationStatus.PENDING,
            created_at=datetime.utcnow(),
        )

        self.storage.store_operation(operation)
        logger.info(f"Started background operation: {operation.id}")
        return operation

    def complete_operation(self, operation_id: str, result: Any = None) -> None:
        """Complete a background operation."""
        operation = self.storage.get_operation(operation_id)
        if operation:
            operation.status = OperationStatus.COMPLETED
            operation.completed_at = datetime.utcnow()
            operation.result = result
            self.storage.store_operation(operation)

    def fail_operation(self, operation_id: str, error: str) -> None:
        """Fail a background operation."""
        operation = self.storage.get_operation(operation_id)
        if operation:
            operation.status = OperationStatus.FAILED
            operation.completed_at = datetime.utcnow()
            operation.error = error
            self.storage.store_operation(operation)

class BackgroundOperationsMiddleware:
    """FastAPI middleware for background operations."""

    def __init__(self, app, manager: BackgroundOperationsManager | None = None) -> None:
        self.app = app
        self.manager = manager or BackgroundOperationsManager()

    async def __call__(self, scope, receive, send):
        """Middleware call."""
        # Simple pass-through for now
        result = self.app(scope, receive, send)
        if asyncio.iscoroutine(result):
            await result

def add_background_operations_middleware(app, manager: BackgroundOperationsManager | None = None):
    """Add background operations middleware to FastAPI app."""
    return BackgroundOperationsMiddleware(app, manager)

def get_idempotency_key(request_data: dict[str, Any]) -> str | None:
    """Get idempotency key from request data."""
    return request_data.get("idempotency_key")

def is_idempotent_request(request_data: dict[str, Any]) -> bool:
    """Check if request is idempotent."""
    return get_idempotency_key(request_data) is not None

def set_operation_result(operation_id: str, result: Any) -> None:
    """Set operation result."""
    # This would typically interact with a global manager
    logger.info(f"Setting result for operation {operation_id}: {result}")

class TaskDispatchError(Exception):
    """Raised when a background task cannot be dispatched."""

class TaskDispatcher:
    """Bridge between legacy background operations and Celery tasks."""

    def __init__(
        self,
        manager: BackgroundOperationsManager | None = None,
        celery_enabled: bool | None = None,
    ) -> None:
        self.manager = manager or BackgroundOperationsManager()
        self._celery_enabled = CELERY_AVAILABLE if celery_enabled is None else celery_enabled

    @property
    def celery_enabled(self) -> bool:
        return self._celery_enabled and celery_app is not None

    def submit(
        self,
        task_name: str,
        *args: Any,
        queue: str | None = None,
        use_celery: bool | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Submit a background task via Celery or inline fallback."""

        operation = self.manager.start_operation(task_name)
        self.manager.mark_running(operation.id)

        dispatch_via_celery = (
            use_celery if use_celery is not None else True
        ) and self.celery_enabled

        if dispatch_via_celery:
            try:
                async_result = celery_app.send_task(
                    task_name,
                    args=args,
                    kwargs=kwargs,
                    queue=queue,
                )
                operation.result = {
                    "task_id": async_result.id,
                    "dispatched_at": datetime.utcnow().isoformat(),
                    "metadata": metadata or {},
                }
                self.manager.storage.store_operation(operation)
                return {
                    "operation_id": operation.id,
                    "task_id": async_result.id,
                    "dispatched": True,
                }
            except Exception as exc:
                logger.error(
                    "Celery dispatch failed; falling back to inline execution",
                    exc_info=True,
                )
                if use_celery:
                    self.manager.fail_operation(operation.id, str(exc))
                    raise TaskDispatchError(str(exc)) from exc

        return self._run_inline(operation, task_name, *args, metadata=metadata, **kwargs)

    def _run_inline(
        self,
        operation: BackgroundOperation,
        task_name: str,
        *args: Any,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        module_name, func_name = task_name.rsplit(".", 1)
        try:
            module = importlib.import_module(module_name)
            func = getattr(module, func_name)
        except Exception as exc:  # pragma: no cover - defensive fallback
            self.manager.fail_operation(operation.id, str(exc))
            raise TaskDispatchError(f"Unable to import task {task_name}: {exc}") from exc

        async def _execute_async(coro: Awaitable[Any]) -> Any:
            try:
                result = await coro
                self.manager.complete_operation(operation.id, result)
                return result
            except Exception as error:
                self.manager.fail_operation(operation.id, str(error))
                raise

        try:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    final = asyncio.run(_execute_async(result))
                    return {
                        "operation_id": operation.id,
                        "result": final,
                        "dispatched": False,
                    }
                else:
                    task = loop.create_task(_execute_async(result))
                    return {
                        "operation_id": operation.id,
                        "task": task,
                        "dispatched": False,
                    }

            self.manager.complete_operation(operation.id, result)
            return {
                "operation_id": operation.id,
                "result": result,
                "dispatched": False,
            }

        except Exception as exc:
            self.manager.fail_operation(operation.id, str(exc))
            raise TaskDispatchError(str(exc)) from exc

_DEFAULT_DISPATCHER: Optional[TaskDispatcher] = None

def get_task_dispatcher() -> TaskDispatcher:
    """Get (or lazily create) the default task dispatcher."""

    global _DEFAULT_DISPATCHER
    if _DEFAULT_DISPATCHER is None:
        _DEFAULT_DISPATCHER = TaskDispatcher()
    return _DEFAULT_DISPATCHER

def submit_background_task(
    task_name: str,
    *args: Any,
    queue: str | None = None,
    use_celery: bool | None = None,
    metadata: dict[str, Any] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Submit a background task using the shared dispatcher."""

    dispatcher = get_task_dispatcher()
    return dispatcher.submit(
        task_name,
        *args,
        queue=queue,
        use_celery=use_celery,
        metadata=metadata,
        **kwargs,
    )

# Import new utilities
from .idempotency import (
    IdempotencyError,
    IdempotencyManager,
    generate_idempotency_key,
    idempotent,
    idempotent_sync,
)
from .retry import (
    AsyncRetryManager,
    RetryError,
    calculate_backoff,
    retry_async,
    retry_sync,
    retry_with_manager,
)

# For backward compatibility, export everything
__all__ = [
    "TaskConfig",
    "BackgroundOperation",
    "BackgroundOperationsManager",
    "BackgroundOperationsMiddleware",
    "IdempotencyKey",
    "MemoryStorage",
    "OperationStatus",
    "SagaStep",
    "SagaStepStatus",
    "SagaWorkflow",
    "add_background_operations_middleware",
    "get_idempotency_key",
    "is_idempotent_request",
    "set_operation_result",
    # Retry utilities
    "retry_async",
    "retry_sync",
    "RetryError",
    "calculate_backoff",
    "AsyncRetryManager",
    "retry_with_manager",
    # Idempotency utilities
    "idempotent",
    "idempotent_sync",
    "IdempotencyError",
    "IdempotencyManager",
    "generate_idempotency_key",
    # Task dispatch bridging
    "TaskDispatcher",
    "TaskDispatchError",
    "get_task_dispatcher",
    "submit_background_task",
]

# Enums expected by tests
class RetryStrategy(str, Enum):
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"

class TaskPriority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class TaskState(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

__all__ += ["RetryStrategy", "TaskPriority", "TaskState"]
