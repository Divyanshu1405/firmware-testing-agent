"""Test plan generator mapping requirements and hardware profiles to fault scenarios.

Expands beyond hardcoded fault categories to support nominal, boundary, abnormal,
communication-failure, state-transition, and combined conditions.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import agent.llm.router as _router
from agent.llm.router import _extract_json, _log_decision
from agent.models import Requirement

_MAX_TESTS = 8
_FAULT_TYPES = [
    "nominal",
    "boundary",
    "abnormal",
    "dropout",
    "stuck",
    "spike",
    "glitch",
    "drift",
    "error_reading",
    "corrupted_uart",
    "state_transition",
    "combined",
]

PLAN_PROMPT_TEMPLATE = """\
You are an autonomous embedded firmware verification planner. Given the extracted requirements and available hardware interfaces, generate an executable test plan.

Target Hardware Interfaces:
{interfaces_json}

Requirements:
{requirements_json}

Available Fault and Scenario Types:
{fault_types}

Instructions:
Generate an executable test plan covering normal, boundary, abnormal, and fault-injection conditions.
- Generate at most {max_tests} test scenarios.
- Each scenario must cover 1-2 requirements and focus on 1 scenario/fault type.
- Target only channels available in the hardware interfaces. If no sensor inputs exist, focus on nominal execution and UART/crash resilience.
- Output a single JSON object with key "test_plan" mapping to an array of objects.

Each test object MUST have EXACTLY these fields:
- "test_id": string (e.g. "T01", "T02")
- "requirement_ids": array of string (e.g. ["REQ-01", "REQ-02"])
- "fault_type": string (one of: {fault_types})
- "channel": string (valid channel from available interfaces, or "uart")
- "reason": string (rationale explaining why this test validates the requirement)
- "expected_observable": string (observable output expected on UART/GPIO/system)

Example Output Format:
{{
  "test_plan": [
    {{
      "test_id": "T01",
      "requirement_ids": ["REQ-01"],
      "fault_type": "nominal",
      "channel": "temp_c",
      "reason": "Baseline check to ensure sensor reports properly under normal conditions.",
      "expected_observable": "Periodic telemetry emitted over USART."
    }}
  ]
}}

Return ONLY valid JSON.
"""


def _synthesize_deterministic_plan(
    requirements: Optional[List[Requirement]] = None,
    channel: str = "temp_c",
) -> List[Dict[str, Any]]:
    """Synthesize a robust baseline plan when offline with empty cache."""
    req_ids = [r.id for r in (requirements or [])] or ["REQ-01", "REQ-02", "REQ-03", "REQ-04", "REQ-05", "REQ-06"]

    plan = []
    # Test 1: Nominal
    r_nom = [req_ids[0]] if req_ids else ["REQ-01"]
    if len(req_ids) > 1:
        r_nom.append(req_ids[1])
    plan.append({
        "test_id": "T01",
        "requirement_ids": r_nom,
        "fault_type": "nominal",
        "channel": channel,
        "reason": "Baseline operational check under nominal parameters.",
        "expected_observable": "Periodic formatted telemetry matching specification.",
    })

    # Test 2: Sensor fault / dropout
    r_drop = [req_ids[2]] if len(req_ids) > 2 else r_nom
    plan.append({
        "test_id": "T02",
        "requirement_ids": r_drop,
        "fault_type": "dropout",
        "channel": channel,
        "reason": "Verify sensor communication failure triggers error indication.",
        "expected_observable": "Transmits error indication upon sensor disconnection.",
    })

    # Test 3: Boundary
    r_bound = [req_ids[3]] if len(req_ids) > 3 else r_nom
    plan.append({
        "test_id": "T03",
        "requirement_ids": r_bound,
        "fault_type": "boundary",
        "channel": channel,
        "reason": "Verify boundary behavior near upper/lower limits.",
        "expected_observable": "Reported values remain clamped within valid range.",
    })

    # Test 4: Stuck / continuous execution
    r_stuck = req_ids[4:] if len(req_ids) > 4 else r_nom
    plan.append({
        "test_id": "T04",
        "requirement_ids": r_stuck,
        "fault_type": "stuck",
        "channel": channel,
        "reason": "Check system stability and continuous execution during static inputs.",
        "expected_observable": "System executes continuously without HardFault or reset loop.",
    })

    return plan[:_MAX_TESTS]


def _call_llm_raw_plan(prompt: str, step_tag: str = "plan") -> str:
    """Invoke LLM router with caching and fast model tier."""
    _tier = "fast"
    _model = _router.GEMINI_MODEL_FAST

    cache_key = hashlib.sha256(f"{_model}::{prompt}".encode()).hexdigest()

    cached = _router._read_cache(cache_key)
    if cached is not None:
        _router._log_provenance(cached.get("model_used", _model), True, cache_key, step_tag, tier=_tier)
        return json.dumps(cached["data"])

    if _router.is_offline() or getattr(_router, "_gemini_exhausted", False):
        return json.dumps({"test_plan": _synthesize_deterministic_plan()})

    if _router._calls_this_run >= _router.LLM_CALL_BUDGET:
        return json.dumps({"test_plan": _synthesize_deterministic_plan()})

    _router._calls_this_run += 1
    model_used = _model
    raw: Optional[str] = None

    try:
        raw = _router._call_gemini(prompt, _model)
    except Exception as exc:
        _log_decision(f"plan Gemini ({_model}) failed ({exc}); falling back to Ollama")
        try:
            raw = _router._call_ollama(prompt, _router.OLLAMA_MODEL)
            model_used = _router.OLLAMA_MODEL
        except Exception:
            return json.dumps({"test_plan": _synthesize_deterministic_plan()})

    data = _router._extract_json(raw)
    _router._write_cache(cache_key, {"model_used": model_used, "data": data})
    _router._log_provenance(model_used, False, cache_key, step_tag, tier=_tier)
    return json.dumps(data)


def generate_plan(
    requirements: List[Requirement], io_map: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Generate a validated test plan paired with requirements and hardware capabilities."""
    active_io = io_map or {}
    valid_channels = list(active_io.get("inputs", {}).keys()) + list(active_io.get("outputs", {}).keys())
    if not valid_channels:
        valid_channels = ["temp_c", "uart"]

    if not requirements:
        return _synthesize_deterministic_plan(channel=valid_channels[0])

    prompt = PLAN_PROMPT_TEMPLATE.format(
        interfaces_json=json.dumps(active_io, indent=2),
        requirements_json=json.dumps([r.model_dump() for r in requirements], indent=2),
        fault_types=", ".join(_FAULT_TYPES),
        max_tests=_MAX_TESTS,
    )

    for attempt in range(1, 3):
        try:
            raw = _call_llm_raw_plan(prompt, step_tag="plan:batch")
            data = _extract_json(raw)
            if isinstance(data, dict):
                items = data.get("test_plan", [])
            elif isinstance(data, list):
                items = data
            else:
                items = _synthesize_deterministic_plan(requirements, channel=valid_channels[0])

            if not isinstance(items, list):
                items = _synthesize_deterministic_plan(requirements, channel=valid_channels[0])

            validated_plan = []
            for idx, item in enumerate(items[:_MAX_TESTS]):
                tid = item.get("test_id") or f"T{idx+1:02d}"
                req_ids = item.get("requirement_ids") or [requirements[0].id]
                ft = item.get("fault_type", "nominal")
                if ft not in _FAULT_TYPES:
                    ft = "nominal"
                ch = item.get("channel", valid_channels[0])
                if ch not in valid_channels:
                    ch = valid_channels[0]

                validated_plan.append({
                    "test_id": tid,
                    "requirement_ids": req_ids,
                    "fault_type": ft,
                    "channel": ch,
                    "reason": item.get("reason", "Verification test scenario."),
                    "expected_observable": item.get("expected_observable", "Deterministic observable behavior."),
                })

            return validated_plan
        except Exception as exc:
            if attempt == 2:
                _log_decision(f"plan: batch failed after 2 attempts ({exc}); using fallback plan")
                return _synthesize_deterministic_plan(requirements, channel=valid_channels[0])
            continue

    return _synthesize_deterministic_plan(requirements, channel=valid_channels[0])


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

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2)

    print(f"Generated {len(plan)} test plan entries to {args.out}")
