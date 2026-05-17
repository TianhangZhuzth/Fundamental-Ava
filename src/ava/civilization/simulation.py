"""Top-level simulation engine: ties agents, the message bus, execution
scheduler, and emergent civilization-level systems into one tick loop.

Civilization is intentionally thin — it owns no domain logic of its own.
Each tick it: (1) snapshots shared world state, (2) hands every live agent
to the ExecutionEngine for parallel stepping, (3) feeds the resulting
actions into CulturalTransmission and GovernanceSystem so norms and laws
can emerge from aggregate behavior, and (4) records a trace frame.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import structlog
