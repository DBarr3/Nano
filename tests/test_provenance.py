"""Tests for the optional Protocol-C provenance adapter (nano/bridge/provenance.py).

The whole module is skipped when the optional ``aether-protocol-c`` package
is not installed, except the availability-guard test, which only needs the
internal flag flipped and asserts the install-instructions error path.
"""

from __future__ import annotations

import json

import pytest

from nano.bridge import (
    NanoBridge,
    ProtocolCUnavailable,
    ProvenanceRiskEngine,
    RiskDecision,
)
from nano.bridge import provenance as provenance_module
from nano.compiler import compile_source
from nano.runtime.effects import Intent
from nano.runtime.interpreter import MarketFrame

aether_protocol_c = pytest.importorskip("aether_protocol_c")

MOMENTUM_SOURCE = """
strategy ProvenanceDemo {
    every 5m {
        if RSI(14) < 30 {
            buy(BTC, 0.9)
        }
    }
}
"""


class ThresholdEngine:
    def __init__(self, floor: float = 0.8) -> None:
        self._floor = floor

    def dispose(self, intent: Intent, *, frame: MarketFrame) -> RiskDecision:
        approved = (intent.confidence or 0.0) >= self._floor
        reason = f"confidence>={self._floor}" if approved else "confidence below floor"
        return RiskDecision(intent=intent, approved=approved, reason=reason)


def test_availability_guard_raises_with_install_instructions(monkeypatch, tmp_path):
    monkeypatch.setattr(provenance_module, "PROTOCOL_C_AVAILABLE", False)
    with pytest.raises(ProtocolCUnavailable, match="pip install aether-protocol-c"):
        ProvenanceRiskEngine(ThresholdEngine(), tmp_path / "audit.jsonl")


def test_dispose_returns_inner_decision_unchanged(tmp_path):
    inner = ThresholdEngine(floor=0.8)
    engine = ProvenanceRiskEngine(inner, tmp_path / "audit.jsonl")
    intent = Intent(action="BUY", timestamp=300, asset="BTC", confidence=0.9)
    frame = MarketFrame(timestamps=(0, 300), signals={})

    decision = engine.dispose(intent, frame=frame)

    assert isinstance(decision, RiskDecision)
    assert decision.intent == intent
    assert decision.approved is True
    assert decision.reason == "confidence>=0.8"


def test_receipt_created_and_self_verifies(tmp_path):
    engine = ProvenanceRiskEngine(ThresholdEngine(), tmp_path / "audit.jsonl")
    intent = Intent(action="BUY", timestamp=300, asset="BTC", confidence=0.9)
    frame = MarketFrame(timestamps=(0, 300), signals={})

    engine.dispose(intent, frame=frame)

    assert len(engine.receipts) == 1
    order_id, receipt = next(iter(engine.receipts.items()))
    assert receipt.order_id == order_id
    assert receipt.verified is True
    assert engine.verify_receipt(order_id) is True
    assert aether_protocol_c.verify(receipt.commitment, receipt.signature) is True


def test_rejected_intent_still_gets_a_signed_receipt(tmp_path):
    """A "no" is a decision too -- provenance covers rejections, not just approvals."""
    engine = ProvenanceRiskEngine(ThresholdEngine(floor=0.95), tmp_path / "audit.jsonl")
    intent = Intent(action="BUY", timestamp=300, asset="BTC", confidence=0.5)
    frame = MarketFrame(timestamps=(0, 300), signals={})

    decision = engine.dispose(intent, frame=frame)

    assert decision.approved is False
    assert len(engine.receipts) == 1
    receipt = next(iter(engine.receipts.values()))
    assert receipt.verified is True
    assert receipt.commitment["trade_details"]["approved"] is False


def test_tampering_with_a_commitment_breaks_verification(tmp_path):
    engine = ProvenanceRiskEngine(ThresholdEngine(), tmp_path / "audit.jsonl")
    intent = Intent(action="BUY", timestamp=300, asset="BTC", confidence=0.9)
    frame = MarketFrame(timestamps=(0, 300), signals={})
    engine.dispose(intent, frame=frame)

    receipt = next(iter(engine.receipts.values()))
    tampered = dict(receipt.commitment)
    tampered["trade_details"] = dict(tampered["trade_details"])
    tampered["trade_details"]["approved"] = not tampered["trade_details"]["approved"]

    assert aether_protocol_c.verify(tampered, receipt.signature) is False


def test_audit_log_is_append_only_jsonl(tmp_path):
    log_path = tmp_path / "audit.jsonl"
    engine = ProvenanceRiskEngine(ThresholdEngine(), log_path)
    frame = MarketFrame(timestamps=(0, 300, 600), signals={})

    for ts in (300, 600):
        engine.dispose(Intent(action="BUY", timestamp=ts, asset="BTC", confidence=0.9), frame=frame)

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    for line in lines:
        entry = json.loads(line)
        assert entry["phase"] == "DECISION_COMMITMENT"


def test_nonce_is_monotonic_and_engine_owned(tmp_path):
    """Caller-supplied nonces are ignored -- the engine's own counter is authoritative."""
    engine = ProvenanceRiskEngine(
        ThresholdEngine(), tmp_path / "audit.jsonl", account_state={"nonce": 999}
    )
    frame = MarketFrame(timestamps=(0, 300, 600), signals={})

    engine.dispose(Intent(action="BUY", timestamp=300, asset="BTC", confidence=0.9), frame=frame)
    engine.dispose(Intent(action="BUY", timestamp=600, asset="BTC", confidence=0.9), frame=frame)

    nonces = [r.commitment["nonce"] for r in engine.receipts.values()]
    assert nonces == [1, 2]


def test_end_to_end_through_bridge_and_replay_stays_deterministic(tmp_path):
    """Signing is a side channel: the BridgeResult itself must still replay bit-identically."""
    graph = compile_source(MOMENTUM_SOURCE)
    frame = MarketFrame(timestamps=(0, 300), signals={"RSI": (45.0, 22.0)})

    engine_a = ProvenanceRiskEngine(ThresholdEngine(), tmp_path / "run_a.jsonl")
    bridge_a = NanoBridge(engine_a)
    bridge_a.load(graph.to_dict())
    result_a = bridge_a.run(frame)

    engine_b = ProvenanceRiskEngine(ThresholdEngine(), tmp_path / "run_b.jsonl")
    bridge_b = NanoBridge(engine_b)
    bridge_b.load(graph.to_dict())
    result_b = bridge_b.run(frame)

    assert result_a.to_dict() == result_b.to_dict()
    assert len(engine_a.receipts) == 1
    assert len(engine_b.receipts) == 1
    assert next(iter(engine_a.receipts.values())).verified
