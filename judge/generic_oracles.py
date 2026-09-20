"""Generic Oracles for Deterministic Firmware Testing.

Detects firmware crashes, HardFaults, reset loops, hangs, UART silence,
garbled UART output, and invalid memory accesses directly from execution traces.
Independent of LLM and specification requirements.
"""

import string
from typing import Any, Dict, List, Optional


def check_hardfault(trace: Dict[str, Any]) -> Dict[str, Any]:
    """Check for HardFault, crash events, or crash end-reason."""
    test_id = trace.get("test_id", "UNKNOWN")
    events = trace.get("events", [])
    end_reason = trace.get("end_reason", "")

    # Check for hardfault or crash in events
    for event in events:
        kind = str(event.get("kind", "")).lower()
        if kind in ("hardfault", "hard_fault", "crash"):
            t_ms = event.get("t_ms", 0)
            return {
                "test_id": test_id,
                "monitor_id": "GENERIC_HARDFAULT",
                "requirement_id": "GENERIC_CRASH",
                "result": "FAIL",
                "evidence": {
                    "t_ms": t_ms,
                    "kind": event.get("kind"),
                    "detail": f"HardFault/crash event '{event.get('kind')}' detected at {t_ms} ms",
                },
                "oracle_source": "generic",
            }

    # Check end_reason
    if end_reason.lower() in ("crash", "sim_error"):
        all_times = [s.get("t_ms", 0) for s in trace.get("samples", [])]
        t_ms = max(all_times) if all_times else 0
        return {
            "test_id": test_id,
            "monitor_id": "GENERIC_HARDFAULT",
            "requirement_id": "GENERIC_CRASH",
            "result": "FAIL",
            "evidence": {
                "t_ms": t_ms,
                "end_reason": end_reason,
                "detail": f"Simulation terminated abnormally with end_reason='{end_reason}'",
            },
            "oracle_source": "generic",
        }

    return {
        "test_id": test_id,
        "monitor_id": "GENERIC_HARDFAULT",
        "requirement_id": "GENERIC_CRASH",
        "result": "PASS",
        "evidence": {"detail": "No HardFault or crash detected"},
        "oracle_source": "generic",
    }


def check_reset_loop(trace: Dict[str, Any], threshold: int = 2) -> Dict[str, Any]:
    """Check for repeated reset/reboot events exceeding the given threshold."""
    test_id = trace.get("test_id", "UNKNOWN")
    events = trace.get("events", [])

    reset_events = [
        e for e in events if str(e.get("kind", "")).lower() in ("reset", "reboot", "restart")
    ]
    reset_count = len(reset_events)

    if reset_count >= threshold:
        timestamps = [e.get("t_ms", 0) for e in reset_events]
        return {
            "test_id": test_id,
            "monitor_id": "GENERIC_RESET_LOOP",
            "requirement_id": "GENERIC_RESET",
            "result": "FAIL",
            "evidence": {
                "reset_count": reset_count,
                "threshold": threshold,
                "timestamps": timestamps,
                "detail": f"Reset loop detected: {reset_count} resets observed (threshold {threshold}) at {timestamps} ms",
            },
            "oracle_source": "generic",
        }

    return {
        "test_id": test_id,
        "monitor_id": "GENERIC_RESET_LOOP",
        "requirement_id": "GENERIC_RESET",
        "result": "PASS",
        "evidence": {
            "reset_count": reset_count,
            "threshold": threshold,
            "detail": f"No reset loop detected ({reset_count} resets below threshold {threshold})",
        },
        "oracle_source": "generic",
    }


def check_hang(trace: Dict[str, Any], hang_threshold_ms: int = 5000) -> Dict[str, Any]:
    """Check for hang event, timeout end-reason, or protracted output inactivity."""
    test_id = trace.get("test_id", "UNKNOWN")
    events = trace.get("events", [])
    end_reason = trace.get("end_reason", "")
    samples = trace.get("samples", [])

    # Check hang in events
    for event in events:
        if str(event.get("kind", "")).lower() == "hang":
            t_ms = event.get("t_ms", 0)
            return {
                "test_id": test_id,
                "monitor_id": "GENERIC_HANG",
                "requirement_id": "GENERIC_HANG",
                "result": "FAIL",
                "evidence": {
                    "t_ms": t_ms,
                    "detail": f"Hang event recorded at {t_ms} ms",
                },
                "oracle_source": "generic",
            }

    # Check timeout end_reason
    if end_reason.lower() == "timeout":
        all_times = [s.get("t_ms", 0) for s in samples]
        t_ms = max(all_times) if all_times else 0
        return {
            "test_id": test_id,
            "monitor_id": "GENERIC_HANG",
            "requirement_id": "GENERIC_HANG",
            "result": "FAIL",
            "evidence": {
                "t_ms": t_ms,
                "end_reason": end_reason,
                "detail": f"Simulation timed out with end_reason='{end_reason}'",
            },
            "oracle_source": "generic",
        }

    # Check silence on output channels
    out_samples = [s for s in samples if s.get("dir") == "out"]
    out_samples_sorted = sorted(out_samples, key=lambda s: s.get("t_ms", 0))

    if out_samples_sorted:
        # Check gap between consecutive output samples
        for i in range(len(out_samples_sorted) - 1):
            gap = out_samples_sorted[i + 1].get("t_ms", 0) - out_samples_sorted[i].get("t_ms", 0)
            if gap >= hang_threshold_ms:
                return {
                    "test_id": test_id,
                    "monitor_id": "GENERIC_HANG",
                    "requirement_id": "GENERIC_HANG",
                    "result": "FAIL",
                    "evidence": {
                        "t_ms": out_samples_sorted[i].get("t_ms", 0),
                        "gap_ms": gap,
                        "hang_threshold_ms": hang_threshold_ms,
                        "detail": f"Output silence gap of {gap} ms between {out_samples_sorted[i].get('t_ms')} ms and {out_samples_sorted[i+1].get('t_ms')} ms (threshold {hang_threshold_ms} ms)",
                    },
                    "oracle_source": "generic",
                }

        # Check gap after last output sample to end of trace
        all_times = [s.get("t_ms", 0) for s in samples]
        max_t = max(all_times) if all_times else 0
        trailing_gap = max_t - out_samples_sorted[-1].get("t_ms", 0)
        if trailing_gap >= hang_threshold_ms:
            return {
                "test_id": test_id,
                "monitor_id": "GENERIC_HANG",
                "requirement_id": "GENERIC_HANG",
                "result": "FAIL",
                "evidence": {
                    "t_ms": out_samples_sorted[-1].get("t_ms", 0),
                    "gap_ms": trailing_gap,
                    "hang_threshold_ms": hang_threshold_ms,
                    "detail": f"Output activity ceased at {out_samples_sorted[-1].get('t_ms')} ms with no output for remaining {trailing_gap} ms",
                },
                "oracle_source": "generic",
            }
    else:
        # No output samples at all
        all_times = [s.get("t_ms", 0) for s in samples]
        duration = max(all_times) if all_times else int(trace.get("duration_ms", 0) or 0)
        if duration >= hang_threshold_ms:
            return {
                "test_id": test_id,
                "monitor_id": "GENERIC_HANG",
                "requirement_id": "GENERIC_HANG",
                "result": "FAIL",
                "evidence": {
                    "duration_ms": duration,
                    "hang_threshold_ms": hang_threshold_ms,
                    "detail": f"Zero output samples produced over {duration} ms duration (threshold {hang_threshold_ms} ms)",
                },
                "oracle_source": "generic",
            }

    return {
        "test_id": test_id,
        "monitor_id": "GENERIC_HANG",
        "requirement_id": "GENERIC_HANG",
        "result": "PASS",
        "evidence": {"detail": "No hang, timeout, or protracted output silence detected"},
        "oracle_source": "generic",
    }


def check_uart_silence(trace: Dict[str, Any], min_samples: int = 1) -> Dict[str, Any]:
    """Check for complete absence of UART output samples."""
    test_id = trace.get("test_id", "UNKNOWN")
    samples = trace.get("samples", [])

    uart_samples = [
        s for s in samples if str(s.get("channel", "")).lower().startswith("uart") and s.get("dir") == "out"
    ]
    # Fallback to any uart channel if dir not specified
    if not uart_samples:
        uart_samples = [s for s in samples if str(s.get("channel", "")).lower().startswith("uart")]

    if len(uart_samples) < min_samples:
        return {
            "test_id": test_id,
            "monitor_id": "GENERIC_UART_SILENCE",
            "requirement_id": "GENERIC_UART",
            "result": "FAIL",
            "evidence": {
                "uart_sample_count": len(uart_samples),
                "detail": f"UART silence detected: observed {len(uart_samples)} UART samples (expected at least {min_samples})",
            },
            "oracle_source": "generic",
        }

    return {
        "test_id": test_id,
        "monitor_id": "GENERIC_UART_SILENCE",
        "requirement_id": "GENERIC_UART",
        "result": "PASS",
        "evidence": {
            "uart_sample_count": len(uart_samples),
            "detail": f"UART active with {len(uart_samples)} sample(s)",
        },
        "oracle_source": "generic",
    }


def check_uart_garbage(trace: Dict[str, Any], garbage_threshold: float = 0.20) -> Dict[str, Any]:
    """Check for corrupted, framing-errored, or unprintable UART output."""
    test_id = trace.get("test_id", "UNKNOWN")
    events = trace.get("events", [])
    samples = trace.get("samples", [])

    # Check for hardware framing or parity errors in events
    for event in events:
        kind = str(event.get("kind", "")).lower()
        if kind in ("uart_framing_error", "uart_parity_error", "uart_garbage", "uart_noise_error"):
            t_ms = event.get("t_ms", 0)
            return {
                "test_id": test_id,
                "monitor_id": "GENERIC_UART_GARBAGE",
                "requirement_id": "GENERIC_UART",
                "result": "FAIL",
                "evidence": {
                    "t_ms": t_ms,
                    "kind": event.get("kind"),
                    "detail": f"UART communication fault event '{event.get('kind')}' detected at {t_ms} ms",
                },
                "oracle_source": "generic",
            }

    # Inspect UART samples
    uart_samples = [
        s for s in samples if str(s.get("channel", "")).lower().startswith("uart")
    ]

    printable_set = set(string.printable)

    for s in uart_samples:
        val = s.get("value")
        t_ms = s.get("t_ms", 0)

        # Convert bytes or string
        if isinstance(val, bytes):
            try:
                text = val.decode("utf-8")
            except UnicodeDecodeError:
                return {
                    "test_id": test_id,
                    "monitor_id": "GENERIC_UART_GARBAGE",
                    "requirement_id": "GENERIC_UART",
                    "result": "FAIL",
                    "evidence": {
                        "t_ms": t_ms,
                        "raw_bytes": repr(val)[:50],
                        "detail": f"Garbled UART bytes (Unicode decode error) at {t_ms} ms",
                    },
                    "oracle_source": "generic",
                }
        elif isinstance(val, str):
            text = val
        else:
            continue

        if not text:
            continue

        # Check for unprintable character ratio
        unprintable_count = sum(1 for ch in text if ch not in printable_set and ch != "\ufffd")
        has_replacement_char = "\ufffd" in text
        has_null_bytes = "\x00" in text

        ratio = unprintable_count / len(text)
        if ratio >= garbage_threshold or has_replacement_char or has_null_bytes:
            return {
                "test_id": test_id,
                "monitor_id": "GENERIC_UART_GARBAGE",
                "requirement_id": "GENERIC_UART",
                "result": "FAIL",
                "evidence": {
                    "t_ms": t_ms,
                    "sample": repr(text)[:60],
                    "unprintable_ratio": round(ratio, 3),
                    "detail": f"Garbled UART output detected at {t_ms} ms: observed {repr(text)[:60]}",
                },
                "oracle_source": "generic",
            }

    return {
        "test_id": test_id,
        "monitor_id": "GENERIC_UART_GARBAGE",
        "requirement_id": "GENERIC_UART",
        "result": "PASS",
        "evidence": {"detail": "UART output clean and printable"},
        "oracle_source": "generic",
    }


def check_invalid_memory_access(trace: Dict[str, Any]) -> Dict[str, Any]:
    """Check for invalid memory access, bus faults, or memory management violations."""
    test_id = trace.get("test_id", "UNKNOWN")
    events = trace.get("events", [])

    memory_fault_kinds = {
        "invalid_memory_access",
        "busfault",
        "bus_fault",
        "memmanage",
        "mem_fault",
        "segfault",
        "usagefault",
    }

    for event in events:
        kind = str(event.get("kind", "")).lower()
        if kind in memory_fault_kinds:
            t_ms = event.get("t_ms", 0)
            addr = event.get("address")
            addr_str = f" at address {hex(addr) if isinstance(addr, int) else addr}" if addr else ""
            return {
                "test_id": test_id,
                "monitor_id": "GENERIC_INVALID_MEM",
                "requirement_id": "GENERIC_MEM",
                "result": "FAIL",
                "evidence": {
                    "t_ms": t_ms,
                    "kind": event.get("kind"),
                    "address": addr,
                    "detail": f"Memory fault '{event.get('kind')}'{addr_str} recorded at {t_ms} ms",
                },
                "oracle_source": "generic",
            }

    return {
        "test_id": test_id,
        "monitor_id": "GENERIC_INVALID_MEM",
        "requirement_id": "GENERIC_MEM",
        "result": "PASS",
        "evidence": {"detail": "No invalid memory access or bus fault recorded"},
        "oracle_source": "generic",
    }


def evaluate_generic_oracles(
    trace: Dict[str, Any],
    oracles: Optional[List[str]] = None,
    hang_threshold_ms: int = 5000,
    reset_loop_threshold: int = 2,
    uart_garbage_threshold: float = 0.20,
) -> List[Dict[str, Any]]:
    """Evaluate all generic oracles against an execution trace deterministically.

    Args:
        trace: Execution trace dictionary.
        oracles: Optional list of oracle names to execute ('hardfault', 'reset_loop',
                 'hang', 'uart_silence', 'uart_garbage', 'invalid_memory_access').
        hang_threshold_ms: Millisecond inactivity threshold for hang detection.
        reset_loop_threshold: Count of resets triggering reset loop fault.
        uart_garbage_threshold: Unprintable character ratio triggering garbage fault.

    Returns:
        List of Verdict dictionaries with oracle_source='generic'.
    """
    all_checkers = {
        "hardfault": lambda: check_hardfault(trace),
        "reset_loop": lambda: check_reset_loop(trace, threshold=reset_loop_threshold),
        "hang": lambda: check_hang(trace, hang_threshold_ms=hang_threshold_ms),
        "uart_silence": lambda: check_uart_silence(trace),
        "uart_garbage": lambda: check_uart_garbage(trace, garbage_threshold=uart_garbage_threshold),
        "invalid_memory_access": lambda: check_invalid_memory_access(trace),
    }

    selected = oracles if oracles is not None else list(all_checkers.keys())
    verdicts = []

    for name in selected:
        if name in all_checkers:
            verdicts.append(all_checkers[name]())

    return verdicts
