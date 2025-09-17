import pytest

from dotmac.platform.core.result import Result, try_async_result, try_result


@pytest.mark.unit
def test_result_success_and_failure_basics():
    r_ok = Result.success(42)
    assert r_ok.is_success and not r_ok.is_failure
    assert r_ok.value == 42 and r_ok.error is None
    assert bool(r_ok)
    assert r_ok.unwrap() == 42
    assert r_ok.unwrap_or(0) == 42
    assert r_ok.unwrap_or_else(lambda e: -1) == 42
    assert r_ok.to_dict()["success"] is True
    assert "Result.success" in repr(r_ok)

    r_err = Result.failure("boom")
    assert r_err.is_failure and not r_err.is_success
    assert r_err.value is None and r_err.error is not None
    assert not bool(r_err)
    with pytest.raises(Exception):
        r_err.unwrap()
    assert r_err.unwrap_or(7) == 7
    assert r_err.unwrap_or_else(lambda e: 9) == 9
    d = r_err.to_dict()
    assert d["success"] is False and "boom" in d["error"]
    assert "Result.failure" in repr(r_err)


@pytest.mark.unit
def test_result_combinators():
    r = Result.success(3)
    r2 = r.map(lambda x: x + 1)
    assert r2.is_success and r2.unwrap() == 4

    # map catching exceptions -> failure
    r3 = r.map(lambda _: 1 / 0)
    assert r3.is_failure

    # map_error changes error
    r_err = Result.failure(ValueError("bad"))
    r_err2 = r_err.map_error(lambda e: RuntimeError(f"wrap: {e}"))
    assert r_err2.is_failure and isinstance(r_err2.error, RuntimeError)

    # and_then chains
    def next_step(x: int) -> Result[int]:
        return Result.success(x * 2)

    r4 = r.and_then(next_step)
    assert r4.is_success and r4.unwrap() == 6

    def bad_step(_: int) -> Result[int]:
        raise RuntimeError("oops")

    r5 = r.and_then(bad_step)
    assert r5.is_failure

    # or_else recovers
    def recover(_: Exception) -> Result[int]:
        return Result.success(10)

    r6 = r_err.or_else(recover)
    assert r6.is_success and r6.unwrap() == 10


@pytest.mark.unit
def test_try_result_decorator_sync():
    @try_result
    def ok(x: int) -> int:
        return x + 1

    @try_result
    def bad(_: int) -> int:
        raise ValueError("nope")

    assert ok(1).unwrap() == 2
    res = bad(1)
    assert res.is_failure and isinstance(res.error, ValueError)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_try_async_result_wrapper():
    async def good():
        return 5

    async def bad():
        raise RuntimeError("fail")

    r1 = await try_async_result(good())
    assert r1.is_success and r1.unwrap() == 5

    r2 = await try_async_result(bad())
    assert r2.is_failure and isinstance(r2.error, RuntimeError)
