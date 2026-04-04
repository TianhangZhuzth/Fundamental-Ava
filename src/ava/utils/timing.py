"""Context-manager timer used throughout benchmarks and tracing."""

from __future__ import annotations

import time
from types import TracebackType


class Timer:
    def __init__(self) -> None:
        self.elapsed_seconds: float = 0.0
        self._start: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.elapsed_seconds = time.perf_counter() - self._start
