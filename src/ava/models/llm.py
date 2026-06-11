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
    repeated runs with the same inputs are reproducible — important for
    regression tests against emergent-behavior benchmarks.
    """

    def __init__(self, *, latency_seconds: float = 0.01) -> None:
        self.latency_seconds = latency_seconds

    async def complete(self, request: LLMRequest) -> LLMResponse:
        await asyncio.sleep(self.latency_seconds)
        digest = hashlib.sha256(request.prompt.encode("utf-8")).hexdigest()[:24]
        text = f"[mock:{digest}] response to: {request.prompt[:64]}"
        return LLMResponse(
            text=text,
            prompt_tokens=len(request.prompt.split()),
            completion_tokens=len(text.split()),
            latency_seconds=self.latency_seconds,
        )


class RateLimitedBackend(LLMBackend):
    """Wraps any backend with a token-bucket limiter and retry policy.

    `requests_per_second` caps sustained throughput; bursts up to
    `burst_size` are absorbed by the bucket so a sudden spike from many
    agents deliberating in the same tick doesn't immediately 429.
    """

    def __init__(
        self,
        backend: LLMBackend,
        *,
        requests_per_second: float = 20.0,
        burst_size: int = 40,
    ) -> None:
        self.backend = backend
        self.rate = requests_per_second
        self.capacity = burst_size
        self._tokens = float(burst_size)
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def _acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last_refill = now

            if self._tokens < 1.0:
                wait_time = (1.0 - self._tokens) / self.rate
