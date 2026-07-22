"""Deterministic backtester over historical MarketFrames.

Embedding note: this module is designed to be embedded in a host trading
platform's execution layer. Every import is absolute from the ``nano``
package so the file works unchanged wherever the ``nano`` package is installed.

Invariant protected here: **bit-identical replay.** A backtest is a pure
function of (graph, frames, risk engine); running it twice must produce
byte-for-byte identical reports. ``verify_replay`` is the Milestone 5
acceptance test — any divergence (a stateful or nondeterministic risk engine,
ambient clock, hidden randomness) raises ``ReplayDivergence`` instead of
silently producing an untrustworthy simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

from nano.bridge.ats_bridge import BridgeResult, NanoBridge, DecisionGate
from nano.ir.graph import StrategyGraph
from nano.runtime.effects import LogEntry
from nano.runtime.interpreter import MarketFrame


class ReplayDivergence(Exception):
    """Two runs of the same backtest produced different reports."""


@dataclass(frozen=True)
class BacktestReport:
    """Aggregate of a full backtest: exact counts plus the complete audit trail."""

    frames_run: int
    intents_emitted: int
    approved: int
    rejected: int
    results: Tuple[BridgeResult, ...]
    log: Tuple[LogEntry, ...]

    def to_dict(self) -> dict:
        return {
            "frames_run": self.frames_run,
            "intents_emitted": self.intents_emitted,
            "approved": self.approved,
            "rejected": self.rejected,
            "results": [r.to_dict() for r in self.results],
            "log": [e.to_dict() for e in self.log],
        }


class Backtester:
    """Runs a validated graph over recorded frames through the bridge + decision gate."""

    def __init__(self, gate: DecisionGate) -> None:
        self._gate = gate

    def run(self, graph: StrategyGraph, frames: Sequence[MarketFrame]) -> BacktestReport:
        """Execute the graph over every frame in order; aggregate the results.

        The graph is round-tripped through ``StrategyGraph.from_dict`` via the
        bridge's ``load``, so the effect manifest is re-verified at the start
        of every backtest.
        """
        bridge = NanoBridge(self._gate)
        bridge.load(graph.to_dict())

        results: list[BridgeResult] = []
        log: list[LogEntry] = []
        intents_emitted = 0
        approved = 0
        rejected = 0

        for frame in frames:
            result = bridge.run(frame)
            results.append(result)
            log.extend(result.log)
            intents_emitted += len(result.intents)
            for decision in result.decisions:
                if decision.approved:
                    approved += 1
                else:
                    rejected += 1

        return BacktestReport(
            frames_run=len(results),
            intents_emitted=intents_emitted,
            approved=approved,
            rejected=rejected,
            results=tuple(results),
            log=tuple(log),
        )

    def verify_replay(self, graph: StrategyGraph, frames: Sequence[MarketFrame]) -> bool:
        """Milestone 5 acceptance test: the whole backtest replays bit-identically.

        Runs the backtest twice and compares the serialized reports. Returns
        True on equality; raises ``ReplayDivergence`` otherwise.
        """
        first = self.run(graph, frames).to_dict()
        second = self.run(graph, frames).to_dict()
        if first != second:
            raise ReplayDivergence(
                f"Backtest of {graph.name!r} did not replay bit-identically: "
                "the risk engine or environment is nondeterministic"
            )
        return True
