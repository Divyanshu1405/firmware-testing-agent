"""
agent/steps/report.py
Render the HTML report from AgentState using Jinja2.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

if TYPE_CHECKING:
    from agent.models import AgentState

_TEMPLATE_DIR = Path(__file__).parent.parent.parent / "report"
_TEMPLATE_NAME = "template.html"


def render_report(state: "AgentState", demo_failure: bool = False) -> str:
    """Render report.html from state and return the HTML string."""
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR), encoding="utf-8"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template(_TEMPLATE_NAME)

    # Read provenance log if it exists
    prov_entries = _read_provenance()

    # 1. Backend Banner
    if state.traces:
        backend_name = "SIMULATED BACKEND" if any(t.sim == "mock" for t in state.traces) else "REAL SIMULATOR"
    else:
        backend_name = "NO BACKEND RUN"

    # 2. Tests Table
    test_rows = []
    verdict_by_test = {}
    for v in state.verdicts:
        verdict_by_test.setdefault(v.test_id, []).append(v)
        
    for plan in state.test_plan:
        tid = plan.get("test_id", "")
        vs = verdict_by_test.get(tid, [])
        if any(v.result.value == "FAIL" for v in vs):
            final_res = "FAIL"
        elif any(v.result.value == "INCONCLUSIVE" for v in vs):
            final_res = "INCONCLUSIVE"
        elif vs:
            final_res = "PASS"
        else:
            final_res = "DROPPED"
            
        test_rows.append({
            "test_id": tid,
            "requirement_ids": plan.get("requirement_ids", []),
            "reason": plan.get("reason", ""),
            "fault": plan.get("fault_type", ""),
            "verdict": final_res
        })
        
    # 3. Requirement coverage
    req_cov = {}
    for r in state.requirements:
        req_cov[r.id] = {"tests": [], "healed": [], "dropped": False}
        
    for plan in state.test_plan:
        tid = plan.get("test_id")
        for rid in plan.get("requirement_ids", []):
            if rid not in req_cov:
                req_cov[rid] = {"tests": [], "healed": [], "dropped": False}
            req_cov[rid]["tests"].append(tid)
            tl = next((t for t in state.timelines if t.test_id == tid), None)
            if not tl:
                req_cov[rid]["dropped"] = True
            elif getattr(tl, "healed", False):
                req_cov[rid]["healed"].append(tid)
                
    # 4. Failures & Plots
    failures_data = []
    processed_fails = set()
    fail_verdicts = [v for v in state.verdicts if v.result.value in ("FAIL", "INCONCLUSIVE")]
    for v in fail_verdicts:
        tid = v.test_id
        if tid in processed_fails: continue
        processed_fails.add(tid)
        
        trace = next((t for t in state.traces if t.test_id == tid), None)
        plot_b64 = ""
        if trace:
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                import io
                import base64
                
                plt.figure(figsize=(8, 2))
                channels = {}
                for s in trace.samples:
                    ch = f"{s.dir.value}:{s.channel}"
                    channels.setdefault(ch, {"x": [], "y": []})
                    val = s.value
                    try: val = float(val)
                    except: val = 1.0 if str(val).lower() in ("true", "1", "high", "ready") else 0.0
                    channels[ch]["x"].append(s.t_ms)
                    channels[ch]["y"].append(val)
                    
                for ch, data in channels.items():
                    plt.step(data["x"], data["y"], where="post", label=ch)
                
                plt.xlabel("Time (ms)", color="#94a3b8")
                plt.ylabel("Value", color="#94a3b8")
                # format for dark mode
                ax = plt.gca()
                ax.set_facecolor('#0f1117')
                ax.tick_params(colors='#94a3b8')
                for spine in ax.spines.values(): spine.set_color('#334155')
                plt.legend(facecolor='#1e293b', edgecolor='#334155', labelcolor='#e2e8f0')
                
                buf = io.BytesIO()
                plt.savefig(buf, format="png", facecolor="#0f1117", edgecolor="none", bbox_inches="tight")
                plt.close()
                plot_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
            except Exception as e:
                plot_b64 = ""
                
        req = next((r for r in state.requirements if r.id == v.requirement_id), None)
        code_lines = f"{req.source}:{req.source_line}" if req else "Unknown code"
                
        failures_data.append({
            "test_id": tid,
            "evidence": v.evidence.detail,
            "time_ms": v.evidence.t_ms,
            "explanation": state.explanations.get(tid, "No explanation generated."),
            "code_lines": code_lines,
            "plot_b64": plot_b64
        })

    html = template.render(
        firmware_path=state.firmware_path,
        backend_name=backend_name,
        demo_failure=demo_failure,
        test_rows=test_rows,
        req_cov=req_cov,
        failures_data=failures_data,
        has_fails=len(failures_data) > 0,
        prov_entries=prov_entries,
    )
    return html


def _read_provenance() -> list[dict]:
    prov_path = Path("llm_provenance.jsonl")
    if not prov_path.exists():
        return []
    entries = []
    for line in prov_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries
