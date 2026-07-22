<div align="center">

<img src="assets/nano-hex.png" alt="Nano — deterministic AI agent compiler" width="210" />

# Nano

### The compiler language for autonomous AI agents

**Compile reasoning into deterministic, auditable execution.**

*Reason once. Compile forever.*

[![CI](https://github.com/DBarr3/Nano/actions/workflows/ci.yml/badge.svg)](https://github.com/DBarr3/Nano/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-22d3ee.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-38bdf8.svg)](pyproject.toml)
[![Tests](https://img.shields.io/badge/tests-173%20passing-22c55e.svg)](tests)
[![Made by Aether AI](https://img.shields.io/badge/made%20by-Aether%20AI-0ea5e9.svg)](https://aethersystems.net)

**[Website](https://aethersystems.net)** · **[Playground (Aether Code) →](https://app.aethersystems.net/code)** · **[Papers →](docs/papers/README.md)**

</div>

---

> Current AI agents ask a model what to do on every step.
>
> Nano compiles reasoning into execution graphs that can **run, replay, audit, and improve**.

> **Status:** research preview · Milestones 1–6 shipped · **173 tests passing**. The IR, compiler,
> interpreter, risk-gate bridge, and optimization loop are real and tested; the CLI and
> `Series<T>` typing are still design. [Full status ↓](#status--whats-real)

## What is Nano?

Nano is an open-source **compiler and runtime for deterministic AI agents**.

Today's agents repeatedly do:

```
Observe → LLM → Decide → Act → Repeat
```

Expensive, slow, and different every run. Nano changes the loop:

```
Reason once
   ↓
Compile behavior
   ↓
Execute deterministically
   ↓
Escalate only when needed
```

Instead of running an LLM for every decision, Nano compiles agent behavior into reusable
execution graphs. Known situations execute deterministically. Unknown situations escalate
back to reasoning.

The result:

- **Lower inference cost** — the model runs on escalation, not on every tick
- **Reproducible behavior** — identical inputs replay bit-for-bit, log included
- **Audit trails** — every decision is proposed, gated, and recorded
- **Safer autonomous systems** — programs emit intents; a policy gate decides

> Nano is not a replacement for intelligence.
>
> Nano is the **compiled memory** of intelligence.

## Why Nano exists

Current AI agents spend intelligence repeatedly. Nano compiles intelligence once and reuses it.

The model is the **author** and the **escalation path** — never the per-tick decision
bottleneck. That single inversion is what makes deterministic AI agents possible: inference
becomes the exception; execution becomes the default.

## Nano vs. the alternatives

| Approach | Strength | Limitation |
|---|---|---|
| Hand-written scripts | Fast | No reasoning layer, no audit trail |
| LLM-in-the-loop agents | Flexible | Expensive, slow, inconsistent |
| Workflow engines | Reliable | Heavy ops, not AI-native |
| **Nano** | **Intelligence + deterministic execution** | New architecture |

<details>
<summary><b>Full capability comparison</b></summary>

<br>

| Capability | Nano | Typical agent frameworks |
|---|---|---|
| Deterministic, bit-identical replay | ✅ core guarantee | ❌ |
| Serializable execution-graph IR | ✅ | ❌ |
| LLM required on every decision | ❌ — only on escalation | usually |
| Actions gated by a policy layer | ✅ enforced in the IR | limited / opt-in |
| Signed provenance receipts | ✅ optional adapter | rare |
| Backtest / live parity | ✅ same artifact | rare |
| Dedicated server infrastructure | ❌ pure Python | varies |

</details>

The full argument — the orchestration crisis, prompt compilation, the state-management
landscape — is [Paper 01: Why Nano](docs/papers/01-why-nano.md).

Any system where an AI proposes actions and something must decide whether they run is a Nano
target: autonomous agents, automation pipelines, monitoring and response workflows, robotics —
anywhere an **Observe → Decide → Act → Record** loop exists. Quantitative trading is the
**first workload, not the product**: deterministic inputs, replayable history, measurable
outcomes.

---

## Architecture — the missing layer between AI and execution

```
        .nano source (human- or AI-authored)
                      │
                      ▼
                  Compiler
        (lexer → parser → type checks)
                      │
                      ▼
                   Nano IR
   (deterministic, serializable execution graph)
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
    Backtest        Paper         Live
    (recorded      (simulated    (via your
     frames)        gate)         risk gate)
```

Everything compiles to **Nano IR** — a hardware-independent, deterministic, serializable
execution graph. The same program runs in local development, historical backtesting, and live
execution because it *is* the same artifact:

```
Write Once. Optimize Everywhere. Execute Anywhere.
```

Every compiled workflow carries provenance and a fallback route. Known states execute
deterministically; unknown states escalate back to reasoning.

## See Nano in action

```nano
strategy Momentum {

  every 5m {

    observe market

    if RSI(14) < 30
    and volume > average {

      execute()
    }
  }
}
```

What happens to that file:

```
strategy.nano
     ↓
  Compiler          type-checked, effect-checked
     ↓
  Nano IR           content-addressed execution graph
     ↓
  Replay            bit-identical against recorded frames
     ↓
  Decision gate     intent approved or rejected, with reason
     ↓
  Recorded result   append-only audit log
```

The scheduler owns the clock, the gate owns every order, and every decision is replayable
bit-for-bit.

## Quickstart

> **Prefer the browser?** The Nano compiler runs live in **[Aether Code](https://app.aethersystems.net/code)** —
> a VS Code–style web IDE with syntax highlighting, inline diagnostics, and an IR preview. Write a
> `.nano` strategy, compile it, and replay it deterministically without installing anything.

```python
from nano.compiler import compile_source
from nano.runtime.interpreter import MarketFrame, execute
from nano.bridge import NanoBridge

graph = compile_source(open("strategy.nano").read())

frame = MarketFrame(timestamps=(0,), signals={"RSI": [25.0]})

# Direct interpretation — pure, deterministic
result = execute(graph, frame)

# Or bridge into your own risk engine (any object with a .dispose() method)
bridge = NanoBridge(my_risk_engine)
bridge.load(graph.to_dict())
frame_result = bridge.run(frame)
```

See [`nano/examples/`](nano/examples/) for the conformance corpus (`basic_rsi`, `momentum`,
`mean_reversion`, `volatility_guard`, `risk_manager`, `ai_agent`) — each exists as `.nano`
source and hand-written IR JSON that must match bit-for-bit.

### Find your path

| I want to… | Go to |
|---|---|
| **Run something now** | [Quickstart](#quickstart) above · [Aether Code](https://app.aethersystems.net/code) |
| **See real strategies** | [`nano/examples/`](nano/examples/) · [`nano/library/`](nano/library/README.md) |
| **Read the argument in depth** | [The paper series](docs/papers/README.md) — one question per paper |
| **Understand the guarantees** | [Deterministic by construction](#deterministic-by-construction) |
| **See how it's built** | [BUILD_ORDER.md](BUILD_ORDER.md) |
| **Know what's real vs. roadmap** | [Status](#status--whats-real) |
| **Contribute** | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

## The defining rule: agents propose, gates decide

A Nano program **cannot act on the world directly**. There is no exchange API, no
side-effecting call in the language — programs emit *intents*, and a pluggable gate disposes of
each one (approve or reject, with a recorded reason). In trading that gate is a risk engine
(implement the `DecisionGate` protocol in `nano/bridge/`); in any other agentic system it's
whatever policy layer owns the consequences.

Every action is therefore proposed, gated, logged, and replayable — which is what makes
autonomy auditable. It also enables AI-in-the-loop improvement: an analysis system proposes
evidence-backed patches, a human disposes, the compiler recompiles, and release gates govern
deployment. **Nothing self-modifies silently.**

For deployments that need proof a decision happened — not just a log line — an optional adapter
(`nano/bridge/provenance.py`, `pip install aether-nano[provenance]`) wraps any gate so every
disposition also produces a signed, independently re-verifiable receipt. Entirely outside the
language.

## Deterministic by construction

| Guarantee | How |
|---|---|
| Deterministic replay | No ambient clock or RNG — time and entropy are injected, logged inputs |
| Strategies can't bypass risk | No exchange API in the language; programs emit intents, the runtime disposes |
| No look-ahead in backtests | `Series<T>` types make peeking at the future a compile error *(design)* |
| Least-privilege execution | Every IR module carries an effect manifest — a capability boundary |
| Reproducible builds | Content-addressed IR, pinned package hashes |
| Gated self-improvement | AI-compiled workflows pass admission gates before any runtime loads them |

Restrictions are the feature. Nano intentionally removes sockets, randomness, arbitrary IO,
threads, and mutable globals — each one destroys replayability.

## Nano architecture roadmap

Three conceptual tiers over one compiler and one IR. A user starts with `buy when RSI < 30`
and never has to leave the language as their agents grow.

| Tier | Question it answers | State |
|---|---|---|
| **Nano** (this repo) | *What should the agent do?* — rules and intents | shipped |
| **Nano+** | *How should it reason and coordinate?* — memory, confidence routing, multi-agent | roadmap |
| **Nano++** | *How is complex computation optimized and secured?* — optimization, quantum research track | early |

```
Shipped        →  IR · compiler · deterministic interpreter · risk-gate bridge
                  backtester · pattern memory · editor services · optimization loop

Next           →  CLI (nano compile / replay / visualize)
                  Series<T> look-ahead typing (no-peek backtests as a compile error)

Then           →  Nano+ adaptive layer — memory, confidence routing, multi-agent
                  Real quantum-hardware dispatch (research)
```

The Nano++ autonomous optimization loop ([`nano/loop/`](nano/loop/)) already ships a
vendor-agnostic `QuantumRuntime` protocol with a deterministic `SimulatorRuntime` reference
backend. Real-hardware dispatch remains research, not a promise. Details and sequencing:
[BUILD_ORDER.md](BUILD_ORDER.md) · [Paper 14: Future Work](docs/papers/14-future-work.md).

## FAQ

**Is Nano an LLM?**
No. Nano is a compilation and execution layer. Models create reasoning; Nano compiles it into
deterministic execution graphs and runs them.

**Does Nano replace AI models?**
No — it changes *when* they run. Models author behavior and handle novel situations; compiled
graphs handle everything repeatable. Inference becomes the exception, not the default.

**Can Nano run without an LLM?**
Yes. Compiled programs execute deterministically with no model in the loop. You can write
`.nano` source by hand and never touch a model.

**Can a Nano program place an order / call an API / act on the world?**
No, by construction. Programs emit *intents*; a pluggable gate (your risk engine, policy
layer, or a human) approves or rejects each one, with a recorded reason.

**Is this only for trading?**
No. Trading is the first workload because it is the most measurable one. The architecture
targets any Observe → Decide → Act → Record loop: automation, monitoring/response, robotics.

**How is this different from LangChain or LangGraph?**
Those orchestrate live model calls; state and control flow involve the model at runtime. Nano
compiles behavior *ahead of time* into a replayable IR — the model is never the router. See
[Paper 01](docs/papers/01-why-nano.md) for the full landscape comparison.

**Is it production-ready?**
It is a research preview with 173 passing tests. The core (IR, compiler, interpreter, bridge)
is real and tested; the CLI and several typing features are still design. The
[status table](#status--whats-real) is kept honest.

## The paper series

Seventeen short papers, each answering one question — **[docs/papers/](docs/papers/README.md)**.
Start with these four; they carry the whole thesis:
[Why Nano](docs/papers/01-why-nano.md) → [The Agentic Compiler](docs/papers/02-the-agentic-compiler.md)
→ [Determinism](docs/papers/03-determinism.md) → [Provenance](docs/papers/04-provenance.md).

| Papers | Theme |
|---|---|
| [Why Nano](docs/papers/01-why-nano.md) · [The Agentic Compiler](docs/papers/02-the-agentic-compiler.md) · [Determinism](docs/papers/03-determinism.md) · [Provenance](docs/papers/04-provenance.md) | the core thesis |
| [Why Not Go](docs/papers/05-why-not-go.md) · [Why Not TypeScript](docs/papers/06-why-not-typescript.md) · [Nano vs. Pine](docs/papers/07-nano-vs-pine.md) | positioning |
| [LLM Integration](docs/papers/08-llm-integration.md) · [Autonomous Systems](docs/papers/09-autonomous-systems.md) · [The Nano Family](docs/papers/10-nano-family.md) | scope |
| [Performance](docs/papers/11-performance.md) · [Security](docs/papers/12-security.md) · [Design Principles](docs/papers/13-design-principles.md) · [Future Work](docs/papers/14-future-work.md) | engineering |
| [Closed-Loop Engineering](docs/papers/15-closed-loop-engineering.md) · [Quantum Computing](docs/papers/16-quantum-computing.md) · [Heterogeneous Compute](docs/papers/17-heterogeneous-compute.md) | the horizon |

## Status — what's real

| Shipped (tested) | Design / roadmap / research |
|---|---|
| Nano IR (`nano/ir/`) | CLI (`nano compile` / `replay` / `visualize`) |
| Reference interpreter (`nano/runtime/`) | `Series<T>` look-ahead typing |
| `.nano` → IR compiler (`nano/compiler/`) | Nano+ adaptive layer (memory, multi-agent) |
| Risk-gate bridge + backtester (`nano/bridge/`) | Real quantum-hardware dispatch |
| Editor services (`nano/aethercode/`) | Cognitive execution / confidence routing |
| Pattern cache (`nano/memory/`) + optimization loop (`nano/loop/`) | |
| Conformance corpus (`nano/examples/`) + strategy library (`nano/library/`) | |

Every claim in the docs cites shipped code or is explicitly labeled design, roadmap, or
research.

## Contributing

Contributions are welcome — the [strategy library](nano/library/README.md) is the easiest
entry point (add a classic strategy as `.nano` source + expected IR), and
[CONTRIBUTING.md](CONTRIBUTING.md) covers setup, tests, and where help is most valuable.
Security reports: see [SECURITY.md](SECURITY.md).

## Documentation

| Document | Contents |
|---|---|
| [Paper Series](docs/papers/README.md) | 17 papers — one question each |
| [Build Order](BUILD_ORDER.md) | IR-first build sequence, the intent/gate lock, milestone status |
| [Strategy Library](nano/library/README.md) | Pine-inspired quant strategy corpus + contribution guide |
| [Optimization Loop](docs/nano-optimization-loop.md) | Nano++ autonomous optimization loop overview |
| [Contributing](CONTRIBUTING.md) | Dev setup, test workflow, contribution areas |
| [Security Policy](SECURITY.md) | Reporting, threat model, what determinism does and doesn't protect |

---

<div align="center">

**Nano is part of the [Aether](https://aethersystems.net) ecosystem** — autonomous AI, quantitative
trading, and cryptographic execution provenance. Built by **Aether AI LLC**.

[Website](https://aethersystems.net) · [Aether Code (web IDE)](https://app.aethersystems.net/code) · [Papers](docs/papers/README.md) · [Strategy Library](nano/library/README.md)

<sub>If Nano's ideas resonate, a ⭐ helps others find it.</sub>

</div>

<sub>*Naming is under trademark review; the language codename and `.nano` extension are stable for
development.*</sub>
