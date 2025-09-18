"""
Progress Tracking and Resumable Operations

Handles progress tracking, persistence, and resumable upload/download operations.
"""

import json
import pickle
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, UTC
from pathlib import Path
from typing import Any, AsyncGenerator, Callable

import aiofiles
from pydantic import BaseModel, ConfigDict, Field

from ..core import BaseModel as DotMacBaseModel
from .base import (
    DataTransferError,
    ProgressError,
    ProgressInfo,
    TransferStatus,
)


class ProgressStore(ABC):
    """Abstract base class for progress storage."""

    @abstractmethod
    async def save_progress(self, operation_id: str, progress: ProgressInfo) -> None:
        """Save progress information."""
        ...

    @abstractmethod
    async def load_progress(self, operation_id: str) -> ProgressInfo | None:
        """Load progress information."""
        ...

    @abstractmethod
    async def delete_progress(self, operation_id: str) -> None:
        """Delete progress information."""
        ...

    @abstractmethod
    async def list_operations(self) -> list[str]:
        """List all operation IDs."""
        ...


class FileProgressStore(ProgressStore):
    """File-based progress storage."""

    def __init__(self, storage_dir: Path | str = Path(".progress")):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def _get_progress_file(self, operation_id: str) -> Path:
        """Get progress file path for operation."""
        return self.storage_dir / f"{operation_id}.json"

    async def save_progress(self, operation_id: str, progress: ProgressInfo) -> None:
        """Save progress to JSON file."""
        try:
            progress_file = self._get_progress_file(operation_id)
            progress_data = progress.model_dump(mode="json")

            async with aiofiles.open(progress_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(progress_data, indent=2, default=str))
        except Exception as e:
            raise ProgressError(f"Failed to save progress: {e}") from e

    async def load_progress(self, operation_id: str) -> ProgressInfo | None:
        """Load progress from JSON file."""
        try:
            progress_file = self._get_progress_file(operation_id)
            if not progress_file.exists():
                return None

            async with aiofiles.open(progress_file, "r", encoding="utf-8") as f:
                content = await f.read()
                progress_data = json.loads(content)
                return ProgressInfo.model_validate(progress_data)
        except Exception as e:
            raise ProgressError(f"Failed to load progress: {e}") from e

    async def delete_progress(self, operation_id: str) -> None:
        """Delete progress file."""
        try:
            progress_file = self._get_progress_file(operation_id)
            if progress_file.exists():
                progress_file.unlink()
        except Exception as e:
            raise ProgressError(f"Failed to delete progress: {e}") from e

    async def list_operations(self) -> list[str]:
        """List all operation IDs."""
        try:
            return [f.stem for f in self.storage_dir.glob("*.json") if f.is_file()]
        except Exception as e:
            raise ProgressError(f"Failed to list operations: {e}") from e


class CheckpointData(DotMacBaseModel):
    """Checkpoint data for resumable operations."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    operation_id: str = Field(description="Operation identifier")
    checkpoint_id: str = Field(description="Checkpoint identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    position: int = Field(0, description="Current position in stream/file")
    batch_number: int = Field(0, description="Current batch number")
    processed_records: int = Field(0, description="Records processed so far")
    metadata: dict[str, Any] = Field(default_factory=dict)
    state_data: bytes = Field(description="Serialized state data")


class CheckpointStore:
    """Storage for operation checkpoints."""

    def __init__(self, storage_dir: Path | str = Path(".checkpoints")):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def _get_checkpoint_file(self, operation_id: str, checkpoint_id: str) -> Path:
        """Get checkpoint file path."""
        return self.storage_dir / f"{operation_id}_{checkpoint_id}.checkpoint"

    async def save_checkpoint(
        self,
        operation_id: str,
        checkpoint_id: str,
        position: int,
        batch_number: int,
        processed_records: int,
        state: Any,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Save checkpoint data."""
        try:
            # Serialize state data
            state_data = pickle.dumps(state)

            checkpoint = CheckpointData(
                operation_id=operation_id,
                checkpoint_id=checkpoint_id,
                position=position,
                batch_number=batch_number,
                processed_records=processed_records,
                metadata=metadata or {},
                state_data=state_data,
            )

            checkpoint_file = self._get_checkpoint_file(operation_id, checkpoint_id)
            checkpoint_json = checkpoint.model_dump_json(indent=2)

            async with aiofiles.open(checkpoint_file, "w", encoding="utf-8") as f:
                await f.write(checkpoint_json)
        except Exception as e:
            raise ProgressError(f"Failed to save checkpoint: {e}") from e

    async def load_checkpoint(
        self, operation_id: str, checkpoint_id: str
    ) -> tuple[int, int, int, Any, dict[str, Any]] | None:
        """Load checkpoint data."""
        try:
            checkpoint_file = self._get_checkpoint_file(operation_id, checkpoint_id)
            if not checkpoint_file.exists():
                return None

            async with aiofiles.open(checkpoint_file, "r", encoding="utf-8") as f:
                content = await f.read()
                checkpoint_data = json.loads(content)
                checkpoint = CheckpointData.model_validate(checkpoint_data)

                # Deserialize state data
                state = pickle.loads(checkpoint.state_data)

                return (
                    checkpoint.position,
                    checkpoint.batch_number,
                    checkpoint.processed_records,
                    state,
                    checkpoint.metadata,
                )
        except Exception as e:
            raise ProgressError(f"Failed to load checkpoint: {e}") from e

    async def delete_checkpoint(self, operation_id: str, checkpoint_id: str) -> None:
        """Delete checkpoint."""
        try:
            checkpoint_file = self._get_checkpoint_file(operation_id, checkpoint_id)
            if checkpoint_file.exists():
                checkpoint_file.unlink()
        except Exception as e:
            raise ProgressError(f"Failed to delete checkpoint: {e}") from e

    async def list_checkpoints(self, operation_id: str) -> list[str]:
        """List checkpoints for an operation."""
        try:
            pattern = f"{operation_id}_*.checkpoint"
            return [f.stem.split("_", 1)[1] for f in self.storage_dir.glob(pattern) if f.is_file()]
        except Exception as e:
            raise ProgressError(f"Failed to list checkpoints: {e}") from e


class ProgressTracker:
    """Progress tracking with persistence and resumability."""

    def __init__(
        self,
        operation_id: str,
        progress_store: ProgressStore | None = None,
        checkpoint_store: CheckpointStore | None = None,
        auto_save_interval: int = 10,
        checkpoint_interval: int = 100,
    ):
        self.operation_id = operation_id
        self.progress_store = progress_store or FileProgressStore()
        self.checkpoint_store = checkpoint_store or CheckpointStore()
        self.auto_save_interval = auto_save_interval
        self.checkpoint_interval = checkpoint_interval

        self._progress = ProgressInfo(operation_id=operation_id)
        self._last_save = datetime.now(UTC)
        self._update_count = 0
        self._callbacks: list[Callable[[ProgressInfo], None]] = []

    @property
    def progress(self) -> ProgressInfo:
        """Get current progress."""
        return self._progress

    def add_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """Add progress callback."""
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[ProgressInfo], None]) -> None:
        """Remove progress callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    async def initialize(
        self, total_records: int | None = None, total_bytes: int | None = None
    ) -> None:
        """Initialize progress tracking."""
        self._progress.total_records = total_records
        self._progress.bytes_total = total_bytes
        self._progress.status = TransferStatus.RUNNING
        self._progress.start_time = datetime.now(UTC)
        await self._save_progress()

    async def update(
        self,
        processed_records: int | None = None,
        failed_records: int | None = None,
        bytes_processed: int | None = None,
        current_batch: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Update progress information."""
        if processed_records is not None:
            self._progress.processed_records = processed_records

        if failed_records is not None:
            self._progress.failed_records = failed_records

        if bytes_processed is not None:
            self._progress.bytes_processed = bytes_processed

        if current_batch is not None:
            self._progress.current_batch = current_batch

        # Update additional fields
        for key, value in kwargs.items():
            if hasattr(self._progress, key):
                setattr(self._progress, key, value)

        self._progress.last_update = datetime.now(UTC)
        self._update_count += 1

        # Auto-save progress
        if self._update_count % self.auto_save_interval == 0:
            await self._save_progress()

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(self._progress)
            except Exception:
                # Don't let callback errors interrupt processing
                pass

    async def complete(self) -> None:
        """Mark operation as completed."""
        self._progress.status = TransferStatus.COMPLETED
        self._progress.last_update = datetime.now(UTC)
        await self._save_progress()

    async def fail(self, error_message: str) -> None:
        """Mark operation as failed."""
        self._progress.status = TransferStatus.FAILED
        self._progress.error_message = error_message
        self._progress.last_update = datetime.now(UTC)
        await self._save_progress()

    async def pause(self) -> None:
        """Pause the operation."""
        self._progress.status = TransferStatus.PAUSED
        self._progress.last_update = datetime.now(UTC)
        await self._save_progress()

    async def resume(self) -> None:
        """Resume the operation."""
        self._progress.status = TransferStatus.RUNNING
        self._progress.last_update = datetime.now(UTC)
        await self._save_progress()

    async def cancel(self) -> None:
        """Cancel the operation."""
        self._progress.status = TransferStatus.CANCELLED
        self._progress.last_update = datetime.now(UTC)
        await self._save_progress()

    async def create_checkpoint(
        self, checkpoint_id: str, position: int, state: Any, metadata: dict[str, Any] | None = None
    ) -> None:
        """Create a checkpoint."""
        await self.checkpoint_store.save_checkpoint(
            self.operation_id,
            checkpoint_id,
            position,
            self._progress.current_batch,
            self._progress.processed_records,
            state,
            metadata,
        )

    async def load_checkpoint(
        self, checkpoint_id: str
    ) -> tuple[int, int, int, Any, dict[str, Any]] | None:
        """Load a checkpoint."""
        return await self.checkpoint_store.load_checkpoint(self.operation_id, checkpoint_id)

    async def restore_from_latest_checkpoint(self) -> bool:
        """Restore from the most recent checkpoint."""
        try:
            # Load existing progress
            saved_progress = await self.progress_store.load_progress(self.operation_id)
            if saved_progress:
                self._progress = saved_progress

            # Find latest checkpoint
            checkpoints = await self.checkpoint_store.list_checkpoints(self.operation_id)
            if not checkpoints:
                return False

            # Load the most recent checkpoint
            latest_checkpoint = max(checkpoints)
            checkpoint_data = await self.load_checkpoint(latest_checkpoint)

            if checkpoint_data:
                position, batch_number, processed_records, state, metadata = checkpoint_data

                # Restore progress state
                self._progress.current_batch = batch_number
                self._progress.processed_records = processed_records
                self._progress.status = TransferStatus.RUNNING

                return True

            return False
        except Exception as e:
            raise ProgressError(f"Failed to restore from checkpoint: {e}") from e

    async def cleanup(self) -> None:
        """Clean up progress and checkpoint data."""
        try:
            await self.progress_store.delete_progress(self.operation_id)

            checkpoints = await self.checkpoint_store.list_checkpoints(self.operation_id)
            for checkpoint_id in checkpoints:
                await self.checkpoint_store.delete_checkpoint(self.operation_id, checkpoint_id)
        except Exception as e:
            raise ProgressError(f"Failed to cleanup progress data: {e}") from e

    async def _save_progress(self) -> None:
        """Save progress to storage."""
        try:
            await self.progress_store.save_progress(self.operation_id, self._progress)
            self._last_save = datetime.now(UTC)
        except Exception as e:
            raise ProgressError(f"Failed to save progress: {e}") from e


class ResumableOperation(ABC):
    """Base class for resumable operations."""

    def __init__(self, operation_id: str, tracker: ProgressTracker | None = None):
        self.operation_id = operation_id
        self.tracker = tracker or ProgressTracker(operation_id)
        self._paused = False
        self._cancelled = False

    async def start(self, **kwargs: Any) -> Any:
        """Start the operation."""
        try:
            # Try to restore from checkpoint
            restored = await self.tracker.restore_from_latest_checkpoint()

            if restored:
                result = await self._resume_operation(**kwargs)
            else:
                result = await self._start_new_operation(**kwargs)

            await self.tracker.complete()
            return result
        except Exception as e:
            await self.tracker.fail(str(e))
            raise

    async def pause(self) -> None:
        """Pause the operation."""
        self._paused = True
        await self.tracker.pause()

    async def resume(self) -> None:
        """Resume the operation."""
        self._paused = False
        await self.tracker.resume()

    async def cancel(self) -> None:
        """Cancel the operation."""
        self._cancelled = True
        await self.tracker.cancel()

    def is_paused(self) -> bool:
        """Check if operation is paused."""
        return self._paused

    def is_cancelled(self) -> bool:
        """Check if operation is cancelled."""
        return self._cancelled

    @abstractmethod
    async def _start_new_operation(self, **kwargs: Any) -> Any:
        """Start a new operation (override in subclasses)."""
        ...

    async def _resume_operation(self, **kwargs: Any) -> Any:
        """Resume an existing operation (override in subclasses)."""
        # Default implementation restarts the operation
        return await self._start_new_operation(**kwargs)


# Utility functions


def create_progress_tracker(
    operation_id: str,
    storage_dir: Path | str | None = None,
    auto_save_interval: int = 10,
    checkpoint_interval: int = 100,
) -> ProgressTracker:
    """Create a progress tracker with file-based storage."""
    progress_store = FileProgressStore(storage_dir or Path(".progress"))
    checkpoint_store = CheckpointStore(storage_dir or Path(".checkpoints"))

    return ProgressTracker(
        operation_id=operation_id,
        progress_store=progress_store,
        checkpoint_store=checkpoint_store,
        auto_save_interval=auto_save_interval,
        checkpoint_interval=checkpoint_interval,
    )


async def cleanup_old_operations(
    storage_dir: Path | str = Path(".progress"), max_age_days: int = 7
) -> None:
    """Clean up old operation progress data."""
    try:
        progress_store = FileProgressStore(storage_dir)
        checkpoint_store = CheckpointStore(storage_dir)

        cutoff_date = datetime.now(UTC) - timedelta(days=max_age_days)
        operations = await progress_store.list_operations()

        for operation_id in operations:
            progress = await progress_store.load_progress(operation_id)
            if progress and progress.last_update < cutoff_date:
                await progress_store.delete_progress(operation_id)

                # Clean up associated checkpoints
                checkpoints = await checkpoint_store.list_checkpoints(operation_id)
                for checkpoint_id in checkpoints:
                    await checkpoint_store.delete_checkpoint(operation_id, checkpoint_id)
    except Exception as e:
        raise ProgressError(f"Failed to cleanup old operations: {e}") from e
