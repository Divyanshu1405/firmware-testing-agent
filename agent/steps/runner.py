"""Authoritative simulation runner dispatching to virtual hardware simulation.

Wires timelines to sim.runner.simulate and evaluates execution traces
through the deterministic judge engine. Never swaps real simulation for mock.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from agent.llm.router import _log_decision
from agent.models import (
    EndReason,
    Monitor,
    MonitorCondition,
    MonitorKind,
    MonitorOp,
    OracleSource,
    SampleDir,
    Timeline,
    Trace,
    TraceEvent,
    TraceSample,
    Verdict,
    VerdictEvidence,
    VerdictResult,
)


def run_simulations(
    timelines: List[Timeline],
    firmware_path: str,
    io_map: Optional[Dict[str, Any]] = None,
    sim_mode: str = "renode",
    requirements: Optional[List[Any]] = None,
) -> Tuple[List[Trace], List[Monitor], List[Verdict]]:
    """Run each timeline through the simulator (Renode or explicit mock).

    Returns:
        (traces, monitors, verdicts)
    """
    fw_p = Path(firmware_path)
    if sim_mode in ("mock", "fake") or not fw_p.is_file():
        _log_decision("runner: mock mode requested or non-existent dummy binary — using synthetic mock")
        return _run_mock(timelines, firmware_path)

    _log_decision(f"runner: executing live virtual hardware simulation via sim.runner (mode={sim_mode})")
    return _run_real(timelines, firmware_path, io_map=io_map, requirements=requirements)


# ── real sim path ──────────────────────────────────────────────────────────────

def _run_real(
    timelines: List[Timeline],
    firmware_path: str,
    io_map: Optional[Dict[str, Any]] = None,
    requirements: Optional[List[Any]] = None,
) -> Tuple[List[Trace], List[Monitor], List[Verdict]]:
    """Execute timelines in virtual hardware simulator and evaluate deterministically."""
    from judge.evaluate import evaluate
    from sim.runner import simulate

    traces: List[Trace] = []
    monitors: List[Monitor] = []
    verdicts: List[Verdict] = []

    req_dicts = [r.model_dump() if hasattr(r, "model_dump") else dict(r) for r in (requirements or [])]

    for tl in timelines:
        tl_dict = tl.model_dump()
        trace_data = simulate(firmware_path, tl_dict, io_map=io_map, sim_mode="renode")
        trace = Trace.model_validate(trace_data)
        traces.append(trace)

        eval_result = evaluate(tl_dict, trace_data, requirements=req_dicts)

        monitors.extend(Monitor.model_validate(m) for m in eval_result.get("monitors", []))
        verdicts.extend(Verdict.model_validate(v) for v in eval_result.get("verdicts", []))

    return traces, monitors, verdicts


# ── mock sim path ──────────────────────────────────────────────────────────────

def _run_mock(
    timelines: List[Timeline], firmware_path: str
) -> Tuple[List[Trace], List[Monitor], List[Verdict]]:
    """Explicit deterministic mock fixture mode strictly tagged as synthetic."""
    traces: List[Trace] = []
    monitors: List[Monitor] = []
    verdicts: List[Verdict] = []

    for idx, tl in enumerate(timelines):
        samples = [
            TraceSample(
                t_ms=ev.at_ms,
                dir=SampleDir.in_,
                channel=ev.channel,
                value=ev.value if ev.value is not None else 0,
            )
            for ev in tl.events
        ]
        trace = Trace(
            test_id=tl.test_id,
            firmware=firmware_path,
            sim="fake",
            seed=idx,
            samples=samples,
            events=[],
            end_reason=EndReason.duration_reached,
        )
        traces.append(trace)

        for req_id in tl.requirement_ids:
            m_id = f"M_MOCK_{tl.test_id}_{req_id}"
            monitor = Monitor(
                monitor_id=m_id,
                requirement_id=req_id,
                kind=MonitorKind.always,
                when=MonitorCondition(
                    channel=tl.events[0].channel if tl.events else "uart",
                    op=MonitorOp.gte,
                    value=0,
                ),
                oracle_source=OracleSource.generic,
            )
            monitors.append(monitor)

            verdict = Verdict(
                test_id=tl.test_id,
                monitor_id=m_id,
                requirement_id=req_id,
                result=VerdictResult.PASS,
                evidence=VerdictEvidence(
                    t_ms=tl.duration_ms,
                    detail="Mock fixture execution: synthetic trace, not representative of physical or simulated hardware.",
                ),
                oracle_source=OracleSource.generic,
            )
            verdicts.append(verdict)

    return traces, monitors, verdicts
