# Firmware Testing Agent: Complete System Hand-off Document

This document describes the final architecture, interface contracts, and verification status across all subsystems of the Autonomous Firmware Testing Agent.

---

## 1. System Architecture

The verification pipeline operates as an authoritative 8-node LangGraph sequential DAG initialized from the `triage` node:

```
[triage]  ──>  [profile]  ──>  [spec]  ──>  [plan]  ──>  [timeline]  ──>  [run]  ──>  [explain]  ──>  [report]
```

1. **`triage` (`profile/static/triage.py`):**
   Validates ELF magic bytes, inspects vector table addresses, extracts symbol tables, and scans string literals. Rejects invalid binaries immediately.
2. **`profile` (`profile/infer.py`):**
   Infers peripheral bindings, memory layout, and UART channels with confidence scoring. Guarantees unknown binaries (`generic_arm_firmware`) do **not** inherit SI7021 sensor platform or script bindings.
3. **`spec` (`agent/steps/spec.py`):**
   Extracts formal requirements from specification text with line provenance. Employs a SHA-256 disk cache with two-tier LLM fallback (Gemini free-tier primary $\to$ Ollama local fallback).
4. **`plan` (`agent/steps/plan.py`):**
   Generates a balanced test matrix capped at 8 tests, covering nominal conditions, boundary limits, and fault injections (dropout, stuck, spike, noise).
5. **`timeline` (`agent/steps/timelines.py`):**
   Compiles concrete input event sequences. Auto-heals timeline durations exceeding 120 seconds and validates channels against the active I/O map.
6. **`run` (`agent/steps/runner.py` $\to$ `sim/runner.py` $\to$ `sim/backend.py`):**
   Dispatches to `RenodeBackend` for ELF binaries or `FakeBackend` for dummy test fixtures. Advances virtual CPU time via `emulation RunFor`, records microsecond-accurate UART output via Asciinema, and applies dynamic sensor fault injection.
7. **`explain` (`agent/steps/explain.py`):**
   Synthesizes failure hypotheses for failing or inconclusive tests, linking observed telemetry anomalies to likely firmware root causes.
8. **`report` (`agent/steps/report.py`):**
   Renders a standalone, dark-themed HTML report embedding verdict summaries, trace telemetry charts, and requirement matrices.

---

## 2. Core Interfaces & Contracts

### A. SimBackend Interface (`sim/runner.py`)

```python
def simulate(
    firmware_path: str | Path,
    timeline_dict: Dict[str, Any],
    io_map: Optional[Dict[str, Any]] = None,
    sim_mode: str = "renode",
    timeout_s: int = 60,
) -> Dict[str, Any]:
```

- **Zero Silent Mock Fallback:** If Renode is not found or fails to start on real firmware, returns explicit `end_reason: "sim_error"` and `error_detail: "INFRASTRUCTURE_ERROR: ..."`. Never falls back silently to mock data.
- **Trace Output:** Fully conforms to `contracts/trace.schema.json`.

### B. Deterministic Judge Interface (`judge/evaluate.py`)

```python
def evaluate(
    timeline_dict: Dict[str, Any],
    trace_data: Dict[str, Any],
    requirements: Optional[List[Dict[str, Any]]] = None,
    monitors: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
```

- **Evaluation Firewall:** The LLM never participates in pass/fail decisions.
- **Honest Inconclusive:** Simulation crashes, infrastructure errors, or unhandled exceptions evaluate to `INCONCLUSIVE` with detailed evidence.
- **Gold Calibration:** Loads pre-calibrated gold monitors from `calib/gold/monitors.json` when evaluating STM32F4/SI7021 firmware.

---

## 3. Benchmark Verification Status

### Live Renode Mutation Scoreboard (`eval/scoreboard.py`)

- **Total Mutants:** 5 (ARM Thumb-2 binary mutants)
- **Mutants Caught:** 5 / 5 (**100.0% Detection Rate**)
- **Baseline Golden Firmware (`original.elf`):** 9 / 9 Passing (**0 False Alarms**)
- **Overall Status:** **PASSED**

| Firmware Binary                 | Mutation Class      | Key Failing Monitor                        | Observed Anomaly                     | Result                    |
| :------------------------------ | :------------------ | :----------------------------------------- | :----------------------------------- | :------------------------ |
| `original.elf`                  | Golden Reference    | None                                       | Nominal telemetry stream             | **PASS (0 False Alarms)** |
| `mutant_1_branch_inversion.elf` | Branch Inversion    | `M_TELEMETRY_PERIOD`, `M_TELEMETRY_FORMAT` | Emits `"Error"` payload              | **CAUGHT**                |
| `mutant_2_timing_delay.elf`     | Delay Removal       | `M_TELEMETRY_PERIOD`                       | 7 ms transmission flood (< 200 ms)   | **CAUGHT**                |
| `mutant_3_humidity_offset.elf`  | Arithmetic Offset   | `M_HUMIDITY_RANGE_HIGH`                    | 102.0% RH (> 100%)                   | **CAUGHT**                |
| `mutant_4_humidity_scale.elf`   | Scale Coefficient   | `M_HUMIDITY_RANGE_LOW`                     | -6.0% RH (< 0%)                      | **CAUGHT**                |
| `mutant_5_i2c_command.elf`      | I2C Protocol Opcode | `M_TEMP_RANGE_HIGH`                        | 65535.0°C (> 125°C) from opcode 0xFF | **CAUGHT**                |

---

## 4. Web Dashboard & API Security (`backend/main.py`)

- **CORS Explicit Origins:** Configured for `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000`, `http://127.0.0.1:3000`.
- **Upload Validation:** Enforces 20MB file size limit and checks for `\x7fELF` magic bytes.
- **Run Isolation:** Every pipeline execution generates a UUID `run_id` and persists artifacts to `out/runs/<run_id>/`.
- **Honest Compliance:** Zero verdicts computed reports 0.0% compliance, not false 100.0%.

---

## 5. Test Suite

Run all automated unit and integration tests:

```powershell
pytest -v
```

**Status:** 70 passed in 1.76s (100% green).
