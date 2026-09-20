# PS3 Firmware Testing Agent

Bare-bones starting repository for **AI Agent for Autonomous Embedded Firmware Testing**.

## Initial stack

- Frontend: React
- Backend: FastAPI / Python
- LLM: Gemini API, with Ollama fallback planned
- Firmware analysis: Tree-sitter + Gemini
- Agent orchestration: LangGraph
- Simulation: Renode + Wokwi
- PASS/FAIL: deterministic Python judge
- Report: HTML -> PDF
- Database: none

## Current product flow

```text
Firmware upload
    -> firmware analysis
    -> test-plan generation
    -> simulation (Renode/Wokwi)
    -> deterministic verdict
    -> failure analysis
    -> report
```

## Run backend

```bash
cd backend
python -m venv .venv
# activate the venv
pip install -r requirements.txt
uvicorn main:app --reload
```

## Run frontend

```bash
cd frontend
npm install
npm run dev
```

## Configuration

Copy `.env.example` to `.env` and fill values as needed. Never commit `.env`.

---

## Agent Demo Commands (Person C Scope)

In its current version, this framework demonstrates the logic orchestrator executing fully isolated in `mock` mode via synthetic backends and intelligent graph healing endpoints natively decoupled from real simulator nodes.

**1. Normal Offline Execution** (Reuses LLM cache deterministically to seamlessly generate the pristine reports output.)
```bash
LLM_OFFLINE=1 python -m agent.run dummy_fw.bin --spec tests/fixtures/sample_spec.md
```

**2. Buggy Hardware Demo** (Dynamically targets the R7 thermal management fault and natively constructs an HTML test report `out/demo_fail_report.html` securely containing embedded explanation graphs.)
```bash
python -m agent.run dummy_fw.bin --spec tests/fixtures/sample_spec.md --demo-failure
```

**3. Integration Validation Suite** (Tests bounding heuristics, deterministic plan requirement corrections, and native offline schema compliance checks end to end out of network constraints.)
```bash
pytest -v
```
