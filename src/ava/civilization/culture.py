"""Norm and meme emergence from aggregate agent behavior.

A `Norm` starts as an informal observation: many agents independently take
the same action under similar conditions. Once adoption crosses a
threshold, `CulturalTransmission` promotes it to an established norm,
which agents can then query when deciding how to behave in ambiguous
situations (social proof bias).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import structlog

from ava.agents.base import Action

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class Norm:
    behavior: str
    adoption_count: int
    first_observed_tick: int
    strength: float = 0.0
    established: bool = False


class CulturalTransmission:
    """Tracks behavior frequency across the population and promotes
    sufficiently common patterns into durable, queryable norms."""
