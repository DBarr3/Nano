"""Nano bridge — ATSv2 adapter + deterministic backtester tests (Milestone 5)."""

from dataclasses import dataclass
from pathlib import Path

import pytest

from nano.bridge import (
    Backtester,
    BridgeError,
    NanoBridge,
    ReplayDivergence,
    RiskDecision,
)
from nano.ir.graph import StrategyGraph
from nano.ir.schema import IRValidationError, ManifestViolation, NANO_IR_VERSION
from nano.runtime.interpreter import MarketFrame

MOMENTUM_IR = {
    "type": "Strategy",
    "nanoIrVersion": NANO_IR_VERSION,
    "name": "Momentum",
    "effects": ["intent.emit", "log.append"],
    "nodes": [
        {"type": "Schedule", "interval": "5m"},
        {"type": "Condition", "signal": "RSI", "operator": "<", "value": 30},
        {"type": "Intent", "action": "BUY", "asset": "BTC", "confidence": 0.91},
    ],
}

MOMENTUM_JSON = Path(__file__).resolve().parent.parent / "nano" / "examples" / "momentum_ir.json"


def fire_frame(ts: int = 0) -> MarketFrame:
    """Single tick where RSI 25 < 30 — the strategy emits one BUY intent."""
    return MarketFrame(timestamps=(ts,), signals={"RSI": (25.0,)})


def calm_frame(ts: int = 0) -> MarketFrame:
    """Single tick where RSI 55 — no intent."""
    return MarketFrame(timestamps=(ts,), signals={"RSI": (55.0,)})


@dataclass(frozen=True)
class ThresholdRiskEngine:
    """Deterministic stub gate: approve iff confidence >= threshold."""

    threshold: float

    def dispose(self, intent, *, frame) -> RiskDecision:
        confidence = intent.confidence if intent.confidence is not None else 0.0
        if confidence >= self.threshold:
            return RiskDecision(
                intent=intent,
                approved=True,
                reason=f"confidence {confidence} >= threshold {self.threshold}",
            )
        return RiskDecision(
            intent=intent,
            approved=False,
            reason=f"confidence {confidence} < threshold {self.threshold}",
        )


class StatefulRiskEngine:
    """Deliberately nondeterministic: decision depends on hidden call count."""

    def __init__(self) -> None:
        self.calls = 0

    def dispose(self, intent, *, frame) -> RiskDecision:
        self.calls += 1
        return RiskDecision(
            intent=intent,
            approved=self.calls % 2 == 1,
            reason=f"call #{self.calls}",
        )


def loaded_bridge(engine) -> NanoBridge:
    bridge = NanoBridge(engine)
    bridge.load(MOMENTUM_IR)
    return bridge


# --- RiskDecision paths ------------------------------------------------------


def test_approved_path_exact_decision():
    bridge = loaded_bridge(ThresholdRiskEngine(threshold=0.9))
    result = bridge.run(fire_frame())
    assert len(result.intents) == 1
    assert len(result.decisions) == 1
    decision = result.decisions[0]
    assert decision.approved is True
    assert decision.reason == "confidence 0.91 >= threshold 0.9"
    assert decision.intent == result.intents[0]
    assert decision.intent.action == "BUY"
    assert decision.intent.asset == "BTC"
    assert decision.to_dict() == {
        "intent": {"intent": "BUY", "timestamp": 0, "asset": "BTC", "confidence": 0.91},
        "approved": True,
        "reason": "confidence 0.91 >= threshold 0.9",
    }
    assert [e.event for e in result.log if e.event.startswith("risk.")] == ["risk.approved"]


def test_rejected_path_exact_decision():
    bridge = loaded_bridge(ThresholdRiskEngine(threshold=0.95))
    result = bridge.run(fire_frame())
    assert len(result.decisions) == 1
    decision = result.decisions[0]
    assert decision.approved is False
    assert decision.reason == "confidence 0.91 < threshold 0.95"
    assert [e.event for e in result.log if e.event.startswith("risk.")] == ["risk.rejected"]


def test_rejection_does_not_suppress_intent_from_audit_trail():
    bridge = loaded_bridge(ThresholdRiskEngine(threshold=0.95))
    result = bridge.run(fire_frame())
    # The rejected intent still appears in the intent tuple...
    assert len(result.intents) == 1
    assert result.intents[0].action == "BUY"
    # ...and its full lifecycle is in the log: emitted, forwarded, rejected.
    events = [e.event for e in result.log]
    assert "intent.emitted" in events
    assert "intent.forwarded" in events
    assert "risk.rejected" in events
    assert events.index("intent.emitted") < events.index("intent.forwarded")
    assert events.index("intent.forwarded") < events.index("risk.rejected")


def test_no_intents_means_no_decisions():
    bridge = loaded_bridge(ThresholdRiskEngine(threshold=0.9))
    result = bridge.run(calm_frame())
    assert result.intents == ()
    assert result.decisions == ()


# --- Loading and manifest verification ---------------------------------------


def test_manifest_violation_surfaces_at_load():
    bad_ir = {
        "type": "Strategy",
        "nanoIrVersion": NANO_IR_VERSION,
        "name": "NoManifest",
        "effects": ["log.append"],  # Intent nodes but no "intent.emit"
        "nodes": [
            {"type": "Condition", "signal": "RSI", "operator": "<", "value": 30},
            {"type": "Intent", "action": "BUY", "asset": "BTC"},
        ],
    }
    bridge = NanoBridge(ThresholdRiskEngine(threshold=0.9))
    with pytest.raises(ManifestViolation):
        bridge.load(bad_ir)


def test_invalid_ir_surfaces_at_load():
    bridge = NanoBridge(ThresholdRiskEngine(threshold=0.9))
    with pytest.raises(IRValidationError):
        bridge.load({"type": "NotAStrategy"})


def test_run_before_load_is_an_explicit_error():
    bridge = NanoBridge(ThresholdRiskEngine(threshold=0.9))
    with pytest.raises(BridgeError):
        bridge.run(fire_frame())


# --- Determinism --------------------------------------------------------------


def test_same_graph_frame_engine_twice_is_identical():
    engine = ThresholdRiskEngine(threshold=0.9)
    a = loaded_bridge(engine).run(fire_frame())
    b = loaded_bridge(engine).run(fire_frame())
    assert a.to_dict() == b.to_dict()


# --- Backtester ----------------------------------------------------------------


def frames_fire_calm_fire():
    return [fire_frame(0), calm_frame(0), fire_frame(0)]


def test_backtest_report_counts_exact_all_approved():
    backtester = Backtester(ThresholdRiskEngine(threshold=0.9))
    graph = StrategyGraph.from_dict(MOMENTUM_IR)
    report = backtester.run(graph, frames_fire_calm_fire())
    assert report.frames_run == 3
    assert report.intents_emitted == 2
    assert report.approved == 2
    assert report.rejected == 0
    assert len(report.results) == 3
    assert [len(r.intents) for r in report.results] == [1, 0, 1]
    d = report.to_dict()
    assert d["frames_run"] == 3
    assert d["intents_emitted"] == 2
    assert d["approved"] == 2
    assert d["rejected"] == 0


def test_backtest_report_counts_exact_all_rejected():
    backtester = Backtester(ThresholdRiskEngine(threshold=0.95))
    graph = StrategyGraph.from_dict(MOMENTUM_IR)
    report = backtester.run(graph, frames_fire_calm_fire())
    assert report.intents_emitted == 2
    assert report.approved == 0
    assert report.rejected == 2


def test_backtest_aggregates_full_audit_log():
    backtester = Backtester(ThresholdRiskEngine(threshold=0.9))
    graph = StrategyGraph.from_dict(MOMENTUM_IR)
    report = backtester.run(graph, frames_fire_calm_fire())
    assert len(report.log) == sum(len(r.log) for r in report.results)
    assert [e.event for e in report.log].count("risk.approved") == 2


def test_verify_replay_passes_with_deterministic_engine():
    backtester = Backtester(ThresholdRiskEngine(threshold=0.9))
    graph = StrategyGraph.from_dict(MOMENTUM_IR)
    assert backtester.verify_replay(graph, frames_fire_calm_fire()) is True


def test_verify_replay_catches_nondeterministic_engine():
    backtester = Backtester(StatefulRiskEngine())
    graph = StrategyGraph.from_dict(MOMENTUM_IR)
    with pytest.raises(ReplayDivergence):
        backtester.verify_replay(graph, [fire_frame(0)])


# --- End-to-end with the example corpus ---------------------------------------


def test_momentum_example_end_to_end():
    engine = ThresholdRiskEngine(threshold=0.9)
    bridge = NanoBridge(engine)
    graph = bridge.load(str(MOMENTUM_JSON))
    assert graph.name == "Momentum"

    # Six 1-minute timestamps; the 5m schedule fires at t=0 and t=300, and
    # RSI dips below 30 only at t=300 — exactly one BUY intent.
    frame = MarketFrame(
        timestamps=(0, 60, 120, 180, 240, 300),
        signals={"RSI": (55.0, 50.0, 40.0, 35.0, 31.0, 25.0)},
    )
    result = bridge.run(frame)
    assert len(result.intents) == 1
    assert result.intents[0].timestamp == 300
    assert result.decisions[0].approved is True

    backtester = Backtester(engine)
    calm = MarketFrame(
        timestamps=(0, 60, 120, 180, 240, 300),
        signals={"RSI": (55.0, 56.0, 57.0, 58.0, 59.0, 60.0)},
    )
    report = backtester.run(graph, [frame, calm])
    assert report.frames_run == 2
    assert report.intents_emitted == 1
    assert report.approved == 1
    assert report.rejected == 0
    assert backtester.verify_replay(graph, [frame, calm]) is True
