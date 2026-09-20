"""
agent/models.py
Pydantic v2 models mirroring the frozen contract schemas exactly.
Field names and types match contracts/*.schema.json — do not rename them.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


# ── Requirement (Person C's own artifact) ────────────────────────────────────
class Requirement(BaseModel):
    id: str
    description: str
    source: str
    source_line: int = Field(ge=1)
    threshold: Optional[float] = None
    time_value_ms: Optional[int] = None
    ambiguous: bool = False


# ── Timeline ─────────────────────────────────────────────────────────────────
class TimelineAction(str, Enum):
    set = "set"
    ramp = "ramp"
    step = "step"
    dropout = "dropout"
    stuck = "stuck"
    spike = "spike"
    glitch = "glitch"
    drift = "drift"
    uart_write = "uart_write"
    uart_garbage = "uart_garbage"


class TimelineEvent(BaseModel):
    at_ms: int = Field(ge=0)
    action: TimelineAction
    channel: str
    value: Any = None
    to: Optional[float] = None
    over_ms: Optional[int] = None
    for_ms: Optional[int] = None

    model_config = {"extra": "allow"}


class Timeline(BaseModel):
    test_id: str
    requirement_ids: List[str] = Field(min_length=1)
    duration_ms: int = Field(ge=0)
    events: List[TimelineEvent]


# ── Trace ─────────────────────────────────────────────────────────────────────
class SampleDir(str, Enum):
    in_ = "in"
    out = "out"


class TraceSample(BaseModel):
    t_ms: int = Field(ge=0)
    dir: SampleDir
    channel: str
    value: Any


class TraceEventKind(str, Enum):
    hardfault = "hardfault"
    reset = "reset"
    hang = "hang"
    invalid_memory_access = "invalid_memory_access"


class TraceEvent(BaseModel):
    t_ms: int = Field(ge=0)
    kind: TraceEventKind


class EndReason(str, Enum):
    duration_reached = "duration_reached"
    timeout = "timeout"
    crash = "crash"
    sim_error = "sim_error"


class Trace(BaseModel):
    test_id: str
    firmware: str
    sim: str
    seed: int
    samples: List[TraceSample]
    events: List[TraceEvent]
    end_reason: EndReason


# ── Monitor ───────────────────────────────────────────────────────────────────
class MonitorKind(str, Enum):
    always = "always"
    never = "never"
    within = "within"
    eventually = "eventually"


class MonitorOp(str, Enum):
    lt = "<"
    lte = "<="
    eq = "=="
    ne = "!="
    gte = ">="
    gt = ">"


class MonitorCondition(BaseModel):
    channel: str
    op: MonitorOp
    value: Any
    hold_ms: Optional[int] = None

    model_config = {"extra": "allow"}


class OracleSource(str, Enum):
    spec = "spec"
    inferred = "inferred"
    generic = "generic"


class Monitor(BaseModel):
    monitor_id: str
    requirement_id: str
    kind: MonitorKind
    when: MonitorCondition
    then: Optional[MonitorCondition] = None
    within_ms: Optional[int] = None
    oracle_source: OracleSource


# ── Verdict ───────────────────────────────────────────────────────────────────
class VerdictResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class VerdictEvidence(BaseModel):
    t_ms: int = Field(ge=0)
    detail: str

    model_config = {"extra": "allow"}


class Verdict(BaseModel):
    test_id: str
    monitor_id: str
    requirement_id: str
    result: VerdictResult
    evidence: VerdictEvidence
    oracle_source: OracleSource


# ── IO Map ────────────────────────────────────────────────────────────────────
class IOPin(BaseModel):
    kind: str
    peripheral: Optional[str] = None
    channel: Optional[int] = None
    scale: Optional[float] = None
    pin: Optional[str] = None

    model_config = {"extra": "allow"}


class IOMap(BaseModel):
    firmware: str
    platform: str
    uart: str
    inputs: dict[str, IOPin]
    outputs: dict[str, IOPin]
    notes: List[str]


# ── Agent pipeline state ──────────────────────────────────────────────────────
class AgentState(BaseModel):
    """Shared state object threaded through every LangGraph node."""
    firmware_path: str = ""
    spec_text: str = ""
    requirements: List[Requirement] = []
    timelines: List[Timeline] = []
    traces: List[Trace] = []
    monitors: List[Monitor] = []
    verdicts: List[Verdict] = []
    explanations: dict[str, str] = {}  # test_id → explanation text
    report_html: str = ""
    error: Optional[str] = None
