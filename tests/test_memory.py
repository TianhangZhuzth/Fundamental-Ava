from __future__ import annotations

from ava.agents.memory import EpisodicMemory, MemoryStore, ProceduralMemory, Skill


def test_episodic_retrieve_orders_by_recency() -> None:
    memory = EpisodicMemory()
