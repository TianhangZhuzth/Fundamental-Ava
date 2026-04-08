from __future__ import annotations

import pytest

from ava.agents.base import Action, AgentCore, Percept
from ava.communication.protocol import MessageBus


class EchoAgent(AgentCore):
    """Minimal concrete agent used across the test suite: always emits a
    no-op action so lifecycle and scheduling logic can be exercised
    without depending on any particular cognitive strategy."""

    async def deliberate(
        self, percepts: list[Percept], world_state: dict
    ) -> Action | None:
        return Action(kind="noop", payload={"energy_cost": 1.0})


@pytest.fixture
def bus() -> MessageBus:
    return MessageBus()


@pytest.fixture
def echo_agent(bus: MessageBus) -> EchoAgent:
    return EchoAgent(name="echo", bus=bus)
