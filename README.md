<div align="center">

<img src="assets/nano-hex.png" alt="Nano logo" width="210" />

# Nano

### A deterministic DSL for replayable, host-governed decision rules.

[![CI](https://github.com/DBarr3/Nano/actions/workflows/ci.yml/badge.svg)](https://github.com/DBarr3/Nano/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-22d3ee.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-38bdf8.svg)](pyproject.toml)

</div>

> **For quant teams and product engineers: write familiar decision rules, replay them against your own signals, and keep final authority in your own controls.**
>
> Nano is a small, Python-embeddable language for transparent threshold rules. It compiles source into validated IR, evaluates host-provided numeric signals deterministically, and returns proposed `Intent` values plus an ordered run log—not an API call or an order.

**Alpha reference implementation (v0.1.0).** Nano is for systems that need repeatable, inspectable decisions without letting the rule itself call an exchange, API, or other external system. The examples are trading-oriented, but the core contract works anywhere a host supplies numeric signals and owns the policy boundary.

## Quick start: compile, run, and verify

From a fresh checkout, run a tested Momentum strategy and then the full suite:

```bash
git clone https://github.com/DBarr3/Nano.git
cd Nano
python -m venv .venv

# macOS/Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install -e ".[dev]"
python examples/momentum_demo.py
python -m pytest -q
```

The demo compiles the checked-in strategy, injects two RSI values, and prints the proposal that crosses the threshold:

```text
BUY BTC at timestamp=300 (confidence=0.91)
```

This is the small `.nano` program it runs:

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

`RSI(14)` is a source-level signal convention. In v0.1.0, the host computes and injects the `RSI` series; Nano does not calculate indicators or fetch market data. See the [language reference](docs/language.md) for the exact contract.

## How Nano fits into your stack

![From a Nano strategy to a host-governed decision](assets/nano-governed-decision-flow.svg)

Nano owns parsing, IR validation, and deterministic reference evaluation. Your host owns data quality, policy, persistence, and any real-world action. The same graph and frame produce the same reference result; bridge replay is deterministic when the host gate is deterministic too.

To add policy, provide a complete gate. Nano records its decision; it never places an order or calls an API:

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

## Explore the quant strategy library

The strategy library is Nano's community on-ramp: a small, tested collection of familiar trading ideas translated into the DSL. It currently contains **15 paired strategies** across six categories.

| Momentum | Mean reversion | Trend | Volatility | Volume | Risk |
| --- | --- | --- | --- | --- | --- |
| 4 strategies | 3 strategies | 3 strategies | 2 strategies | 2 strategies | 1 strategy |

Every entry pairs readable `.nano` source with expected IR. The test suite verifies compilation, `StrategyGraph` round-tripping, and deterministic replay. Use the library to learn the language, prototype an integration, or contribute a well-specified strategy—not as a performance claim, live signal service, or trading recommendation.

**Bring a rule to the library.** Start with a familiar strategy, document the host-provided signal convention, add its expected IR, and let the conformance suite keep the contract honest.

[Browse the strategy library →](nano/library/README.md) · [Add a strategy →](CONTRIBUTING.md#add-a-strategy) · [Propose a language change →](https://github.com/DBarr3/Nano/issues/new?template=language-change.yml)

## Build with Nano

Nano stays approachable because its contract is deliberately small and every change is reviewable. We welcome:

- **Quant researchers** translating a strategy into a source/IR pair with a clear signal contract.
- **Application engineers** improving host integration, replay coverage, documentation, or developer experience.
- **Language contributors** proposing grammar or IR changes through a focused issue before implementation.

Strategy and language proposals start with structured GitHub issue forms; focused pull requests then carry the source, expected IR, tests, and rationale together. See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution guide and [the issue templates](.github/ISSUE_TEMPLATE/) for a place to begin.

## Why the boundary matters

An application often needs to answer two separate questions:

1. **What rule should propose an action?**
2. **May that action have consequences here and now?**

Nano keeps them separate. A `.nano` program describes the first as a compact, versioned artifact; the host retains the second through its own `DecisionGate`. That makes rule evaluation easy to replay, test, and audit without turning a rule into an authority to act.

Nano does **not** include an LLM runtime, automatic escalation, a live data feed, an exchange/API connector, or an action executor. Those remain host concerns.

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
| Source/IR conformance corpus and strategy library | Real quantum-hardware dispatch | Autonomous loop execution or self-modifying deployment |

For a fuller implementation map, see [Architecture](docs/architecture.md) and [Status](docs/status.md).

## Documentation

| Need | Start here |
| --- | --- |
| Run the first example | [Momentum demo](examples/momentum_demo.py) |
| Explore or contribute a strategy | [Strategy library](nano/library/README.md) |
| Exact grammar and runtime semantics | [Language reference](docs/language.md) |
| Module boundaries and data flow | [Architecture](docs/architecture.md) |
| Implemented vs. experimental vs. planned work | [Status](docs/status.md) |
| Integration and contribution setup | [Contributing](CONTRIBUTING.md) |
| Security boundaries and reporting | [Security policy](SECURITY.md) |
| Design essays and research directions | [Paper series](docs/papers/README.md) |

The paper series records design arguments and research directions; it is not the API specification. When a paper and the reference documentation differ, the source and tests define current behavior.
