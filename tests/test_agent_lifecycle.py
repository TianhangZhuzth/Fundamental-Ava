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
    assert action.kind == "noop"
    assert echo_agent.state == AgentState.IDLE
    assert echo_agent.tick == 1


@pytest.mark.asyncio
async def test_energy_depletes_and_blocks(echo_agent: EchoAgent) -> None:
    echo_agent.energy = 1.0
    await echo_agent.step(world_state={})
    assert echo_agent.energy == 0.0
    assert echo_agent.state == AgentState.BLOCKED


def test_invalid_transition_raises(echo_agent: EchoAgent) -> None:
    with pytest.raises(InvalidTransition):
        echo_agent._transition(AgentState.ACTING)


@pytest.mark.asyncio
