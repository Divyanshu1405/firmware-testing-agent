"""
agent/fake_agent.py
Returns canned mock data for every pipeline stage.
Used by `python -m agent.graph --mock` to verify the full graph runs
end-to-end without a real LLM or simulator.
"""

from agent.models import (
    AgentState,
    Requirement,
    Timeline, TimelineEvent, TimelineAction,
    Trace, TraceSample, SampleDir, TraceEvent, TraceEventKind, EndReason,
    Monitor, MonitorKind, MonitorCondition, MonitorOp, OracleSource,
    Verdict, VerdictResult, VerdictEvidence,
)


def mock_requirements() -> list[Requirement]:
    return [
        Requirement(
            id="R1",
            description="Fan must activate within 1000 ms when temperature exceeds 30°C for ≥2 s.",
            source="README.md",
            source_line=22,
            threshold=30.0,
            time_value_ms=1000,
            ambiguous=False,
        ),
        Requirement(
            id="R2",
            description="UART must echo 'READY' within 500 ms of power-on.",
            source="README.md",
            source_line=26,
            threshold=None,
            time_value_ms=500,
            ambiguous=False,
        ),
    ]


def mock_timelines() -> list[Timeline]:
    return [
        Timeline(
            test_id="T01",
            requirement_ids=["R1"],
            duration_ms=12000,
            events=[
                TimelineEvent(at_ms=0, action=TimelineAction.set, channel="temp_c", value=25.0),
                TimelineEvent(at_ms=2000, action=TimelineAction.ramp, channel="temp_c", to=33.0, over_ms=4000),
                TimelineEvent(at_ms=8000, action=TimelineAction.dropout, channel="temp_c", for_ms=4000),
            ],
        ),
        Timeline(
            test_id="T02",
            requirement_ids=["R2"],
            duration_ms=2000,
            events=[
                TimelineEvent(at_ms=0, action=TimelineAction.set, channel="power", value=1),
            ],
        ),
    ]


def mock_traces() -> list[Trace]:
    return [
        Trace(
            test_id="T01",
            firmware="dummy_fw.bin",
            sim="mock",
            seed=0,
            samples=[
                TraceSample(t_ms=0, dir=SampleDir.in_, channel="temp_c", value=25.0),
                TraceSample(t_ms=6000, dir=SampleDir.out, channel="gpio.PA5", value=1),
            ],
            events=[],
            end_reason=EndReason.duration_reached,
        ),
        Trace(
            test_id="T02",
            firmware="dummy_fw.bin",
            sim="mock",
            seed=0,
            samples=[
                TraceSample(t_ms=100, dir=SampleDir.out, channel="uart", value="READY"),
            ],
            events=[],
            end_reason=EndReason.duration_reached,
        ),
    ]


def mock_monitors() -> list[Monitor]:
    return [
        Monitor(
            monitor_id="M1",
            requirement_id="R1",
            kind=MonitorKind.within,
            when=MonitorCondition(channel="temp_c", op=MonitorOp.gt, value=30, hold_ms=2000),
            then=MonitorCondition(channel="gpio.PA5", op=MonitorOp.eq, value=1),
            within_ms=1000,
            oracle_source=OracleSource.spec,
        ),
        Monitor(
            monitor_id="M2",
            requirement_id="R2",
            kind=MonitorKind.within,
            when=MonitorCondition(channel="power", op=MonitorOp.eq, value=1),
            then=MonitorCondition(channel="uart", op=MonitorOp.eq, value="READY"),
            within_ms=500,
            oracle_source=OracleSource.spec,
        ),
    ]


def mock_verdicts() -> list[Verdict]:
    return [
        Verdict(
            test_id="T01",
            monitor_id="M1",
            requirement_id="R1",
            result=VerdictResult.PASS,
            evidence=VerdictEvidence(t_ms=6000, detail="gpio.PA5 went HIGH at 6000 ms, within 1000 ms of threshold."),
            oracle_source=OracleSource.spec,
        ),
        Verdict(
            test_id="T02",
            monitor_id="M2",
            requirement_id="R2",
            result=VerdictResult.PASS,
            evidence=VerdictEvidence(t_ms=100, detail="UART echoed READY at 100 ms, within 500 ms."),
            oracle_source=OracleSource.spec,
        ),
    ]


def mock_explanations() -> dict[str, str]:
    """Return explanations only for FAIL verdicts — empty here since all mock verdicts PASS."""
    return {}


def build_mock_state(firmware_path: str = "dummy_fw.bin") -> AgentState:
    """Build a fully-populated AgentState from mock data."""
    return AgentState(
        firmware_path=firmware_path,
        spec_text="(mock spec text)",
        requirements=mock_requirements(),
        timelines=mock_timelines(),
        traces=mock_traces(),
        monitors=mock_monitors(),
        verdicts=mock_verdicts(),
        explanations=mock_explanations(),
    )
