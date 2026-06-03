"""Concurrent per-tick execution scheduler.

Stepping a population of agents is embarrassingly parallel — each agent's
`step()` only touches its own state plus a read-only world_state snapshot
and the shared MessageBus, which is itself coroutine-safe. ExecutionEngine
exploits this with a bounded `asyncio.Semaphore` so a tick over thousands
of agents doesn't fan out into thousands of concurrent coroutines at once,
and `asyncio.TaskGroup` so a single agent's unhandled exception doesn't
silently swallow the rest of the tick.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from ava.agents.base import Action, AgentCore

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class TickTimings:
    wall_seconds: float
    agents_run: int
    agents_failed: int
    slowest_agent_id: str | None
    slowest_seconds: float


class ExecutionEngine:
    """Bounded-concurrency scheduler for one simulation tick."""

    def __init__(self, *, max_concurrency: int = 256, per_agent_timeout: float = 1.0) -> None:
        self.max_concurrency = max_concurrency
        self.per_agent_timeout = per_agent_timeout
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self.last_timings: TickTimings | None = None

    async def run_tick(
        self, agents: list[AgentCore], world_state: dict[str, Any]
