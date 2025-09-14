import asyncio
import time

import pytest

from dotmac.platform.tasks.retry import RetryError, calculate_backoff, retry_async, retry_sync


@pytest.mark.unit
def test_calculate_backoff_without_and_with_jitter():
    # No jitter deterministic
    assert calculate_backoff(0, base_delay=1.0, backoff_factor=2.0, jitter=False) == 1.0
    assert calculate_backoff(1, base_delay=1.0, backoff_factor=2.0, jitter=False) == 2.0
    # Cap at max_delay
    assert calculate_backoff(10, base_delay=1.0, backoff_factor=3.0, max_delay=5.0, jitter=False) == 5.0

    # With jitter, ensure within +/-25%
    d = calculate_backoff(2, base_delay=2.0, backoff_factor=2.0, jitter=True)
    expected = 2.0 * (2.0**2)  # 8.0
    assert expected * 0.75 <= d <= expected * 1.25


@pytest.mark.unit
def test_retry_sync_success_after_retries(monkeypatch):
    delays = []
    monkeypatch.setattr(time, "sleep", lambda s: delays.append(s))

    calls = {"n": 0}

    @retry_sync(max_attempts=3, base_delay=0.1, backoff_factor=2.0, jitter=False)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("fail")
        return 42

    assert flaky() == 42
    assert delays == [0.1, 0.2]


@pytest.mark.unit
def test_retry_sync_raises_after_exhaust(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda s: None)

    @retry_sync(max_attempts=2, base_delay=0.1, jitter=False, exceptions=(ValueError,))
    def always_fail():
        raise ValueError("nope")

    with pytest.raises(RetryError) as ei:
        always_fail()
    assert ei.value.attempts == 2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_retry_async_success_and_exhaust(monkeypatch):
    async def _fast_sleep(_):
        return None

    monkeypatch.setattr(asyncio, "sleep", _fast_sleep)

    calls = {"n": 0}

    @retry_async(max_attempts=3, base_delay=0.01, jitter=False)
    async def flaky_async():
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("fail")
        return "ok"

    assert await flaky_async() == "ok"

    @retry_async(max_attempts=2, base_delay=0.01, jitter=False, exceptions=(RuntimeError,))
    async def always_fail_async():
        raise RuntimeError("bad")

    with pytest.raises(RetryError):
        await always_fail_async()
