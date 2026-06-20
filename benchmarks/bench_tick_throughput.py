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


