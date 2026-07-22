"""Nano reference runtime — deterministic execution tests (Milestone 2)."""

import pytest

from nano.ir.graph import StrategyGraph
from nano.ir.schema import NANO_IR_VERSION
from nano.runtime.interpreter import MarketFrame, RuntimeError_, execute
from nano.runtime.scheduler import interval_seconds, ticks

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

# Six 1-minute timestamps; only t=300 aligns with the 5m schedule after t=0.
TIMESTAMPS = (0, 60, 120, 180, 240, 300)
RSI_SERIES = (55.0, 50.0, 40.0, 35.0, 31.0, 25.0)  # dips below 30 only at t=300


def frame():
    return MarketFrame(timestamps=TIMESTAMPS, signals={"RSI": RSI_SERIES})


def test_interval_seconds():
    assert interval_seconds("5m") == 300
    assert interval_seconds("1h") == 3600
    assert interval_seconds("1d") == 86400
    with pytest.raises(ValueError):
        interval_seconds("5x")


def test_ticks_align_to_interval():
    assert ticks("5m", TIMESTAMPS) == ((0, 0), (5, 300))


def test_momentum_emits_buy_only_when_condition_true():
    result = execute(StrategyGraph.from_dict(MOMENTUM_IR), frame())
    assert len(result.intents) == 1
    intent = result.intents[0]
    assert intent.action == "BUY"
    assert intent.asset == "BTC"
    assert intent.confidence == 0.91
    assert intent.timestamp == 300  # RSI 25 < 30 at t=300; t=0 RSI 55 fails


def test_execution_is_deterministic():
    a = execute(StrategyGraph.from_dict(MOMENTUM_IR), frame())
    b = execute(StrategyGraph.from_dict(MOMENTUM_IR), frame())
    assert a.to_dict() == b.to_dict()


def test_every_scheduled_tick_is_logged():
    result = execute(StrategyGraph.from_dict(MOMENTUM_IR), frame())
    evaluations = [e for e in result.log if e.event == "condition.evaluated"]
    assert len(evaluations) == 2  # t=0 and t=300
    assert [e.timestamp for e in evaluations] == [0, 300]


def test_missing_signal_is_an_error():
    bad_frame = MarketFrame(timestamps=TIMESTAMPS, signals={"EMA": RSI_SERIES})
    with pytest.raises(RuntimeError_):
        execute(StrategyGraph.from_dict(MOMENTUM_IR), bad_frame)


def test_mismatched_series_length_rejected():
    with pytest.raises(ValueError):
        MarketFrame(timestamps=TIMESTAMPS, signals={"RSI": (1.0, 2.0)})


def test_no_intents_when_condition_never_true():
    calm = MarketFrame(
        timestamps=TIMESTAMPS, signals={"RSI": (55.0, 56.0, 57.0, 58.0, 59.0, 60.0)}
    )
    result = execute(StrategyGraph.from_dict(MOMENTUM_IR), calm)
    assert result.intents == ()
