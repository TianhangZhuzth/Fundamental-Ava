"""Theory-of-mind and social relationship modeling.

Each agent maintains a lightweight model of every other agent it has
interacted with: an estimate of that agent's disposition, a trust score,
and a recursive belief about what that agent believes about *them*
(depth-1 theory of mind, which is sufficient to drive emergent cooperation
and reputation dynamics without the combinatorial blowup of deeper
recursion).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Relationship:
    other_id: str
    trust: float = 0.5
    affinity: float = 0.0  # -1 (hostile) .. 1 (allied)
    interaction_count: int = 0
    reputation_estimate: float = 0.5

    def record_interaction(self, *, outcome: float, weight: float = 0.25) -> None:
        """outcome in [-1, 1]: negative for harm, positive for cooperation."""
        self.affinity += weight * (outcome - self.affinity)
        self.affinity = min(1.0, max(-1.0, self.affinity))
        self.trust += weight * ((outcome + 1) / 2 - self.trust)
