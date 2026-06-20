"""Benchmark episodic memory retrieval latency as the event store grows.

Run with: python benchmarks/bench_memory_retrieval.py
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ava.agents.memory import EpisodicMemory


