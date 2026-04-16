from __future__ import annotations

from ava.agents.memory import EpisodicMemory, MemoryStore, ProceduralMemory, Skill


def test_episodic_retrieve_orders_by_recency() -> None:
    memory = EpisodicMemory()
    for tick in range(5):
        memory.record(event_type="walk", content={}, tick=tick)

    results = memory.retrieve(query_embedding=None, now_tick=5, top_k=3)
