"""
agent/steps/plan.py
Generate a test plan (≤8 tests) from extracted requirements.
Each test is associated with one or more requirements and has
a one-line reason for inclusion.
Output: intermediate out/test_plan.json mapping test_id -> reqs + fault + reason.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from agent.models import Requirement
import agent.llm.router as _router
from agent.llm.router import _extract_json, _log_decision

_MAX_TESTS = 8
_FAULT_TYPES = ["nominal", "dropout", "ramp_overshoot", "stuck"]

PLAN_PROMPT_TEMPLATE = """\
You are a firmware test planner. Given the requirements below, generate a test plan that pairs requirements with specific hardware fault types.

Requirements:
{requirements_json}

Available Fault types for this phase:
{fault_types}

Instructions:
Generate a test plan covering the requirements and faults.
- You MUST generate exactly or at most {max_tests} test scenarios.
- Each scenario should cover 1-2 requirements and focus on 1 fault type.
- Batch all entries into a single JSON response.

Output a JSON object with a single key "test_plan" that maps to an array of objects.
Each object MUST have exactly these fields:
- "test_id": string (e.g. "T01", "T02")
- "requirement_ids": array of string (e.g. ["R1"])
- "fault_type": string (must be one of the provided available fault types)
- "reason": string (one sentence explaining why this test matters for these requirements)

Example Output Format:
{{
  "test_plan": [
    {{
      "test_id": "T01",
      "requirement_ids": ["R7"],
      "fault_type": "nominal",
      "reason": "Baseline check to ensure fan activates perfectly within normal parameters."
    }},
    {{
      "test_id": "T02",
      "requirement_ids": ["R8"],
      "fault_type": "dropout",
      "reason": "Simulates sensor signal dropout to verify emergency shutdown triggers safely."
    }}
  ]
}}

Return ONLY valid JSON.
"""

def _call_llm_raw_plan(prompt: str, step_tag: str = "plan") -> str:
    """Uses tier='fast' for planning."""
    import hashlib, json as _json

    _tier = "fast"
    _model = _router.GEMINI_MODEL_FAST

    cache_key = hashlib.sha256(f"{_model}::{prompt}".encode()).hexdigest()

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

def generate_plan(requirements: List[Requirement]) -> List[Dict[str, Any]]:
    if not requirements:
        return []

    prompt = PLAN_PROMPT_TEMPLATE.format(
        requirements_json=json.dumps([r.model_dump() for r in requirements], indent=2),
        fault_types=", ".join(_FAULT_TYPES),
        max_tests=_MAX_TESTS
    )

    for attempt in range(1, 3):
        try:
            raw = _call_llm_raw_plan(prompt, step_tag="plan:batch")
            data = _extract_json(raw)
            if isinstance(data, dict):
                items = data.get("test_plan", [])
            else:
                items = data

            # Truncate if LLM ignored instructions
            results = items[:_MAX_TESTS]
            return results
        except Exception as exc:
            if attempt == 2:
                _log_decision(f"plan: batch failed after 2 attempts: {exc}")
                raise RuntimeError(f"Plan generation failed: {exc}")
            continue

    return []

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--reqs", default="out/requirements.json")
    parser.add_argument("--out", default="out/test_plan.json")
    args = parser.parse_args()

    reqs_path = Path(args.reqs)
    if not reqs_path.exists():
        print(f"No requirements found at {args.reqs}.")
        import sys
        sys.exit(1)

    with open(reqs_path, "r", encoding="utf-8") as f:
        req_dicts = json.load(f)
    reqs = [Requirement.model_validate(r) for r in req_dicts]

    plan = generate_plan(reqs)
    
    # Log to DECISIONS.md as requested:
    decision_msg = f"Generated {len(plan)} tests in batch."
    for p in plan:
        req_str = ",".join(p.get("requirement_ids", []))
        decision_msg += f" {p.get('test_id')}:[{req_str}]({p.get('fault_type')}),"
    _log_decision(decision_msg.rstrip(","))

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    print(f"Generated {len(plan)} test plan entries to {args.out}")

