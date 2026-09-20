"""
agent/steps/timelines.py
Convert out/test_plan.json entries into full Timeline objects by calling the LLM.
Runs a stand-in lint pass on generated timelines:
  - at_ms values must be within [0, duration_ms]
  - events must be in chronological order
  - at least one event per timeline
  - action values must be from the allowed enum
  - referenced requirements must exist in the original requirements list
Rejects failing timelines and retries up to 2 times before dropping them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Any

from agent.models import Timeline, TimelineAction, Requirement
import agent.llm.router as _router
from agent.llm.router import _extract_json, _log_decision

ALLOWED_ACTIONS = {a.value for a in TimelineAction}

TIMELINE_PROMPT_TEMPLATE = """\
You are a firmware test automation system. The planner has assigned you a test scenario.
Generate a detailed test timeline (events array) that fulfills this test plan.

Available Requirements:
{requirements_json}

Test Plan Entry:
{plan_json}

Output a single JSON object with EXACTLY these fields (no other keys, no root wrappers):
- "test_id": string (MUST be exactly "{test_id}")
- "requirement_ids": array of strings (the requirements covered by this test)
- "duration_ms": integer, total test duration in milliseconds
- "events": array of event objects, each with:
    - "at_ms": integer (milliseconds from start, MUST be ordered chronologically and <= duration_ms)
    - "action": string (MUST be one of: set, ramp, step, dropout, stuck, spike, glitch, drift, uart_write, uart_garbage)
    - "channel": string (e.g. "temp_c", "power")
    - optional: "value", "to", "over_ms", "for_ms"

Return ONLY valid JSON.
"""

def _standin_lint(tl_dict: dict, valid_req_ids: set[str]) -> list[str]:
    """Return a list of lint error strings, empty if clean."""
    errors: list[str] = []
    
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
            errors.append(f"event at {at_ms} ms exceeds duration_ms {duration_ms}. Keep event at {at_ms} ms <= duration_ms.")
        if at_ms < prev_ms:
            errors.append(f"events not chronological: {at_ms} after {prev_ms}")
        if action not in ALLOWED_ACTIONS:
            errors.append(f"unknown action '{action}'")
        prev_ms = at_ms

    return errors


def expand_plan_to_timelines(plan: List[Dict[str, Any]], requirements: List[Requirement]) -> List[Timeline]:
    """
    Generate and lint full Timeline objects from a list of plan dicts.
    """
    valid_req_ids = {r.id for r in requirements}
    timelines: List[Timeline] = []

    for entry in plan:
        test_id = entry.get("test_id", "TXX")
        prompt = TIMELINE_PROMPT_TEMPLATE.format(
            requirements_json=json.dumps([r.model_dump() for r in requirements], indent=2),
            plan_json=json.dumps(entry, indent=2),
            test_id=test_id
        )

        for attempt in range(1, 4):  # up to 3 tries total (1 + 2 retries)
            try:
                import hashlib
                _model = _router.GEMINI_MODEL_FAST
                _tier = "fast"
                # Vary cache key for retries so we don't just fetch the same failed response
                cache_raw = f"{_model}::{prompt}::attempt{attempt}"
                cache_key = hashlib.sha256(cache_raw.encode()).hexdigest()

                raw = None
                cached = _router._read_cache(cache_key)
                if cached is not None:
                    _router._log_provenance(cached.get("model_used", _model), True, cache_key, f"timeline:{test_id}", tier=_tier)
                    data = cached["data"]
                else:
                    if _router.LLM_OFFLINE:
                        raise RuntimeError(f"LLM_OFFLINE=1 but no cache entry for timeline (key {cache_key[:8]})")
                    if _router._calls_this_run >= _router.LLM_CALL_BUDGET:
                        raise RuntimeError("LLM call budget exhausted")

                    _router._calls_this_run += 1
                    model_used = _model
                    try:
                        raw = _router._call_gemini(prompt, _model)
                    except Exception as exc:
                        _log_decision(f"timeline Gemini ({_model}) failed ({exc}); falling back to Ollama")
                        raw = _router._call_ollama(prompt, _router.OLLAMA_MODEL)
                        model_used = _router.OLLAMA_MODEL

                    data = _extract_json(raw)
                    _router._write_cache(cache_key, {"model_used": model_used, "data": data})
                    _router._log_provenance(model_used, False, cache_key, f"timeline:{test_id}", tier=_tier)

                # Clean out explicit nulls from events and naturally auto-repair duration_ms limits
                if isinstance(data, dict):
                    # Deterministic override of plan properties
                    overwritten = []
                    for key in ["test_id", "requirement_ids", "fault_type"]:
                        if key in entry:
                            plan_val = entry[key]
                            llm_val = data.get(key)
                            # compare lists set-wise or values natively
                            differs = set(plan_val) != set(llm_val) if isinstance(plan_val, list) and isinstance(llm_val, list) else plan_val != llm_val
                            print(f"[DEBUG] {test_id} key={key} plan={plan_val} llm={llm_val} differs={differs}")
                            if differs:
                                overwritten.append(f"{key} (was {llm_val}, forced to {plan_val})")
                                data[key] = plan_val
                                print(f"[DEBUG] {test_id} actually forced {key} to {data[key]}")
                    
                    if overwritten:
                        _log_decision(f"timeline {test_id} deterministic overwrite: {', '.join(overwritten)}")

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
                                    _log_decision(f"timeline {test_id} rejected by stand-in lint (attempt {attempt}): {'; '.join(errors)}")
                                    if attempt == 3:
                                        _log_decision(f"timeline {test_id} dropped after 3 attempts.")
                                    continue
                                data["duration_ms"] = new_dur
                                data["healed"] = True
                                _log_decision(f"timeline {test_id} auto-repair: extended duration_ms from {old_dur} to {data['duration_ms']} to fit events")

                errors = _standin_lint(data, valid_req_ids)
                if errors:
                    _log_decision(f"timeline {test_id} rejected by stand-in lint (attempt {attempt}): {'; '.join(errors)}")
                    if attempt == 3:
                        _log_decision(f"timeline {test_id} dropped after 3 attempts.")
                    continue  # Retry

                # Try to use Pydantic validation now
                try:
                    tl = Timeline.model_validate(data)
                except Exception as eval_exc:
                    _log_decision(f"timeline {test_id} failed pydantic schema (attempt {attempt}): {eval_exc}")
                    if attempt == 3:
                        _log_decision(f"timeline {test_id} dropped after 3 attempts due to schema.")
                    continue  # Retry

                timelines.append(tl)
                _log_decision(f"timeline {test_id} accepted after {attempt} attempts.")
                break
            except Exception as exc:
                _log_decision(f"timeline {test_id} hard error (attempt {attempt}): {exc}")
                if attempt == 3:
                    pass

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
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}")
        import sys; sys.exit(1)
        
    with open(schema_path, "r", encoding="utf-8") as f:
        timeline_schema = json.load(f)
        
    for td in timeline_dicts:
        try:
            jsonschema.validate(instance=td, schema=timeline_schema)
        except jsonschema.ValidationError as ve:
            print(f"FATAL: Validating timeline {td.get('test_id')} against schema failed: {ve}")
            import sys; sys.exit(1)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(timeline_dicts, f, indent=2)

    print(f"Generated {len(timelines)} timelines to {args.out}")
