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
