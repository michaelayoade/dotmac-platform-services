"""Task configuration module."""

from pydantic import BaseModel, Field


class TaskConfig(BaseModel):
    """Task queue and worker configuration."""

    # Worker settings
    worker_count: int = Field(4, description="Number of worker processes")
    max_tasks_per_worker: int = Field(100, description="Max tasks per worker before restart")
    task_timeout: int = Field(300, description="Task timeout in seconds")

    # Queue settings
    queue_type: str = Field("redis", description="Queue backend type")
    queue_url: str | None = Field(None, description="Queue backend URL")
    max_retries: int = Field(3, description="Maximum task retry attempts")
    retry_delay: int = Field(60, description="Delay between retries in seconds")

    # Scheduling settings
    enable_scheduler: bool = Field(True, description="Enable task scheduler")
    scheduler_interval: int = Field(60, description="Scheduler check interval in seconds")

    # Dead letter queue
    enable_dlq: bool = Field(True, description="Enable dead letter queue")
    dlq_max_size: int = Field(10000, description="Maximum size of dead letter queue")
