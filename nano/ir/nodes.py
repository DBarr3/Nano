"""Nano IR node primitives.

Milestone-1 vocabulary is deliberately tiny: Schedule, Condition, Intent, and
(placeholder) Agent. All nodes are immutable; graphs never mutate after load.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from .schema import (
    CONDITION_OPERATORS,
    INTENT_ACTIONS,
    IRValidationError,
)


@dataclass(frozen=True)
class ScheduleNode:
    interval: str

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "ScheduleNode":
        interval = data.get("interval")
        if not isinstance(interval, str) or not interval:
            raise IRValidationError("Schedule node requires a non-empty 'interval'")
        return ScheduleNode(interval=interval)

    def to_dict(self) -> dict:
        return {"type": "Schedule", "interval": self.interval}


@dataclass(frozen=True)
class ConditionNode:
    signal: str
    operator: str
    value: float

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "ConditionNode":
        signal = data.get("signal")
        operator = data.get("operator")
        value = data.get("value")
        if not isinstance(signal, str) or not signal:
            raise IRValidationError("Condition node requires a non-empty 'signal'")
        if operator not in CONDITION_OPERATORS:
            raise IRValidationError(
                f"Condition operator {operator!r} not in {sorted(CONDITION_OPERATORS)}"
            )
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise IRValidationError("Condition 'value' must be numeric")
        return ConditionNode(signal=signal, operator=operator, value=value)

    def evaluate(self, observed: float) -> bool:
        op = self.operator
        if op == "<":
            return observed < self.value
        if op == "<=":
            return observed <= self.value
        if op == ">":
            return observed > self.value
        if op == ">=":
            return observed >= self.value
        if op == "==":
            return observed == self.value
        return observed != self.value

    def to_dict(self) -> dict:
        return {
            "type": "Condition",
            "signal": self.signal,
            "operator": self.operator,
            "value": self.value,
        }


@dataclass(frozen=True)
class IntentNode:
    action: str
    asset: Optional[str] = None
    confidence: Optional[float] = None

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "IntentNode":
        action = data.get("action")
        if action not in INTENT_ACTIONS:
            raise IRValidationError(
                f"Intent action {action!r} not in {sorted(INTENT_ACTIONS)}"
            )
        asset = data.get("asset")
        if asset is not None and (not isinstance(asset, str) or not asset):
            raise IRValidationError("Intent 'asset' must be a non-empty string")
        confidence = data.get("confidence")
        if confidence is not None:
            if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
                raise IRValidationError("Intent 'confidence' must be numeric")
            if not 0.0 <= float(confidence) <= 1.0:
                raise IRValidationError("Intent 'confidence' must be within [0, 1]")
        return IntentNode(action=action, asset=asset, confidence=confidence)

    def to_dict(self) -> dict:
        out: dict = {"type": "Intent", "action": self.action}
        if self.asset is not None:
            out["asset"] = self.asset
        if self.confidence is not None:
            out["confidence"] = self.confidence
        return out


@dataclass(frozen=True)
class AgentNode:
    """Placeholder for named behavior blocks (post-Milestone-3)."""

    name: str

    @staticmethod
    def from_dict(data: Mapping[str, Any]) -> "AgentNode":
        name = data.get("name")
        if not isinstance(name, str) or not name:
            raise IRValidationError("Agent node requires a non-empty 'name'")
        return AgentNode(name=name)

    def to_dict(self) -> dict:
        return {"type": "Agent", "name": self.name}
