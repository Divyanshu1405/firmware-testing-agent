"""Deterministic PASS/FAIL logic. The LLM must not decide verdicts."""
"""Deterministic verification logic redirected to authoritative judge engine."""

from judge.judge import evaluate, matches_condition
from judge.generic_oracles import evaluate_generic_oracles

def judge(expected: dict, observed: dict) -> dict:
    passed = expected == observed
    return {
        "status": "PASS" if passed else "FAIL",
        "expected": expected,
        "observed": observed,
    }
__all__ = ["evaluate", "matches_condition", "evaluate_generic_oracles"]
