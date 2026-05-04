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
