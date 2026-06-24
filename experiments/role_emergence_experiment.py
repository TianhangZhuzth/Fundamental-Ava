"""Experiment: do agents with simple local utility functions self-sort
into distinct roles without being assigned one?

Each agent picks between {forage, build, guard} weighted by its own
accumulated skill success rate and the current population's established
norms. We track the specialization_index over time and look for a
significant jump, which would indicate role emergence rather than
agents continuing to act as generalists.
"""

from __future__ import annotations

import asyncio
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ava.agents.base import Action, AgentCore, Percept
from ava.analysis.emergence import EmergenceDetector, specialization_index
from ava.civilization.simulation import Civilization, SimulationConfig
from ava.communication.protocol import MessageBus

ROLES = ("forage", "build", "guard")


class RoleSeekingAgent(AgentCore):
    """Chooses actions via a simple reinforcement rule: actions that
    succeeded recently become more likely, which is enough pressure for
    specialization to emerge without any explicit role assignment."""

    def __init__(self, *args, **kwargs) -> None:
