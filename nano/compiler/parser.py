"""Recursive-descent parser for `.nano` (v0.1.0 grammar) plus its AST.

Invariant: a StrategyAst that leaves this module already satisfies every
semantic rule of the locked grammar — at most one schedule block, at most one
rule per schedule, known action names only, confidence within [0, 1] — because
this is the last place a violation can still be reported with the exact 1-based
line/column of the offending token. The AST is immutable; codegen only
transforms, it never re-validates positions.

Grammar (locked, v0.1.0):

    program    := "strategy" IDENT "{" item* "}"
    item       := schedule-block | agent-decl
    agent-decl := "agent" IDENT
    schedule   := "every" INTERVAL "{" rule? "}"
    rule       := "if" condition ("and" condition)* "{" action+ "}"
    condition  := IDENT [ "(" INT ")" ] OP NUMBER
    action     := "buy" "(" IDENT ["," NUMBER] ")"
                | "sell" "(" IDENT ["," NUMBER] ")"
                | "execute" "(" ")" | "pause" "(" ")" | "observe" "(" ")"
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union

from .errors import NanoSyntaxError
from .lexer import tokenize
from .tokens import Token

Number = Union[int, float]

# Surface action name -> IR intent action. buy/sell take (asset[, confidence]);
# the rest take no arguments.
_ASSET_ACTIONS = {"buy": "BUY", "sell": "SELL"}
_NULLARY_ACTIONS = {"execute": "EXECUTE", "pause": "PAUSE", "observe": "OBSERVE"}
_ALL_ACTIONS = {**_ASSET_ACTIONS, **_NULLARY_ACTIONS}


@dataclass(frozen=True)
class ConditionAst:
    signal: str
    operator: str
    value: Number


@dataclass(frozen=True)
class ActionAst:
    action: str  # IR action: BUY, SELL, EXECUTE, PAUSE, OBSERVE
    asset: Optional[str] = None
    confidence: Optional[Number] = None


@dataclass(frozen=True)
class RuleAst:
    conditions: Tuple[ConditionAst, ...]
    actions: Tuple[ActionAst, ...]


@dataclass(frozen=True)
class ScheduleAst:
    interval: str
    rule: Optional[RuleAst]


@dataclass(frozen=True)
class AgentAst:
    name: str


@dataclass(frozen=True)
class StrategyAst:
    name: str
    schedule: Optional[ScheduleAst]
    agents: Tuple[AgentAst, ...]  # in source order


class _Parser:
    def __init__(self, tokens: Tuple[Token, ...]) -> None:
        self._tokens = tokens
        self._pos = 0

    # -- token plumbing ----------------------------------------------------

    def _peek(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        token = self._tokens[self._pos]
        if token.type != "EOF":
            self._pos += 1
        return token

    @staticmethod
    def _error(message: str, token: Token) -> NanoSyntaxError:
        return NanoSyntaxError(message, token.line, token.column)

    @staticmethod
    def _describe(token: Token) -> str:
        return "end of input" if token.type == "EOF" else repr(token.value)

    def _expect(self, token_type: str, what: str) -> Token:
        token = self._peek()
        if token.type != token_type:
            raise self._error(f"Expected {what}, got {self._describe(token)}", token)
        return self._advance()

    def _expect_keyword(self, keyword: str) -> Token:
        token = self._peek()
        if token.type != "IDENT" or token.value != keyword:
            raise self._error(
                f"Expected {keyword!r} keyword, got {self._describe(token)}", token
            )
        return self._advance()

    def _at_keyword(self, keyword: str) -> bool:
        token = self._peek()
        return token.type == "IDENT" and token.value == keyword

    def _expect_closing_brace(self, block: str) -> None:
        token = self._peek()
        if token.type == "EOF":
            raise self._error(f"Unterminated {block} block (missing '}}')", token)
        if token.type != "RBRACE":
            raise self._error(
                f"Unexpected token {self._describe(token)} in {block} block", token
            )
        self._advance()

    # -- grammar productions -----------------------------------------------

    def parse_program(self) -> StrategyAst:
        self._expect_keyword("strategy")
        name = self._expect("IDENT", "strategy name").value
        self._expect("LBRACE", "'{'")

        schedule: Optional[ScheduleAst] = None
        agents: list[AgentAst] = []
        while True:
            token = self._peek()
            if token.type == "RBRACE":
                self._advance()
                break
            if token.type == "EOF":
                raise self._error("Unterminated 'strategy' block (missing '}')", token)
            if self._at_keyword("agent"):
                self._advance()
                agents.append(AgentAst(name=self._expect("IDENT", "agent name").value))
                continue
            if self._at_keyword("every"):
                if schedule is not None:
                    raise self._error(
                        "At most one schedule block is allowed per strategy", token
                    )
                schedule = self._parse_schedule()
                continue
            raise self._error(
                f"Unexpected token {self._describe(token)} in 'strategy' block "
                "(expected 'every' or 'agent')",
                token,
            )

        trailing = self._peek()
        if trailing.type != "EOF":
            raise self._error(
                f"Unexpected token {self._describe(trailing)} after strategy block",
                trailing,
            )
        return StrategyAst(name=name, schedule=schedule, agents=tuple(agents))

    def _parse_schedule(self) -> ScheduleAst:
        self._expect_keyword("every")
        interval = self._expect("INTERVAL", "interval (e.g. 5m, 1h)").value
        self._expect("LBRACE", "'{'")

        rule: Optional[RuleAst] = None
        if self._at_keyword("if"):
            rule = self._parse_rule()

        token = self._peek()
        if token.type == "EOF":
            raise self._error("Unterminated 'every' block (missing '}')", token)
        if self._at_keyword("if"):
            raise self._error(
                "At most one rule is allowed per schedule block", token
            )
        if token.type != "RBRACE":
            raise self._error(
                f"Unexpected token {self._describe(token)} in 'every' block", token
            )
        self._advance()
        return ScheduleAst(interval=interval, rule=rule)

    def _parse_rule(self) -> RuleAst:
        self._expect_keyword("if")
        conditions = [self._parse_condition()]
        while self._at_keyword("and"):
            self._advance()
            conditions.append(self._parse_condition())
        self._expect("LBRACE", "'{'")

        actions = [self._parse_action()]
        while True:
            token = self._peek()
            if token.type == "IDENT":
                actions.append(self._parse_action())
                continue
            self._expect_closing_brace("rule")
            break
        return RuleAst(conditions=tuple(conditions), actions=tuple(actions))

    def _parse_condition(self) -> ConditionAst:
        signal = self._expect("IDENT", "signal name").value
        if self._peek().type == "LPAREN":
            # Parenthesized argument, e.g. RSI(14): accepted, dropped from IR.
            self._advance()
            self._expect("INT", "integer signal argument")
            self._expect("RPAREN", "')'")
        operator_token = self._peek()
        if operator_token.type != "OP":
            raise self._error(
                "Expected comparison operator (one of <, <=, >, >=, ==, !=), "
                f"got {self._describe(operator_token)}",
                operator_token,
            )
        self._advance()
        value = self._parse_number("condition value")
        return ConditionAst(signal=signal, operator=operator_token.value, value=value)

    def _parse_action(self) -> ActionAst:
        name_token = self._expect("IDENT", "action name")
        surface_name = name_token.value
        if surface_name not in _ALL_ACTIONS:
            raise self._error(
                f"Unknown action {surface_name!r} "
                "(expected one of buy, sell, execute, pause, observe)",
                name_token,
            )
        action = _ALL_ACTIONS[surface_name]
        self._expect("LPAREN", "'('")

        if surface_name in _NULLARY_ACTIONS:
            self._expect("RPAREN", "')'")
            return ActionAst(action=action)

        asset = self._expect("IDENT", "asset name").value
        confidence: Optional[Number] = None
        if self._peek().type == "COMMA":
            self._advance()
            confidence_token = self._peek()
            confidence = self._parse_number("confidence value")
            if not 0 <= confidence <= 1:
                raise self._error(
                    f"Confidence {confidence} is out of range [0, 1]",
                    confidence_token,
                )
        self._expect("RPAREN", "')'")
        return ActionAst(action=action, asset=asset, confidence=confidence)

    def _parse_number(self, what: str) -> Number:
        token = self._peek()
        if token.type == "INT":
            self._advance()
            return int(token.value)
        if token.type == "FLOAT":
            self._advance()
            return float(token.value)
        raise self._error(
            f"Expected numeric {what}, got {self._describe(token)}", token
        )


def parse(source: str) -> StrategyAst:
    """Parse `.nano` source into a validated, immutable AST."""
    return _Parser(tokenize(source)).parse_program()
