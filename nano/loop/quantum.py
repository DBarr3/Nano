"""Abstract quantum runtime interface (Nano++).

Nano++ introduces a vendor-neutral execution interface for specialized compute backends.

Nano does not know IBM Quantum, IonQ, Azure Quantum, Rigetti, or D-Wave.

Nano knows **jobs**
A backend implements the `QuantumRuntime` protocol. The optimization loop submits a portable execution request, receives a structured result, and continues without knowing whether the computation ran on:

- a deterministic simulator
- a noise model
- a quantum processor
- a future accelerator backend

Changing hardware means changing the runtime — not rewriting the agent, compiler, or execution graph.

The reference implementation is `SimulatorRuntime`.

It is intentionally deterministic:
- no ambient randomness
- no external state
- seed derived from job content
- identical inputs produce identical outputs

This allows Nano optimization loops to be replayed bit-for-bit during development, testing, and research.

Real quantum hardware dispatch remains an experimental research direction.
The stable abstraction is the runtime boundary.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, Protocol, Tuple, runtime_checkable


@dataclass(frozen=True)
class QuantumJob:
    """A vendor-agnostic quantum task. Deliberately carries no vendor field."""

    circuit_id: str
    shots: int
    params: Tuple[float, ...] = ()

    def content_key(self) -> str:
        raw = f"{self.circuit_id}|{self.shots}|{','.join(map(repr, self.params))}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class QuantumResult:
    backend: str
    fidelity: float
    distribution: Dict[str, float]

    def to_dict(self) -> dict:
        return {
            "backend": self.backend,
            "fidelity": self.fidelity,
            "distribution": self.distribution,
        }


@runtime_checkable
class QuantumRuntime(Protocol):
    """Any quantum backend — simulator, noise model, or real QPU."""

    def submit(self, job: QuantumJob) -> QuantumResult: ...


class SimulatorRuntime:
    """Deterministic reference backend. Result is a pure function of the job."""

    backend_name = "simulator"

    def submit(self, job: QuantumJob) -> QuantumResult:
        digest = job.content_key()
        # Derive a stable two-outcome distribution + fidelity from the digest.
        a = int(digest[:8], 16) / 0xFFFFFFFF
        p0 = round(a, 6)
        p1 = round(1.0 - p0, 6)
        fidelity = round(0.5 + 0.5 * (int(digest[8:16], 16) / 0xFFFFFFFF), 6)
        return QuantumResult(
            backend=self.backend_name,
            fidelity=fidelity,
            distribution={"0": p0, "1": p1},
        )
