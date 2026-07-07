"""Logging helpers for service stages."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

import pandas as pd

P = ParamSpec("P")
T = TypeVar("T")


def dataframe_step(name: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Log DataFrame stage timing and row counts."""

    def decorator(function: Callable[P, T]) -> Callable[P, T]:
        @wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            logger = logging.getLogger(function.__module__)
            started_at = time.perf_counter()
            logger.info("%s started", name)
            try:
                result = function(*args, **kwargs)
            except Exception:
                logger.exception("%s failed", name)
                raise

            duration = time.perf_counter() - started_at
            logger.info(
                "%s finished rows=%s duration=%.3fs",
                name,
                _row_count(result),
                duration,
            )
            return result

        return wrapper

    return decorator


def _row_count(value: object) -> int | str:
    """Return a row count for DataFrame-like values."""
    if isinstance(value, pd.DataFrame):
        return len(value)
    return "n/a"
