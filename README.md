# Autonomous Embedded Firmware Testing Agent

An autonomous firmware verification framework combining **Renode** hardware simulation, deterministic **Python judging**, seeded **mutant calibration**, and a **LangGraph LLM agent** for automated test planning, timeline generation, and failure diagnosis.

---

## Architecture Overview

```
                 ┌─────────────────────────────────────────────────┐
                 │                LangGraph Agent                  │
                 │  Spec Extraction → Test Planning → Timelines   │
                 └──────────────┬──────────────────▲───────────────┘
                                │ Timelines        │ Hypotheses
                                ▼                  │ & Report
┌──────────────────────────────────────────────┐   │
│             Renode / Sim Backend             │   │
│   STM32F4 + SI7021 I2C Injection + UART Log  │   │
└──────────────────────┬───────────────────────┘   │
                       │ Traces                    │
                       ▼                           │
┌──────────────────────────────────────────────┐   │
│             Deterministic Judge              │   │
│   Temporal Monitors + Generic Crash Oracles  │───┘
│       (LLM NEVER decides PASS / FAIL)        │   Verdicts & Evidence
└──────────────────────────────────────────────┘
```

- **Person A (Simulation)**: Renode STM32 simulation backend, SI7021 sensor injection, UART capture, timeline linting, fault execution, parallel matrix runner.
- **Person B (Evaluation)**: Deterministic temporal logic judge (`always`, `never`, `within`, `eventually`, `hold_ms`), generic crash oracles (HardFault, reset loop, hang, UART silence/corruption, invalid memory access), 5 ARM Thumb-2 binary mutants, and scoreboard.
- **Person C (Agent & Reporting)**: 6-node LangGraph pipeline extracting requirements, synthesizing bounded test plans and sensor timelines, managing offline replay caches, diagnosing failures, and rendering dark-themed HTML reports.

---

## Quick Start

### 1. Environment Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run Test Suite

Run all 61 automated tests verifying simulation modules, judge logic, generic oracles, mutant validity, scoreboard metrics, router caching, and offline replay:

```powershell
pytest -v
```

---

## Running Demos

### 1. Offline Agent Run (LangGraph Replay)

Runs the complete LangGraph pipeline end-to-end using pre-recorded responses in `demo_cache/`. No API keys or Ollama instance required:

```powershell
$env:LLM_OFFLINE="1"; python -m agent.run firmware/inputs/firmware1.elf --spec tests/fixtures/sample_spec.md
```

Outputs:

- `out/report.html`: Interactive HTML report with requirement matrix, test verdicts, and provenance.
- `out/requirements.json`: Structured requirements extracted from markdown.
- `out/test_plan.json`: Test matrix and fault assignments.
- `out/timelines.json`: Validated and duration-bounded input timelines.

### 2. Simulated Fault & Failure Diagnosis Demo

Demonstrates the failure diagnosis loop by simulating a thermal management fault (cooling fan failure under load) and producing an evidence-backed failure report:

```powershell
python -m agent.run dummy_fw.bin --spec tests/fixtures/sample_spec.md --demo-failure
```

Report generated at: `out/demo_fail_report.html`

### 3. Renode Simulation Demo

Executes simulation using the deterministic fake backend or real Renode instance:

```powershell
# Offline / fake backend (fast verification)
python run_demo.py --offline

# Live Renode backend (requires Renode on PATH)
python run_demo.py
```

### 4. Renode Hardware & Sensor Probe

Interactively probes the STM32F4 Discovery platform with I2C1 SI7021 sensor injection and USART2 monitoring:

```powershell
python sim/probe_sensor.py --injected
```

---

## Core Principles & Constraints

1. **Deterministic Judging**: The LLM **never** decides PASS or FAIL verdicts. Verdicts are strictly computed by `judge/judge.py` and `judge/generic_oracles.py` against concrete trace samples and execution events.
2. **Contract Enforced**: All pipeline boundaries exchange JSON data validated against frozen schemas in `contracts/` (`timeline.schema.json`, `trace.schema.json`, `verdict.schema.json`, `monitor.schema.json`, `requirement.schema.json`, `io_map.schema.json`).
3. **Bounded & Auto-Healed**: Test plans are capped at 8 tests, and timeline durations exceeding 120 seconds are automatically clamped and healed by `agent/steps/timelines.py`.
4. **Offline Reproducibility**: The test suite and offline demos execute completely self-contained via `demo_cache/` without network dependencies.

---

## Repository Layout

```
firmware-testing-agent/
├── agent/                  # LangGraph LLM test planning & reporting
│   ├── graph.py            # 6-node state machine pipeline
│   ├── models.py           # Pydantic v2 data models matching schemas
│   ├── run.py              # Main CLI entry point
│   ├── llm/                # Router with Gemini/Ollama fallback & caching
│   └── steps/              # Spec extraction, planning, timelines, report
├── calib/                  # Calibration mutants & reference gold spec
│   ├── gold/               # Gold requirements & monitors
│   └── mutants/            # 5 ARM Thumb-2 byte-patched ELF mutants
├── contracts/              # Frozen JSON schemas and example payloads
├── demo_cache/             # 81 committed LLM responses for deterministic replay
├── eval/                   # Mutation testing scoreboard & benchmarks
│   └── scoreboard.py       # Computes mutation score (100% detection rate)
├── faults/                 # Sensor fault definitions & catalog
│   └── library.json        # Dropout, stuck, ramp_overshoot, glitch, etc.
├── firmware/               # Firmware binaries
│   └── inputs/             # Reference STM32 ELF firmware (firmware1.elf)
├── judge/                  # Deterministic verification engine
│   ├── judge.py            # Temporal monitors (always, never, within, eventually)
│   ├── generic_oracles.py  # HardFault, hang, UART silence, memory access
│   └── fake_judge.py       # Stand-in judge for offline pipeline testing
├── profile/                # Hardware & ELF static analysis
│   ├── io_map.json         # Peripherals, pins, and I2C mappings
│   └── static/             # Static ELF triage (vectors, sections, symbols)
├── report/                 # HTML templates for report generation
├── sim/                    # Simulation infrastructure
│   ├── backend.py          # Renode execution backend & command builder
│   ├── fake_backend.py     # Deterministic simulation mock
│   ├── lint.py             # Timeline and channel validation
│   ├── matrix.py           # Parallel test execution matrix
│   └── si7021_injected.py  # Renode I2C sensor injection logic
└── tests/                  # Automated pytest suite (61 tests)
```
