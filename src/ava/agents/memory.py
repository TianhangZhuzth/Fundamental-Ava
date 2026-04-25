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
        # Heuristic fallback when no LLM-backed scorer is wired in: events
        # touching survival-critical fields are weighted higher.
        weight_keys = {"conflict", "death", "alliance", "discovery", "law"}
        return 8.0 if weight_keys & content.keys() else 2.0

    def _evict(self) -> None:
        self._events.sort(key=lambda e: e.importance)
        self._events = self._events[len(self._events) - self.capacity :]

    def retrieve(
        self,
        *,
        query_embedding: np.ndarray[Any, Any] | None,
        now_tick: int,
        top_k: int = 10,
        recency_weight: float = 1.0,
        importance_weight: float = 1.0,
        relevance_weight: float = 1.0,
    ) -> list[EpisodicEvent]:
        if not self._events:
            return []

        scored: list[tuple[float, EpisodicEvent]] = []
        for event in self._events:
            recency = self.decay ** max(0, now_tick - event.tick)
            relevance = 0.0
            if query_embedding is not None and event.embedding is not None:
                relevance = _cosine_similarity(query_embedding, event.embedding)
            score = (
                recency_weight * recency
                + importance_weight * (event.importance / 10.0)
                + relevance_weight * relevance
            )
            scored.append((score, event))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        top = [event for _, event in scored[:top_k]]
        for event in top:
            event.last_accessed = time.time()
        return top

    def __len__(self) -> int:
        return len(self._events)


@dataclass(slots=True)
class SemanticFact:
    subject: str
    predicate: str
    obj: str
    confidence: float = 1.0
    source_event_ticks: tuple[int, ...] = ()


class SemanticMemory:
    """Distilled facts about the world, derived from episodic reflection."""

    def __init__(self) -> None:
        self._facts: dict[tuple[str, str], SemanticFact] = {}

    def upsert(self, fact: SemanticFact) -> None:
        key = (fact.subject, fact.predicate)
        existing = self._facts.get(key)
        if existing is None or fact.confidence >= existing.confidence:
            self._facts[key] = fact

    def query(
        self, *, subject: str | None = None, predicate: str | None = None
    ) -> list[SemanticFact]:
        results = []
        for (subj, pred), fact in self._facts.items():
            if subject is not None and subj != subject:
                continue
            if predicate is not None and pred != predicate:
                continue
            results.append(fact)
        return results

    def __len__(self) -> int:
        return len(self._facts)


@dataclass(slots=True)
class Skill:
    name: str
    trigger_conditions: dict[str, Any]
    action_sequence: list[dict[str, Any]]
    success_rate: float = 0.5
    uses: int = 0


class ProceduralMemory:
    """Reusable action sequences ("skills") learned from repeated success.

    Skills are reinforced via an exponential moving average over outcomes,
    which lets agents prefer plans that have historically worked without
    discarding a skill after a single bad roll.
    """

    def __init__(self, *, learning_rate: float = 0.2) -> None:
        self.learning_rate = learning_rate
        self._skills: dict[str, Skill] = {}

    def learn(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def reinforce(self, name: str, *, success: bool) -> None:
        skill = self._skills.get(name)
        if skill is None:
            return
        target = 1.0 if success else 0.0
        skill.success_rate += self.learning_rate * (target - skill.success_rate)
        skill.uses += 1

    def best_match(self, world_state: dict[str, Any]) -> Skill | None:
        candidates = [
            skill
            for skill in self._skills.values()
            if all(world_state.get(k) == v for k, v in skill.trigger_conditions.items())
        ]
        if not candidates:
            return None
        return max(candidates, key=lambda s: s.success_rate)

    def __len__(self) -> int:
        return len(self._skills)


class MemoryStore:
    """Aggregate of an agent's episodic, semantic, and procedural memory."""

    def __init__(self, *, owner_id: str) -> None:
        self.owner_id = owner_id
        self.episodic = EpisodicMemory()
        self.semantic = SemanticMemory()
        self.procedural = ProceduralMemory()

    def reflect(self, *, now_tick: int, top_k: int = 20) -> list[SemanticFact]:
        """Distill recent high-importance episodes into semantic facts.

        This is a simplified analogue of the reflection step in generative
        agent architectures: pull the most salient recent events and turn
        repeated co-occurrences into durable facts.
        """
        salient = self.episodic.retrieve(query_embedding=None, now_tick=now_tick, top_k=top_k)
        derived: list[SemanticFact] = []
        for event in salient:
            if event.importance < 6.0:
                continue
            fact = SemanticFact(
                subject=str(event.content.get("actor", self.owner_id)),
                predicate=event.event_type,
                obj=str(event.content.get("target", "world")),
                confidence=min(1.0, event.importance / 10.0),
                source_event_ticks=(event.tick,),
            )
            self.semantic.upsert(fact)
            derived.append(fact)
        return derived


def _cosine_similarity(a: np.ndarray[Any, Any], b: np.ndarray[Any, Any]) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or math.inf
    return float(np.dot(a, b) / denom) if denom != math.inf else 0.0
