<div align="center">

<img src="https://cdn.prod.website-files.com/69082c5061a39922df8ed3b6/6a431485f177ac4d53309ce4_80c5cb27-f39b-41ff-b1ac-390870fc2a31_1920x1080.jpg" alt="Ava banner" width="100%" />

# Ava

**A many-agent simulation framework for studying emergent civilization-level
behavior in populations of cognitive agents.**

[![CI](https://github.com/TianhangZhuzth/Fundamental-Ava/actions/workflows/ci.yml/badge.svg)](https://github.com/TianhangZhuzth/Fundamental-Ava/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-261230)](https://github.com/astral-sh/ruff)

<img src="https://cdn.prod.website-files.com/69082c5061a39922df8ed3b6/6a4314953f719d29690f224f_fundamental.png" alt="Fundamental Research Labs" width="64" height="64" style="border-radius:50%" />

Built on research from [Fundamental Research Labs](https://fundamentalresearchlabs.com/) · [@Fundamental](https://x.com/Fundamental)

</div>

---

## What this is

`Ava` runs large populations of autonomous agents — each with its
own memory, belief system, and social model — inside a shared environment
and asks a simple question: **what happens at the population level that
nobody programmed in directly?**

Individual agents are deliberately simple: a perceive-deliberate-act loop,
a tiered memory store, and a goal-weighted decision procedure. None of
them are told to specialize into roles, form alliances, write laws, or
develop shared norms. Those are civilization-level properties this
framework is built to detect and measure as they emerge from thousands of
local interactions — the same phenomenon documented in Stanford's
generative agents work and AI Digital Human Group's Project SID research
into thousand-agent societies.

```python
import asyncio

from ava import Civilization, SimulationConfig
from ava.agents.base import Action, AgentCore


class Settler(AgentCore):
    async def deliberate(self, percepts, world_state):
        return Action(kind="forage", payload={"energy_cost": 1.0})


async def main() -> None:
    civ = Civilization(SimulationConfig(max_ticks=200))
    for i in range(500):
        civ.add_agent(Settler(name=f"settler-{i}", bus=civ.bus))

    reports = await civ.run()
    print(f"ran {len(reports)} ticks, final population {reports[-1].population}")


asyncio.run(main())
```

## Interface preview

A reference dashboard for inspecting a running civilization in real time —
shown here with **Ava**, one of the cognitive agents, surfaced alongside
her current state, memory, and relationships:

<div align="center">
<img src="https://cdn.prod.website-files.com/69082c5061a39922df8ed3b6/6a43169ce388becc2732c739_fundamental%20(1).png" alt="Agent inspector UI showing agent Ava" width="100%" />
</div>

The simulation engine itself is headless; this view is built on top of
`SimulationTracer` and `Civilization.population_snapshot()` to render live
agent state without coupling the core library to any particular frontend.

## Why it's built this way

Most multi-agent demos top out at a handful of agents because the
scheduler, memory system, or message bus wasn't designed for scale.
`Ava` makes three architectural bets up front:

1. **Concurrency is structural, not bolted on.** Every tick runs through
   `asyncio.TaskGroup` with a bounded `asyncio.Semaphore`, so a population
   of agents steps in parallel without one slow agent blocking the tick,
   and one agent's unhandled exception can't silently corrupt the rest of
   the run.
2. **Memory is tiered, not a flat log.** Episodic, semantic, and
   procedural memory are separate stores with different retrieval and
   decay semantics — recent events fade, important events persist,
   reusable skills get reinforced independently of any single episode.
3. **Emergence is measured statistically, not eyeballed.** The analysis
   layer runs change-point detection (Mann-Whitney U over a rolling
   window) against population metrics like specialization and wealth
   distribution, so a claim like "agents formed distinct roles" is backed
   by a p-value, not a hunch.
