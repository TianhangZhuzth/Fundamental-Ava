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

from ava.agents.base import AgentCore
from ava.civilization.culture import CulturalTransmission
from ava.civilization.governance import GovernanceSystem
from ava.communication.protocol import MessageBus
from ava.execution.engine import ExecutionEngine
from ava.execution.tracer import SimulationTracer

log = structlog.get_logger(__name__)


@dataclass(slots=True)
class SimulationConfig:
    max_ticks: int = 1_000
    max_concurrent_agents: int = 256
    tick_budget_seconds: float = 2.0
    enable_culture: bool = True
    enable_governance: bool = True
    seed: int | None = None


@dataclass(slots=True)
class TickReport:
    tick: int
    duration_seconds: float
    actions_taken: int
    population: int
    new_norms: int = 0
    new_laws: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


class Civilization:
    """A population of agents evolving under shared rules over time."""

    def __init__(
        self,
        config: SimulationConfig | None = None,
        *,
        bus: MessageBus | None = None,
    ) -> None:
        self.config = config or SimulationConfig()
        self.bus = bus or MessageBus()
        self.agents: dict[str, AgentCore] = {}
        self.tick: int = 0
        self.world_state: dict[str, Any] = {}

        self.engine = ExecutionEngine(max_concurrency=self.config.max_concurrent_agents)
        self.tracer = SimulationTracer()
        self.culture = CulturalTransmission() if self.config.enable_culture else None
        self.governance = GovernanceSystem() if self.config.enable_governance else None

        self._tick_reports: list[TickReport] = []

    def add_agent(self, agent: AgentCore) -> None:
        self.agents[agent.id] = agent

    def remove_agent(self, agent_id: str) -> None:
        agent = self.agents.pop(agent_id, None)
        if agent is not None:
            agent.terminate()

    async def run(self, *, ticks: int | None = None) -> list[TickReport]:
        target = ticks if ticks is not None else self.config.max_ticks
        reports = []
        for _ in range(target):
            report = await self.step()
            reports.append(report)
            if not self.agents:
                log.info("civilization.population_collapsed", tick=self.tick)
                break
        return reports

    async def step(self) -> TickReport:
        start = time.perf_counter()
        self.tick += 1
        self.world_state["tick"] = self.tick

        results = await self.engine.run_tick(list(self.agents.values()), self.world_state)
        actions = [action for action in results.values() if action is not None]

        new_norms = 0
        if self.culture is not None:
            new_norms = self.culture.observe_actions(actions, tick=self.tick)

        new_laws = 0
        if self.governance is not None:
            new_laws = self.governance.evaluate_proposals(tick=self.tick)

        duration = time.perf_counter() - start
        report = TickReport(
            tick=self.tick,
            duration_seconds=duration,
            actions_taken=len(actions),
            population=len(self.agents),
            new_norms=new_norms,
            new_laws=new_laws,
        )
        self.tracer.record_tick(report.__dict__)
        self._tick_reports.append(report)

