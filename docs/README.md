# docs/

Documentation for the Nano language and runtime.

- **[papers/](papers/)** — the research-paper series. One question per paper, from
  *Why Nano?* through determinism, provenance, the language comparisons, and the
  quantum / heterogeneous-compute research track. Start at [papers/README.md](papers/README.md).
- **[nano-optimization-loop.md](nano-optimization-loop.md)** — overview of the Nano++
  autonomous optimization loop (`nano/loop/`).

For the top-level story, see the repository [README.md](../README.md) and
[BUILD_ORDER.md](../BUILD_ORDER.md). The language contract is defined by the code:
`nano/ir/` (the IR schema), `nano/runtime/` (the reference interpreter), and
`nano/examples/` (the conformance corpus).
