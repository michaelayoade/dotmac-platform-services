import pytest

from dotmac.platform.tasks.decorators import periodic_task, retry, task


@pytest.mark.unit
def test_task_and_periodic_task_metadata_and_execution():
    @task(name="my-task")
    def add(a, b):
        return a + b

    assert getattr(add, "__dotmac_task__", False) is True
    assert getattr(add, "__dotmac_task_name__", "") == "my-task"
    assert add(1, 2) == 3

    @periodic_task(schedule="* * * * *", name="p-task")
    def mul(a, b):
        return a * b

    assert getattr(mul, "__dotmac_task__", False) is True
    assert getattr(mul, "__dotmac_periodic__", False) is True
    assert getattr(mul, "__dotmac_task_name__", "") == "p-task"
    assert getattr(mul, "__dotmac_task_schedule__", "") == "* * * * *"
    assert mul(2, 3) == 6


@pytest.mark.unit
def test_retry_decorator_with_stop_attempts_and_reraise():
    calls = {"n": 0}

    @retry(stop=2)
    def flaky():
        calls["n"] += 1
        raise ValueError("boom")

    with pytest.raises(ValueError):
        flaky()
    # Should have attempted twice
    assert calls["n"] == 2

