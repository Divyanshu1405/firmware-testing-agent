# Firmware Testing Agent

Autonomous embedded firmware testing with Renode, deterministic traces, and a Python judge.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python run_demo.py --offline
```

The offline demo writes `out/demo_trace.json` and `out/report.html` without network access or API keys.

## Renode probe

Renode `1.17.0` is expected on `PATH`.

```powershell
python .\sim\probe_sensor.py
python .\sim\probe_sensor.py --injected
```

The injected probe uses the STM32F4 board, I2C1 at SI7021 address `0x40`, and USART2. The project-owned model produces a calibrated default of 25 C and 50 percent RH for this firmware.

## Project layout

- `sim/`: Renode backend, environment generation, linting, faults, matrix runner
- `profile/`: firmware IO map
- `contracts/`: timeline, trace, and verdict examples
- `report/`: failure plots
- `backend/`: API and agent modules

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
