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
