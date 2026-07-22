"""Nano bridge (Milestone 5) — risk-gate adapter + deterministic backtester.

Designed to be embedded in a host trading platform's execution layer.
Nano never places trades: the bridge forwards
Intents to a risk engine and records decisions; execution belongs to the
caller's gates.
"""

from nano.bridge.ats_bridge import (
    BridgeError,
    BridgeResult,
    NanoBridge,
    RiskDecision,
    RiskEngine,
)
from nano.bridge.backtester import BacktestReport, Backtester, ReplayDivergence
from nano.bridge.provenance import (
    PROTOCOL_C_AVAILABLE,
    ProtocolCUnavailable,
    ProvenanceError,
    ProvenanceReceipt,
    ProvenanceRiskEngine,
)

__all__ = [
    "BacktestReport",
    "Backtester",
    "BridgeError",
    "BridgeResult",
    "NanoBridge",
    "PROTOCOL_C_AVAILABLE",
    "ProtocolCUnavailable",
    "ProvenanceError",
    "ProvenanceReceipt",
    "ProvenanceRiskEngine",
    "ReplayDivergence",
    "RiskDecision",
    "RiskEngine",
]
