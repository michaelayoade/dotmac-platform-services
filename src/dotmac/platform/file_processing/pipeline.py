"""
File Processing Pipeline

Provides chaining of file processors for complex processing workflows.
"""

import asyncio
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Callable, Optional, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..core import BaseModel as DotMacBaseModel, DotMacError
from .base import (
    FileMetadata,
    FileProcessor,
    ProcessingError,
    ProcessingOptions,
    ProcessingResult,
    ProcessingStatus,
)


class PipelineError(ProcessingError):
    """Exception raised during pipeline execution."""


class PipelineStepError(ProcessingError):
    """Exception raised during pipeline step execution."""


class StepMode(str, Enum):
    """Pipeline step execution mode."""

    REQUIRED = "required"  # Step failure fails the entire pipeline
    OPTIONAL = "optional"  # Step failure is logged but pipeline continues
    CONDITIONAL = "conditional"  # Step runs based on condition


class PipelineStepResult(DotMacBaseModel):
    """Result of a pipeline step execution."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    step_name: str = Field(description="Name of the step")
    status: ProcessingStatus = Field(description="Step execution status")
    result: ProcessingResult | None = Field(None, description="Processing result")
    execution_time: float = Field(0.0, description="Execution time in seconds")
    error_message: str | None = Field(None, description="Error message if failed")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @property
    def success(self) -> bool:
        """Check if step was successful."""
        return self.status == ProcessingStatus.COMPLETED


class PipelineConfig(DotMacBaseModel):
    """Configuration for processing pipeline."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    pipeline_name: str = Field(description="Pipeline identifier")
    description: str | None = Field(None, description="Pipeline description")
    fail_fast: bool = Field(True, description="Stop on first failure")
    parallel_execution: bool = Field(False, description="Enable parallel step execution")
    max_workers: int = Field(4, ge=1, le=32, description="Maximum parallel workers")
    timeout_seconds: int = Field(300, ge=1, description="Pipeline timeout in seconds")
    retry_failed_steps: bool = Field(False, description="Retry failed steps")
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    cleanup_on_failure: bool = Field(True, description="Cleanup on pipeline failure")
    preserve_intermediate: bool = Field(False, description="Keep intermediate results")

    @field_validator("pipeline_name")
    @classmethod
    def validate_pipeline_name(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Pipeline name cannot be empty")
        return v.strip()


class PipelineStep:
    """Individual step in a processing pipeline."""

    def __init__(
        self,
        name: str,
        processor: FileProcessor,
        options: ProcessingOptions | None = None,
        mode: StepMode = StepMode.REQUIRED,
        condition: Callable[[FileMetadata], bool] | None = None,
        depends_on: list[str] | None = None,
    ):
        """
        Initialize a pipeline step.

        Args:
            name: Step identifier
            processor: File processor instance
            options: Processing options for this step
            mode: Execution mode (required, optional, conditional)
            condition: Condition function for conditional steps
            depends_on: List of step names this step depends on
        """
        self.name = name
        self.processor = processor
        self.options = options or ProcessingOptions()
        self.mode = mode
        self.condition = condition
        self.depends_on = depends_on or []

    async def can_execute(self, metadata: FileMetadata, completed_steps: set[str]) -> bool:
        """Check if step can be executed based on dependencies and conditions."""
        # Check dependencies
        for dependency in self.depends_on:
            if dependency not in completed_steps:
                return False

        # Check condition for conditional steps
        if self.mode == StepMode.CONDITIONAL and self.condition:
            try:
                return self.condition(metadata)
            except Exception:
                return False

        return True

    async def execute(self, file_path: str) -> PipelineStepResult:
        """Execute the processing step."""
        start_time = datetime.now(UTC)
        step_result = PipelineStepResult(
            step_name=self.name,
            status=ProcessingStatus.PROCESSING,
            result=None,
            execution_time=0.0,
            error_message=None
        )

        try:
            # Validate file can be processed
            can_process = await self.processor.validate(file_path)
            if not can_process:
                raise PipelineStepError(f"File validation failed for step {self.name}")

            # Execute processing
            result = await self.processor.process(file_path, self.options)

            step_result.result = result
            step_result.status = result.status

            if not result.success and self.mode == StepMode.REQUIRED:
                step_result.error_message = (
                    f"Required step {self.name} failed: {'; '.join(result.errors)}"
                )
            elif result.warnings:
                step_result.warnings.extend(result.warnings)

        except Exception as e:
            step_result.status = ProcessingStatus.FAILED
            step_result.error_message = str(e)

        finally:
            end_time = datetime.now(UTC)
            step_result.execution_time = (end_time - start_time).total_seconds()

        return step_result


class PipelineResult(DotMacBaseModel):
    """Result of pipeline execution."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    pipeline_name: str = Field(description="Pipeline identifier")
    status: ProcessingStatus = Field(description="Overall pipeline status")
    original_file: str = Field(description="Original file path")
    step_results: list[PipelineStepResult] = Field(default_factory=list)
    total_execution_time: float = Field(0.0, description="Total execution time")
    processed_files: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if pipeline was successful."""
        return self.status == ProcessingStatus.COMPLETED

    @property
    def completed_steps(self) -> list[PipelineStepResult]:
        """Get successfully completed steps."""
        return [step for step in self.step_results if step.success]

    @property
    def failed_steps(self) -> list[PipelineStepResult]:
        """Get failed steps."""
        return [step for step in self.step_results if step.status == ProcessingStatus.FAILED]

    def get_step_result(self, step_name: str) -> PipelineStepResult | None:
        """Get result for a specific step."""
        for step_result in self.step_results:
            if step_result.step_name == step_name:
                return step_result
        return None

    def add_processed_files(self, files: list[str]) -> None:
        """Add processed files from all steps."""
        self.processed_files.extend(files)

    def collect_all_outputs(self) -> list[str]:
        """Collect all output files from all successful steps."""
        all_files = []
        for step_result in self.completed_steps:
            if step_result.result:
                all_files.extend(step_result.result.processed_files)
                all_files.extend(step_result.result.thumbnails)
        return list(set(all_files))  # Remove duplicates


class ProcessingPipeline:
    """Pipeline for chaining file processing operations."""

    def __init__(self, config: PipelineConfig):
        """Initialize the processing pipeline."""
        self.config = config
        self.steps: list[PipelineStep] = []
        self._step_map: dict[str, PipelineStep] = {}

    def add_step(self, step: PipelineStep) -> "ProcessingPipeline":
        """Add a processing step to the pipeline."""
        if step.name in self._step_map:
            raise PipelineError(f"Step '{step.name}' already exists in pipeline")

        self.steps.append(step)
        self._step_map[step.name] = step
        return self

    def add_processor(
        self,
        name: str,
        processor: FileProcessor,
        options: ProcessingOptions | None = None,
        mode: StepMode = StepMode.REQUIRED,
        condition: Callable[[FileMetadata], bool] | None = None,
        depends_on: list[str] | None = None,
    ) -> "ProcessingPipeline":
        """Add a processor as a pipeline step."""
        step = PipelineStep(
            name=name,
            processor=processor,
            options=options,
            mode=mode,
            condition=condition,
            depends_on=depends_on,
        )
        return self.add_step(step)

    def get_step(self, name: str) -> PipelineStep | None:
        """Get a step by name."""
        return self._step_map.get(name)

    def remove_step(self, name: str) -> bool:
        """Remove a step from the pipeline."""
        if name not in self._step_map:
            return False

        step = self._step_map[name]
        self.steps.remove(step)
        del self._step_map[name]
        return True

    def _validate_dependencies(self) -> None:
        """Validate step dependencies form a valid DAG."""
        visited = set()
        rec_stack = set()

        def has_cycle(step_name: str) -> bool:
            if step_name in rec_stack:
                return True
            if step_name in visited:
                return False

            visited.add(step_name)
            rec_stack.add(step_name)

            step = self._step_map.get(step_name)
            if step:
                for dependency in step.depends_on:
                    if dependency not in self._step_map:
                        raise PipelineError(
                            f"Unknown dependency '{dependency}' for step '{step_name}'"
                        )
                    if has_cycle(dependency):
                        return True

            rec_stack.remove(step_name)
            return False

        for step_name in self._step_map:
            if has_cycle(step_name):
                raise PipelineError("Circular dependency detected in pipeline")

    def _get_execution_order(self) -> list[str]:
        """Get steps in dependency order using topological sort."""
        in_degree = {step.name: 0 for step in self.steps}

        # Calculate in-degrees
        for step in self.steps:
            for dependency in step.depends_on:
                in_degree[step.name] += 1

        # Topological sort
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            step = self._step_map[current]
            for other_step in self.steps:
                if current in other_step.depends_on:
                    in_degree[other_step.name] -= 1
                    if in_degree[other_step.name] == 0:
                        queue.append(other_step.name)

        if len(result) != len(self.steps):
            raise PipelineError("Cannot determine execution order - circular dependencies exist")

        return result

    async def execute(self, file_path: str) -> PipelineResult:
        """Execute the processing pipeline on a file."""
        start_time = datetime.now(UTC)

        result = PipelineResult(
            pipeline_name=self.config.pipeline_name,
            status=ProcessingStatus.PROCESSING,
            original_file=file_path,
            total_execution_time=0.0
        )

        if not self.steps:
            result.status = ProcessingStatus.COMPLETED
            return result

        try:
            # Validate pipeline structure
            self._validate_dependencies()

            # Get file metadata for conditional steps
            from .base import FileMetadata

            metadata = FileMetadata.from_file(file_path)

            # Execute steps in dependency order
            if self.config.parallel_execution:
                await self._execute_parallel(file_path, metadata, result)
            else:
                await self._execute_sequential(file_path, metadata, result)

            # Determine overall status
            if result.failed_steps and self.config.fail_fast:
                result.status = ProcessingStatus.FAILED
                result.errors.append("Pipeline failed due to failed required steps")
            else:
                result.status = ProcessingStatus.COMPLETED

            # Collect all output files
            result.add_processed_files(result.collect_all_outputs())

        except Exception as e:
            result.status = ProcessingStatus.FAILED
            result.errors.append(str(e))

        finally:
            end_time = datetime.now(UTC)
            result.total_execution_time = (end_time - start_time).total_seconds()

        return result

    async def _execute_sequential(
        self,
        file_path: str,
        metadata: FileMetadata,
        result: PipelineResult,
    ) -> None:
        """Execute steps sequentially."""
        execution_order = self._get_execution_order()
        completed_steps: set[str] = set()

        for step_name in execution_order:
            step = self._step_map[step_name]

            # Check if step can execute
            if not await step.can_execute(metadata, completed_steps):
                continue

            # Execute step
            step_result = await step.execute(file_path)
            result.step_results.append(step_result)

            # Handle step result
            if step_result.success:
                completed_steps.add(step_name)
                if step_result.warnings:
                    result.warnings.extend(step_result.warnings)
            else:
                if step.mode == StepMode.REQUIRED and self.config.fail_fast:
                    result.errors.append(
                        step_result.error_message or f"Required step {step_name} failed"
                    )
                    break
                elif step_result.error_message:
                    result.warnings.append(
                        f"Optional step {step_name} failed: {step_result.error_message}"
                    )

    async def _execute_parallel(
        self,
        file_path: str,
        metadata: FileMetadata,
        result: PipelineResult,
    ) -> None:
        """Execute steps in parallel where possible."""
        execution_order = self._get_execution_order()
        completed_steps: set[str] = set()
        semaphore = asyncio.Semaphore(self.config.max_workers)

        async def execute_step_with_semaphore(step: PipelineStep) -> PipelineStepResult:
            async with semaphore:
                return await step.execute(file_path)

        # Group steps by dependency level
        levels: list[list[str]] = []
        remaining_steps = set(execution_order)

        while remaining_steps:
            current_level = []
            for step_name in list(remaining_steps):
                step = self._step_map[step_name]
                if all(dep in completed_steps for dep in step.depends_on):
                    current_level.append(step_name)
                    remaining_steps.remove(step_name)

            if not current_level:
                break  # Should not happen with valid dependencies

            levels.append(current_level)

        # Execute each level in parallel
        for level in levels:
            # Filter steps that can execute
            executable_steps = []
            for step_name in level:
                step = self._step_map[step_name]
                if await step.can_execute(metadata, completed_steps):
                    executable_steps.append(step)

            if not executable_steps:
                continue

            # Execute steps in parallel
            tasks = [execute_step_with_semaphore(step) for step in executable_steps]
            step_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, step_result in enumerate(step_results):
                step = executable_steps[i]

                if isinstance(step_result, Exception):
                    step_result = PipelineStepResult(
                        step_name=step.name,
                        status=ProcessingStatus.FAILED,
                        result=None,
                        execution_time=0.0,
                        error_message=str(step_result),
                    )

                result.step_results.append(step_result)

                if step_result.success:
                    completed_steps.add(step.name)
                    if step_result.warnings:
                        result.warnings.extend(step_result.warnings)
                else:
                    if step.mode == StepMode.REQUIRED and self.config.fail_fast:
                        result.errors.append(
                            step_result.error_message or f"Required step {step.name} failed"
                        )
                        return

    async def validate(self, file_path: str) -> bool:
        """Validate if file can be processed by the pipeline."""
        try:
            self._validate_dependencies()

            # Check if at least one step can process the file
            for step in self.steps:
                if await step.processor.validate(file_path):
                    return True

            return False
        except Exception:
            return False


# Utility functions for pipeline creation


def create_simple_pipeline(
    name: str, processors: list[tuple[str, FileProcessor]]
) -> ProcessingPipeline:
    """Create a simple sequential pipeline from a list of processors."""
    config = PipelineConfig(pipeline_name=name)
    pipeline = ProcessingPipeline(config)

    for step_name, processor in processors:
        pipeline.add_processor(step_name, processor)

    return pipeline


def create_conditional_pipeline(
    name: str, steps: list[tuple[str, FileProcessor, Callable[[FileMetadata], bool]]]
) -> ProcessingPipeline:
    """Create a pipeline with conditional steps."""
    config = PipelineConfig(pipeline_name=name)
    pipeline = ProcessingPipeline(config)

    for step_name, processor, condition in steps:
        pipeline.add_processor(step_name, processor, mode=StepMode.CONDITIONAL, condition=condition)

    return pipeline
