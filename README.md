<div align="center">

<img src="assets/nano-hex.png" alt="Nano logo" width="180" />

# Nano

### A deterministic DSL for replayable, host-governed decision rules.

[![CI](https://github.com/DBarr3/Nano/actions/workflows/ci.yml/badge.svg)](https://github.com/DBarr3/Nano/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-22d3ee.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-38bdf8.svg)](pyproject.toml)

</div>

> **Alpha reference implementation (v0.1.0).** Nano compiles a deliberately small `.nano` strategy into validated, serializable IR. Its reference runtime evaluates caller-supplied numeric signals on a caller-supplied schedule and returns proposed actions (`Intent` values) plus an ordered event log. A host-owned gate decides whether to approve any proposal.

Nano is for systems that need repeatable, inspectable threshold decisions without letting the decision rule call an exchange, API, or other external system directly. The checked-in examples are trading-oriented, but the core contract is useful anywhere a host supplies numeric signals, owns the policy boundary, and needs deterministic replay.

## Why Nano?

A host application often needs to answer two separate questions:

1. **What rule should propose an action?**
2. **May that action have consequences here and now?**

Nano keeps those questions separate. A `.nano` program describes the first as a compact, versioned artifact. The host retains the second through its own `DecisionGate`. This makes rule evaluation easy to replay, test, and audit without treating the rule as an authority to act.

Nano does **not** include an LLM runtime, automatic escalation, a live data feed, an exchange/API connector, or an action executor. Those remain host concerns.

## From source to a governed decision

```text
.nano source
    |
    v
lexer -> parser -> canonical StrategyGraph IR
    |
    v
reference interpreter + injected MarketFrame
    |
    v
Intent(s) + ordered per-run event log
    |
    v
optional NanoBridge -> host DecisionGate -> Decision record(s)
```

The reference interpreter is a pure function of a validated strategy graph and a `MarketFrame`: the same inputs produce the same result. A bridge replay is deterministic only when the host gate is deterministic too; `Backtester.verify_replay()` compares two complete runs and reports divergence.

The base event log is returned in memory with each result. Durable storage, signed receipts, and real-world actuation are outside the core runtime.

## Run a real strategy

Create an environment and install the package from a checkout:

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -e ".[dev]"
python -m pytest -q
```

This is valid Nano v0.1.0 source from the checked-in conformance corpus:

<!-- README-EXAMPLE:START -->
```nano
strategy Momentum {
  every 5m {
    if RSI(14) < 30 {
      buy(BTC, 0.91)
    }
  }
}
```
<!-- README-EXAMPLE:END -->

`RSI(14)` is a source-level signal convention. In v0.1.0, the host computes and injects the `RSI` series; the lookback label is not stored separately in strategy IR. See the [language reference](docs/language.md) for the full rule.

Compile and run it against an injected frame:

```python
from pathlib import Path

from nano.compiler import compile_source
from nano.runtime import MarketFrame, execute

source = Path("nano/examples/momentum.nano").read_text(encoding="utf-8")
graph = compile_source(source)
frame = MarketFrame(
    timestamps=(0, 300),
    signals={"RSI": (45.0, 22.0)},
)

result = execute(graph, frame)
print([intent.to_dict() for intent in result.intents])
# [{'intent': 'BUY', 'timestamp': 300, 'asset': 'BTC', 'confidence': 0.91}]
```

To involve policy, provide a complete host gate. The gate returns a record; it does not cause Nano to place an order or call an API:

```python
from nano.bridge import Decision, NanoBridge


class ApproveForDemo:
    def decide(self, intent, *, frame):
        return Decision(intent=intent, approved=True, reason="demo policy")


bridge = NanoBridge(ApproveForDemo())
bridge.load(graph.to_dict())
bridge_result = bridge.run(frame)
print([decision.to_dict() for decision in bridge_result.decisions])
```

## The language is intentionally small

| Current capability | What it means |
| --- | --- |
| One strategy, schedule, and rule | A v0.1 strategy has at most one `every` block and one `if` rule. |
| Numeric, host-provided signals | Conditions compare named signal series with numeric literals; Nano does not calculate indicators or fetch data. |
| AND-only conditions | Every condition must pass before the rule emits its intents. |
| Five intent actions | `buy`, `sell`, `execute`, `pause`, and `observe` emit proposals. `execute()` does not execute code. |
| Manifest validation | The strategy IR rejects unknown node/effect names and intent nodes without `intent.emit`; it is not a static type system. |
| Agent labels | `agent Name` is metadata today; the interpreter does not coordinate agents. |

There are no variables, arithmetic, functions, imports, `or`/`not`, user-defined actions, type checking, or CLI in the current implementation. The exact grammar and execution semantics are documented in [docs/language.md](docs/language.md).

## What ships today

| Implemented and tested | Experimental or optional | Not implemented |
| --- | --- | --- |
| `.nano` lexer, parser, canonical strategy IR, and reference interpreter | `PatternStore` lookup primitive (not wired into the runtime) | LLM calls, automatic escalation, or agent orchestration |
| Host `DecisionGate` bridge and deterministic replay checker | `LoopGraph` validation/hash helpers and a deterministic simulator protocol | CLI, type system, `Series<T>`, or general strategy graphs |
| Diagnostics, semantic tokens, and IR preview helpers | Protocol-C provenance adapter when its optional dependency is installed | Live feeds, exchange/API execution, or persistent core audit storage |
| Source/IR conformance corpus and strategy corpus | Real quantum-hardware dispatch | Autonomous loop execution or self-modifying deployment |

For a fuller implementation map, see [Architecture](docs/architecture.md) and [Status](docs/status.md).

## A tested strategy corpus

Nano includes a paired source/IR corpus that keeps the language contract concrete:

- [`nano/examples/`](nano/examples/) contains the core conformance fixtures.
- [`nano/library/`](nano/library/README.md) contains 15 trading-oriented strategies across momentum, mean-reversion, trend, volatility, volume, and risk categories.

Each pair is compiled, round-tripped through `StrategyGraph`, and replayed in the test suite. The corpus demonstrates syntax and deterministic behavior; it is not a strategy registry, a performance guarantee, or production trading advice.

## Documentation

| Need | Start here |
| --- | --- |
| Exact grammar and runtime semantics | [Language reference](docs/language.md) |
| Module boundaries and data flow | [Architecture](docs/architecture.md) |
| Implemented vs. experimental vs. planned work | [Status](docs/status.md) |
| Strategy-corpus conventions | [Strategy corpus](nano/library/README.md) |
| Integration and contribution setup | [Contributing](CONTRIBUTING.md) |
| Security boundaries and reporting | [Security policy](SECURITY.md) |
| Design essays and research directions | [Paper series](docs/papers/README.md) |

The paper series records design arguments and research directions; it is not the API specification. When a paper and the reference documentation differ, the source and tests define current behavior.

## Contributing

Nano is most useful when its compact contract stays explicit. Contributions should preserve deterministic reference execution, the intent/gate boundary, conformance coverage, and clear implemented-versus-planned labeling. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and contribution paths.
