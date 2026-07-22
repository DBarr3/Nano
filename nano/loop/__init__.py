"""Nano++ autonomous optimization loop.

The universal lifecycle (observe -> propose -> compile -> execute -> measure ->
verify -> admit -> repeat) as deterministic, replayable IR. One loop model
across trading, engineering, and quantum optimization workloads.
"""

from .graph import KNOWN_LOOP_EFFECTS, LoopGraph
from .mutation import AdmissionDecision, Candidate, admit_mutation
from .nodes import LOOP_STAGES, LoopNode, LoopValidationError
from .quantum import QuantumJob, QuantumResult, QuantumRuntime, SimulatorRuntime

__all__ = [
    "AdmissionDecision",
    "Candidate",
    "KNOWN_LOOP_EFFECTS",
    "LOOP_STAGES",
    "LoopGraph",
    "LoopNode",
    "LoopValidationError",
    "QuantumJob",
    "QuantumResult",
    "QuantumRuntime",
    "SimulatorRuntime",
    "admit_mutation",
]
