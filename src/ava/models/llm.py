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
