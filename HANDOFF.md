# Firmware Agent: Hand-off Document

This document describes the integration state across all three subsystems after the Person A (Simulator), Person B (Judge), and Person C (Agent/LLM) sprints are merged.

## A. SimBackend Interface

Simulations are invoked via `run_simulations()` in `agent/steps/runner.py`. It auto-detects the real backend (`sim.runner.simulate`) or falls back to the deterministic mock. The function accepts an array of validated `Timeline` models and the target `firmware_path`, returning:
`(List[Trace], List[Monitor], List[Verdict])`

## B. Trace Contract

All simulator runners return traces matching `contracts/trace.schema.json`:

```json
{
  "test_id": "T05",
  "firmware": "fw_v1.bin",
  "sim": "mock",
  "seed": 100,
  "events": [{ "t_ms": 1500, "kind": "hardfault" }],
  "end_reason": "crash",
  "samples": [
    { "t_ms": 100, "dir": "in", "channel": "temp", "value": 35.0 },
    { "t_ms": 200, "dir": "out", "channel": "fan", "value": 0 }
  ]
}
```

## C. Timeline Contract

Timelines match `contracts/timeline.schema.json`. The agent compiler auto-heals durations exceeding `120000ms` and flags `healed: true`.

## D. Integration Status

### Integrated & Verified

- **Person A (`sim/`):** `RenodeBackend`, `FakeBackend`, `si7021_injected`, timeline linting, fault injection, matrix runner.
- **Person B (`judge/`):** Deterministic judge engine (`always`, `never`, `within`, `eventually`, `hold_ms`), generic oracles (HardFault, hang, reset loop, UART silence/garbage, invalid memory access), 5 calibration mutants, scoreboard.
- **Person C (`agent/`):** LangGraph 6-node pipeline (spec → plan → timeline → run → explain → report), LLM router with Gemini/Ollama fallback, SHA-256 disk cache, offline replay via `demo_cache/`, Jinja2 HTML report.

### Mock (To be replaced with live wiring)

- **Runner dispatch:** `agent/steps/runner.py` currently falls back to `_run_mock()` because `sim.runner.simulate()` is not yet exposed as a top-level importable function. The real `sim/backend.py::RenodeBackend.run()` works independently.
- **Judge wiring:** The runner's `_run_real()` path imports `judge.evaluate.evaluate` — this module path needs to be confirmed (the actual function is `judge.judge.evaluate`).

## E. Quick Start

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Validate contracts
python contracts/validate_examples.py

# Run all tests (57+ tests)
pytest -v

# Offline agent run (uses demo_cache/)
$env:LLM_OFFLINE="1"; python -m agent.run dummy_fw.bin --spec tests/fixtures/sample_spec.md

# Offline sim demo (uses FakeBackend)
python run_demo.py --offline
```
