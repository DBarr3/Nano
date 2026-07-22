"""AST -> Nano IR code generation.

Invariant: output is canonical. The generated dict has exactly the shape and
node ordering StrategyGraph.to_dict produces (schedule, then conditions,
intents, and agents in source order), so compile -> from_dict -> to_dict is a
fixed point and compiled IR is byte-diffable against the hand-written example
corpus. Codegen only transforms a parser-validated AST; it performs no
position-carrying validation of its own — the final StrategyGraph.from_dict
pass re-checks the IR contract itself.
"""

from __future__ import annotations

from ..ir.graph import StrategyGraph
from ..ir.schema import NANO_IR_VERSION
from .parser import StrategyAst, parse

# Every v0.1.0 strategy declares exactly this manifest, in this order.
EFFECTS_V0_1_0 = ("intent.emit", "log.append")


def ast_to_dict(strategy: StrategyAst) -> dict:
    """Lower a parsed strategy to a canonical Nano IR dict."""
    nodes: list[dict] = []
    if strategy.schedule is not None:
        nodes.append({"type": "Schedule", "interval": strategy.schedule.interval})
        rule = strategy.schedule.rule
        if rule is not None:
            for condition in rule.conditions:
                nodes.append(
                    {
                        "type": "Condition",
                        "signal": condition.signal,
                        "operator": condition.operator,
                        "value": condition.value,
                    }
                )
            for action in rule.actions:
                intent: dict = {"type": "Intent", "action": action.action}
                if action.asset is not None:
                    intent["asset"] = action.asset
                if action.confidence is not None:
                    intent["confidence"] = action.confidence
                nodes.append(intent)
    for agent in strategy.agents:
        nodes.append({"type": "Agent", "name": agent.name})

    return {
        "type": "Strategy",
        "nanoIrVersion": NANO_IR_VERSION,
        "name": strategy.name,
        "effects": list(EFFECTS_V0_1_0),
        "nodes": nodes,
    }


def compile_source(source: str) -> StrategyGraph:
    """Compile `.nano` source to a validated StrategyGraph."""
    return StrategyGraph.from_dict(ast_to_dict(parse(source)))


def compile_to_dict(source: str) -> dict:
    """Compile `.nano` source to the canonical Nano IR dict."""
    return compile_source(source).to_dict()
