"""
FastAPI Backend for Autonomous Embedded Firmware Testing Agent.

Endpoints:
  - GET /health: Health check and simulator availability
  - GET /api/firmware: List available firmware binaries
  - GET /api/spec: Return default operational rules
  - POST /api/upload: Upload firmware binary (.elf or .bin)
  - POST /api/run: Execute autonomous testing pipeline
  - GET /api/report: View generated HTML report
  - GET /api/report/download: Download standalone HTML report
"""

from __future__ import annotations

import json
import os
import shutil
import sys
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

app = FastAPI(
    title="Firmware Testing Agent Backend",
    description="REST API connecting the React frontend to LangGraph and Renode simulation.",
    version="2.0.0",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Models ───────────────────────────────────────────────────────────
class RunRequest(BaseModel):
    firmware: str = "firmware/inputs/firmware1.elf"
    spec_text: Optional[str] = None
    mode: str = "offline"  # "offline" or "live"


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_available_firmware() -> List[Dict[str, Any]]:
    items = []
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
        "1. The main cooling fan MUST activate within 1000 ms when core temperature exceeds 30.0°C.\n"
        "2. If the temperature stays above 45.0°C for >= 5000 ms, the system MUST initiate an emergency shutdown.\n"
        "3. When the temperature drops below 25.0°C, the fan MUST deactivate within 500 ms to conserve power.\n"
        "4. The system SHALL log a warning if sensor disconnects or communications fail.\n"
    )


# ── API Endpoints ────────────────────────────────────────────────────────────
@app.get("/health")
def health() -> dict:
    has_renode = shutil.which("renode") is not None or Path(r"C:\Program Files\Renode\renode.exe").exists()
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
    """Upload a new firmware binary (.elf or .bin) for testing."""
    clean_name = Path(file.filename or "uploaded_firmware.elf").name
    dest = UPLOAD_DIR / clean_name
    content = await file.read()
    dest.write_bytes(content)
    return {
        "filename": clean_name,
        "path": str(dest.relative_to(REPO_ROOT)).replace("\\", "/"),
        "size_bytes": len(content),
    }


@app.post("/api/run")
def run_test_pipeline(req: RunRequest) -> Dict[str, Any]:
    """
    Execute the autonomous firmware testing pipeline:
      Spec Extraction → Test Planning → Timeline Compilation → Simulation → Verdicts → Report.
    """
    firmware_path = req.firmware
    spec_text = req.spec_text or get_default_spec()
    mode = req.mode.lower().strip()

    if mode == "offline":
        os.environ["LLM_OFFLINE"] = "1"
        import agent.llm.router as _r
        _r.LLM_OFFLINE = True
    else:
        os.environ["LLM_OFFLINE"] = "0"
        import agent.llm.router as _r
        _r.LLM_OFFLINE = False

    from agent.models import AgentState
    from agent.graph import build_graph, _write_report

    initial = AgentState(firmware_path=firmware_path, spec_text=spec_text)
    graph = build_graph()
    state_dict = graph.invoke(initial)
    state = AgentState.model_validate(state_dict)

    # Write HTML report to out/
    _write_report(state.report_html, OUT_DIR)

    # Persist JSON artifacts
    if state.requirements:
        (OUT_DIR / "requirements.json").write_text(
            json.dumps([r.model_dump() for r in state.requirements], indent=2), encoding="utf-8"
        )
    if state.test_plan:
        (OUT_DIR / "test_plan.json").write_text(json.dumps(state.test_plan, indent=2), encoding="utf-8")
    if state.timelines:
        (OUT_DIR / "timelines.json").write_text(
            json.dumps([t.model_dump(exclude_none=True) for t in state.timelines], indent=2), encoding="utf-8"
        )

    passed_cnt = sum(1 for v in state.verdicts if v.result.value == "PASS")
    failed_cnt = sum(1 for v in state.verdicts if v.result.value == "FAIL")
    inconclusive_cnt = sum(1 for v in state.verdicts if v.result.value == "INCONCLUSIVE")
    total_cnt = len(state.verdicts)

    return {
        "status": "completed",
        "mode": mode,
        "summary": {
            "total_verdicts": total_cnt,
            "passed": passed_cnt,
            "failed": failed_cnt,
            "inconclusive": inconclusive_cnt,
            "verdict_rate": round(passed_cnt / max(1, total_cnt) * 100, 1) if total_cnt else 100.0,
        },
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
