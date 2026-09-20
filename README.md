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
