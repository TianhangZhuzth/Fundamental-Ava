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
