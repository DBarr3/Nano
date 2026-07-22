"""Lexer for `.nano` source (v0.1.0 surface).

Invariant: only the locked token vocabulary leaves this module. Anything
outside it — stray characters, half-written operators, malformed intervals or
number literals — fails here, immediately, with the 1-based line and column of
the offending text. Pure function of the source string; no I/O.
"""

from __future__ import annotations

from typing import Tuple

from .errors import NanoSyntaxError
from .tokens import Token

_PUNCT = {
    "{": "LBRACE",
    "}": "RBRACE",
    "(": "LPAREN",
    ")": "RPAREN",
    ",": "COMMA",
}

_INTERVAL_UNITS = frozenset("smhd")


def _is_ident_start(ch: str) -> bool:
    return "a" <= ch <= "z" or "A" <= ch <= "Z" or ch == "_"


def _is_ident_char(ch: str) -> bool:
    return _is_ident_start(ch) or "0" <= ch <= "9"


def _is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def tokenize(source: str) -> Tuple[Token, ...]:
    """Split source into tokens; always ends with a single EOF token."""
    tokens: list[Token] = []
    i = 0
    line = 1
    column = 1
    n = len(source)

    while i < n:
        ch = source[i]

        if ch == "\n":
            i += 1
            line += 1
            column = 1
            continue
        if ch in " \t\r":
            i += 1
            column += 1
            continue
        if ch == "/" and i + 1 < n and source[i + 1] == "/":
            while i < n and source[i] != "\n":
                i += 1
                column += 1
            continue

        start_line, start_column = line, column

        if ch in _PUNCT:
            tokens.append(Token(_PUNCT[ch], ch, start_line, start_column))
            i += 1
            column += 1
            continue

        if ch in "<>":
            if i + 1 < n and source[i + 1] == "=":
                tokens.append(Token("OP", ch + "=", start_line, start_column))
                i += 2
                column += 2
            else:
                tokens.append(Token("OP", ch, start_line, start_column))
                i += 1
                column += 1
            continue

        if ch in "=!":
            if i + 1 < n and source[i + 1] == "=":
                tokens.append(Token("OP", ch + "=", start_line, start_column))
                i += 2
                column += 2
                continue
            raise NanoSyntaxError(
                f"Unknown operator {ch!r} (expected one of <, <=, >, >=, ==, !=)",
                start_line,
                start_column,
            )

        if _is_ident_start(ch):
            j = i
            while j < n and _is_ident_char(source[j]):
                j += 1
            text = source[i:j]
            tokens.append(Token("IDENT", text, start_line, start_column))
            column += j - i
            i = j
            continue

        if _is_digit(ch):
            j = i
            while j < n and _is_digit(source[j]):
                j += 1
            is_float = False
            if j < n and source[j] == ".":
                if j + 1 < n and _is_digit(source[j + 1]):
                    is_float = True
                    j += 1
                    while j < n and _is_digit(source[j]):
                        j += 1
                else:
                    raise NanoSyntaxError(
                        f"Malformed number literal {source[i : j + 1]!r} "
                        "(digits required after '.')",
                        start_line,
                        start_column,
                    )
            if j < n and _is_ident_char(source[j]):
                # A letter glued to a number is only legal as an interval:
                # an integer followed by exactly one unit in {s, m, h, d}.
                k = j
                while k < n and _is_ident_char(source[k]):
                    k += 1
                suffix = source[j:k]
                if not is_float and suffix in _INTERVAL_UNITS:
                    tokens.append(Token("INTERVAL", source[i:k], start_line, start_column))
                    column += k - i
                    i = k
                    continue
                raise NanoSyntaxError(
                    f"Malformed interval {source[i:k]!r} "
                    "(expected an integer followed by one of s, m, h, d)",
                    start_line,
                    start_column,
                )
            text = source[i:j]
            tokens.append(
                Token("FLOAT" if is_float else "INT", text, start_line, start_column)
            )
            column += j - i
            i = j
            continue

        raise NanoSyntaxError(f"Unexpected character {ch!r}", start_line, start_column)

    tokens.append(Token("EOF", "", line, column))
    return tuple(tokens)
