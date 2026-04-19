"""Tiered memory subsystem: episodic, semantic, and procedural stores.

Modeled loosely on the generative-agent memory stream (Park et al.) but
extended with a procedural layer so agents can accumulate reusable skills
rather than re-deriving the same plans every tick. Retrieval blends
recency, importance, and relevance, matching the scoring approach used in
most long-horizon agent memory designs.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class EpisodicEvent:
    event_type: str
    content: dict[str, Any]
    tick: int
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.0
    embedding: np.ndarray[Any, Any] | None = None
    last_accessed: float = field(default_factory=time.time)


class EpisodicMemory:
    """Append-only stream of timestamped events with recency/importance/
    relevance retrieval, scored the way reflective generative agents do."""

    def __init__(self, *, decay: float = 0.995, capacity: int = 5_000) -> None:
        self.decay = decay
        self.capacity = capacity
        self._events: list[EpisodicEvent] = []

    def record(
        self,
        *,
        event_type: str,
        content: dict[str, Any],
        tick: int,
        importance: float | None = None,
        embedding: np.ndarray[Any, Any] | None = None,
    ) -> EpisodicEvent:
        event = EpisodicEvent(
            event_type=event_type,
            content=content,
            tick=tick,
            importance=importance if importance is not None else self._score_importance(content),
            embedding=embedding,
        )
        self._events.append(event)
        if len(self._events) > self.capacity:
            self._evict()
        return event

    def _score_importance(self, content: dict[str, Any]) -> float:
