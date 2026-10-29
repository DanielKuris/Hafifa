
import logging
from collections.abc import Callable
from functools import wraps
from time import perf_counter
from typing import ParamSpec, TypeVar

from src.config.settings import settings

P = ParamSpec("P")
T = TypeVar("T")

logger = logging.getLogger("bottleneck_metrics")
logger.setLevel(logging.INFO)
logger.propagate = False

destination = settings.BOTTLENECK_DATA_FILE
destination.parent.mkdir(parents=True, exist_ok=True)

if destination.exists() and destination.stat().st_size > 0:
    destination.write_text("", encoding="utf-8")

if not logger.handlers:
    handler = logging.FileHandler(destination, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger.addHandler(handler)


def timed[**P, T](func: Callable[P, T]) -> Callable[P, T]:
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start = perf_counter()

        try:
            result = func(*args, **kwargs)
        finally:
            elapsed = perf_counter() - start
            logger.info(f"{func.__qualname__} took {elapsed:.2f} seconds")

        return result

    return wrapper
