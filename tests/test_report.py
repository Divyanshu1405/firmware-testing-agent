import json
import pytest
from pathlib import Path
from agent.models import AgentState, Trace, Verdict, VerdictResult, VerdictEvidence, OracleSource, Requirement
from agent.steps.report import render_report

def test_render_report_with_buggy_trace():
    trace_data = json.loads(Path("tests/fixtures/buggy_trace.json").read_text(encoding="utf-8"))
    traces = [Trace.model_validate(t) for t in trace_data]
    
    state = AgentState(
        firmware_path="dummy.bin",
        spec_text="dummy",
        requirements=[Requirement(id="R7", description="temp > threshold -> fan on", source="file", source_line=1)],
        test_plan=[{"test_id": "T_DEMO", "requirement_ids": ["R7"], "reason": "demo", "fault_type": "nominal"}],
        timelines=[],
        traces=traces,
        verdicts=[
            Verdict(
                test_id="T_DEMO",
                monitor_id="M1",
                requirement_id="R7",
                result=VerdictResult.FAIL,
                evidence=VerdictEvidence(t_ms=250, detail="Simulated failure: ch_FAN remained 0 over threshold target."),
                oracle_source=OracleSource.generic
            )
        ],
        explanations={"T_DEMO": "HYPOTHESIS: [example on simulated data] Thermal management routine skipped the activation block."}
    )
    
    html = render_report(state, demo_failure=True)
    
    # Assertions per user instruction
    assert "SIMULATED FAILURE" in html, "Report must visibly flag simulated failures flag"
    assert "FAIL" in html, "Report must reflect the synthetic failure"
    assert "HYPOTHESIS:" in html, "Report must correctly render the linked explanation"
    assert "example on simulated data" in html, "Explanation must contain string explicitly stating mock"
    assert "R7" in html, "Must display the R7 requirement block explicitly mapping the mock logic"
    assert "data:image/png;base64" in html, "Matplotlib plot string missing from HTML template"
