"""Compiler error type.

Invariant: every compile-time failure carries a 1-based line and column that
points at real source text. Downstream tooling (editor services, the LSP) relies on
these positions being exact — no error is ever raised without them.
"""

from __future__ import annotations


class NanoSyntaxError(ValueError):
    """`.nano` source failed to compile. Carries .line, .column, .message."""

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(f"{line}:{column}: {message}")
        self.message = message
        self.line = line
        self.column = column
