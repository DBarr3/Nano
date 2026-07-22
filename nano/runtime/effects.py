"""Intents and the append-only execution log.

Nano never places trades. The runtime's terminal output is a tuple of Intents —
proposals a downstream gate (the host platform's risk engine) may accept or reject.
Components propose; gates decide.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Intent:
    action: str
    timestamp: int
    asset: Optional[str] = None
    confidence: Optional[float] = None

    def to_dict(self) -> dict:
        out: dict = {"intent": self.action, "timestamp": self.timestamp}
        if self.asset is not None:
            out["asset"] = self.asset
        if self.confidence is not None:
            out["confidence"] = self.confidence
        return out


@dataclass(frozen=True)
class LogEntry:
    event: str
    timestamp: int
    detail: str

    def to_dict(self) -> dict:
        return {"event": self.event, "timestamp": self.timestamp, "detail": self.detail}
