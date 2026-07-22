"""Editor tooling for Nano (Milestone 6).

Editor-facing language services — semantic highlighting, diagnostics, and IR
preview — as pure functions over the public compiler API. This package is the
engine a host IDE/editor extension (VS Code-style) calls; it performs no I/O
and speaks no wire protocol. Keep this surface stable: it is what the
extension imports.
"""

from .diagnostics import Diagnostic, diagnostics
from .highlight import SemanticToken, semantic_tokens
from .preview import ir_json, ir_preview

__all__ = [
    "Diagnostic",
    "SemanticToken",
    "diagnostics",
    "ir_json",
    "ir_preview",
    "semantic_tokens",
]
