"""
agent/graph.py
LangGraph pipeline for the firmware testing agent.

Nodes (each operates on AgentState):
  spec_node      → read spec, extract requirements via LLM
  plan_node      → generate test plan (≤8 tests)
  timeline_node  → compile timelines from plan
  run_node       → execute simulations (or mock)
  explain_node   → produce FAIL hypotheses
  report_node    → render HTML report

Run with mock data (no LLM, no simulator):
  python -m agent.graph --mock [--firmware <path>] [--spec <path>]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from langgraph.graph import StateGraph, END
from pydantic import ValidationError

from agent.models import AgentState
from agent import steps


# ── node implementations ──────────────────────────────────────────────────────

def spec_node(state: AgentState) -> AgentState:
    """Extract requirements from spec text via LLM (or load from cache)."""
    from agent.steps.spec import extract_requirements
    try:
        reqs = extract_requirements(state.spec_text or "")
        return state.model_copy(update={"requirements": reqs})
    except Exception as exc:
        return state.model_copy(update={"error": f"spec_node: {exc}"})


def plan_node(state: AgentState) -> AgentState:
    """Generate test plan entries from requirements."""
    if state.error:
        return state
    from agent.steps.plan import generate_plan
    try:
        test_plan = generate_plan(state.requirements)
        return state.model_copy(update={"test_plan": test_plan})
    except Exception as exc:
        return state.model_copy(update={"error": f"plan_node: {exc}"})


def timeline_node(state: AgentState) -> AgentState:
    """Compile/lint timelines (stand-in lint if A's isn't ready)."""
    if state.error:
        return state
    from agent.steps.timelines import expand_plan_to_timelines
    try:
        timelines = expand_plan_to_timelines(state.test_plan, state.requirements)
        return state.model_copy(update={"timelines": timelines})
    except Exception as exc:
        return state.model_copy(update={"error": f"timeline_node: {exc}"})


def run_node(state: AgentState) -> AgentState:
    """Run simulations (mock if no real sim available) and produce verdicts."""
    if state.error:
        return state
    from agent.steps.runner import run_simulations
    try:
        traces, monitors, verdicts = run_simulations(state.timelines, state.firmware_path)
        return state.model_copy(update={
            "traces": traces,
            "monitors": monitors,
            "verdicts": verdicts,
        })
    except Exception as exc:
        return state.model_copy(update={"error": f"run_node: {exc}"})


def explain_node(state: AgentState) -> AgentState:
    """Produce a hypothesis for each FAIL verdict."""
    if state.error:
        return state
    from agent.steps.explain import explain_failures
    try:
        explanations = explain_failures(state.verdicts, state.requirements, state.traces)
        return state.model_copy(update={"explanations": explanations})
    except Exception as exc:
        return state.model_copy(update={"error": f"explain_node: {exc}"})


def report_node(state: AgentState) -> AgentState:
    """Render the HTML report from the current state."""
    if state.error:
        return state
    from agent.steps.report import render_report
    try:
        html = render_report(state)
        return state.model_copy(update={"report_html": html})
    except Exception as exc:
        return state.model_copy(update={"error": f"report_node: {exc}"})


# ── graph assembly ────────────────────────────────────────────────────────────

def build_graph():
    """Build and compile the LangGraph state machine."""
    sg = StateGraph(AgentState)

    sg.add_node("spec", spec_node)
    sg.add_node("plan", plan_node)
    sg.add_node("timeline", timeline_node)
    sg.add_node("run", run_node)
    sg.add_node("explain", explain_node)
    sg.add_node("report", report_node)

    sg.set_entry_point("spec")
    sg.add_edge("spec", "plan")
    sg.add_edge("plan", "timeline")
    sg.add_edge("timeline", "run")
    sg.add_edge("run", "explain")
    sg.add_edge("explain", "report")
    sg.add_edge("report", END)

    return sg.compile()


# ── CLI ───────────────────────────────────────────────────────────────────────

def _write_report(html: str, out_dir: Path = Path("out")) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "report.html"
    report_path.write_text(html, encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser(description="Run firmware testing agent pipeline")
    parser.add_argument("--mock", action="store_true", help="Use mock data (no LLM/sim)")
    parser.add_argument("--firmware", default="dummy_fw.bin", help="Path to firmware file")
    parser.add_argument("--spec", default="README.md", help="Path to spec/README")
    args = parser.parse_args()

    if args.mock:
        from agent.fake_agent import build_mock_state
        from agent.steps.report import render_report

        print("[mock] Building pipeline with mock data...")
        state = build_mock_state(firmware_path=args.firmware)
        # Skip LLM-dependent nodes; render directly from mock state
        html = render_report(state)
        state = state.model_copy(update={"report_html": html})
    else:
        spec_text = Path(args.spec).read_text(encoding="utf-8") if Path(args.spec).exists() else ""
        initial = AgentState(firmware_path=args.firmware, spec_text=spec_text)
        graph = build_graph()
        state = graph.invoke(initial)

    report_path = _write_report(state.report_html)
    print(f"[done] Report written to {report_path}")

    if state.error:
        print(f"[error] Pipeline error: {state.error}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
