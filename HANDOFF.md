# Firmware Agent: Hand-off Document

This document clarifies the integration boundaries for Person A (Simulator/Backend) and Person B (Frontend Dashboard) as established during the Person C (Agent Logic) sprint (H1-H10).

## A. SimBackend Interface 
The orchestration relies on a strictly bounded execution hand-off. 
Currently, simulations are invoked via the `run_simulations` function inside `agent/steps/runner.py`. The agent pipeline expects this function to accept an array of validated `Timeline` models and the target `firmware_path`. It must block until simulator execution completes and must return exactly a tuple of:
`(List[Trace], List[Any], List[Verdict])`

## B. Trace Contract 
All Simulator runners MUST return payload traces strictly mimicking `contracts/trace.schema.json`.
An acceptable response maps output paths per test explicitly without missing values:
```json
{
  "test_id": "T05",
  "firmware": "fw_v1.bin",
  "sim": "mock",
  "seed": 100,
  "events": [{"t_ms": 1500, "kind": "hardfault"}],
  "end_reason": "crash",
  "samples": [
    {"t_ms": 100, "dir": "in", "channel": "temp", "value": 35.0},
    {"t_ms": 200, "dir": "out", "channel": "fan", "value": 0}
  ]
}
```

## C. Timeline Contract
Timelines are compiled deterministically and are guaranteed to match `contracts/timeline.schema.json`. 
Note the introduction of the optional `healed` field. The agent compiler aggressively traps durations that drop beyond `120000ms`, truncating oversized boundaries silently to save cloud cycles and flagging `healed: true`. 
```json
{
  "test_id": "T05",
  "requirement_ids": ["R8"],
  "duration_ms": 1250,
  "healed": true,
  "events": [
    {
      "at_ms": 50,
      "action": "set",
      "channel": "ch_VCC",
      "value": 3.3
    }
  ]
}
```

## D. Swapping Mock for Real Backend
To bridge true simulator hardware (Renode/Wokwi) directly to the LangGraph pipeline:
1. Open `agent/steps/runner.py`
2. Locate `def run_simulations(timelines: List[Timeline], firmware_path: str) -> tuple:`
3. **Swap the invocation:** Currently, it passes execution to `_run_mock(...)`. Comment out `_run_mock` and wire the method to your simulator bindings (e.g. `_run_renode(timelines)`). 

## E. What is Real vs. Mock Today?

### Real (Fully Functional & Hardened)
- **LangGraph Flow:** Spec parsing -> LLM Batch Planning -> LLM Timelines Builder -> Failure Explanations -> Report Generations.
- **Determinism:** Rate limiting, LLM hallucination overrides (ensuring test plan limits are physically mirrored onto timeline requirement IDs), duration_ms bounds checking, LLM tracing & provenance logs.
- **Reporting Engine:** Complete offline support integrating Base64 Matplotlib embedded visualizations against output vs input plots, comprehensive mapping tables, and Jinja2 rendering.

### Mock (To be Replaced)
- **Runner Executions:** Hardware interaction is bypassed securely via `agent.fake_agent.py` generators.
- **Judging/Assertions:** Currently relying on naive dummy Python assertions since true backend output evaluation nodes mapping memory outputs are awaiting your native implementations.
