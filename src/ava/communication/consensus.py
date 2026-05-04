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
