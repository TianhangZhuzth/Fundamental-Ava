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
    assert report.actions_taken == 10
    assert civ.tick == 1


@pytest.mark.asyncio
async def test_civilization_run_produces_history() -> None:
    bus = MessageBus()
    civ = Civilization(SimulationConfig(max_ticks=3), bus=bus)
    civ.add_agent(EchoAgent(name="solo", bus=bus))

    reports = await civ.run()
    assert len(reports) == 3
    assert civ.history()[-1].tick == 3


def test_culture_establishes_norm_above_threshold() -> None:
    from ava.agents.base import Action

    culture = CulturalTransmission(adoption_threshold=0.3, window=10)
    actions = [Action(kind="share_food", payload={}) for _ in range(8)] + [
        Action(kind="hoard_food", payload={}) for _ in range(2)
    ]
    new_norms = culture.observe_actions(actions, tick=1)
    assert new_norms == 2
    norm = culture.query("share_food")
    assert norm is not None
    assert norm.established


def test_governance_ratifies_with_majority_and_quorum() -> None:
    gov = GovernanceSystem(ratification_margin=0.5, min_quorum=3)
    proposal = gov.propose(text="share water equally", proposer_id="a", tick=1)
    for voter in ("a", "b", "c"):
        gov.cast_vote(proposal.id, voter, support=True)
    gov.cast_vote(proposal.id, "d", support=False)

    ratified = gov.evaluate_proposals(tick=2)
    assert ratified == 1
    assert len(gov.active_laws()) == 1


def test_governance_rejects_without_majority() -> None:
    gov = GovernanceSystem(ratification_margin=0.6, min_quorum=2)
    proposal = gov.propose(text="ban trading", proposer_id="a", tick=1)
    gov.cast_vote(proposal.id, "a", support=True)
    gov.cast_vote(proposal.id, "b", support=False)

    ratified = gov.evaluate_proposals(tick=2)
    assert ratified == 0
    assert len(gov.active_laws()) == 0
