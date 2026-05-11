from __future__ import annotations

import pytest

from ava.communication.consensus import (
    ConsensusError,
    Phase,
    Proposal,
    RaftLikeConsensus,
    max_faulty,
    quorum_size,
)
from ava.communication.protocol import Message, MessageBus, MessageType


@pytest.mark.asyncio
async def test_direct_message_delivered_to_recipient(bus: MessageBus) -> None:
    received: list[Message] = []

    async def handler(message: Message) -> None:
        received.append(message)

    bus.subscribe("agent-b", handler)
    count = await bus.publish(
        Message(sender_id="agent-a", recipient_id="agent-b", body={"hi": True})
    )
    assert count == 1
    assert received[0].body == {"hi": True}


@pytest.mark.asyncio
async def test_broadcast_excludes_sender(bus: MessageBus) -> None:
    received_ids: list[str] = []

    for agent_id in ("a", "b", "c"):
        async def handler(message: Message, _id: str = agent_id) -> None:
            received_ids.append(_id)

        bus.subscribe(agent_id, handler)

    count = await bus.publish(
        Message(sender_id="a", body={}, type=MessageType.BROADCAST)
    )
    assert count == 2
    assert "a" not in received_ids


def test_quorum_math_matches_pbft_bound() -> None:
    assert max_faulty(4) == 1
    assert quorum_size(4) == 3
    assert max_faulty(7) == 2
    assert quorum_size(7) == 5


@pytest.mark.asyncio
async def test_consensus_commits_with_sufficient_votes() -> None:
    participants = ["a", "b", "c", "d"]
    consensus = RaftLikeConsensus(participants)

    async def all_vote(_proposal: Proposal, _phase: Phase) -> set[str]:
        return {"a", "b", "c"}

    result = await consensus.propose(
        Proposal(id="p1", proposer_id="a", payload={"rule": "share_water"}),
        vote_collector=all_vote,
    )
    assert result == {"rule": "share_water"}
    assert consensus.is_decided("p1")


@pytest.mark.asyncio
async def test_consensus_fails_without_quorum() -> None:
    participants = ["a", "b", "c", "d"]
