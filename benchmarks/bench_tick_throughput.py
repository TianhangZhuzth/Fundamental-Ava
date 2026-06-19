"""Throughput benchmark: how many agents can complete one tick within budget.

Run with: python benchmarks/bench_tick_throughput.py --agents 1000 5000 10000
"""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
from pathlib import Path

