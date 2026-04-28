"""Cognitive architecture: belief maintenance and action selection.

`CognitiveArchitecture` wires together a `BeliefSystem` (what the agent
currently holds to be true about the world and other agents) with a
deliberation strategy that produces candidate actions and ranks them by
expected utility under the agent's current beliefs and goals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class Belief:
    statement: str
    confidence: float
    evidence_count: int = 1

    def update(self, *, observed: bool, weight: float = 0.3) -> None:
        target = 1.0 if observed else 0.0
        self.confidence += weight * (target - self.confidence)
        self.confidence = min(1.0, max(0.0, self.confidence))
        self.evidence_count += 1


class BeliefSystem:
    """A bounded set of probabilistic beliefs an agent holds about the world.

    Beliefs decay toward neutral (0.5) over time absent reinforcement,
    which keeps stale assumptions from dominating decisions indefinitely.
    """

    def __init__(self, *, decay_rate: float = 0.01) -> None:
        self.decay_rate = decay_rate
        self._beliefs: dict[str, Belief] = {}

    def assert_belief(self, statement: str, *, confidence: float = 0.5) -> Belief:
        belief = self._beliefs.setdefault(statement, Belief(statement, confidence))
        return belief

    def observe(self, statement: str, *, true: bool) -> Belief:
        belief = self._beliefs.get(statement) or self.assert_belief(statement)
        belief.update(observed=true)
        return belief

    def decay_all(self) -> None:
        for belief in self._beliefs.values():
            belief.confidence += self.decay_rate * (0.5 - belief.confidence)

    def confidence_in(self, statement: str) -> float:
        belief = self._beliefs.get(statement)
        return belief.confidence if belief else 0.5

    def strongest(self, n: int = 5) -> list[Belief]:
        ranked = sorted(self._beliefs.values(), key=lambda b: abs(b.confidence - 0.5), reverse=True)
        return ranked[:n]

    def __len__(self) -> int:
        return len(self._beliefs)


@dataclass(slots=True)
class Goal:
    name: str
    utility_fn: Any  # Callable[[dict[str, Any], BeliefSystem], float]
    priority: float = 1.0


@dataclass(slots=True)
class CandidateAction:
    kind: str
    payload: dict[str, Any]
    expected_utility: float = 0.0


class CognitiveArchitecture:
    """Goal-directed deliberation layered on top of a BeliefSystem.

    Each tick, registered goals score the candidate action set under
    current beliefs; the highest expected-utility action wins, with a
    softmax fallback to avoid agents getting deterministically stuck in
    local optima across long simulations.
    """

    def __init__(self, *, beliefs: BeliefSystem | None = None, temperature: float = 0.15) -> None:
        self.beliefs = beliefs or BeliefSystem()
        self.temperature = temperature
