# .loop/HANDOFF.md
## What is done

- `.env.example` — all required env vars, no real secrets
- `.loop/` scaffold — `STATE.md`, `DECISIONS.md`, `LOG.md`, `evidence/`
- `contracts/validate_examples.py` — validates all `*.example.json` against frozen schemas
- `agent/` top-level package:
  - `agent/models.py` — Pydantic v2 models matching all 6 frozen contract schemas
  - `agent/llm/router.py` — Gemini+Ollama fallback, SHA-256 disk cache, budget, provenance
  - `agent/llm/test_router.py` — 4-case pytest suite
  - `agent/fake_agent.py` — canned mock data for all pipeline stages
  - `agent/graph.py` — LangGraph 6-node pipeline (spec→plan→timeline→run→explain→report)
  - `agent/steps/spec.py` — LLM requirement extraction with source_line tracking
  - `agent/steps/plan.py` — test planner (≤8 tests, requirements×fault matrix)
  - `agent/steps/timelines.py` — lint step (delegates to sim.lint or stand-in)
  - `agent/steps/runner.py` — real sim or mock sim (judge decides PASS/FAIL)
  - `agent/steps/explain.py` — FAIL hypotheses citing requirement + evidence
  - `agent/steps/report.py` — Jinja2 HTML renderer
  - `agent/run.py` — main CLI entry point
- `report/template.html` — dark-themed HTML report with provenance footer
- `DEMO_SCRIPT.md` — 2-minute walkthrough

## What is stubbed / pending

- `demo_cache/` — real Gemini responses not yet recorded (needs one live run)
- `LLM_OFFLINE=1` byte-for-bit replay — pending demo_cache population
- Plots — pending Person A's trace format
- `sim.runner` and `sim.lint` — Person A's modules; agent currently uses mock
- `judge.evaluate` — Person B's module; agent currently uses mock verdicts

## What still needs A / B

| Item | Owner | Status |
|---|---|---|
| `sim/runner.simulate(firmware, timeline)` → raw trace dict | Person A | pending |
| `sim/lint.validate_timeline(timeline_dict)` | Person A | pending |
| `judge/evaluate.evaluate(timeline, trace)` → monitors + verdicts | Person B | pending |
| Contract sign-off on any `contracts/` changes | A + B | see DECISIONS.md |

## Exact commands to rerun everything

```powershell
# 0. Activate venv and install deps
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1. Validate contracts
python contracts/validate_examples.py

# 2. Router smoke tests
pytest agent/llm/test_router.py -q

# 3. Mock graph end-to-end
python -m agent.graph --mock

# 4. Full mock run (writes out/report.html, out/requirements.json, out/timelines.json)
python -m agent.run dummy_fw.bin --spec README.md --mock

# 5. Offline replay (requires demo_cache/ populated from a live run first)
$env:LLM_OFFLINE="1"; python -m agent.run dummy_fw.bin --spec README.md --mock
```
