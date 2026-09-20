"""
agent/run.py
Main entry point for a full firmware testing agent run.

Usage:
  python -m agent.run <firmware_path> --spec <spec_path>
  python -m agent.run dummy_fw.bin --spec README.md
  LLM_OFFLINE=1 python -m agent.run dummy_fw.bin --spec README.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Firmware testing agent — full pipeline run"
    )
    parser.add_argument("firmware", help="Path to firmware binary")
    parser.add_argument("--spec", default="README.md", help="Path to spec/README")
    parser.add_argument("--demo-failure", action="store_true", help="Create isolated dummy demo failure report")
    parser.add_argument("--mock", action="store_true", help="Use mock sim (no real hardware)")
    parser.add_argument("--out", default="out", help="Output directory for report")
    args = parser.parse_args()

    if args.demo_failure:
        from agent.models import AgentState, Trace, Verdict, VerdictResult, VerdictEvidence, OracleSource, Requirement
        from agent.steps.report import render_report
        
        trace_data = json.loads(Path("tests/fixtures/buggy_trace.json").read_text(encoding="utf-8"))
        traces = [Trace.model_validate(t) for t in trace_data]
        state = AgentState(
            firmware_path=args.firmware,
            spec_text="simulated requirements payload",
            requirements=[Requirement(id="R7", description="temp above threshold -> fan stays on", source="sample_spec.md", source_line=29)],
            test_plan=[{"test_id": "T_DEMO", "requirement_ids": ["R7"], "reason": "demo", "fault_type": "nominal"}],
            timelines=[],
            traces=traces,
            verdicts=[
                Verdict(
                    test_id="T_DEMO", monitor_id="M1", requirement_id="R7", result=VerdictResult.FAIL,
                    evidence=VerdictEvidence(t_ms=250, detail="Fan failed to turn on when temp hit 35."),
                    oracle_source=OracleSource.generic
                )
            ],
            explanations={"T_DEMO": "HYPOTHESIS: [example on simulated data] Thermal fan actuation was bypassed natively."}
        )
        html = render_report(state, demo_failure=True)
        out_report = Path(os.environ.get("OUT_DIR", args.out)) / "demo_fail_report.html"
        out_report.parent.mkdir(parents=True, exist_ok=True)
        out_report.write_text(html, encoding="utf-8")
        print(f"[run] demo failure report → {out_report}")
        sys.exit(0)

    spec_path = Path(args.spec)
    spec_text = spec_path.read_text(encoding="utf-8") if spec_path.exists() else ""
    out_dir = Path(args.out)

    print(f"[run] firmware={args.firmware}  spec={args.spec}")
    print(f"[run] LLM_OFFLINE={_is_offline()}")

    from agent.models import AgentState
    from agent.graph import build_graph, _write_report
    from agent.steps.report import render_report

    if args.mock:
        from agent.fake_agent import build_mock_state
        print("[run] using mock state")
        state = build_mock_state(firmware_path=args.firmware)
        html = render_report(state)
        state = state.model_copy(update={"report_html": html})
    else:
        initial = AgentState(firmware_path=args.firmware, spec_text=spec_text)
        graph = build_graph()
        state_dict = graph.invoke(initial)
        state = AgentState.model_validate(state_dict)

    report_path = _write_report(state.report_html, out_dir)
    print(f"[run] report → {report_path}")

    # Write requirements JSON for artifact tracking
    if state.requirements:
        reqs_path = out_dir / "requirements.json"
        with open(reqs_path, "w", encoding="utf-8") as f:
            json.dump(
                [r.model_dump() for r in state.requirements],
                f, indent=2
            )
        print(f"[run] requirements → {reqs_path}")

    # Write test plan JSON
    if state.test_plan:
        plan_path = out_dir / "test_plan.json"
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(state.test_plan, f, indent=2)
        print(f"[run] test_plan → {plan_path}")

    # Write timelines JSON
    if state.timelines:
        tl_path = out_dir / "timelines.json"
        with open(tl_path, "w", encoding="utf-8") as f:
            json.dump([t.model_dump(exclude_none=True) for t in state.timelines], f, indent=2)
        print(f"[run] timelines → {tl_path}")

    # Validate traces before exiting (H7 gate)
    if state.traces:
        trace_schema_path = Path("contracts/trace.schema.json")
        if trace_schema_path.exists():
            with open(trace_schema_path, "r", encoding="utf-8") as sf:
                trace_schema = json.load(sf)
            import jsonschema
            for t in state.traces:
                try:
                    jsonschema.validate(instance=t.model_dump(exclude_none=True), schema=trace_schema)
                except jsonschema.ValidationError as ve:
                    print(f"FATAL: Validating trace for test {t.test_id} against schema failed: {ve}", file=sys.stderr)
                    sys.exit(1)
            print("[run] traces successfully validated against trace.schema.json")
        else:
            print("FATAL: trace.schema.json not found.", file=sys.stderr)
            sys.exit(1)

    if state.error:
        print(f"[run] ERROR: {state.error}", file=sys.stderr)
        sys.exit(1)

    fails = [v for v in state.verdicts if v.result.value in ("FAIL", "INCONCLUSIVE")]
    print(f"[run] {len(state.verdicts)} verdicts, {len(fails)} FAIL/INCONCLUSIVE")
    if fails:
        sys.exit(1)
    sys.exit(0)

def _is_offline() -> bool:
    import os
    return os.getenv("LLM_OFFLINE", "0") == "1"

if __name__ == "__main__":
    main()
