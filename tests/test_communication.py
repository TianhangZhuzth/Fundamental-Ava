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
