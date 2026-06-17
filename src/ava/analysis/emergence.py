"""Statistical detection of emergent civilization-level phenomena.

Individually scripted agents do not "decide" to specialize, form
alliances, or stratify into classes — those are properties of the
population over time. EmergenceDetector watches the tick-by-tick action
and relationship data a Civilization produces and flags when a
distribution shifts enough to call it a genuine emergent pattern rather
than noise, using change-point detection over a rolling window.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import stats

EMERGENCE_KINDS = (
    "role_specialization",
    "wealth_stratification",
    "alliance_clustering",
    "behavioral_synchrony",
)


@dataclass(slots=True)
class EmergenceEvent:
    kind: str
    tick: int
    magnitude: float
    p_value: float
    description: str
    details: dict[str, Any] = field(default_factory=dict)


def specialization_index(action_counts_by_agent: dict[str, Counter[str]]) -> float:
    """Gini-style index over each agent's action-type distribution entropy.

    Returns 0.0 when every agent does the same spread of things
    (generalists) and approaches 1.0 when agents diverge into narrow,
    distinct roles (specialists) — the population-level signal Project SID
    uses to identify role emergence such as farmers vs. guards vs. traders.
    """
    if not action_counts_by_agent:
        return 0.0

    entropies = []
    for counts in action_counts_by_agent.values():
        total = sum(counts.values())
        if total == 0:
            continue
        probs = np.array([c / total for c in counts.values()])
        entropy = -np.sum(probs * np.log2(probs + 1e-12))
        max_entropy = np.log2(len(counts)) if len(counts) > 1 else 1.0
        entropies.append(1.0 - (entropy / max_entropy if max_entropy > 0 else 0.0))

    return float(np.mean(entropies)) if entropies else 0.0


def gini_coefficient(values: list[float]) -> float:
    """Standard Gini coefficient, used here for wealth/resource stratification."""
    if not values or all(v == 0 for v in values):
        return 0.0
    arr = np.sort(np.array(values, dtype=float))
    n = len(arr)
    cumulative = np.cumsum(arr)
    return float((n + 1 - 2 * np.sum(cumulative) / cumulative[-1]) / n)
