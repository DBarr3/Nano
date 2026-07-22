"""Nano bridge (Milestone 5) — decision-gate adapter + deterministic backtester.

Designed to be embedded in a host platform's execution layer.
Nano never acts on the world: the bridge forwards Intents to a decision
gate and records decisions; execution belongs to the caller's gates.

``RiskDecision``, ``RiskEngine``, and ``ProvenanceRiskEngine`` remain as
backward-compatible aliases of ``Decision``, ``DecisionGate``, and
``ProvenanceGate``.
"""

from nano.bridge.ats_bridge import (
    BridgeError,
    BridgeResult,
    Decision,
    DecisionGate,
    NanoBridge,
    RiskDecision,
    RiskEngine,
)
from nano.bridge.backtester import BacktestReport, Backtester, ReplayDivergence
from nano.bridge.provenance import (
    PROTOCOL_C_AVAILABLE,
    ProtocolCUnavailable,
    ProvenanceError,
    ProvenanceGate,
    ProvenanceReceipt,
    ProvenanceRiskEngine,
)

__all__ = [
    "BacktestReport",
    "Backtester",
    "BridgeError",
    "BridgeResult",
    "Decision",
    "DecisionGate",
    "NanoBridge",
    "PROTOCOL_C_AVAILABLE",
    "ProtocolCUnavailable",
    "ProvenanceError",
    "ProvenanceGate",
    "ProvenanceReceipt",
    "ProvenanceRiskEngine",
    "ReplayDivergence",
    "RiskDecision",
    "RiskEngine",
]
