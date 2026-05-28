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

        if not self._recent_actions:
            return 0

        counts = Counter(kind for _, kind in self._recent_actions)
        total = sum(counts.values())
        newly_established = 0

        for behavior, count in counts.items():
            share = count / total
            norm = self._norms.get(behavior)
            if norm is None:
                norm = Norm(behavior=behavior, adoption_count=count, first_observed_tick=tick)
                self._norms[behavior] = norm
            else:
                norm.adoption_count = count
            norm.strength = share

            if not norm.established and share >= self.adoption_threshold:
                norm.established = True
                newly_established += 1
                log.info("culture.norm_established", behavior=behavior, strength=share, tick=tick)

        return newly_established

    def established_norms(self) -> list[Norm]:
        return [n for n in self._norms.values() if n.established]

    def query(self, behavior: str) -> Norm | None:
        return self._norms.get(behavior)

    def social_proof_bonus(self, behavior: str) -> float:
        """Utility bonus an agent should apply when an action matches an
        established norm — used by CognitiveArchitecture goal functions."""
        norm = self._norms.get(behavior)
        if norm is None or not norm.established:
            return 0.0
        return min(1.0, norm.strength)
