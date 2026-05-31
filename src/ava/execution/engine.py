"""Concurrent per-tick execution scheduler.

Stepping a population of agents is embarrassingly parallel — each agent's
`step()` only touches its own state plus a read-only world_state snapshot
