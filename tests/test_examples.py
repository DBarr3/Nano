"""Example corpus — every shipped IR example must load and execute (Milestone 3)."""

import json
from pathlib import Path

from nano.ir.graph import StrategyGraph
from nano.runtime.interpreter import MarketFrame, execute

EXAMPLES = Path(__file__).resolve().parent.parent / "nano" / "examples"


def _load(name: str) -> StrategyGraph:
    return StrategyGraph.from_dict(json.loads((EXAMPLES / name).read_text()))


def test_momentum_example_loads_and_executes():
    data = json.loads((EXAMPLES / "momentum_ir.json").read_text())
    graph = StrategyGraph.from_dict(data)

    frame = MarketFrame(timestamps=(0, 300), signals={"RSI": (45.0, 22.0)})
    result = execute(graph, frame)

    assert [i.to_dict() for i in result.intents] == [
        {"intent": "BUY", "timestamp": 300, "asset": "BTC", "confidence": 0.91}
    ]


def test_all_ir_examples_are_valid():
    ir_files = sorted(EXAMPLES.glob("*_ir.json"))
    assert ir_files, "example corpus must not be empty"
    for path in ir_files:
        StrategyGraph.from_dict(json.loads(path.read_text()))


# --- Corpus-wide invariants -------------------------------------------------


def test_every_ir_example_round_trips():
    ir_files = sorted(EXAMPLES.glob("*_ir.json"))
    assert ir_files, "example corpus must not be empty"
    for path in ir_files:
        data = json.loads(path.read_text())
        assert StrategyGraph.from_dict(data).to_dict() == data, path.name


def test_every_nano_source_has_an_ir_partner_and_vice_versa():
    nano_stems = {p.name[: -len(".nano")] for p in EXAMPLES.glob("*.nano")}
    ir_stems = {p.name[: -len("_ir.json")] for p in EXAMPLES.glob("*_ir.json")}
    assert nano_stems, "example corpus must not be empty"
    assert nano_stems == ir_stems


# --- Per-example execution: fire and no-fire paths --------------------------


def test_basic_rsi_fires_when_oversold():
    graph = _load("basic_rsi_ir.json")

    fired = execute(graph, MarketFrame(timestamps=(0, 900), signals={"RSI": (55.0, 25.0)}))
    assert [i.to_dict() for i in fired.intents] == [
        {"intent": "BUY", "timestamp": 900, "asset": "BTCUSD", "confidence": 0.85}
    ]

    quiet = execute(graph, MarketFrame(timestamps=(0, 900), signals={"RSI": (55.0, 41.0)}))
    assert quiet.intents == ()


def test_mean_reversion_sells_on_stretched_zscore():
    graph = _load("mean_reversion_ir.json")

    fired = execute(
        graph, MarketFrame(timestamps=(0, 3600), signals={"ZSCORE": (0.4, 2.5)})
    )
    assert [i.to_dict() for i in fired.intents] == [
        {"intent": "SELL", "timestamp": 3600, "asset": "SPY", "confidence": 0.8}
    ]

    quiet = execute(
        graph, MarketFrame(timestamps=(0, 3600), signals={"ZSCORE": (0.4, 1.9)})
    )
    assert quiet.intents == ()


def test_volatility_guard_pauses_on_atr_spike():
    graph = _load("volatility_guard_ir.json")

    fired = execute(graph, MarketFrame(timestamps=(0, 300), signals={"ATR": (12.0, 63.0)}))
    assert [i.to_dict() for i in fired.intents] == [
        {"intent": "PAUSE", "timestamp": 300}
    ]

    quiet = execute(graph, MarketFrame(timestamps=(0, 300), signals={"ATR": (12.0, 48.0)}))
    assert quiet.intents == ()


def test_risk_manager_pauses_at_drawdown_threshold():
    graph = _load("risk_manager_ir.json")
    assert [a.name for a in graph.agents] == ["RiskManager"]

    fired = execute(
        graph, MarketFrame(timestamps=(0, 60), signals={"DRAWDOWN": (1.2, 3.0)})
    )
    assert [i.to_dict() for i in fired.intents] == [
        {"intent": "PAUSE", "timestamp": 60}
    ]

    quiet = execute(
        graph, MarketFrame(timestamps=(0, 60), signals={"DRAWDOWN": (1.2, 2.9)})
    )
    assert quiet.intents == ()


def test_ai_agent_observes_then_executes_on_opportunity():
    graph = _load("ai_agent_ir.json")
    assert [a.name for a in graph.agents] == ["ATS"]

    fired = execute(
        graph, MarketFrame(timestamps=(0, 60), signals={"OPPORTUNITY": (40.0, 95.0)})
    )
    assert [i.to_dict() for i in fired.intents] == [
        {"intent": "OBSERVE", "timestamp": 60},
        {"intent": "EXECUTE", "timestamp": 60},
    ]

    quiet = execute(
        graph, MarketFrame(timestamps=(0, 60), signals={"OPPORTUNITY": (40.0, 89.0)})
    )
    assert quiet.intents == ()
