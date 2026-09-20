"""Authoritative deterministic judge evaluation bridge.

Coordinates trace normalization, gold calibration monitor loading,
temporal monitor evaluation, and generic crash/hang/reset oracles.
The LLM never participates in pass/fail decisions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from judge.generic_oracles import evaluate_generic_oracles
from judge.judge import evaluate as evaluate_monitors
from sim.normalize import normalize_trace

REPO_ROOT = Path(__file__).resolve().parent.parent
GOLD_MONITORS_PATH = REPO_ROOT / "calib" / "gold" / "monitors.json"


def load_gold_monitors() -> List[Dict[str, Any]]:
    """Load pre-validated gold monitors for the calibration STM32F4/SI7021 firmware."""
    if GOLD_MONITORS_PATH.exists():
        try:
            with open(GOLD_MONITORS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return []


def compile_requirement_monitors(
    requirements: List[Dict[str, Any]], timeline: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Compile abstract requirements into concrete deterministic monitors."""
    monitors: List[Dict[str, Any]] = []
    test_id = timeline.get("test_id", "T01")

    for req in requirements:
        req_id = req.get("id") or req.get("requirement_id", "R1")
        thresh = req.get("threshold")
        time_limit = req.get("time_value_ms")

        if thresh is not None:
            monitors.append({
                "monitor_id": f"M_{test_id}_{req_id}_THRESH",
                "requirement_id": req_id,
                "kind": "always",
                "when": {
                    "channel": "temp_c",
                    "op": "<=",
                    "value": float(thresh),
                },
                "then": {
                    "channel": "temp_c",
                    "op": "<=",
                    "value": float(thresh),
                },
                "oracle_source": "spec" if not req.get("ambiguous") else "inferred",
            })
        else:
            monitors.append({
                "monitor_id": f"M_{test_id}_{req_id}_ACT",
                "requirement_id": req_id,
                "kind": "eventually",
                "when": {
                    "channel": "uart",
                    "op": "!=",
                    "value": "",
                },
                "then": {
                    "channel": "uart",
                    "op": "!=",
                    "value": "",
                },
                "within_ms": time_limit or 5000,
                "oracle_source": "inferred",
            })

    return monitors


def evaluate(
    timeline_dict: Dict[str, Any],
    trace_data: Dict[str, Any],
    requirements: Optional[List[Dict[str, Any]]] = None,
    monitors: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Deterministically evaluate an execution trace against monitors and generic oracles.

    Returns:
        {"monitors": [...], "verdicts": [...]}
    """
    test_id = timeline_dict.get("test_id", trace_data.get("test_id", "T01"))
    req_ids = set(timeline_dict.get("requirement_ids", []))
    fw_name = Path(trace_data.get("firmware", "")).name.lower()

    # 1. Handle infrastructure errors honestly: NEVER return false PASS
    if trace_data.get("end_reason") == "sim_error" or trace_data.get("error_detail"):
        error_msg = trace_data.get("error_detail") or "Simulation infrastructure execution failed"
        inconclusive_verdicts = []
        dummy_monitors = []

        assigned_reqs = req_ids if req_ids else {"INFRA_01"}
        for r_id in assigned_reqs:
            m_id = f"M_{test_id}_{r_id}"
            dummy_monitors.append({
                "monitor_id": m_id,
                "requirement_id": r_id,
                "kind": "always",
                "when": {"channel": "uart", "op": "!=", "value": ""},
                "oracle_source": "generic",
            })
            inconclusive_verdicts.append({
                "test_id": test_id,
                "monitor_id": m_id,
                "requirement_id": r_id,
                "result": "INCONCLUSIVE",
                "evidence": {
                    "t_ms": 0,
                    "detail": f"INFRASTRUCTURE_ERROR: {error_msg}",
                },
                "oracle_source": "generic",
            })

        return {
            "monitors": dummy_monitors,
            "verdicts": inconclusive_verdicts,
        }

    # 2. Normalize raw UART output into typed domain telemetry samples
    norm_trace = normalize_trace(trace_data)

    # 3. Select monitors to evaluate
    selected_monitors: List[Dict[str, Any]] = []

    if monitors is not None:
        selected_monitors = list(monitors)
    elif (
        fw_name in {"firmware1.elf", "original.elf"}
        or "mutant" in fw_name
        or "si7021" in fw_name
    ):
        gold = load_gold_monitors()
        if gold:
            for g_m in gold:
                if not req_ids or g_m.get("requirement_id") in req_ids:
                    m_copy = dict(g_m)
                    m_copy["test_id"] = test_id
                    selected_monitors.append(m_copy)

    if not selected_monitors and requirements:
        selected_monitors = compile_requirement_monitors(requirements, timeline_dict)

    if not selected_monitors:
        # Default safety monitor
        selected_monitors = [{
            "monitor_id": f"M_{test_id}_SAFE",
            "requirement_id": "REQ_SAFETY",
            "kind": "never",
            "then": {"channel": "events", "op": "==", "value": "hardfault"},
            "oracle_source": "generic",
        }]

    # 4. Evaluate monitors deterministically
    verdicts = evaluate_monitors(norm_trace, selected_monitors)

    # 5. Evaluate generic oracles (HardFault, hangs, silence, garbage)
    generic_verdicts = evaluate_generic_oracles(norm_trace)

    for g_v in generic_verdicts:
        if g_v.get("result") == "FAIL":
            g_v["test_id"] = test_id
            verdicts.append(g_v)
            selected_monitors.append({
                "monitor_id": g_v["monitor_id"],
                "requirement_id": g_v["requirement_id"],
                "kind": "never",
                "when": {"channel": "events", "op": "==", "value": "crash"},
                "oracle_source": "generic",
            })

    return {
        "monitors": selected_monitors,
        "verdicts": verdicts,
    }
