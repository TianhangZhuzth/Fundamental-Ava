"""Context-manager timer used throughout benchmarks and tracing."""

from __future__ import annotations

import time
from types import TracebackType


class Timer:
