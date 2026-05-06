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
