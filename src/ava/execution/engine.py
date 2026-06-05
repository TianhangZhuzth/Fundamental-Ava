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
    ) -> dict[str, Action | None]:
        results: dict[str, Action | None] = {}
        timings: dict[str, float] = {}
        failed = 0
        start = time.perf_counter()

        async def run_one(agent: AgentCore) -> None:
            nonlocal failed
            async with self._semaphore:
                agent_start = time.perf_counter()
                try:
                    action = await asyncio.wait_for(
                        agent.step(world_state), timeout=self.per_agent_timeout
                    )
                    results[agent.id] = action
                except TimeoutError:
                    log.warning("engine.agent_timeout", agent_id=agent.id)
                    results[agent.id] = None
                    failed += 1
                except Exception:
                    log.exception("engine.agent_step_failed", agent_id=agent.id)
                    results[agent.id] = None
                    failed += 1
                finally:
                    timings[agent.id] = time.perf_counter() - agent_start

