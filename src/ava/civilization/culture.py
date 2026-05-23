"""Norm and meme emergence from aggregate agent behavior.

A `Norm` starts as an informal observation: many agents independently take
the same action under similar conditions. Once adoption crosses a
threshold, `CulturalTransmission` promotes it to an established norm,
which agents can then query when deciding how to behave in ambiguous
situations (social proof bias).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import structlog

from ava.agents.base import Action

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class Norm:
    behavior: str
    adoption_count: int
    first_observed_tick: int
    strength: float = 0.0
    established: bool = False


class CulturalTransmission:
    """Tracks behavior frequency across the population and promotes
    sufficiently common patterns into durable, queryable norms."""

    def __init__(self, *, adoption_threshold: float = 0.35, window: int = 50) -> None:
        self.adoption_threshold = adoption_threshold
        self.window = window
        self._recent_actions: list[tuple[int, str]] = []
        self._norms: dict[str, Norm] = {}

    def observe_actions(self, actions: list[Action], *, tick: int) -> int:
        for action in actions:
            self._recent_actions.append((tick, action.kind))

        cutoff = tick - self.window
        self._recent_actions = [(t, k) for t, k in self._recent_actions if t >= cutoff]
