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

    def __init__(self, participant_ids: list[str], *, vote_timeout: float = 5.0) -> None:
        self.participant_ids = list(participant_ids)
        self.vote_timeout = vote_timeout
        self.f = max_faulty(len(participant_ids))
        self.quorum = quorum_size(len(participant_ids))
        self._tallies: dict[str, VoteTally] = defaultdict(VoteTally)
        self._decided: dict[str, dict[str, Any]] = {}

    async def propose(
        self,
        proposal: Proposal,
        *,
        vote_collector: VoteCollector,
    ) -> dict[str, Any]:
        """Drive one proposal through PREPARE and COMMIT phases.

        `vote_collector` is an async callable
        `(proposal, phase) -> set[str]` returning the set of participant
        ids that voted yes for that phase, used to decouple the consensus
        state machine from any particular transport.
        """
        if len(self.participant_ids) < 3 * self.f + 1:
            raise ConsensusError("insufficient participants for BFT guarantees")

        prepare_votes = await self._run_phase(proposal, Phase.PREPARE, vote_collector)
        if len(prepare_votes) < self.quorum:
            raise ConsensusError(
                f"proposal {proposal.id} failed PREPARE: {len(prepare_votes)}/{self.quorum}"
            )

        commit_votes = await self._run_phase(proposal, Phase.COMMIT, vote_collector)
        if len(commit_votes) < self.quorum:
            raise ConsensusError(
                f"proposal {proposal.id} failed COMMIT: {len(commit_votes)}/{self.quorum}"
            )

        self._decided[proposal.id] = proposal.payload
        log.info(
            "consensus.committed",
            proposal_id=proposal.id,
            votes=len(commit_votes),
            quorum=self.quorum,
        )
        return proposal.payload

    async def _run_phase(
        self, proposal: Proposal, phase: Phase, vote_collector: VoteCollector
    ) -> set[str]:
        try:
            votes = await asyncio.wait_for(
                vote_collector(proposal, phase), timeout=self.vote_timeout
            )
        except TimeoutError as exc:
            raise ConsensusError(f"phase {phase.value} timed out for {proposal.id}") from exc

        tally = self._tallies[proposal.id]
        if phase == Phase.PREPARE:
            tally.prepare_votes |= votes
        else:
            tally.commit_votes |= votes
        return votes

    def is_decided(self, proposal_id: str) -> bool:
        return proposal_id in self._decided
