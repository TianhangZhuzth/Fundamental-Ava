"""Async message bus used for all inter-agent communication.

Every agent subscribes with its id; messages are delivered through
per-recipient asyncio queues so that a slow consumer never blocks the
publisher. Broadcast messages fan out to every subscriber except the
sender. A bounded delivery queue prevents memory blowup if an agent stops
draining its inbox (e.g. while BLOCKED).
"""

from __future__ import annotations

import asyncio
import enum
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

import structlog

log = structlog.get_logger(__name__)

Subscriber = Callable[["Message"], Awaitable[None]]


class MessageType(enum.Enum):
    DIRECT = "direct"
    BROADCAST = "broadcast"
    PROPOSAL = "proposal"
    VOTE = "vote"
    ANNOUNCE = "announce"


@dataclass(slots=True)
class Message:
    sender_id: str
    body: dict[str, Any]
    type: MessageType = MessageType.DIRECT
    recipient_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)


class MessageBus:
    """Pub/sub fabric connecting all agents in a Civilization.

    Delivery is fire-and-forget from the sender's perspective: `publish`
    schedules delivery coroutines and returns immediately, so a burst of
    agent messages within one tick does not serialize on slow subscribers.
    """

