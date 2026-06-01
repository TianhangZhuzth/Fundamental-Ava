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
