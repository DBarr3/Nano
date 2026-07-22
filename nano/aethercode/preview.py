"""IR preview renderers for `.nano` source.

Invariant: both renderers are total and deterministic — the same source always
produces the same string, and invalid source produces an "error:" rendering of
its diagnostics instead of an exception. ir_json emits the canonical IR dict
(compile_to_dict) as two-space-indented JSON, so it round-trips byte-exactly
against the hand-written example corpus; ir_preview is a human-readable tree
of the same graph, node for node, in graph order.
"""

from __future__ import annotations

import json

from ..compiler import compile_source, compile_to_dict
from ..ir.graph import StrategyGraph
from ..ir.nodes import IntentNode
from .diagnostics import diagnostics


def _number(value: float) -> str:
    """Render a numeric literal compactly (30 -> '30', 0.91 -> '0.91')."""
    return f"{value:g}"


def _render_intent(intent: IntentNode) -> str:
    parts = [intent.action]
    if intent.asset is not None:
        parts.append(intent.asset)
    if intent.confidence is not None:
        parts.append(f"@{_number(intent.confidence)}")
    return f"Intent: {' '.join(parts)}"


def _render_graph(graph: StrategyGraph) -> str:
    lines = [f"Strategy: {graph.name}"]
    lines.append(f"  Effects: {', '.join(graph.effects)}")
    if graph.schedule is not None:
        lines.append(f"  Schedule: every {graph.schedule.interval}")
    for condition in graph.conditions:
        lines.append(
            f"  Condition: {condition.signal} {condition.operator} "
            f"{_number(condition.value)}"
        )
    for intent in graph.intents:
        lines.append(f"  {_render_intent(intent)}")
    for agent in graph.agents:
        lines.append(f"  Agent: {agent.name}")
    return "\n".join(lines)


def _render_errors(source: str) -> str:
    return "\n".join(
        f"error: {d.line}:{d.column}: {d.message}" for d in diagnostics(source)
    )


def ir_preview(source: str) -> str:
    """Render the compiled strategy graph as a compact tree; never raises."""
    try:
        graph = compile_source(source)
    except Exception:
        return _render_errors(source)
    return _render_graph(graph)


def ir_json(source: str) -> str:
    """Render the canonical IR dict as two-space-indented JSON; never raises."""
    try:
        ir = compile_to_dict(source)
    except Exception:
        return _render_errors(source)
    return json.dumps(ir, indent=2)
