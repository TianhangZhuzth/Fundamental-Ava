"""Experiment: do agents with simple local utility functions self-sort
into distinct roles without being assigned one?

Each agent picks between {forage, build, guard} weighted by its own
accumulated skill success rate and the current population's established
norms. We track the specialization_index over time and look for a
significant jump, which would indicate role emergence rather than
agents continuing to act as generalists.
"""

from __future__ import annotations

import asyncio
