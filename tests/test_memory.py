from __future__ import annotations

from ava.agents.memory import EpisodicMemory, MemoryStore, ProceduralMemory, Skill


def test_episodic_retrieve_orders_by_recency() -> None:
    memory = EpisodicMemory()
    for tick in range(5):
        memory.record(event_type="walk", content={}, tick=tick)

    results = memory.retrieve(query_embedding=None, now_tick=5, top_k=3)
    assert len(results) == 3
    assert results[0].tick == 4


def test_episodic_eviction_respects_capacity() -> None:
    memory = EpisodicMemory(capacity=10)
    for tick in range(50):
        memory.record(event_type="noop", content={}, tick=tick)
    assert len(memory) == 10


def test_importance_scoring_weights_critical_events() -> None:
    memory = EpisodicMemory()
    routine = memory.record(event_type="walk", content={}, tick=0)
    critical = memory.record(event_type="fight", content={"conflict": True}, tick=1)
    assert critical.importance > routine.importance


def test_procedural_memory_reinforcement_converges() -> None:
    procedural = ProceduralMemory(learning_rate=0.5)
    procedural.learn(
        Skill(name="forage", trigger_conditions={"biome": "forest"}, action_sequence=[])
