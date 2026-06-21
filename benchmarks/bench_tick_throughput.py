"""Throughput benchmark: how many agents can complete one tick within budget.

Run with: python benchmarks/bench_tick_throughput.py --agents 1000 5000 10000
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ava.agents.base import Action, AgentCore, Percept
from ava.civilization.simulation import Civilization, SimulationConfig
from ava.communication.protocol import MessageBus


class BenchAgent(AgentCore):
    async def deliberate(self, percepts: list[Percept], world_state: dict) -> Action | None:
        return Action(kind="noop", payload={"energy_cost": 0.0})


async def run_benchmark(n_agents: int, *, ticks: int = 20) -> dict[str, float]:
    bus = MessageBus()
    civ = Civilization(SimulationConfig(max_ticks=ticks, max_concurrent_agents=512), bus=bus)
    for i in range(n_agents):
