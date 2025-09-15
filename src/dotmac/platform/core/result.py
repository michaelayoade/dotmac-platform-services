"""Result container for functional error handling."""

from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


class Result(Generic[T]):
    """
    Result container for functional error handling.

    Provides a way to handle errors without exceptions,
    similar to Rust's Result or Haskell's Either.
    """

    def __init__(self, value: T | None = None, error: Exception | None = None):
        """
        Initialize Result.

        Either value or error should be provided, not both.

        Args:
            value: Success value
            error: Error if operation failed
        """
        if value is not None and error is not None:
            raise ValueError("Result cannot have both value and error")
        if value is None and error is None:
            raise ValueError("Result must have either value or error")

        self._value = value
        self._error = error

    @classmethod
    def success(cls, value: T) -> "Result[T]":
        """
        Create successful result.

        Args:
            value: Success value

        Returns:
            Result with value
        """
        return cls(value=value)

    @classmethod
    def failure(cls, error: Exception | str) -> "Result[T]":
        """
        Create failed result.

        Args:
            error: Error or error message

        Returns:
            Result with error
        """
        if isinstance(error, str):
            error = Exception(error)
        return cls(error=error)

    @property
    def is_success(self) -> bool:
        """Check if result is successful."""
        return self._error is None

    @property
    def is_failure(self) -> bool:
        """Check if result is failure."""
        return self._error is not None

    @property
    def value(self) -> T | None:
        """Get value (None if failure)."""
        return self._value

    @property
    def error(self) -> Exception | None:
        """Get error (None if success)."""
        return self._error

    def unwrap(self) -> T:
        """
        Get value or raise error.

        Returns:
            Success value

        Raises:
            Exception: If result is failure
        """
        if self._error:
            raise self._error
        return self._value  # type: ignore

    def unwrap_or(self, default: T) -> T:
        """
        Get value or return default.

        Args:
            default: Default value if failure

        Returns:
            Value or default
        """
        if self._error:
            return default
        return self._value  # type: ignore

    def unwrap_or_else(self, func: Callable[[Exception], T]) -> T:
        """
        Get value or compute default from error.

        Args:
            func: Function to compute default from error

        Returns:
            Value or computed default
        """
        if self._error:
            return func(self._error)
        return self._value  # type: ignore

    def map(self, func: Callable[[T], Any]) -> "Result[Any]":
        """
        Map function over success value.

        Args:
            func: Function to apply to value

        Returns:
            New Result with mapped value or same error
        """
        if self._error:
            return Result(error=self._error)
        try:
            return Result.success(func(self._value))  # type: ignore
        except Exception as e:
            return Result.failure(e)

    def map_error(self, func: Callable[[Exception], Exception]) -> "Result[T]":
        """
        Map function over error.

        Args:
            func: Function to apply to error

        Returns:
            New Result with same value or mapped error
        """
        if self._value is not None:
            return Result.success(self._value)
        return Result.failure(func(self._error))  # type: ignore

    def and_then(self, func: Callable[[T], "Result[Any]"]) -> "Result[Any]":
        """
        Chain operations that return Results.

        Args:
            func: Function that returns a Result

        Returns:
            Result from function or propagated error
        """
        if self._error:
            return Result(error=self._error)
        try:
            return func(self._value)  # type: ignore
        except Exception as e:
            return Result.failure(e)

    def or_else(self, func: Callable[[Exception], "Result[T]"]) -> "Result[T]":
        """
        Recover from error with function.

        Args:
            func: Function to recover from error

        Returns:
            Original success or result from recovery function
        """
        if self._value is not None:
            return Result.success(self._value)
        return func(self._error)  # type: ignore

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        if self.is_success:
            return {"success": True, "value": self._value}
        else:
            return {
                "success": False,
                "error": str(self._error),
                "error_type": type(self._error).__name__,
            }

    def __repr__(self) -> str:
        """String representation."""
        if self.is_success:
            return f"Result.success({self._value!r})"
        else:
            return f"Result.failure({self._error!r})"

    def __bool__(self) -> bool:
        """Boolean evaluation (True if success)."""
        return self.is_success


def try_result(func: Callable[..., T]) -> Callable[..., Result[T]]:
    """
    Decorator to wrap function in Result.

    Catches exceptions and returns Result.failure.

    Args:
        func: Function to wrap

    Returns:
        Wrapped function returning Result
    """

    def wrapper(*args, **kwargs) -> Result[T]:
        try:
            return Result.success(func(*args, **kwargs))
        except Exception as e:
            return Result.failure(e)

    return wrapper


async def try_async_result(func: Callable[..., T]) -> Result[T]:
    """
    Wrap async function execution in Result.

    Args:
        func: Async function to execute

    Returns:
        Result with value or error
    """
    try:
        value = await func
        return Result.success(value)
    except Exception as e:
        return Result.failure(e)