"""Nano IR schema constants and validation errors.

The IR is the contract between the compiler and every runtime. No runtime
executes `.nano` source directly — everything becomes this IR.
"""

NANO_IR_VERSION = "0.1.0"

NODE_TYPES = frozenset({"Schedule", "Condition", "Intent", "Agent"})

CONDITION_OPERATORS = frozenset({"<", "<=", ">", ">=", "==", "!="})

# Effect manifest vocabulary. Emitting an intent requires "intent.emit" in the
# strategy's declared effects — this is the capability boundary: a graph that
# does not declare it cannot propose actions, regardless of its nodes.
KNOWN_EFFECTS = frozenset({"intent.emit", "log.append"})

INTENT_ACTIONS = frozenset({"BUY", "SELL", "EXECUTE", "PAUSE", "OBSERVE"})


class IRValidationError(ValueError):
    """The document is not valid Nano IR."""


class ManifestViolation(IRValidationError):
    """A node requires an effect the manifest does not declare."""
