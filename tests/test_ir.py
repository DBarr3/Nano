"""Nano IR — node, graph, and manifest tests (Milestone 1)."""

import pytest

from nano.ir.graph import StrategyGraph
from nano.ir.nodes import ConditionNode, IntentNode, ScheduleNode
from nano.ir.schema import IRValidationError, ManifestViolation, NANO_IR_VERSION

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


def test_graph_round_trip():
    graph = StrategyGraph.from_dict(MOMENTUM_IR)
    assert graph.name == "Momentum"
    assert isinstance(graph.schedule, ScheduleNode)
    assert graph.schedule.interval == "5m"
    assert len(graph.conditions) == 1
    assert isinstance(graph.conditions[0], ConditionNode)
    assert graph.conditions[0].signal == "RSI"
    assert len(graph.intents) == 1
    assert isinstance(graph.intents[0], IntentNode)
    assert graph.to_dict() == MOMENTUM_IR


def test_intent_without_manifest_effect_rejected():
    bad = dict(MOMENTUM_IR, effects=["log.append"])
    with pytest.raises(ManifestViolation):
        StrategyGraph.from_dict(bad)


def test_unknown_node_type_rejected():
    bad = dict(MOMENTUM_IR, nodes=[{"type": "Order", "asset": "BTC"}])
    with pytest.raises(IRValidationError):
        StrategyGraph.from_dict(bad)


def test_bad_operator_rejected():
    bad = dict(
        MOMENTUM_IR,
        nodes=[
            {"type": "Schedule", "interval": "5m"},
            {"type": "Condition", "signal": "RSI", "operator": "<<", "value": 30},
        ],
    )
    with pytest.raises(IRValidationError):
        StrategyGraph.from_dict(bad)


def test_two_schedules_rejected():
    bad = dict(
        MOMENTUM_IR,
        nodes=[
            {"type": "Schedule", "interval": "5m"},
            {"type": "Schedule", "interval": "1h"},
        ],
    )
    with pytest.raises(IRValidationError):
        StrategyGraph.from_dict(bad)


def test_missing_version_rejected():
    bad = {k: v for k, v in MOMENTUM_IR.items() if k != "nanoIrVersion"}
    with pytest.raises(IRValidationError):
        StrategyGraph.from_dict(bad)
