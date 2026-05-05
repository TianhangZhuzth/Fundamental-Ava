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
