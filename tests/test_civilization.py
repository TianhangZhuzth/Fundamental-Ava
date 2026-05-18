from __future__ import annotations

import pytest

from ava.civilization.culture import CulturalTransmission
from ava.civilization.governance import GovernanceSystem
from ava.civilization.simulation import Civilization, SimulationConfig
from ava.communication.protocol import MessageBus
from tests.conftest import EchoAgent


@pytest.mark.asyncio
async def test_civilization_steps_all_agents() -> None:
    bus = MessageBus()
    civ = Civilization(SimulationConfig(max_ticks=5), bus=bus)
    for i in range(10):
        civ.add_agent(EchoAgent(name=f"agent-{i}", bus=bus))

    report = await civ.step()
    assert report.population == 10
