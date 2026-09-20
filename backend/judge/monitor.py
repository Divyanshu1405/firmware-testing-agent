"""Deterministic PASS/FAIL logic. The LLM must not decide verdicts."""


def judge(expected: dict, observed: dict) -> dict:
    passed = expected == observed
    return {
        "status": "PASS" if passed else "FAIL",
        "expected": expected,
        "observed": observed,
    }
