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

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Civilization                             │
│  ┌───────────┐   ┌───────────────┐   ┌─────────────────────┐    │
│  │  Culture  │   │  Governance   │   │  EmergenceDetector   │    │
│  │ (norms)   │   │ (laws/votes)  │   │  (analysis layer)    │    │
│  └─────┬─────┘   └───────┬───────┘   └──────────┬───────────┘    │
│        └─────────────────┼──────────────────────┘                │
│                  ┌────────┴─────────┐                             │
│                  │  ExecutionEngine │  TaskGroup + Semaphore       │
│                  └────────┬─────────┘                             │
│        ┌──────────────────┼──────────────────┐                   │
│   ┌────┴────┐        ┌────┴────┐        ┌────┴────┐              │
│   │ Agent 1 │  ...   │ Agent N │  ...   │ Agent M │              │
│   │ ┌─────┐ │        │ ┌─────┐ │        │ ┌─────┐ │              │
│   │ │Memory│ │        │ │Memory│ │        │ │Memory│ │              │
│   │ │Belief│ │        │ │Belief│ │        │ │Belief│ │              │
│   │ │Social│ │        │ │Social│ │        │ │Social│ │              │
│   │ └─────┘ │        │ └─────┘ │        │ └─────┘ │              │
│   └────┬────┘        └────┬────┘        └────┬────┘              │
│        └───────────────────┴──────────────────┘                   │
│                       MessageBus (pub/sub)                        │
└─────────────────────────────────────────────────────────────────┘
```

| Layer | Module | Responsibility |
|---|---|---|
| Agent | `ava.agents.base` | Perceive → deliberate → act lifecycle, state machine |
| Memory | `ava.agents.memory` | Episodic stream, semantic facts, procedural skills |
| Cognition | `ava.agents.cognitive` | Belief system, goal-weighted action selection |
| Social | `ava.agents.social` | Relationship tracking, depth-1 theory of mind |
| Communication | `ava.communication` | Async pub/sub bus, BFT-style consensus |
| Civilization | `ava.civilization` | Tick orchestration, culture, governance |
| Execution | `ava.execution` | Bounded-concurrency scheduler, tracing |
| Analysis | `ava.analysis` | Change-point detection over population metrics |

## Memory architecture

Each agent's `MemoryStore` separates *what happened* from *what it means*:

```python
from ava.agents.memory import MemoryStore

memory = MemoryStore(owner_id="settler-12")

memory.episodic.record(
    event_type="alliance",
    content={"alliance": True, "actor": "settler-12", "target": "settler-47"},
    tick=88,
)

# Reflection distills high-importance episodes into durable semantic facts,
# the way a generative agent periodically summarizes its memory stream.
facts = memory.reflect(now_tick=89)

# Retrieval blends recency, importance, and embedding relevance.
recent = memory.episodic.retrieve(query_embedding=None, now_tick=89, top_k=10)
```

Procedural memory reinforces successful action sequences independently,
so an agent that keeps succeeding at foraging in forest biomes converges
on that skill without anyone hand-tuning a policy:

```python
from ava.agents.memory import ProceduralMemory, Skill

procedural = ProceduralMemory(learning_rate=0.2)
procedural.learn(Skill(name="forage", trigger_conditions={"biome": "forest"}, action_sequence=[]))
procedural.reinforce("forage", success=True)
```

## Governance and consensus

Laws are not declared — they are proposed, voted on, and ratified by
agents through the same `GovernanceSystem` substrate, with quorum and
majority thresholds that scale with population size:

```python
from ava.civilization.governance import GovernanceSystem

gov = GovernanceSystem(ratification_margin=0.5, min_quorum=3)
proposal = gov.propose(text="share water equally", proposer_id="settler-3", tick=120)

for voter in ("settler-3", "settler-7", "settler-19"):
    gov.cast_vote(proposal.id, voter, support=True)

ratified = gov.evaluate_proposals(tick=121)  # -> 1
```

For decisions that must tolerate adversarial or faulty agents, the
communication layer implements a three-phase PBFT-style protocol
(`PROPOSE → PREPARE → COMMIT`) that commits once `2f + 1` of `n = 3f + 1`
participants agree:

```python
from ava.communication.consensus import RaftLikeConsensus, Proposal, Phase

consensus = RaftLikeConsensus(participant_ids=["a", "b", "c", "d"])

async def collect_votes(proposal: Proposal, phase: Phase) -> set[str]:
    return {"a", "b", "c"}  # quorum reached out of 4 participants, f=1

result = await consensus.propose(
    Proposal(id="p-1", proposer_id="a", payload={"rule": "rotate_leadership"}),
    vote_collector=collect_votes,
)
```

## Detecting emergence

The analysis layer turns "it looks like agents specialized" into a
statistically grounded claim:

```python
from ava.analysis.emergence import EmergenceDetector, specialization_index

detector = EmergenceDetector(window=30, significance=0.05)

for tick, action_counts_by_agent in simulation_log:
    index = specialization_index(action_counts_by_agent)
    event = detector.observe_metric("role_specialization", tick=tick, value=index)
    if event is not None:
        print(event.description)
        # "role_specialization shifted from 0.140 to 0.710 (p=0.0021)"
```

See [`experiments/role_emergence_experiment.py`](experiments/role_emergence_experiment.py)
for a full runnable example where sixty agents, given nothing but a
reinforcement rule over three possible actions, sort themselves into
distinct roles under measurable statistical significance.

## Performance

Concurrency is bounded, not unlimited — `ExecutionEngine` caps in-flight
agents with a semaphore so a tick over a large population degrades
gracefully instead of spawning unbounded coroutines:

```bash
python benchmarks/bench_tick_throughput.py --agents 100 1000 5000 --ticks 20
```

```
n_agents=   100  mean_tick=    4.82ms  p95_tick=    6.10ms  throughput=  20746.9 agents/s
n_agents=  1000  mean_tick=   38.91ms  p95_tick=   45.27ms  throughput=  25700.1 agents/s
n_agents=  5000  mean_tick=  201.44ms  p95_tick=  228.65ms  throughput=  24822.0 agents/s
```

(Representative numbers from a no-op agent on commodity hardware — actual
throughput depends heavily on what `deliberate()` does per agent, e.g.
whether it calls out to an LLM backend.)

## Installation

```bash
git clone https://github.com/TianhangZhuzth/Fundamental-Ava.git
cd Fundamental-Ava
pip install -e ".[dev]"
```

Requires Python 3.11+ (the execution engine uses `asyncio.TaskGroup`,
added in 3.11).

## Running the test suite

```bash
pytest --cov=ava --cov-report=term-missing
ruff check src tests benchmarks experiments
mypy src/ava
```

## Project layout

```
src/ava/
├── agents/          # AgentCore lifecycle, memory, cognition, social modeling
├── communication/    # MessageBus, BFT-style consensus
├── civilization/     # Simulation engine, culture, governance
├── execution/         # Concurrent scheduler, tracer
├── models/             # LLM backend abstraction (mock, rate-limited, caching)
├── analysis/            # Emergence detection over population metrics
└── utils/                 # Small shared helpers

tests/          # pytest suite, one file per module
benchmarks/   # throughput and latency benchmarks
experiments/    # runnable research scripts (e.g. role emergence)
```

## Status

This is research infrastructure under active development. APIs in
`ava.agents` and `ava.civilization` are reasonably
stable; `ava.analysis` is evolving as we add more emergence
detectors beyond specialization and stratification.

## License

Apache 2.0 — see [LICENSE](LICENSE).
