# Autonomous Firmware Testing Agent

An evidence-driven framework for testing embedded ELF firmware in virtual hardware. It profiles a firmware image, derives an execution profile, generates test timelines, runs supported targets in Renode, evaluates trace evidence with deterministic monitors, and produces an HTML verification report.

The system separates planning from verdicts: an LLM may help extract requirements, propose scenarios, and explain failures, but it never decides PASS or FAIL.

## What it does

- Validates and statically inspects ELF firmware: architecture, vectors, symbols, strings, and peripheral clues.
- Selects a hardware profile with provenance and confidence. Unknown firmware is not assigned the known sensor profile.
- Generates nominal, boundary, sensor-fault, communication, and timing scenarios from requirements and supported capabilities.
- Executes supported firmware in Renode with virtual-time scheduling and timestamped UART capture.
- Normalizes telemetry, applies deterministic temporal monitors and generic reliability oracles, then returns PASS, FAIL, or INCONCLUSIVE verdicts.
- Produces run-isolated reports and artifacts through a CLI and FastAPI service.

## Supported scope

The reference target is STM32F4 firmware that communicates with an SI7021 sensor over I2C and emits telemetry through USART2. The included profile supports sensor values, dropout, forced sensor errors, stuck readings, and selected transient faults.

For an unknown ELF, the agent performs static triage and uses a deliberately conservative generic profile. It will not invent an SI7021 device, channels, or peripheral wiring. Unsupported stimuli are reported as not executable or inconclusive rather than presented as tested.

## Architecture

```text
ELF firmware + specification
        |
        v
Static triage -> hardware-profile inference -> scenario planning -> timeline validation
        |
        v
Renode execution -> timestamped trace normalization -> deterministic monitors/oracles
        |
        v
Evidence, verdicts, hypotheses, and HTML report
```

Key directories:

- `agent/` - LangGraph workflow, LLM routing, scenario planning, and reporting.
- `profile/` - ELF triage and hardware-profile inference.
- `sim/` - Renode backend, timeline validation, trace normalization, and SI7021 model.
- `judge/` - deterministic temporal monitors and generic crash, hang, reset, and UART oracles.
- `backend/` - FastAPI service.
- `frontend/` - React/Vite dashboard.
- `contracts/` - JSON schemas for pipeline boundaries.
- `calib/` - reference requirements, monitors, and mutation fixtures.
- `tests/` - unit, API, contract, and integration-oriented tests.

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer (for the dashboard)
- Renode (required for live virtual-hardware execution)
- A supported ELF firmware image

On Windows, make sure `renode.exe` is on `PATH` or installed at `C:\Program Files\Renode\renode.exe`.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install fastapi "uvicorn[standard]" python-multipart

cd frontend
npm install
cd ..
```

Set provider credentials only when using live LLM-assisted planning. Copy `.env.example` to `.env` and configure the provider you intend to use. Offline replay does not require an API key.

## Verify the installation

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The suite validates contracts, judge semantics, profile isolation, fault-model behavior, upload controls, run isolation, and simulator error handling.

## Run from the command line

Run the full pipeline against the included firmware and specification:

```powershell
python -m agent.run firmware/inputs/firmware1.elf --spec tests/fixtures/sample_spec.md --out out
```

Run an offline replay when compatible cached LLM responses are available:

```powershell
$env:LLM_OFFLINE="1"
python -m agent.run firmware/inputs/firmware1.elf --spec tests/fixtures/sample_spec.md --out out
```

Generate the isolated negative-control report:

```powershell
python -m agent.run dummy_fw.bin --spec tests/fixtures/sample_spec.md --demo-failure --out out
```

Artifacts are written to the requested output directory and may include:

- `report.html` - verification report
- `requirements.json` - extracted requirements
- `test_plan.json` - selected scenarios and rationale
- `timelines.json` - validated executable timelines

## Run the API and dashboard

Start the API:

```powershell
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

In another terminal, start the dashboard:

```powershell
cd frontend
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

The API provides:

- `GET /health` - service and Renode availability
- `GET /api/firmware` - available baseline, calibration, and uploaded firmware
- `GET /api/spec` - default reference specification
- `POST /api/upload` - validated ELF upload (20 MB limit)
- `POST /api/run` - isolated verification run
- `GET /api/runs/{run_id}/report` - a specific run report

Each API run receives a unique ID and writes its artifacts below `out/runs/<run_id>/`.

## Interpreting results

Verdicts have distinct meanings:

- **PASS** - collected trace evidence satisfies the selected deterministic monitor.
- **FAIL** - collected trace evidence violates a selected deterministic monitor or generic reliability oracle.
- **INCONCLUSIVE** - evidence is insufficient, the target/profile is unsupported, or simulator infrastructure failed.

An infrastructure error is never converted to a fake pass. The report identifies whether a result came from Renode, explicit fake mode, or an offline/replay path.

## Calibration and mutation artifacts

`calib/` contains reference requirements, monitors, and five binary mutation fixtures. Use these artifacts to evaluate changes to test scenarios and monitoring behavior. Do not interpret the included scoreboard document as proof of a fresh live run; run the benchmark in an environment where Renode executes successfully and retain the generated evidence.

```powershell
python eval/scoreboard.py --results path\to\executed-results.json --output eval\scoreboard.md
```

## Operational limitations

- A successful live run requires a working Renode installation with permission to create its runtime/configuration files.
- The current virtual-hardware profile is intentionally narrow; arbitrary ELF firmware is not guaranteed executable without a suitable board and peripheral profile.
- Static inference produces hypotheses, not proof of hardware wiring or behavioral requirements.
- Simulation cannot reproduce all physical effects such as analog noise, voltage transients, clock drift, DMA timing races, or board-specific electrical faults.
- LLM-generated plans must stay within validated profile capabilities; deterministic monitors remain the authority for verdicts.

See [LIMITATIONS.md](LIMITATIONS.md) for further detail.

## Security and repository hygiene

- Do not commit `.env`, run outputs, uploaded firmware, logs, simulator caches, or LLM provenance files.
- Treat uploaded firmware as untrusted input. The API validates ELF magic and file size, but deployment should also use process isolation and resource limits.
- Keep `out/`, `logs/`, and `firmware/uploads/` empty in source control except for their `.gitkeep` placeholders.

## Development

Before opening a pull request:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q agent backend judge profile sim
git diff --check
```

Keep documentation aligned with actual execution behavior. A report is only as trustworthy as the trace evidence it identifies.
