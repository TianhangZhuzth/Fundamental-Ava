"""Cognitive architecture: belief maintenance and action selection.

`CognitiveArchitecture` wires together a `BeliefSystem` (what the agent
currently holds to be true about the world and other agents) with a
deliberation strategy that produces candidate actions and ranks them by
expected utility under the agent's current beliefs and goals.
"""

from __future__ import annotations
