"""Benchmark episodic memory retrieval latency as the event store grows.

Run with: python benchmarks/bench_memory_retrieval.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ava.agents.memory import EpisodicMemory


def main() -> None:
    for capacity in (1_000, 5_000, 20_000):
        memory = EpisodicMemory(capacity=capacity)
        for tick in range(capacity):
            memory.record(event_type="action", content={"tick": tick}, tick=tick)

        start = time.perf_counter()
        for _ in range(100):
