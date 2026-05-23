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
