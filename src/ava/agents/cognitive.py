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
