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
        self.trust = min(1.0, max(0.0, self.trust))
        self.interaction_count += 1


class TheoryOfMind:
    """Depth-1 model of what another agent believes, intends, and wants.

    Stores per-other-agent estimates that are updated from observed
    actions rather than asserted directly, mirroring how an observer
    would infer intent from behavior alone.
    """

    def __init__(self, *, self_id: str) -> None:
        self.self_id = self_id
        self._models: dict[str, dict[str, float]] = {}

    def infer_intent(self, other_id: str, observed_action: str, *, confidence: float = 0.5) -> None:
        model = self._models.setdefault(other_id, {})
        key = f"intends:{observed_action}"
        prior = model.get(key, 0.0)
        model[key] = prior + confidence * (1.0 - prior)

    def estimate(self, other_id: str, intent: str) -> float:
        return self._models.get(other_id, {}).get(f"intends:{intent}", 0.0)

    def predict_next_action(self, other_id: str) -> str | None:
        model = self._models.get(other_id)
        if not model:
            return None
        best = max(model.items(), key=lambda kv: kv[1])
        return best[0].removeprefix("intends:") if best[1] > 0.3 else None


class SocialModel:
    """Aggregates relationships and theory-of-mind for one agent."""

    def __init__(self, *, self_id: str) -> None:
        self.self_id = self_id
        self.tom = TheoryOfMind(self_id=self_id)
        self._relationships: dict[str, Relationship] = {}

    def relationship_with(self, other_id: str) -> Relationship:
        return self._relationships.setdefault(other_id, Relationship(other_id=other_id))

    def update_from_interaction(
        self, other_id: str, *, action_kind: str, outcome: float
    ) -> Relationship:
        rel = self.relationship_with(other_id)
        rel.record_interaction(outcome=outcome)
        self.tom.infer_intent(other_id, action_kind, confidence=abs(outcome))
        return rel

    def allies(self, *, threshold: float = 0.5) -> list[str]:
        return [
            other_id
            for other_id, rel in self._relationships.items()
            if rel.affinity >= threshold and rel.trust >= threshold
        ]

