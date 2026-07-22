"""StrategyGraph — the loadable, validated unit of Nano IR.

Load-time validation is the security boundary: manifest violations and unknown
node types are rejected here, never discovered at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Tuple

from .nodes import AgentNode, ConditionNode, IntentNode, ScheduleNode
from .schema import (
    IRValidationError,
    KNOWN_EFFECTS,
    ManifestViolation,
    NANO_IR_VERSION,
    NODE_TYPES,
)

_NODE_PARSERS = {
    "Schedule": ScheduleNode.from_dict,
    "Condition": ConditionNode.from_dict,
    "Intent": IntentNode.from_dict,
    "Agent": AgentNode.from_dict,
}


@dataclass(frozen=True)
class StrategyGraph:
    name: str
    effects: Tuple[str, ...]
    schedule: Optional[ScheduleNode]
    conditions: Tuple[ConditionNode, ...]
    intents: Tuple[IntentNode, ...]
    agents: Tuple[AgentNode, ...]

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "StrategyGraph":
        if data.get("type") != "Strategy":
            raise IRValidationError("Root 'type' must be 'Strategy'")
        version = data.get("nanoIrVersion")
        if version != NANO_IR_VERSION:
            raise IRValidationError(
                f"nanoIrVersion {version!r} unsupported (expected {NANO_IR_VERSION!r})"
            )
        name = data.get("name")
        if not isinstance(name, str) or not name:
            raise IRValidationError("Strategy requires a non-empty 'name'")

        effects_raw = data.get("effects")
        if not isinstance(effects_raw, list) or not effects_raw:
            raise IRValidationError("Strategy requires a non-empty 'effects' manifest")
        unknown_effects = set(effects_raw) - KNOWN_EFFECTS
        if unknown_effects:
            raise IRValidationError(f"Unknown effects declared: {sorted(unknown_effects)}")
        effects = tuple(effects_raw)

        nodes_raw = data.get("nodes")
        if not isinstance(nodes_raw, list) or not nodes_raw:
            raise IRValidationError("Strategy requires a non-empty 'nodes' list")

        schedules: list[ScheduleNode] = []
        conditions: list[ConditionNode] = []
        intents: list[IntentNode] = []
        agents: list[AgentNode] = []
        for node_data in nodes_raw:
            node_type = node_data.get("type")
            if node_type not in NODE_TYPES:
                raise IRValidationError(f"Unknown node type {node_type!r}")
            node = _NODE_PARSERS[node_type](node_data)
            if isinstance(node, ScheduleNode):
                schedules.append(node)
            elif isinstance(node, ConditionNode):
                conditions.append(node)
            elif isinstance(node, IntentNode):
                intents.append(node)
            else:
                agents.append(node)

        if len(schedules) > 1:
            raise IRValidationError("At most one Schedule node is allowed")
        if intents and "intent.emit" not in effects:
            raise ManifestViolation(
                "Graph declares Intent nodes but 'intent.emit' is not in the effect manifest"
            )

        return StrategyGraph(
            name=name,
            effects=effects,
            schedule=schedules[0] if schedules else None,
            conditions=tuple(conditions),
            intents=tuple(intents),
            agents=tuple(agents),
        )

    def to_dict(self) -> dict:
        nodes: list[dict] = []
        if self.schedule is not None:
            nodes.append(self.schedule.to_dict())
        nodes.extend(c.to_dict() for c in self.conditions)
        nodes.extend(i.to_dict() for i in self.intents)
        nodes.extend(a.to_dict() for a in self.agents)
        return {
            "type": "Strategy",
            "nanoIrVersion": NANO_IR_VERSION,
            "name": self.name,
            "effects": list(self.effects),
            "nodes": nodes,
        }
