"""Semantic tokens for `.nano` source.

Invariant: semantic_tokens never raises. It classifies whatever prefix of the
source the lexer can tokenize — syntactically invalid but lexable source still
yields its full token stream, and a lexer failure yields the tokens before the
offending text. Positions are the lexer's own 1-based line/column, unmodified,
so highlights always land on real source characters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from ..compiler import NanoSyntaxError, tokenize

# Token kinds. IDENT tokens are classified by value — the lexer has no keyword
# knowledge (the parser assigns keyword meaning by position), so the known
# keyword and action vocabularies are mirrored here for the editor's benefit.
KIND_KEYWORD = "keyword"
KIND_ACTION = "action"
KIND_INTERVAL = "interval"
KIND_NUMBER = "number"
KIND_OPERATOR = "operator"
KIND_PUNCTUATION = "punctuation"
KIND_IDENTIFIER = "identifier"

_KEYWORDS = frozenset({"strategy", "every", "if", "and", "agent"})
_ACTIONS = frozenset({"buy", "sell", "execute", "pause", "observe"})

_TYPE_KINDS = {
    "INTERVAL": KIND_INTERVAL,
    "INT": KIND_NUMBER,
    "FLOAT": KIND_NUMBER,
    "OP": KIND_OPERATOR,
    "LBRACE": KIND_PUNCTUATION,
    "RBRACE": KIND_PUNCTUATION,
    "LPAREN": KIND_PUNCTUATION,
    "RPAREN": KIND_PUNCTUATION,
    "COMMA": KIND_PUNCTUATION,
}


@dataclass(frozen=True)
class SemanticToken:
    line: int
    column: int
    length: int
    kind: str


def _classify(token_type: str, value: str) -> str:
    if token_type == "IDENT":
        if value in _KEYWORDS:
            return KIND_KEYWORD
        if value in _ACTIONS:
            return KIND_ACTION
        return KIND_IDENTIFIER
    return _TYPE_KINDS[token_type]


def _offset_of(source: str, line: int, column: int) -> int:
    """Character offset of a 1-based (line, column) position."""
    offset = 0
    for _ in range(line - 1):
        newline = source.find("\n", offset)
        if newline < 0:
            return len(source)
        offset = newline + 1
    return min(offset + column - 1, len(source))


def semantic_tokens(source: str) -> Tuple[SemanticToken, ...]:
    """Classify source into editor highlight tokens; never raises."""
    text = source
    while True:
        try:
            tokens = tokenize(text)
            break
        except NanoSyntaxError as error:
            cut = _offset_of(text, error.line, error.column)
            if cut >= len(text):
                return ()
            text = text[:cut]
    return tuple(
        SemanticToken(
            line=token.line,
            column=token.column,
            length=len(token.value),
            kind=_classify(token.type, token.value),
        )
        for token in tokens
        if token.type != "EOF"
    )
