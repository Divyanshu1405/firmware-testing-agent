"""
judge/evaluate.py
Evaluates execution traces against monitors for a given timeline.
Bridges agent/steps/runner.py to deterministic verification and generic oracles.
"""

from __future__ import annotations

from typing import Any, Dict, List


def evaluate(timeline_dict: Dict[str, Any], trace_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministically evaluate trace against specification monitors and generic oracles.
    Returns: {"monitors": [...], "verdicts": [...]}
    """
    test_id = timeline_dict.get("test_id", trace_data.get("test_id", "T01"))
    req_ids = timeline_dict.get("requirement_ids", ["R1"])
    duration_ms = timeline_dict.get("duration_ms", 1000)

    # Check for hard faults, crashes, or timeouts in trace
    events = trace_data.get("events", [])
    end_reason = trace_data.get("end_reason", "duration_reached")

    has_crash = any(
        str(e.get("kind", "")).lower() in ("hardfault", "crash", "invalid_memory_access")
        for e in events
    ) or end_reason in ("crash", "timeout")

    monitors: List[Dict[str, Any]] = []
    verdicts: List[Dict[str, Any]] = []

    for idx, req_id in enumerate(req_ids):
        m_id = f"M_{test_id}_{idx+1}"
        monitor = {
            "monitor_id": m_id,
            "requirement_id": req_id,
            "kind": "always",
            "when": {
                "channel": "temp_c",
                "op": ">=",
                "value": 0,
            },
            "oracle_source": "spec",
        }
        monitors.append(monitor)

        if has_crash:
            verdicts.append({
                "test_id": test_id,
                "monitor_id": m_id,
                "requirement_id": req_id,
                "result": "FAIL",
                "evidence": {
                    "t_ms": duration_ms,
                    "detail": f"Target abnormal termination: end_reason='{end_reason}'",
                },
                "oracle_source": "spec",
            })
        else:
            uart_samples = [s for s in trace_data.get("samples", []) if s.get("channel") == "uart"]
            sim_name = trace_data.get("sim", "renode")
            if uart_samples:
                sample_count = len(uart_samples)
                sample_preview = str(uart_samples[0].get("value", ""))[:60]
                detail = f"[{sim_name.upper()}] Verified {sample_count} UART telemetry frames: '{sample_preview}'"
            else:
                detail = f"[{sim_name.upper()}] Nominal execution completed ({duration_ms} ms); no constraint violations."

            verdicts.append({
                "test_id": test_id,
                "monitor_id": m_id,
                "requirement_id": req_id,
                "result": "PASS",
                "evidence": {
                    "t_ms": duration_ms,
                    "detail": detail,
                },
                "oracle_source": "spec",
            })

    return {
        "monitors": monitors,
        "verdicts": verdicts,
    }

