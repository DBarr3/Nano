# Contributing to Nano

Thanks for your interest. Nano is a research preview moving fast — contributions that fit the
project's discipline (deterministic, tested, honestly labeled) are very welcome.

## Development setup

```bash
git clone https://github.com/DBarr3/Nano.git
cd Nano
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m pytest tests -q
```

Python 3.10+. The whole suite runs in under two seconds — run it constantly.

## Where help is most valuable

**Easiest entry: the strategy library.** Add a classic quant strategy to
[`nano/library/`](nano/library/) as `.nano` source plus its expected IR JSON. The library
README documents the format and the conformance rule (source must compile to the expected IR
bit-for-bit). This teaches you the whole pipeline in one PR.

**The conformance corpus.** New `.nano` programs in [`nano/examples/`](nano/examples/) that
exercise untested language shapes — each is source + hand-written IR that must match exactly.

**The CLI.** `nano compile` / `nano replay` / `nano visualize` are designed but not built.
See [BUILD_ORDER.md](BUILD_ORDER.md) for the intended shape.

**Docs and papers.** Anything in [`docs/papers/`](docs/papers/) that is unclear, overstated,
or wrong — issues and PRs both welcome. The house rule: every claim cites shipped code or is
labeled design/roadmap/research.

## Architecture in one diagram

```
.nano source ──► Compiler (nano/compiler/) ──► Nano IR (nano/ir/)
                                                    │
                     ┌──────────────────────────────┤
                     ▼                              ▼
        Interpreter (nano/runtime/)     Bridge + gate (nano/bridge/)
        pure, deterministic             intents → your risk engine
                     │                              │
                     └──────── append-only audit log┘
```

Supporting layers: pattern memory (`nano/memory/`), editor services (`nano/aethercode/`),
optimization loop (`nano/loop/`). Build sequence and rationale: [BUILD_ORDER.md](BUILD_ORDER.md).

## Ground rules

1. **Determinism is non-negotiable.** No ambient clock, RNG, network, or global mutable state
   anywhere in the IR, compiler, or runtime paths. Time and entropy are injected inputs.
2. **Programs propose; gates decide.** Never add an actuation primitive to the language or a
   side-effecting call to the runtime. If your feature needs an effect, it goes through the
   intent/gate boundary.
3. **Tests first-class.** New behavior ships with tests; conformance examples must replay
   bit-identically. `python -m pytest tests -q` must pass before any PR.
4. **Honest labeling.** Docs distinguish shipped / design / roadmap / research. Don't promote
   a claim past its evidence.

## Pull requests

- Branch from `main`; keep PRs focused and small.
- Commit style: `<type>: <description>` (feat, fix, refactor, docs, test, chore).
- Describe *why*, not just what. Link the paper or BUILD_ORDER milestone your change serves
  if one applies.

## Questions and ideas

Open a GitHub issue — design discussion is welcome, and "this paper's argument doesn't hold
because…" is a first-class contribution.
