# Nano++ — The Autonomous Optimization Loop

**Status:** design + reference implementation (`nano/loop/`).

Nano started by describing trading strategies. Nano++ describes **execution itself**: it turns an
optimization *process* into a deterministic, replayable execution graph. The reasoning model does
not stay in the loop — it *builds* the loop, then the loop runs on its own.

```
Think once → Compile → Execute N times → Only think again when necessary.
```

## The universal lifecycle

Trading, security response, quantum-circuit tuning, robotics — different domains, one shape:

```
observe → propose → compile → execute → measure → verify → admit → repeat
```

Every stage is deterministic, every transition recorded, every optimization replayable. Domains
supply different node payloads; the lifecycle never changes. Trading emits BUY/SELL; another
domain emits a different `Execute` payload — the graph is identical.

## Universal node vocabulary (`nano/loop/nodes.py`)

Fifteen stage kinds compose any autonomous loop:

`Observe` · `Infer` · `Evaluate` · `Optimize` · `Mutate` · `Verify` · `Gate` · `Execute` ·
`Pause` · `Replay` · `Checkpoint` · `Rollback` · `Escalate` · `Sign` · `Benchmark`

A `LoopGraph` (`nano/loop/graph.py`) is a validated, content-addressable DAG. Forward references
and undeclared capabilities are load-time rejections — the same effect-manifest security model the
strategy IR uses: a stage that needs a capability the graph did not declare cannot run.

## Safe self-mutation (`nano/loop/mutation.py`)

A loop that rewrites itself must never mutate live. Every proposed change becomes an engineering
artifact through four gates in order:

```
1. Proposal     — a model proposes an improvement
2. Compilation  — the proposal becomes a deterministic artifact
3. Verification — replay match · benchmark gain · zero regressions · static analysis · capability check
4. Admission    — policy · risk · provenance · capability ceiling
```

`admit_mutation` returns the blocking stage + reason on failure, or a gated artifact marked
`admitted_pending_deploy` on success. **Nothing deploys automatically** — an operator does.
Components propose; gates decide.

## Vendor-agnostic quantum runtime (`nano/loop/quantum.py`)

Nano knows *quantum jobs*, not vendors. A `QuantumJob(circuit_id, shots, params)` carries no
vendor field; a backend implements the `QuantumRuntime` protocol
(`submit(job) → QuantumResult{backend, fidelity, distribution}`). Swapping hardware swaps the
runtime, never the loop. `SimulatorRuntime` is the deterministic reference backend, so loop
replays stay bit-identical whether they run on a simulator today or dedicated hardware later.

## Why it matters

One execution model across every autonomous system. The loop is deterministic and replayable, so
"why did the system do that?" always has an exact, reproducible answer — and a self-improving
system can never ship an unverified change. Trading is the proving ground because it has
deterministic inputs and measurable outcomes; the architecture generalizes to any
Observe → Decide → Act → Record loop.

*Reference implementation: `nano/loop/` and `nano/memory/`, covered by the repo test suite.*
