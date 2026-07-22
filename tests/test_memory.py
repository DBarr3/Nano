"""Nano memory layer — pattern store retrieval tests (Milestone 2.5).

Nano answers: "Have we already solved this type of problem?"
Known pattern -> retrieved context (ATS still reasons; it starts with knowledge).
Unknown pattern -> escalate to LLM reasoning.
"""

import pytest

from nano.memory.patterns import Pattern, PatternStore

HEALTHY_CORRECTION = {
    "name": "BTCHealthyCorrection",
    "conditions": [
        {"type": "Condition", "signal": "drawdown", "operator": "<", "value": 8},
        {"type": "Condition", "signal": "funding", "operator": "==", "value": 0},
    ],
    "context": ["maintain_position"],
    "confidence": 0.89,
    "win_rate": 0.72,
    "expires_at": 1000,
    "provenance": "manual",
}


def store():
    return PatternStore.from_dicts([HEALTHY_CORRECTION])


def test_known_pattern_returns_context_not_escalation():
    result = store().retrieve({"drawdown": 4.0, "funding": 0.0}, now=500)
    assert result.escalate is False
    assert len(result.matched) == 1
    match = result.matched[0]
    assert match.name == "BTCHealthyCorrection"
    assert match.context == ("maintain_position",)
    assert match.confidence == 0.89
    assert match.win_rate == 0.72


def test_unknown_pattern_escalates():
    result = store().retrieve({"drawdown": 12.0, "funding": 0.0}, now=500)
    assert result.matched == ()
    assert result.escalate is True


def test_expired_pattern_is_not_retrieved():
    result = store().retrieve({"drawdown": 4.0, "funding": 0.0}, now=2000)
    assert result.matched == ()
    assert result.escalate is True


def test_low_confidence_pattern_is_filtered():
    result = store().retrieve(
        {"drawdown": 4.0, "funding": 0.0}, now=500, min_confidence=0.95
    )
    assert result.matched == ()
    assert result.escalate is True


def test_missing_observation_does_not_match():
    result = store().retrieve({"drawdown": 4.0}, now=500)
    assert result.matched == ()
    assert result.escalate is True


def test_retrieval_is_deterministic_and_serializable():
    a = store().retrieve({"drawdown": 4.0, "funding": 0.0}, now=500)
    b = store().retrieve({"drawdown": 4.0, "funding": 0.0}, now=500)
    assert a.to_dict() == b.to_dict()
    assert a.to_dict()["matched"][0]["pattern"] == "BTCHealthyCorrection"


def test_bad_confidence_rejected():
    bad = dict(HEALTHY_CORRECTION, confidence=1.5)
    with pytest.raises(ValueError):
        Pattern.from_dict(bad)
