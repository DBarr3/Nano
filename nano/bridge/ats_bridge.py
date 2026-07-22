"""Risk-gate adapter — the Milestone 5 hand-off from Nano intents to a risk engine.

Embedding note: this module is designed to be embedded in a host trading
platform's execution layer. Every import is absolute from the ``nano`` package
so the file works unchanged wherever the ``nano`` package is installed.

Invariant protected here: **the bridge never executes anything.** Nano
strategies emit Intents; the injected risk engine disposes of each one; an
approved ``RiskDecision`` is still just a record handed back to the caller.
The host platform's own execution/release-gate discipline consumes those
records — components propose, gates decide. The bridge is a pure function of
(graph, frame, risk engine): no ambient clock, no randomness, no I/O in the
run path, so every run is deterministic and replayable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol, Tuple, Union

from nano.ir.graph import StrategyGraph
from nano.ir.schema import IRValidationError
from nano.runtime.effects import Intent, LogEntry
from nano.runtime.interpreter import MarketFrame, execute


class BridgeError(Exception):
    """The bridge was used out of order or a risk engine broke its contract."""


@dataclass(frozen=True)
class RiskDecision:
    """A risk engine's disposition of a single Intent.

    ``approved=True`` does not execute anything — it is a record the caller's
    own gate discipline may act on.
    """

    intent: Intent
    approved: bool
    reason: str

    def to_dict(self) -> dict:
        return {
            "intent": self.intent.to_dict(),
            "approved": self.approved,
            "reason": self.reason,
        }


class RiskEngine(Protocol):
    """Downstream gate: disposes of each Intent the bridge forwards.

    Implementations must be deterministic functions of (intent, frame) for
    replay verification to hold; the bridge does not (and cannot) enforce
    that, but the backtester's ``verify_replay`` will expose violations.
    """

    def dispose(self, intent: Intent, *, frame: MarketFrame) -> RiskDecision: ...


@dataclass(frozen=True)
class BridgeResult:
    """One frame's complete, append-only account: intents, decisions, audit log.

    Rejected intents are never suppressed — every emitted intent appears in
    ``intents`` and in the log alongside its decision.
    """

    intents: Tuple[Intent, ...]
    decisions: Tuple[RiskDecision, ...]
    log: Tuple[LogEntry, ...]

    def to_dict(self) -> dict:
        return {
            "intents": [i.to_dict() for i in self.intents],
            "decisions": [d.to_dict() for d in self.decisions],
            "log": [e.to_dict() for e in self.log],
        }


class NanoBridge:
    """Loads validated Nano IR and streams frames through interpreter + risk gate."""

    def __init__(self, risk_engine: RiskEngine) -> None:
        self._risk_engine = risk_engine
        self._graph: StrategyGraph | None = None

    @property
    def graph(self) -> StrategyGraph | None:
        return self._graph

    def load(self, source: Union[Mapping[str, Any], str, Path]) -> StrategyGraph:
        """Validate IR from a mapping or a JSON file path.

        All validation (including effect-manifest verification) happens in
        ``StrategyGraph.from_dict``; ``ManifestViolation`` / ``IRValidationError``
        propagate to the caller untouched.
        """
        if isinstance(source, Mapping):
            data = source
        else:
            text = Path(source).read_text(encoding="utf-8")
            try:
                data = json.loads(text)
            except json.JSONDecodeError as exc:
                raise IRValidationError(f"Source {source!r} is not valid JSON: {exc}") from exc
        graph = StrategyGraph.from_dict(data)
        self._graph = graph
        return graph

    def run(self, frame: MarketFrame) -> BridgeResult:
        """Execute the loaded graph over one frame; forward intents to the gate.

        Pure function of (loaded graph, frame, risk engine). Nothing is
        executed here: decisions are records, not actions.
        """
        if self._graph is None:
            raise BridgeError("No strategy loaded; call load() before run()")

        execution = execute(self._graph, frame)
        log: list[LogEntry] = list(execution.log)
        decisions: list[RiskDecision] = []

        for intent in execution.intents:
            log.append(
                LogEntry(
                    event="intent.forwarded",
                    timestamp=intent.timestamp,
                    detail=f"{intent.action} asset={intent.asset} -> risk engine",
                )
            )
            decision = self._risk_engine.dispose(intent, frame=frame)
            if not isinstance(decision, RiskDecision):
                raise BridgeError(
                    f"Risk engine returned {type(decision).__name__}, expected RiskDecision"
                )
            if decision.intent != intent:
                raise BridgeError(
                    "Risk engine returned a decision for a different intent than forwarded"
                )
            decisions.append(decision)
            log.append(
                LogEntry(
                    event="risk.approved" if decision.approved else "risk.rejected",
                    timestamp=intent.timestamp,
                    detail=decision.reason,
                )
            )

        return BridgeResult(
            intents=execution.intents,
            decisions=tuple(decisions),
            log=tuple(log),
        )
