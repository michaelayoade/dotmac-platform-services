FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install Poetry and dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY src ./src
COPY alembic.ini ./
COPY alembic ./alembic

# Set Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "dotmac.platform.main:app", "--host", "0.0.0.0", "--port", "8000"]