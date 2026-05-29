"""Emergent governance: proposal lifecycle, voting, and law enforcement.

GovernanceSystem does not decide what is good policy — it provides the
substrate (propose, vote via RaftLikeConsensus-compatible tallies, ratify,
enforce, repeal) that lets a population of agents arrive at binding rules
on their own, which is the mechanism Project SID-style simulations use to
study governance emergence rather than scripting it directly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum

import structlog

log = structlog.get_logger(__name__)


class ProposalStatus(Enum):
    PENDING = "pending"
    RATIFIED = "ratified"
    REJECTED = "rejected"
    REPEALED = "repealed"


@dataclass(slots=True)
class Law:
    id: str
    text: str
    proposer_id: str
    enacted_tick: int
    votes_for: int
    votes_against: int
    status: ProposalStatus = ProposalStatus.PENDING
    violations: int = 0


@dataclass(slots=True)
class Proposal:
    id: str
    text: str
    proposer_id: str
    created_tick: int
    votes_for: set[str] = field(default_factory=set)
    votes_against: set[str] = field(default_factory=set)


class GovernanceSystem:
    """Manages the proposal -> vote -> ratify -> enforce lifecycle for laws.

    Ratification threshold is a simple majority of votes cast by default,
    but quorum requirements scale with population so a handful of early
    adopters cannot legislate for an entire civilization.
    """

    def __init__(self, *, ratification_margin: float = 0.5, min_quorum: int = 3) -> None:
        self.ratification_margin = ratification_margin
        self.min_quorum = min_quorum
        self._proposals: dict[str, Proposal] = {}
        self._laws: dict[str, Law] = {}

    def propose(self, *, text: str, proposer_id: str, tick: int) -> Proposal:
        proposal = Proposal(
            id=str(uuid.uuid4()), text=text, proposer_id=proposer_id, created_tick=tick
        )
        self._proposals[proposal.id] = proposal
        log.info("governance.proposed", proposal_id=proposal.id, proposer=proposer_id)
        return proposal

    def cast_vote(self, proposal_id: str, voter_id: str, *, support: bool) -> None:
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            return
        proposal.votes_for.discard(voter_id)
        proposal.votes_against.discard(voter_id)
        (proposal.votes_for if support else proposal.votes_against).add(voter_id)

    def evaluate_proposals(self, *, tick: int) -> int:
        """Ratify or reject any pending proposal that has met quorum.

        Returns the number of laws newly ratified this tick.
        """
        ratified = 0
        for proposal in list(self._proposals.values()):
            total_votes = len(proposal.votes_for) + len(proposal.votes_against)
            if total_votes < self.min_quorum:
                continue

            support_share = len(proposal.votes_for) / total_votes
            if support_share >= self.ratification_margin:
                law = Law(
                    id=proposal.id,
                    text=proposal.text,
                    proposer_id=proposal.proposer_id,
                    enacted_tick=tick,
                    votes_for=len(proposal.votes_for),
                    votes_against=len(proposal.votes_against),
                    status=ProposalStatus.RATIFIED,
                )
                self._laws[law.id] = law
                ratified += 1
                log.info("governance.ratified", law_id=law.id, tick=tick, support=support_share)
            else:
                log.info("governance.rejected", proposal_id=proposal.id, support=support_share)

            del self._proposals[proposal.id]

        return ratified

    def active_laws(self) -> list[Law]:
        return [law for law in self._laws.values() if law.status == ProposalStatus.RATIFIED]

    def record_violation(self, law_id: str) -> None:
        law = self._laws.get(law_id)
        if law is not None:
            law.violations += 1

    def repeal(self, law_id: str) -> bool:
        law = self._laws.get(law_id)
