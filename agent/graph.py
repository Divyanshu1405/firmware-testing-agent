"""Authoritative LangGraph pipeline for the firmware testing agent.

Nodes (each operates on AgentState):
  triage_node    -> inspect ELF header, vector table, symbols, and strings
  profile_node   -> infer hardware platform, peripheral bindings, and I/O map
  spec_node      -> extract requirements from specification text
  plan_node      -> generate test plan paired with hardware capabilities
  timeline_node  -> compile executable timelines validated against I/O map
  run_node       -> execute virtual hardware simulation and evaluate deterministically
  explain_node   -> synthesize failure hypotheses
  report_node    -> render standalone verification HTML report
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from langgraph.graph import END, StateGraph

from agent.models import AgentState


# ── node implementations ──────────────────────────────────────────────────────

def triage_node(state: AgentState) -> AgentState:
    """Inspect ELF binary and extract static architecture, symbols, and strings."""
    from profile.static.triage import analyze_firmware, is_elf_file

    fw_path = Path(state.firmware_path) if state.firmware_path else None
    if fw_path and fw_path.is_file():
        if not is_elf_file(fw_path):
            return state.model_copy(
                update={"error": f"Invalid firmware format for '{fw_path.name}'. Only valid ELF binaries are supported."}
            )
        try:
            triage_data = analyze_firmware(fw_path)
            return state.model_copy(update={"firmware_profile": triage_data})
        except Exception as exc:
            return state.model_copy(update={"error": f"triage_node: {exc}"})
    else:
        # Dummy or placeholder firmware for offline/mock test execution
        triage_data = {
            "architecture": "ARM Cortex-M4",
            "entry_point": 0,
            "symbols": [],
            "strings": [],
            "peripherals": ["UART", "GPIO"],
        }
        return state.model_copy(update={"firmware_profile": triage_data})


def profile_node(state: AgentState) -> AgentState:
    """Infer hardware platform bindings, peripheral map, and provenance."""
    if state.error:
        return state
    from profile.infer import infer_profile

    try:
        fw_profile, io_map = infer_profile(state.firmware_profile, state.firmware_path)
        return state.model_copy(update={
            "firmware_profile": fw_profile,
            "io_map": io_map,
        })
    except Exception as exc:
        return state.model_copy(update={"error": f"profile_node: {exc}"})


def spec_node(state: AgentState) -> AgentState:
    """Extract requirements from spec text via LLM router."""
    if state.error:
        return state
    from agent.steps.spec import extract_requirements

    try:
        reqs = extract_requirements(state.spec_text or "")
        return state.model_copy(update={"requirements": reqs})
    except Exception as exc:
        return state.model_copy(update={"error": f"spec_node: {exc}"})


def plan_node(state: AgentState) -> AgentState:
    """Generate test plan covering requirements and hardware interfaces."""
    if state.error:
        return state
    from agent.steps.plan import generate_plan

    try:
        test_plan = generate_plan(state.requirements, io_map=state.io_map)
        return state.model_copy(update={"test_plan": test_plan})
    except Exception as exc:
        return state.model_copy(update={"error": f"plan_node: {exc}"})


def timeline_node(state: AgentState) -> AgentState:
    """Compile test plan scenarios into executable, linted timelines."""
    if state.error:
        return state
    from agent.steps.timelines import expand_plan_to_timelines

    try:
        timelines = expand_plan_to_timelines(
            state.test_plan, state.requirements, io_map=state.io_map
        )
        return state.model_copy(update={"timelines": timelines})
    except Exception as exc:
        return state.model_copy(update={"error": f"timeline_node: {exc}"})


def run_node(state: AgentState) -> AgentState:
    """Execute virtual hardware simulations and evaluate deterministically."""
    if state.error:
        return state
    from agent.steps.runner import run_simulations
    import inspect

    try:
        sig = inspect.signature(run_simulations)
        kwargs = {}
        if "io_map" in sig.parameters:
            kwargs["io_map"] = state.io_map
        if "requirements" in sig.parameters:
            kwargs["requirements"] = state.requirements

        traces, monitors, verdicts = run_simulations(
            state.timelines,
            state.firmware_path,
            **kwargs,
        )
        return state.model_copy(update={
            "traces": traces,
            "monitors": monitors,
            "verdicts": verdicts,
        })
    except Exception as exc:
        return state.model_copy(update={"error": f"run_node: {exc}"})


def explain_node(state: AgentState) -> AgentState:
    """Generate hypotheses for FAIL verdicts (never alters verdict truth)."""
    if state.error:
        return state
    from agent.steps.explain import explain_failures

    try:
        explanations = explain_failures(state.verdicts, state.requirements, state.traces)
        return state.model_copy(update={"explanations": explanations})
    except Exception as exc:
        return state.model_copy(update={"error": f"explain_node: {exc}"})


def report_node(state: AgentState) -> AgentState:
    """Render the comprehensive verification report."""
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
    """Build and compile the authoritative LangGraph state machine."""
    sg = StateGraph(AgentState)

    sg.add_node("triage", triage_node)
    sg.add_node("profile", profile_node)
    sg.add_node("spec", spec_node)
    sg.add_node("plan", plan_node)
    sg.add_node("timeline", timeline_node)
    sg.add_node("run", run_node)
    sg.add_node("explain", explain_node)
    sg.add_node("report", report_node)

    sg.set_entry_point("triage")
    sg.add_edge("triage", "profile")
    sg.add_edge("profile", "spec")
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the firmware testing agent graph.")
    parser.add_argument("--firmware", default="dummy_fw.bin", help="Path to firmware ELF")
    parser.add_argument("--spec", default="README.md", help="Path to specification file")
    parser.add_argument("--out", default="out", help="Output directory")
    args = parser.parse_args()

    spec_text = Path(args.spec).read_text(encoding="utf-8") if Path(args.spec).exists() else ""
    initial = AgentState(firmware_path=args.firmware, spec_text=spec_text)

    graph = build_graph()
    state_dict = graph.invoke(initial)
    final_state = AgentState.model_validate(state_dict)

    if final_state.report_html:
        out_file = _write_report(final_state.report_html, Path(args.out))
        print(f"Report written to {out_file}")
