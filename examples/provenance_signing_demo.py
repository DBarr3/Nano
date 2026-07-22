"""Runnable demo: sign every risk-gate decision with Protocol-C.

Requires the optional dependency:
    pip install aether-protocol-c

Run:
    python examples/provenance_signing_demo.py

What this shows: ProvenanceGate wraps any DecisionGate transparently --
the strategy, the compiler, and the decision itself are all untouched. Every
decide() call additionally produces a signed, independently re-verifiable
receipt in an append-only audit log. Nothing here is a language feature; a
`.nano` author has no way to see or influence this layer.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from nano.bridge import NanoBridge, ProvenanceGate, Decision
from nano.compiler import compile_source
from nano.runtime.interpreter import MarketFrame

SOURCE = """
strategy DemoMomentum {
    every 5m {
        if RSI(14) < 30 {
            buy(BTC, 0.9)
        }
    }
}
"""


class ThresholdGate:
    """A toy risk engine: approve only above a confidence floor."""

    def __init__(self, floor: float = 0.8) -> None:
        self._floor = floor

    def decide(self, intent, *, frame):
        approved = (intent.confidence or 0.0) >= self._floor
        reason = f"confidence>={self._floor}" if approved else "confidence below floor"
        return Decision(intent=intent, approved=approved, reason=reason)


def main() -> None:
    graph = compile_source(SOURCE)
    frame = MarketFrame(timestamps=(0, 300), signals={"RSI": (45.0, 22.0)})

    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "provenance_audit.jsonl"

        engine = ProvenanceGate(
            ThresholdGate(floor=0.8),
            log_path=log_path,
            account_state={"capital": 100_000.0, "equity": 100_000.0, "risk_limit": 0.5},
        )

        bridge = NanoBridge(engine)
        bridge.load(graph.to_dict())
        result = bridge.run(frame)

        for decision in result.decisions:
            print(f"{decision.intent.action} {decision.intent.asset} -> approved={decision.approved}")

        for order_id, receipt in engine.receipts.items():
            # Independent re-verification: only the public commitment +
            # signature are used, no secret material was ever retained.
            assert engine.verify_receipt(order_id)
            print(f"receipt {order_id}: verified={receipt.verified}")

        print(f"audit trail: {log_path} ({log_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
