"""Provider-agnostic LLM abstraction used by cognitive agents.

Real deployments back this with a hosted model behind `httpx.AsyncClient`;
`MockBackend` exists so the rest of the simulation (and the test suite) can
run deterministically without network access or API keys. Every backend
goes through `RateLimitedBackend` in production to keep many-agent runs
from overwhelming provider rate limits when thousands of agents request
completions in the same tick.
"""

from __future__ import annotations

import abc
import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from typing import Any

import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

log = structlog.get_logger(__name__)


class LLMTransientError(RuntimeError):
    """Retryable failure: rate limit, timeout, 5xx."""


@dataclass(slots=True)
class LLMRequest:
    prompt: str
    system: str | None = None
    max_tokens: int = 512
    temperature: float = 0.7
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    latency_seconds: float
    cached: bool = False


class LLMBackend(abc.ABC):
    """Common interface every model backend implements."""

    @abc.abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError


class MockBackend(LLMBackend):
    """Deterministic, network-free backend for tests and offline runs.

    Produces a stable pseudo-response derived from a hash of the prompt so
