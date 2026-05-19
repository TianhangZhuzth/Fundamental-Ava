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

