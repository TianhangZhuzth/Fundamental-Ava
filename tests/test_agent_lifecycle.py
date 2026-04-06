from __future__ import annotations

import pytest

from ava.agents.base import AgentState, InvalidTransition
from tests.conftest import EchoAgent


@pytest.mark.asyncio
async def test_agent_starts_idle(echo_agent: EchoAgent) -> None:
    assert echo_agent.state == AgentState.IDLE


@pytest.mark.asyncio
async def test_step_returns_to_idle(echo_agent: EchoAgent) -> None:
    action = await echo_agent.step(world_state={})
    assert action is not None
