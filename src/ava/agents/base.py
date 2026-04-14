"""Core agent lifecycle and state machine.

An AgentCore is the smallest unit of cognition in a Civilization. It owns a
perceive -> deliberate -> act loop, a memory store, and a handle into the
shared MessageBus. Subclasses override `deliberate` to plug in different
cognitive strategies (reactive, planning, social) without touching the
lifecycle machinery.
"""

from __future__ import annotations

import enum
import time
import uuid
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import structlog

from ava.agents.memory import MemoryStore
from ava.communication.protocol import Message, MessageBus

log = structlog.get_logger(__name__)


class AgentState(enum.Enum):
    """Lifecycle states for an agent within a simulation tick."""

    IDLE = "idle"
    PERCEIVING = "perceiving"
    DELIBERATING = "deliberating"
    ACTING = "acting"
    BLOCKED = "blocked"
    TERMINATED = "terminated"


class InvalidTransition(RuntimeError):
    """Raised when an agent attempts an illegal state transition."""


_TRANSITIONS: dict[AgentState, frozenset[AgentState]] = {
    AgentState.IDLE: frozenset({AgentState.PERCEIVING, AgentState.TERMINATED}),
    AgentState.PERCEIVING: frozenset({AgentState.DELIBERATING, AgentState.BLOCKED}),
    AgentState.DELIBERATING: frozenset({AgentState.ACTING, AgentState.BLOCKED}),
    AgentState.ACTING: frozenset({AgentState.IDLE, AgentState.BLOCKED}),
    AgentState.BLOCKED: frozenset({AgentState.IDLE, AgentState.TERMINATED}),
    AgentState.TERMINATED: frozenset(),
}


@dataclass(slots=True)
class Percept:
    """A single unit of sensory input delivered to an agent for one tick."""

    source: str
    payload: dict[str, Any]
    timestamp: float = field(default_factory=time.time)


@dataclass(slots=True)
class Action:
    """An action emitted by an agent's deliberation step."""

    kind: str
    payload: dict[str, Any]
    confidence: float = 1.0


@dataclass(slots=True)
class AgentSnapshot:
    """Point-in-time view of an agent, used for tracing and analysis."""

    agent_id: str
    state: AgentState
    tick: int
    last_action: Action | None
    energy: float


class AgentCore(ABC):
    """Base class for all agents participating in a Civilization.

    Subclasses must implement `deliberate`. Everything else (state
    transitions, memory writes, message dispatch) is handled here so that
    every concrete agent type behaves consistently under the scheduler.
    """

    def __init__(
        self,
        name: str,
        *,
        bus: MessageBus,
        memory: MemoryStore | None = None,
        initial_energy: float = 100.0,
        agent_id: str | None = None,
    ) -> None:
        self.id = agent_id or str(uuid.uuid4())
        self.name = name
        self.bus = bus
        self.memory = memory or MemoryStore(owner_id=self.id)
        self.state = AgentState.IDLE
        self.energy = initial_energy
        self.tick: int = 0
        self.last_action: Action | None = None
        self._on_state_change: list[Callable[[AgentState, AgentState], Awaitable[None]]] = []
        self.bus.subscribe(self.id, self._inbox)
        self._inbox_queue: list[Message] = []

    async def _inbox(self, message: Message) -> None:
        self._inbox_queue.append(message)

    def _transition(self, target: AgentState) -> None:
        allowed = _TRANSITIONS[self.state]
        if target not in allowed:
            raise InvalidTransition(
                f"agent {self.id} cannot move {self.state.value} -> {target.value}"
            )
        previous, self.state = self.state, target
        log.debug("agent.transition", agent_id=self.id, frm=previous.value, to=target.value)

    async def step(self, world_state: dict[str, Any]) -> Action | None:
        """Run one full perceive -> deliberate -> act cycle."""
        if self.state == AgentState.TERMINATED:
            return None

        self.tick += 1
        self._transition(AgentState.PERCEIVING)
        percepts = self._collect_percepts(world_state)

        self._transition(AgentState.DELIBERATING)
        try:
            action = await self.deliberate(percepts, world_state)
        except Exception:
            log.exception("agent.deliberate_failed", agent_id=self.id)
            self._transition(AgentState.BLOCKED)
            self._transition(AgentState.IDLE)
            return None

        self._transition(AgentState.ACTING)
        if action is not None:
            await self._apply_action(action)
        self.last_action = action

        self._transition(AgentState.IDLE)
        return action

    def _collect_percepts(self, world_state: dict[str, Any]) -> list[Percept]:
        percepts = [Percept(source="world", payload=world_state)]
        while self._inbox_queue:
            msg = self._inbox_queue.pop(0)
            percepts.append(Percept(source=f"agent:{msg.sender_id}", payload=msg.body))
        return percepts

    async def _apply_action(self, action: Action) -> None:
        cost = float(action.payload.get("energy_cost", 1.0))
        self.energy = max(0.0, self.energy - cost)
        self.memory.episodic.record(
            event_type=action.kind,
            content=action.payload,
            tick=self.tick,
        )
        if self.energy <= 0.0:
            self._transition(AgentState.BLOCKED)

    @abstractmethod
