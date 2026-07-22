# 01 — Why Nano

**Answer in one sentence:** Autonomous systems stop reasoning about the same thing over and over by compiling known reasoning into deterministic execution — Nano is the language and IR that makes that compilation possible.

---

## The central question

Watch any production agent for a week and you will see the same pattern: the overwhelming majority of its decisions are decisions it has already made. The market condition it evaluates at 09:35 is structurally identical to one it evaluated last Tuesday. The workflow branch it reasons through is the branch it reasoned through four hundred times this month. Yet the system pays for full inference every single time — in latency, in dollars, and in variance, because a probabilistic model asked the same question twice does not reliably give the same answer twice.

Human experts do not work this way. A radiologist does not re-derive anatomy for every scan; a chess master does not calculate known openings from first principles. Expertise *is* the compilation of reasoning into fast, reliable execution, with conscious deliberation reserved for the genuinely novel. Current agent architectures have no equivalent mechanism. They are permanently deliberating.

So the question Nano is built around is exactly one question:

> **How do autonomous systems stop reasoning about the same thing over and over?**

## The answer

They compile it. Concretely:

```
Reason once → Compile → Execute → Escalate only when necessary
```

1. **Reason once.** A reasoning model — Claude, GPT, Gemini, a local model; Nano is deliberately model-agnostic — works out how to handle a class of situation.
2. **Compile.** That decision is expressed as Nano IR: a small, validated, serializable execution graph. In the shipped implementation ([`nano/ir/graph.py`](../../nano/ir/graph.py)) a graph is a schedule, a set of conditions, and a set of intents, guarded by an effect manifest — authored either as IR JSON or as `.nano` source through the compiler ([`nano/compiler/`](../../nano/compiler/__init__.py)).
3. **Execute.** The deterministic runtime ([`nano/runtime/interpreter.py`](../../nano/runtime/interpreter.py)) evaluates the graph against injected inputs. Identical graph plus identical inputs yields a bit-identical result, including the audit log.
4. **Escalate only when necessary.** When observations match no compiled pattern, the system routes back to inference. The shipped memory layer ([`nano/memory/patterns.py`](../../nano/memory/patterns.py)) implements exactly this: `PatternStore.retrieve()` returns matched patterns or `escalate=True` — never a guess.

The inversion this produces is the whole point: **inference becomes the exception; execution becomes the default.** We call the compiled artifact *compiled memory* — not a cache of answers, but a cache of *decision procedures*, each carrying its confidence, its validity domain, and its provenance.

## Why this needs a language

You could try to get this effect by prompting harder, caching responses, or writing the fast path in Python. Each fails in a specific way.

Response caching fails because decisions are conditional: the value of "buy when RSI < 30 and volume is elevated" is not a cached answer, it is a *predicate over future observations*. You need a representation for the predicate, not the answer.

General-purpose languages fail because they permit too much. A Python fast path can open sockets, read the clock, consult global state, and race threads — so two runs of the "same" decision need not agree, and no one can prove after the fact why the system acted. (Papers [05](05-why-not-go.md) and [06](06-why-not-typescript.md) treat this in depth.)

Nano takes the opposite bet: **restrictions are the feature.** The language removes sockets, ambient randomness, arbitrary I/O, threads, mutable globals, and any direct actuator or exchange API. Every removal exists because that capability destroys replayability. What remains is small — and the smallness is exactly what makes "why did the agent do that?" answerable with a replay instead of a shrug (paper [03](03-determinism.md)).

There is a second structural commitment: Nano programs cannot act. The terminal output of execution is a tuple of **intents** — proposals — plus an append-only log. A downstream gate (a risk engine, an approval policy, a human) disposes. Components propose; gates decide. This is enforced in the IR itself: there is no order or actuation primitive to compile, and emitting intents at all requires `intent.emit` in the module's effect manifest, checked at load time.

## Why trading first

Nano's first workload is trading strategy execution — not because trading is the product, but because trading is the most honest test environment available: inputs are deterministic time series, history is fully replayable, and outcomes are numerically measurable. A framework that claims "compiled decisions replay bit-identically and outperform per-decision inference" can be checked there without ambiguity. The architecture itself — Observe → Decide → Act → Record — generalizes to robotics, vehicles, security response, workflow automation, and beyond (paper [09](09-autonomous-systems.md)).

## What exists today

Honestly stated: the IR, the deterministic reference interpreter, the pattern memory layer, the `.nano` → IR compiler (`nano/compiler/`), the risk-gate bridge and backtester (`nano/bridge/`), the strategy library (`nano/library/`), editor language services (`nano/aethercode/`), and the Nano++ optimization loop with a deterministic quantum simulator backend (`nano/loop/`) are implemented, covered by 121 tests. Every example compiles from `.nano` source to bit-identical IR and replays deterministically. The CLI (`nano compile` / `nano replay` / `nano visualize`) and real quantum-hardware dispatch remain design and research, tracked in [BUILD_ORDER.md](../../BUILD_ORDER.md) and paper [14](14-future-work.md).

---

*Next: [02 — The Agentic Compiler](02-the-agentic-compiler.md), on what it means to compile decisions rather than algorithms.*
