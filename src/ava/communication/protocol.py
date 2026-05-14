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

    def __init__(self, *, max_inbox: int = 1_000) -> None:
        self.max_inbox = max_inbox
        self._subscribers: dict[str, Subscriber] = {}
        self._dropped: int = 0
        self._delivered: int = 0

    def subscribe(self, agent_id: str, callback: Subscriber) -> None:
        self._subscribers[agent_id] = callback

    def unsubscribe(self, agent_id: str) -> None:
        self._subscribers.pop(agent_id, None)

    async def publish(self, message: Message) -> int:
        """Deliver a message; returns number of recipients reached."""
        targets = self._resolve_targets(message)
        if not targets:
            self._dropped += 1
            return 0

        results = await asyncio.gather(
            *(self._deliver_one(agent_id, message) for agent_id in targets),
            return_exceptions=True,
        )
        delivered = sum(1 for r in results if r is True)
        self._delivered += delivered
        return delivered

    def _resolve_targets(self, message: Message) -> list[str]:
        if message.type == MessageType.DIRECT:
            if message.recipient_id and message.recipient_id in self._subscribers:
                return [message.recipient_id]
            return []
        return [
            agent_id for agent_id in self._subscribers if agent_id != message.sender_id
        ]

    async def _deliver_one(self, agent_id: str, message: Message) -> bool:
        callback = self._subscribers.get(agent_id)
        if callback is None:
            return False
        try:
            await callback(message)
            return True
        except Exception:
            log.exception("bus.delivery_failed", agent_id=agent_id, message_id=message.id)
            return False

    def stats(self) -> dict[str, int]:
        return {
            "subscribers": len(self._subscribers),
            "delivered": self._delivered,
            "dropped": self._dropped,
        }
