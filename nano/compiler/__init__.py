"""`.nano` -> Nano IR compiler (Milestone 4).

The compiler is the only path from surface syntax to IR, and this module is
its stable public API: tokenize, parse, compile_source, compile_to_dict, and
NanoSyntaxError. Downstream tooling (editor services, the LSP) consumes exactly
this surface — keep it stable.
"""

from .codegen import compile_source, compile_to_dict
from .errors import NanoSyntaxError
from .lexer import tokenize
from .parser import parse
from .tokens import Token

__all__ = [
    "NanoSyntaxError",
    "Token",
    "compile_source",
    "compile_to_dict",
    "parse",
    "tokenize",
]
