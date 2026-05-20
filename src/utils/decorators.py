import functools
import logging
import traceback
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def safe_operation(default: Optional[T] = None, log_level: int = logging.ERROR) -> Callable:
    """Decorator that catches exceptions and returns a default value.

    Usage:
        @safe_operation(default=[])
        def get_items():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(log_level, f"{func.__name__} failed: {e}\n{traceback.format_exc()}")
                return default
        return wrapper
    return decorator


def safe_void_operation(log_level: int = logging.ERROR) -> Callable:
    """Decorator for void functions that should not raise.

    Usage:
        @safe_void_operation()
        def save_settings():
            ...
    """
    def decorator(func: Callable[..., None]) -> Callable[..., None]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> None:
            try:
                func(*args, **kwargs)
            except Exception as e:
                logger.log(log_level, f"{func.__name__} failed: {e}\n{traceback.format_exc()}")
        return wrapper
    return decorator


def retry_on_error(max_retries: int = 3, delay: float = 0.1) -> Callable:
    """Decorator that retries a function on failure.

    Usage:
        @retry_on_error(max_retries=3)
        def query_db():
            ...
    """
    import time
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                        logger.warning(f"{func.__name__} attempt {attempt + 1} failed, retrying...")
            raise last_exception
        return wrapper
    return decorator
