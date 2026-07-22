"""Conformance suite — the Milestone 3 x Milestone 4 weld.

The BUILD_ORDER rule: every example must compile from `.nano` source to IR
that is byte-for-byte equal to its hand-written `<name>_ir.json`, and the
compiled graph must replay identically through the reference interpreter.
This is the acceptance test that proves the language surface and the IR
corpus never drift apart.
"""

import json
from pathlib import Path

import pytest

from nano.compiler import compile_source, compile_to_dict
from nano.runtime.interpreter import MarketFrame, execute

EXAMPLES = Path(__file__).resolve().parent.parent / "nano" / "examples"

NANO_SOURCES = sorted(EXAMPLES.glob("*.nano"))


def _ir_path(nano_path: Path) -> Path:
    return nano_path.with_name(f"{nano_path.stem}_ir.json")


def test_corpus_is_nonempty_and_paired():
    assert NANO_SOURCES, "conformance corpus must not be empty"
    for nano_path in NANO_SOURCES:
        assert _ir_path(nano_path).exists(), f"{nano_path.name} has no IR partner"


@pytest.mark.parametrize("nano_path", NANO_SOURCES, ids=lambda p: p.stem)
def test_compiled_ir_matches_handwritten_ir(nano_path: Path):
    compiled = compile_to_dict(nano_path.read_text())
    handwritten = json.loads(_ir_path(nano_path).read_text())
    assert compiled == handwritten


@pytest.mark.parametrize("nano_path", NANO_SOURCES, ids=lambda p: p.stem)
def test_compiled_graph_replays_identically(nano_path: Path):
    graph = compile_source(nano_path.read_text())
    signals = {c.signal: (0.0, 1e9) for c in graph.conditions}
    frame = MarketFrame(timestamps=(0, 86400), signals=signals)
    first = execute(graph, frame).to_dict()
    second = execute(graph, frame).to_dict()
    assert first == second
