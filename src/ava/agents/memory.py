"""Tiered memory subsystem: episodic, semantic, and procedural stores.

Modeled loosely on the generative-agent memory stream (Park et al.) but
extended with a procedural layer so agents can accumulate reusable skills
rather than re-deriving the same plans every tick. Retrieval blends
