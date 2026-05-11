"""Byzantine-fault-tolerant consensus for collective agent decisions.

When a civilization needs to agree on something binding (a law, a shared
resource allocation, an elected leader) we run a simplified PBFT-style
three-phase vote: PROPOSE -> PREPARE -> COMMIT. The implementation
tolerates up to f faulty/adversarial agents out of n = 3f + 1 participants,
which is the standard BFT bound.
"""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

log = structlog.get_logger(__name__)


class ConsensusError(RuntimeError):
    """Raised when a proposal cannot reach quorum."""


class Phase(Enum):
    PROPOSE = "propose"
    PREPARE = "prepare"
    COMMIT = "commit"


@dataclass(slots=True)
class Proposal:
    id: str
    proposer_id: str
    payload: dict[str, Any]
    round_id: str = field(default_factory=lambda: str(uuid.uuid4()))


VoteCollector = Callable[[Proposal, Phase], Awaitable[set[str]]]


@dataclass(slots=True)
class VoteTally:
    prepare_votes: set[str] = field(default_factory=set)
    commit_votes: set[str] = field(default_factory=set)


def max_faulty(n_participants: int) -> int:
    """Largest f such that n_participants >= 3f + 1."""
    return max(0, (n_participants - 1) // 3)


def quorum_size(n_participants: int) -> int:
    """Minimum votes required: 2f + 1."""
    f = max_faulty(n_participants)
    return 2 * f + 1


class RaftLikeConsensus:
    """Three-phase BFT-style consensus over a fixed agent set.

    Despite the name (kept for familiarity with operators used to Raft
    terminology), the quorum math follows PBFT: commits require 2f+1
    matching votes out of n = 3f+1, tolerating f Byzantine participants
    rather than only crash failures.
    """
