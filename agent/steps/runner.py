"""
agent/steps/runner.py
Simulation runner — wires timelines to Person A's backend (sim/) when available.
Falls back to a deterministic mock sim that produces synthetic traces and verdicts.
The LLM never decides PASS/FAIL — that's always the deterministic judge.
"""

from __future__ import annotations

from typing import List, Tuple

from agent.models import (
    Timeline, Trace, Monitor, Verdict,
    TraceSample, SampleDir, TraceEvent, EndReason,
    MonitorKind, MonitorCondition, MonitorOp, OracleSource,
    VerdictResult, VerdictEvidence,
)
from agent.llm.router import _log_decision


def run_simulations(
    timelines: List[Timeline],
    firmware_path: str,
) -> Tuple[List[Trace], List[Monitor], List[Verdict]]:
    """
    Run each timeline through the simulator (real or mock).
    Returns (traces, monitors, verdicts).
    PASS/FAIL is determined by the deterministic judge, not the LLM.
    """
    # Try to use Person A's sim backend
    try:
        from sim.runner import simulate  # type: ignore
        _use_real_sim = True
    except ImportError:
        _use_real_sim = False

    if _use_real_sim:
        _log_decision("runner: using real sim.runner.simulate")
        return _run_real(timelines, firmware_path)
    else:
        _log_decision(
            "runner: sim.runner not available — using mock sim; "
            "results are synthetic, not reflective of real firmware"
        )
        return _run_mock(timelines, firmware_path)


# ── real sim path ──────────────────────────────────────────────────────────────
def _run_real(
    timelines: List[Timeline], firmware_path: str
) -> Tuple[List[Trace], List[Monitor], List[Verdict]]:
    from sim.runner import simulate  # type: ignore
    from judge.evaluate import evaluate  # type: ignore

    traces: List[Trace] = []
    monitors: List[Monitor] = []
    verdicts: List[Verdict] = []

    for tl in timelines:
        trace_data = simulate(firmware_path, tl.model_dump())
        trace = Trace.model_validate(trace_data)
        traces.append(trace)

        # Judge produces monitors + verdicts deterministically
        result = evaluate(tl.model_dump(), trace_data)
        monitors.extend(Monitor.model_validate(m) for m in result.get("monitors", []))
        verdicts.extend(Verdict.model_validate(v) for v in result.get("verdicts", []))

    return traces, monitors, verdicts


# ── mock sim path ──────────────────────────────────────────────────────────────
def _run_mock(
    timelines: List[Timeline], firmware_path: str
) -> Tuple[List[Trace], List[Monitor], List[Verdict]]:
    """
    Deterministic mock: all timelines PASS on nominal firmware.
    Produces synthetic traces and verdicts consistent with the frozen schemas.
    """
    traces: List[Trace] = []
    monitors: List[Monitor] = []
    verdicts: List[Verdict] = []

    for idx, tl in enumerate(timelines):
        # Synthetic trace
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
            sim="mock",
            seed=idx,
            samples=samples,
            events=[],
            end_reason=EndReason.duration_reached,
        )
        traces.append(trace)

        # Synthetic monitor + verdict (all PASS in mock)
        for req_id in tl.requirement_ids:
            m_id = f"M{idx+1}"
            monitor = Monitor(
                monitor_id=m_id,
                requirement_id=req_id,
                kind=MonitorKind.always,
                when=MonitorCondition(
                    channel=tl.events[0].channel if tl.events else "signal",
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
                    detail="Mock sim: all signals nominal, no constraint violated.",
                ),
                oracle_source=OracleSource.generic,
            )
            verdicts.append(verdict)

    return traces, monitors, verdicts
