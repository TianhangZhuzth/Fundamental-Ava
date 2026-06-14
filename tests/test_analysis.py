from __future__ import annotations

from collections import Counter

from ava.analysis.emergence import (
    EmergenceDetector,
    gini_coefficient,
    specialization_index,
)


def test_specialization_index_zero_for_generalists() -> None:
    agents = {
        "a": Counter({"farm": 5, "fight": 5, "trade": 5}),
        "b": Counter({"farm": 5, "fight": 5, "trade": 5}),
