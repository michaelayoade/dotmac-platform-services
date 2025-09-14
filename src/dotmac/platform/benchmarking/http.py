"""HTTP benchmarking utilities."""

import asyncio
import time
from typing import Any

import httpx

from .core import BenchmarkResult


async def benchmark_http_request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json_data: dict[str, Any] | None = None,
    iterations: int = 100,
    timeout: float = 30.0,
) -> BenchmarkResult:
    """
    Benchmark HTTP requests.

    Args:
        url: URL to benchmark
        method: HTTP method
        headers: Request headers
        json_data: JSON payload for POST/PUT
        iterations: Number of requests
        timeout: Request timeout

    Returns:
        Benchmark results
    """
    result = BenchmarkResult(f"{method} {url}")

    async with httpx.AsyncClient(timeout=timeout) as client:
        # Warmup
        for _ in range(5):
            try:
                await client.request(
                    method,
                    url,
                    headers=headers,
                    json=json_data,
                )
            except Exception:
                pass

        # Benchmark
        for _ in range(iterations):
            try:
                start = time.perf_counter()
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    json=json_data,
                )
                duration = time.perf_counter() - start

                if response.status_code < 400:
                    result.samples.append(duration)
                else:
                    result.errors += 1

            except Exception:
                result.errors += 1

    return result


async def benchmark_http_batch(
    url: str,
    concurrency: int = 10,
    total_requests: int = 1000,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    json_data: dict[str, Any] | None = None,
    timeout: float = 30.0,
) -> BenchmarkResult:
    """
    Benchmark concurrent HTTP requests.

    Args:
        url: URL to benchmark
        concurrency: Number of concurrent requests
        total_requests: Total requests to make
        method: HTTP method
        headers: Request headers
        json_data: JSON payload
        timeout: Request timeout

    Returns:
        Benchmark results
    """
    result = BenchmarkResult(f"Batch {method} {url} (concurrency={concurrency})")

    async def make_request(client: httpx.AsyncClient) -> float | None:
        """Make single request and return duration."""
        try:
            start = time.perf_counter()
            response = await client.request(
                method,
                url,
                headers=headers,
                json=json_data,
            )
            duration = time.perf_counter() - start

            if response.status_code < 400:
                return duration
            else:
                return None

        except Exception:
            return None

    async with httpx.AsyncClient(
        timeout=timeout,
        limits=httpx.Limits(max_connections=concurrency),
    ) as client:
        # Create tasks in batches
        for batch_start in range(0, total_requests, concurrency):
            batch_size = min(concurrency, total_requests - batch_start)
            tasks = [make_request(client) for _ in range(batch_size)]

            # Execute batch
            results = await asyncio.gather(*tasks)

            # Process results
            for duration in results:
                if duration is not None:
                    result.samples.append(duration)
                else:
                    result.errors += 1

    return result