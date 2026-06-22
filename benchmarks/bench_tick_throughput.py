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
        civ.add_agent(BenchAgent(name=f"agent-{i}", bus=bus))

    durations = []
    for _ in range(ticks):
        report = await civ.step()
        durations.append(report.duration_seconds)

    return {
        "n_agents": n_agents,
        "mean_tick_seconds": statistics.mean(durations),
        "p95_tick_seconds": statistics.quantiles(durations, n=20)[18],
        "agents_per_second": n_agents / statistics.mean(durations),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agents", type=int, nargs="+", default=[100, 1000, 5000])
    parser.add_argument("--ticks", type=int, default=20)
    args = parser.parse_args()

