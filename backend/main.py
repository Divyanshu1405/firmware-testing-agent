"""FastAPI Backend for Autonomous Embedded Firmware Testing Agent.

Endpoints:
  - GET /health: Health check and simulator availability
  - GET /api/firmware: List available firmware binaries
  - GET /api/spec: Return default operational rules
  - POST /api/upload: Upload firmware binary (validated ELF, max 20MB)
  - POST /api/run: Execute autonomous testing pipeline with isolated run IDs
  - GET /api/report: View latest generated HTML report
  - GET /api/report/download: Download standalone HTML report
  - GET /api/runs/{run_id}/report: View specific run report
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

UPLOAD_DIR = REPO_ROOT / "firmware" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR = REPO_ROOT / "out"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RUNS_DIR = OUT_DIR / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE = 20 * 1024 * 1024  # 20 MB

app = FastAPI(
    title="Firmware Testing Agent Backend",
    description="REST API connecting the React frontend to LangGraph and Renode simulation.",
    version="2.0.0",
)

# Enable CORS with explicit origins (compatible with allow_credentials=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ───────────────────────────────────────────────────────────
class RunRequest(BaseModel):
    firmware: str = "original.elf"
    spec_text: Optional[str] = None
    mode: str = "offline"  # "offline" or "live"


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_available_firmware() -> List[Dict[str, Any]]:
    items = []

    # Original firmware at repo root
    orig_elf = REPO_ROOT / "original.elf"
    if orig_elf.exists():
        items.append({
            "name": "original.elf",
            "path": "original.elf",
            "category": "Baseline Firmware",
            "size_bytes": orig_elf.stat().st_size,
        })

    # Built-in baseline firmwares
    inputs_dir = REPO_ROOT / "firmware" / "inputs"
    if inputs_dir.exists():
        for p in inputs_dir.glob("*.elf"):
            items.append({
                "name": p.name,
                "path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                "category": "Baseline Firmware",
                "size_bytes": p.stat().st_size,
            })

    # Mutation benchmark firmwares
    mutants_dir = REPO_ROOT / "calib" / "mutants"
    if mutants_dir.exists():
        for p in sorted(mutants_dir.glob("*.elf")):
            items.append({
                "name": p.name,
                "path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                "category": "Calibration Mutant",
                "size_bytes": p.stat().st_size,
            })

    # Uploaded binaries
    if UPLOAD_DIR.exists():
        for p in UPLOAD_DIR.glob("*"):
            if p.is_file() and not p.name.startswith("."):
                items.append({
                    "name": p.name,
                    "path": str(p.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "category": "User Upload",
                    "size_bytes": p.stat().st_size,
                })

    # Mock synthetic option
    items.append({
        "name": "dummy_fw.bin",
        "path": "dummy_fw.bin",
        "category": "Mock Target",
        "size_bytes": 0,
    })
    return items


def get_default_spec() -> str:
    spec_path = REPO_ROOT / "tests" / "fixtures" / "sample_spec.md"
    if spec_path.exists():
        return spec_path.read_text(encoding="utf-8")
    return (
        "1. The firmware shall periodically transmit telemetry frames over USART2 every 2000 ms.\n"
        "2. Under normal operation, the UART transmission shall contain 'Humidity: %d Temperature: %d'.\n"
        "3. When the Si7021 sensor returns an error (0xFFFF), the firmware shall transmit 'Error'.\n"
        "4. Reported relative humidity shall remain within physical bounds between 0% and 100% RH.\n"
        "5. Reported temperature shall remain within physical limits of -40 deg C to +125 deg C.\n"
        "6. The firmware shall execute continuously without triggering HardFault or reset loops.\n"
        "# Firmware Functional Specification\n\n"
        "1. The system SHALL periodically transmit telemetry frames over USART2 every 2000 ms.\n"
        "2. Under normal operation, the UART transmission SHALL contain 'Humidity: %d Temperature: %d'.\n"
        "3. When the Si7021 sensor returns an error (0xFFFF), the firmware SHALL transmit 'Error'.\n"
        "4. Reported relative humidity SHALL remain within physical bounds between 0% and 100% RH.\n"
        "5. Reported temperature SHALL remain within physical limits of -40 deg C to +125 deg C.\n"
        "6. The firmware SHALL execute continuously without triggering HardFault or reset loops.\n"
    )


# ── API Endpoints ────────────────────────────────────────────────────────────
@app.get("/health")
def health() -> dict:
    from sim.backend import find_renode
    has_renode = find_renode() is not None
    return {
        "status": "healthy",
        "service": "firmware-testing-agent",
        "renode_available": has_renode,
        "repo_root": str(REPO_ROOT),
    }


@app.get("/api/firmware")
def list_firmware() -> List[Dict[str, Any]]:
    """List baseline and uploaded firmware binaries."""
    return get_available_firmware()


@app.get("/api/spec")
def get_spec() -> Dict[str, str]:
    """Get the default specification for firmware behavior."""
    return {"spec_text": get_default_spec()}


@app.post("/api/upload")
async def upload_firmware(file: UploadFile = File(...)) -> dict:
    """Upload a new firmware binary (.elf) with security and format validation."""
    raw_filename = file.filename or "uploaded_firmware.elf"
    clean_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", Path(raw_filename).name)

    content = await file.read()

    # Enforce maximum upload size limit
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Uploaded file exceeds maximum allowed size of {MAX_UPLOAD_SIZE // (1024 * 1024)}MB.",
        )

    # Validate ELF magic header (\x7fELF)
    if not content.startswith(b"\x7fELF"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid firmware binary format for '{clean_name}'. File must be a valid ELF binary starting with '\\x7fELF'.",
        )

    dest = UPLOAD_DIR / clean_name
    dest.write_bytes(content)

    return {
        "filename": clean_name,
        "path": str(dest.relative_to(REPO_ROOT)).replace("\\", "/"),
        "size_bytes": len(content),
    }


@app.post("/api/run")
def run_test_pipeline(req: RunRequest) -> Dict[str, Any]:
    """Execute the autonomous firmware testing pipeline with isolated run IDs:
      Triage -> Profile -> Spec Extraction -> Test Planning -> Timeline Compilation -> Renode Simulation -> Verdicts -> Report.
    """
    firmware_path = req.firmware
    spec_text = req.spec_text or get_default_spec()
    mode = req.mode.lower().strip()
    run_id = str(uuid.uuid4())

    # Create run-isolated directory
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # Scoped execution: preserve previous LLM_OFFLINE state
    import agent.llm.router as _r
    prev_offline = _r.LLM_OFFLINE
    prev_env = os.environ.get("LLM_OFFLINE")

    try:
        if mode == "offline":
            os.environ["LLM_OFFLINE"] = "1"
            _r.LLM_OFFLINE = True
        else:
            os.environ["LLM_OFFLINE"] = "0"
            _r.LLM_OFFLINE = False

        from agent.models import AgentState
        from agent.graph import build_graph, _write_report

        initial = AgentState(firmware_path=firmware_path, spec_text=spec_text)
        graph = build_graph()
        state_dict = graph.invoke(initial)
        state = AgentState.model_validate(state_dict)

    finally:
        # Restore scoped offline environment
        _r.LLM_OFFLINE = prev_offline
        if prev_env is not None:
            os.environ["LLM_OFFLINE"] = prev_env
        elif "LLM_OFFLINE" in os.environ:
            del os.environ["LLM_OFFLINE"]

    if state.error:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {state.error}")

    # Write HTML report to isolated run directory and update latest out/report.html
    _write_report(state.report_html, run_dir)
    _write_report(state.report_html, OUT_DIR)

    # Persist JSON artifacts in isolated run directory
    if state.requirements:
        (run_dir / "requirements.json").write_text(
            json.dumps([r.model_dump() for r in state.requirements], indent=2), encoding="utf-8"
        )
    if state.test_plan:
        (run_dir / "test_plan.json").write_text(json.dumps(state.test_plan, indent=2), encoding="utf-8")
    if state.timelines:
        (run_dir / "timelines.json").write_text(
            json.dumps([t.model_dump(exclude_none=True) for t in state.timelines], indent=2), encoding="utf-8"
        )

    passed_cnt = sum(1 for v in state.verdicts if v.result.value == "PASS")
    failed_cnt = sum(1 for v in state.verdicts if v.result.value == "FAIL")
    inconclusive_cnt = sum(1 for v in state.verdicts if v.result.value == "INCONCLUSIVE")
    total_cnt = len(state.verdicts)

    # Honest compliance calculation: 0 verdicts gives 0.0%, not false 100.0%
    verdict_rate = round(passed_cnt / total_cnt * 100, 1) if total_cnt > 0 else 0.0

    return {
        "status": "completed",
        "run_id": run_id,
        "mode": mode,
        "summary": {
            "total_verdicts": total_cnt,
            "passed": passed_cnt,
            "failed": failed_cnt,
            "inconclusive": inconclusive_cnt,
            "verdict_rate": verdict_rate,
        },
        "firmware_profile": state.firmware_profile,
        "io_map": state.io_map,
        "requirements": [r.model_dump(mode="json") for r in state.requirements],
        "test_plan": state.test_plan,
        "timelines": [t.model_dump(mode="json") for t in state.timelines],
        "traces": [t.model_dump(mode="json") for t in state.traces],
        "verdicts": [v.model_dump(mode="json") for v in state.verdicts],
        "explanations": state.explanations,
        "report_html": state.report_html,
    }


@app.get("/api/report")
def view_latest_report():
    """View the latest generated HTML report directly."""
    report_path = OUT_DIR / "report.html"
    if report_path.exists():
        return HTMLResponse(content=report_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h3>No report has been generated yet. Run a test pipeline first.</h3>")


@app.get("/api/runs/{run_id}/report")
def view_run_report(run_id: str):
    """View the HTML report for a specific isolated run."""
    clean_id = re.sub(r"[^a-zA-Z0-9_-]", "", run_id)
    report_path = RUNS_DIR / clean_id / "report.html"
    if report_path.exists():
        return HTMLResponse(content=report_path.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail=f"No report found for run ID '{clean_id}'.")


@app.get("/api/report/download")
def download_report_file():
    """Download the generated standalone HTML report."""
    report_path = OUT_DIR / "report.html"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="No report generated yet. Run a test pipeline first.")
    return FileResponse(
        path=str(report_path),
        filename="firmware_testing_report.html",
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=firmware_testing_report.html"},
    )
