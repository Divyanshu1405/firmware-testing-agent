"""Timeline generator compiling test plans into executable, linted timelines."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import agent.llm.router as _router
from agent.llm.router import _extract_json, _log_decision
from agent.models import Requirement, Timeline, TimelineAction, TimelineEvent
from sim.lint import lint_timeline

ALLOWED_ACTIONS = {a.value for a in TimelineAction}

TIMELINE_PROMPT_TEMPLATE = """\
You are a firmware test automation system. The planner has assigned you a test scenario.
Generate a detailed test timeline (events array) that fulfills this test plan.

Available Requirements:
{requirements_json}

Target Hardware Interfaces:
{interfaces_json}

Test Plan Entry:
{plan_json}

Output a single JSON object with EXACTLY these fields (no other keys, no root wrappers):
- "test_id": string (MUST be exactly "{test_id}")
- "requirement_ids": array of strings (the requirements covered by this test)
- "duration_ms": integer, total test duration in milliseconds (e.g. 2500)
- "events": array of event objects, each with:
    - "at_ms": integer (milliseconds from start, MUST be ordered chronologically and <= duration_ms)
    - "action": string (one of: set, step, ramp, dropout, stuck, spike, glitch, drift, error_reading, uart_write, uart_garbage)
    - "channel": string (valid channel from available interfaces)
    - optional: "value", "to", "over_ms", "for_ms"

Return ONLY valid JSON.
"""


def _synthesize_fallback_timeline(
    entry: Dict[str, Any], valid_channel: str = "temp_c"
) -> Dict[str, Any]:
    """Deterministically compile a plan entry into a valid executable timeline."""
    tid = entry.get("test_id", "T01")
    req_ids = entry.get("requirement_ids", ["REQ-01"])
    ft = entry.get("fault_type", "nominal").lower()
    ch = entry.get("channel", valid_channel)

    duration_ms = 2500
    events: List[Dict[str, Any]] = []

    if ft == "dropout":
        events = [
            {"at_ms": 500, "action": "set", "channel": ch, "value": 25.0},
            {"at_ms": 1000, "action": "dropout", "channel": ch, "for_ms": 1000},
        ]
    elif ft == "stuck":
        events = [
            {"at_ms": 500, "action": "set", "channel": ch, "value": 25.0},
            {"at_ms": 1000, "action": "stuck", "channel": ch, "value": 35.0, "for_ms": 1000},
        ]
    elif ft in ("spike", "glitch"):
        events = [
            {"at_ms": 500, "action": "set", "channel": ch, "value": 25.0},
            {"at_ms": 1000, "action": "spike", "channel": ch, "value": 75.0, "for_ms": 500},
        ]
    elif ft == "boundary":
        events = [
            {"at_ms": 500, "action": "set", "channel": ch, "value": 90.0},
            {"at_ms": 1500, "action": "set", "channel": ch, "value": 10.0},
        ]
    elif ft == "error_reading":
        events = [
            {"at_ms": 500, "action": "set", "channel": ch, "value": 25.0},
            {"at_ms": 1000, "action": "error_reading", "channel": ch, "for_ms": 1000},
        ]
    else:  # nominal or default
        events = [
            {"at_ms": 200, "action": "set", "channel": ch, "value": 25.0},
            {"at_ms": 1200, "action": "set", "channel": ch, "value": 30.0},
        ]

    return {
        "test_id": tid,
        "requirement_ids": req_ids,
        "duration_ms": duration_ms,
        "events": events,
    }


def _standin_lint(tl_dict: Dict[str, Any], valid_req_ids: Set[str]) -> List[str]:
    """Return a list of lint error strings, empty if clean."""
    errors: List[str] = []
    events = tl_dict.get("events", [])
    if not events:
        errors.append("no events defined")
        return errors

    duration_ms = tl_dict.get("duration_ms", 0)
    for req_id in tl_dict.get("requirement_ids", []):
        if req_id not in valid_req_ids:
            errors.append(f"referenced requirement_id '{req_id}' not found in requirements")

    prev_ms = -1
    for ev in events:
        at_ms = ev.get("at_ms", 0)
        action = ev.get("action", "")
        if at_ms > duration_ms:
            errors.append(f"event at {at_ms} ms exceeds duration_ms {duration_ms}")
        if at_ms < prev_ms:
            errors.append(f"events not chronological: {at_ms} after {prev_ms}")
        if action not in ALLOWED_ACTIONS:
            errors.append(f"unknown action '{action}'")
        prev_ms = at_ms

    return errors


def expand_plan_to_timelines(
    plan: List[Dict[str, Any]],
    requirements: List[Requirement],
    io_map: Optional[Dict[str, Any]] = None,
) -> List[Timeline]:
    """Generate, lint, and validate full Timeline objects from test plan entries."""
    valid_req_ids = {r.id for r in requirements}
    active_io = io_map or {}
    default_ch = list(active_io.get("inputs", {}).keys())[0] if active_io.get("inputs") else "temp_c"

    timelines: List[Timeline] = []

    for entry in plan:
        test_id = entry.get("test_id", "T01")
        prompt = TIMELINE_PROMPT_TEMPLATE.format(
            requirements_json=json.dumps([r.model_dump() for r in requirements], indent=2),
            interfaces_json=json.dumps(active_io, indent=2),
            plan_json=json.dumps(entry, indent=2),
            test_id=test_id,
        )

        timeline_obj: Optional[Timeline] = None

        for attempt in range(1, 4):
            try:
                import hashlib
                _model = _router.GEMINI_MODEL_FAST
                _tier = "fast"
                cache_raw = f"{_model}::{prompt}::attempt{attempt}"
                cache_key = hashlib.sha256(cache_raw.encode()).hexdigest()

                cached = _router._read_cache(cache_key)
                if cached is not None:
                    _router._log_provenance(cached.get("model_used", _model), True, cache_key, f"timeline:{test_id}", tier=_tier)
                    data = cached["data"]
                else:
                    if _router.is_offline() or getattr(_router, "_gemini_exhausted", False):
                        fallback_data = _synthesize_fallback_timeline(entry, default_ch)
                        timeline_obj = Timeline.model_validate(fallback_data)
                        break
                    if _router._calls_this_run >= _router.LLM_CALL_BUDGET:
                        fallback_data = _synthesize_fallback_timeline(entry, default_ch)
                        timeline_obj = Timeline.model_validate(fallback_data)
                        break

                    _router._calls_this_run += 1
                    try:
                        raw = _router._call_gemini(prompt, _model)
                        model_used = _model
                    except Exception as exc:
                        _log_decision(f"timeline Gemini ({_model}) failed ({exc}); falling back to Ollama")
                        raw = _router._call_ollama(prompt, _router.OLLAMA_MODEL)
                        model_used = _router.OLLAMA_MODEL

                    data = _extract_json(raw)
                    _router._write_cache(cache_key, {"model_used": model_used, "data": data})
                    _router._log_provenance(model_used, False, cache_key, f"timeline:{test_id}", tier=_tier)

                if isinstance(data, dict):
                    data["test_id"] = test_id
                    data["requirement_ids"] = entry.get("requirement_ids", ["REQ-01"])

                    if "events" in data:
                        max_ms = 0
                        for ev in data["events"]:
                            if isinstance(ev, dict):
                                for k in list(ev.keys()):
                                    if ev[k] is None:
                                        del ev[k]
                                if "at_ms" in ev and isinstance(ev["at_ms"], (int, float)):
                                    max_ms = max(max_ms, ev["at_ms"])

                        if "duration_ms" in data and isinstance(data["duration_ms"], (int, float)):
                            old_dur = data["duration_ms"]
                            if max_ms > old_dur:
                                new_dur = int(max_ms + 100)
                                if new_dur > 120000:
                                    errors = [f"healed duration_ms {new_dur} exceeds 120000 ms cap"]
                                    _log_decision(f"timeline {test_id} rejected (attempt {attempt}): {'; '.join(errors)}")
                                    if attempt == 3:
                                        _log_decision(f"timeline {test_id} dropped after 3 attempts.")
                                    continue
                                data["duration_ms"] = new_dur
                                data["healed"] = True

                    if io_map:
                        lint_errs = lint_timeline(data, active_io)
                        if lint_errs:
                            _log_decision(f"timeline {test_id} lint issues: {'; '.join(lint_errs)}")
                            continue

                    errors = _standin_lint(data, valid_req_ids)
                    if errors:
                        _log_decision(f"timeline {test_id} rejected by standin lint: {'; '.join(errors)}")
                        continue

                    timeline_obj = Timeline.model_validate(data)
                    break
            except Exception as exc:
                _log_decision(f"timeline {test_id} error (attempt {attempt}): {exc}")
                if _router.is_offline() or getattr(_router, "_gemini_exhausted", False):
                    fallback_data = _synthesize_fallback_timeline(entry, default_ch)
                    timeline_obj = Timeline.model_validate(fallback_data)
                    break
                continue

        if timeline_obj is not None:
            timelines.append(timeline_obj)

    return timelines


if __name__ == "__main__":
    import argparse
    import jsonschema

    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", default="out/test_plan.json")
    parser.add_argument("--reqs", default="out/requirements.json")
    parser.add_argument("--out", default="out/timelines.json")
    args = parser.parse_args()

    plan_path = Path(args.plan)
    reqs_path = Path(args.reqs)

    if not plan_path.exists() or not reqs_path.exists():
        print("Missing plan or reqs. Exiting.")
        import sys
        sys.exit(1)

    with open(reqs_path, "r", encoding="utf-8") as f:
        req_dicts = json.load(f)
    reqs = [Requirement.model_validate(r) for r in req_dicts]

    with open(plan_path, "r", encoding="utf-8") as f:
        plan_dicts = json.load(f)

    timelines = expand_plan_to_timelines(plan_dicts, reqs)
    timeline_dicts = [t.model_dump(exclude_none=True) for t in timelines]

    schema_path = Path("contracts/timeline.schema.json")
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            timeline_schema = json.load(f)
        for td in timeline_dicts:
            jsonschema.validate(instance=td, schema=timeline_schema)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(timeline_dicts, f, indent=2)

    print(f"Generated {len(timelines)} timelines to {args.out}")
