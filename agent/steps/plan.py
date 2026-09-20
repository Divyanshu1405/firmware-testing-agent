"""
agent/steps/plan.py
Generate a test plan (≤8 tests) from extracted requirements.
Each test is associated with one or more requirements and has
a one-line reason for inclusion.
Output: list[Timeline] with populated test_id, requirement_ids,
        duration_ms, and events (as LLM-generated, then validated).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import jsonschema
from pydantic import BaseModel

from agent.models import Requirement, Timeline, TimelineEvent, TimelineAction
from agent.llm.router import _extract_json, _log_decision
import agent.llm.router as _router

_TIMELINE_SCHEMA = Path(__file__).parent.parent.parent / "contracts" / "timeline.schema.json"
_MAX_TESTS = 8

# Fault matrix (Person C's stand-in; expanded when Person A defines theirs)
_FAULT_TYPES = [
    "nominal",         # clean, no fault
    "dropout",         # signal dropout
    "ramp_overshoot",  # ramp beyond threshold
    "stuck",           # signal stuck at value
]

PLAN_PROMPT_TEMPLATE = """\
You are a firmware test planner. Given the requirements below and a fault type,
generate a test timeline JSON object.

Requirements:
{requirements_json}

Fault type: {fault_type}

Output a single JSON object with these EXACT fields:
- "test_id": string, e.g. "T01"
- "requirement_ids": array of requirement id strings that this test covers, e.g. ["R1"]
- "duration_ms": integer, total test duration in milliseconds
- "events": array of event objects, each with:
    - "at_ms": integer (milliseconds from start)
    - "action": one of: set, ramp, step, dropout, stuck, spike, glitch, drift, uart_write, uart_garbage
    - "channel": string (e.g. "temp_c", "power")
    - optional: "value", "to", "over_ms", "for_ms"
- "reason": string, one sentence explaining why this test is needed (added for traceability, strip before schema validation)

Return ONLY the JSON object. No explanation outside the JSON.
"""


def _load_timeline_schema() -> dict:
    with open(_TIMELINE_SCHEMA, encoding="utf-8") as f:
        return json.load(f)


def generate_plan(requirements: List[Requirement]) -> List[Timeline]:
    """
    Generate up to MAX_TESTS timelines from requirements × fault matrix.
    LLM calls are batched; total calls ≤ MAX_TESTS (half the run budget).
    """
    if not requirements:
        return []

    schema = _load_timeline_schema()
    timelines: List[Timeline] = []
    test_counter = 1

    # Pair requirements with fault types, cap at MAX_TESTS
    pairs = [
        (req, fault)
        for fault in _FAULT_TYPES
        for req in requirements
    ][:_MAX_TESTS]

    # Track LLM calls for this step (≤ half budget)
    half_budget = _router.LLM_CALL_BUDGET // 2
    calls_this_step = 0

    for req, fault in pairs:
        if calls_this_step >= half_budget:
            _log_decision(
                f"plan: reached half-budget ({half_budget}) at test {test_counter}; "
                "stopping plan generation to preserve budget for other steps"
            )
            break

        test_id = f"T{test_counter:02d}"
        prompt = PLAN_PROMPT_TEMPLATE.format(
            requirements_json=json.dumps(
                [r.model_dump() for r in requirements], indent=2
            ),
            fault_type=fault,
        )

        for attempt in range(1, 3):
            try:
                raw = _call_llm_raw_plan(prompt, step_tag=f"plan:{test_id}")
                data = _extract_json(raw)

                # Set test_id from our counter (override LLM's suggestion)
                data["test_id"] = test_id
                # Strip reason before schema validation
                data.pop("reason", None)

                jsonschema.validate(instance=data, schema=schema)
                timelines.append(Timeline.model_validate(data))
                calls_this_step += 1
                test_counter += 1
                break
            except (jsonschema.ValidationError, Exception) as exc:
                if attempt == 2:
                    _log_decision(
                        f"plan: {test_id}/{fault} failed after 2 attempts: {exc}; skipping"
                    )
                continue

    return timelines


def _call_llm_raw_plan(prompt: str, step_tag: str = "plan") -> str:
    """Like spec._call_llm_raw but for plan step (tier='fast')."""
    import hashlib, json as _json

    _tier = "fast"
    _model = _router.GEMINI_MODEL_FAST

    cache_key = hashlib.sha256(
        f"{_model}::{prompt}".encode()
    ).hexdigest()

    cached = _router._read_cache(cache_key)
    if cached is not None:
        _router._log_provenance(cached.get("model_used", _model), True, cache_key, step_tag, tier=_tier)
        return _json.dumps(cached["data"])

    if _router.LLM_OFFLINE:
        raise RuntimeError(f"LLM_OFFLINE=1 but no cache entry for plan (key {cache_key[:8]})")

    if _router._calls_this_run >= _router.LLM_CALL_BUDGET:
        raise RuntimeError("LLM call budget exhausted during plan generation")

    _router._calls_this_run += 1
    model_used = _model
    raw: str | None = None

    try:
        raw = _router._call_gemini(prompt, _model)
    except Exception as exc:
        _log_decision(f"plan Gemini ({_model}) failed ({exc}); falling back to Ollama")
        raw = _router._call_ollama(prompt, _router.OLLAMA_MODEL)
        model_used = _router.OLLAMA_MODEL

    data = _router._extract_json(raw)
    _router._write_cache(cache_key, {"model_used": model_used, "data": data})
    _router._log_provenance(model_used, False, cache_key, step_tag, tier=_tier)
    return _json.dumps(data)
