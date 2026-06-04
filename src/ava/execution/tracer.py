"""Lightweight OpenTelemetry-style tracing for simulation runs.

Full OTel is overkill for a research codebase that needs to run offline
and replay deterministically, so SimulationTracer implements the same
mental model — nested spans with attributes and timing — backed by an
in-memory buffer that can be flushed to JSONL for offline analysis.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class TraceSpan:
    name: str
    span_id: str
    parent_id: str | None
    start_time: float
    end_time: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    @property
    def duration_seconds(self) -> float | None:
        if self.end_time is None:
            return None
        return self.end_time - self.start_time


class SimulationTracer:
    """Collects tick reports and nested spans for offline inspection."""

    def __init__(self) -> None:
        self._ticks: list[dict[str, Any]] = []
        self._spans: list[TraceSpan] = []
        self._active_stack: list[str] = []

    def record_tick(self, report: dict[str, Any]) -> None:
        self._ticks.append(report)

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[TraceSpan]:
        parent_id = self._active_stack[-1] if self._active_stack else None
        span = TraceSpan(
            name=name,
            span_id=str(uuid.uuid4()),
            parent_id=parent_id,
            start_time=time.perf_counter(),
            attributes=dict(attributes),
        )
        self._active_stack.append(span.span_id)
        try:
