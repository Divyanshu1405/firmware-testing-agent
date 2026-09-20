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
    parser.add_argument("--mock", action="store_true", help="Use mock sim (no real hardware)")
    parser.add_argument("--out", default="out", help="Output directory for report")
    args = parser.parse_args()

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
        state = graph.invoke(initial)

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

    # Write timelines JSON
    if state.timelines:
        tl_path = out_dir / "timelines.json"
        with open(tl_path, "w", encoding="utf-8") as f:
            json.dump([t.model_dump() for t in state.timelines], f, indent=2)
        print(f"[run] timelines → {tl_path}")

    if state.error:
        print(f"[run] ERROR: {state.error}", file=sys.stderr)
        sys.exit(1)

    fails = [v for v in state.verdicts if v.result.value in ("FAIL", "INCONCLUSIVE")]
    print(f"[run] {len(state.verdicts)} verdicts, {len(fails)} FAIL/INCONCLUSIVE")
    sys.exit(0)


def _is_offline() -> bool:
    import os
    return os.getenv("LLM_OFFLINE", "0") == "1"


if __name__ == "__main__":
    main()
