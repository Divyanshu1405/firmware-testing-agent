# Autonomous Embedded Firmware Verification Agent Demo

Welcome to the autonomous firmware verification agent. This demo illustrates how the system deterministically verifies firmware binaries against functional requirements using virtual hardware simulation (Renode), formal temporal monitors, and autonomous LLM test planning.

---

## 1. Live Hardware Mutation Benchmark (100% Catch Rate)

_Executes the comprehensive mutation evaluation benchmark across `original.elf` and all 5 ARM Thumb-2 binary mutants in live Renode virtual hardware._

```powershell
python eval/scoreboard.py
```

**Expected Results:**

- `original.elf`: **PASS** (9 monitors evaluated, **0 False Alarms**)
- `MUTANT_01` (Branch Inversion): **CAUGHT** by `M_TELEMETRY_PERIOD` & `M_TELEMETRY_FORMAT`
- `MUTANT_02` (Delay Zero Flood): **CAUGHT** by `M_TELEMETRY_PERIOD` (7 ms flood < 200 ms)
- `MUTANT_03` (Humidity +15% Offset): **CAUGHT** by `M_HUMIDITY_RANGE_HIGH` (102.0% > 100%)
- `MUTANT_04` (Humidity Scaling Inversion): **CAUGHT** by `M_HUMIDITY_RANGE_LOW` (-6.0% < 0%)
- `MUTANT_05` (I2C Invalid Opcode 0xFF): **CAUGHT** by `M_TEMP_RANGE_HIGH` (65535.0°C > 125°C)
- **Mutation Detection Rate:** **100.0% (5 / 5 caught)**
- Output updated in: `eval/scoreboard.md`

---

## 2. Web UI & Verification Dashboard

_Launch the full verification dashboard with the FastAPI backend and React frontend:_

```powershell
# Terminal 1: Launch Backend API Server
python -m uvicorn backend.main:app --port 8000 --reload

# Terminal 2: Launch Vite React GUI
cd frontend
npm run dev
```

Open your browser to `http://localhost:5173`.

- Select target firmware (`original.elf`, `mutant_*.elf`, or custom uploaded binary).
- Review or adjust natural-language operational requirements.
- Choose **Deterministic Mode** (local rules + Renode) or **LLM-Augmented Mode** (Gemini/OpenAI + Renode).
- Click **▶ Run Firmware Verification Pipeline** to watch the 8-stage pipeline execute:
  1. Triage $\to$ 2. Profile $\to$ 3. Requirements $\to$ 4. Test Planning $\to$ 5. Timelines $\to$ 6. Renode Simulation $\to$ 7. Deterministic Judge $\to$ 8. Report.
- Inspect the interactive report, failure hypotheses, and microsecond telemetry traces inline.

---

## 3. End-to-End Autonomous Pipeline CLI Run

_Executes the full 8-node LangGraph pipeline directly on the command line:_

```powershell
# Offline Replay / Deterministic Mode (no API key required)
$env:LLM_OFFLINE="1"; python -m agent.run firmware/inputs/firmware1.elf --spec tests/fixtures/sample_spec.md

# Live Renode Hardware Simulation on Original Firmware
python -m agent.run original.elf
```

Outputs generated in `out/`:

- `out/report.html`: Standalone verification report.
- `out/requirements.json`: Formal requirements extracted from specification text.
- `out/test_plan.json`: Synthesized test scenarios and fault injection matrix.
- `out/timelines.json`: Compiled sensor input timelines.

---

## 4. Negative Control Failure Demo

_Executes an intentional negative control fault (cooling fan failure under thermal load) to demonstrate failure hypothesis generation:_

```powershell
python -m agent.run dummy_fw.bin --spec tests/fixtures/sample_spec.md --demo-failure
```

Report generated at: `out/demo_fail_report.html`

---

## 5. Automated Verification Suite

_Executes all 70 unit and integration tests verifying simulation backends, judge logic, generic oracles, mutant validity, microsecond timestamp parsing, and API security:_

```powershell
pytest -v
```

All 70 tests pass in < 2 seconds.
