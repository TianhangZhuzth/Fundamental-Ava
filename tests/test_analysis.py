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
    }
    index = specialization_index(agents)
    assert index < 0.05


def test_specialization_index_high_for_specialists() -> None:
    agents = {
        "a": Counter({"farm": 100}),
        "b": Counter({"fight": 100}),
        "c": Counter({"trade": 100}),
    }
    index = specialization_index(agents)
    assert index > 0.9


def test_gini_zero_for_perfect_equality() -> None:
    assert gini_coefficient([10.0, 10.0, 10.0, 10.0]) == 0.0


def test_gini_high_for_extreme_inequality() -> None:
    values = [0.0, 0.0, 0.0, 100.0]
    assert gini_coefficient(values) > 0.6


def test_detector_flags_significant_shift() -> None:
    detector = EmergenceDetector(window=10, significance=0.05)
    event = None
    for tick in range(40):
        value = 1.0 if tick < 20 else 9.0
        event = detector.observe_metric("cooperation_rate", tick=tick, value=value)
    assert event is not None
    assert event.kind == "cooperation_rate"


