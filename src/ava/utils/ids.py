"""Small id-generation helpers shared across modules."""

from __future__ import annotations

import uuid


def short_id(prefix: str = "") -> str:
    raw = uuid.uuid4().hex[:10]
    return f"{prefix}-{raw}" if prefix else raw
