"""Deterministic schedule expansion.

The scheduler owns the clock: timestamps are injected inputs, never read from
the environment. A tick is (index, timestamp) into the injected timeline.
"""

from __future__ import annotations

import re
from typing import Sequence, Tuple

_INTERVAL_RE = re.compile(r"^(\d+)([smhd])$")
_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}


def interval_seconds(interval: str) -> int:
    match = _INTERVAL_RE.match(interval.lower())
    if not match:
        raise ValueError(f"Unparseable interval {interval!r} (expected e.g. '5m', '1h')")
    return int(match.group(1)) * _UNIT_SECONDS[match.group(2)]


def ticks(interval: str, timestamps: Sequence[int]) -> Tuple[Tuple[int, int], ...]:
    """Return (index, timestamp) pairs where the schedule fires.

    A schedule fires at the first timestamp and at every timestamp that is at
    least one full interval after the previous firing. Alignment is relative to
    the injected timeline, so replays are bit-identical.
    """
    step = interval_seconds(interval)
    fired: list[Tuple[int, int]] = []
    next_due: int | None = None
    for index, ts in enumerate(timestamps):
        if next_due is None or ts >= next_due:
            fired.append((index, ts))
            next_due = ts + step
    return tuple(fired)
