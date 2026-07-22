# Security Policy

Nano is infrastructure for autonomous systems — security posture is a design pillar, not an
afterthought. This document covers how to report issues and what the architecture does and
does not protect.

## Reporting a vulnerability

Please **do not** open a public issue for security-sensitive reports. Instead use
[GitHub private vulnerability reporting](https://github.com/DBarr3/Nano/security/advisories/new)
on this repository. Include a reproduction if possible. You'll get an acknowledgment, and
fixes for confirmed issues are prioritized ahead of all feature work.

Currently supported for security fixes: the latest state of `main`.

## Threat model

What Nano's design defends against, by construction:

| Threat | Defense |
|---|---|
| A compiled program acting on the world directly | No actuation/exchange/network primitive exists in the language; programs emit intents, a gate disposes |
| A program exceeding its declared capabilities | Effect manifests on every IR module, validated at load time — undeclared effects fail closed |
| Nondeterministic or unreproducible execution | No ambient clock/RNG/IO; time and entropy are injected, logged inputs; replay is bit-identical |
| Silent self-modification | Proposed graph changes pass admission gates (validation, replay verification, sign-off) before any runtime loads them |
| Tampered execution history | Append-only audit log; optional provenance adapter produces signed, independently re-verifiable receipts |
| Malicious or malformed IR | Schema validation at load; content-addressed graphs — the hash you audited is the artifact that runs |

## Assumptions and non-goals — read this

Nano's guarantees are **language-level and IR-level**, enforced by a reference interpreter
written in Python. Be clear about the boundary:

- **The host process is trusted.** Nano is not an OS sandbox. Code running in the same Python
  process as the interpreter (your gate, your data feed, an installed package) is outside the
  boundary and can do anything Python can do.
- **The gate is yours.** Nano guarantees every intent reaches your gate with a full record; it
  cannot guarantee your gate's policy is correct. A permissive gate approves bad trades
  deterministically.
- **Inputs are trusted-as-logged.** Determinism means identical inputs replay identically. It
  does not authenticate the inputs themselves — feed integrity is the deployment's job.
- **The escalation path is a model.** Anything routed back to LLM reasoning inherits LLM
  failure modes (including prompt injection). Nano bounds *when* that path is used and gates
  its output; it does not make the model safe.

Paper [12 — Security](docs/papers/12-security.md) covers the capability-restriction argument
in depth.

## Scope for reports

In scope: IR validation bypasses, effect-manifest escapes, determinism violations (same graph +
same inputs → different result or log), intent/gate boundary escapes, provenance-receipt
forgery.

Out of scope: vulnerabilities in your gate implementation, market losses from strategy logic,
Python-ecosystem supply-chain issues (report those upstream — but tell us if Nano's pinning
should catch them).
