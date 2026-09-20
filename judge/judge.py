"""Deterministic Judge Core for Firmware Testing.

Interprets monitors (always, never, within, eventually) against execution
traces and produces evidence-backed PASS / FAIL / INCONCLUSIVE verdicts.
The LLM never participates in verdict decisions.
"""

from typing import Any, Dict, List, Optional, Tuple


def _safe_float(val: Any) -> Optional[float]:
    """Convert value to float if possible, else return None."""
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def matches_condition(sample_val: Any, cond: Dict[str, Any]) -> bool:
    """Deterministically check if a sample value satisfies a condition dict."""
    if "op" not in cond and "value" not in cond:
        return True

    op = cond.get("op", "==").strip()
    target_val = cond.get("value")

    # Numeric comparison when both values can be cast to float
    s_float = _safe_float(sample_val)
    t_float = _safe_float(target_val)

    if s_float is not None and t_float is not None:
        if op in ("==", "eq"):
            return abs(s_float - t_float) < 1e-6
        elif op in ("!=", "ne"):
            return abs(s_float - t_float) >= 1e-6
        elif op in (">", "gt"):
            return s_float > t_float
        elif op in (">=", "gte", "ge"):
            return s_float >= t_float
        elif op in ("<", "lt"):
            return s_float < t_float
        elif op in ("<=", "lte", "le"):
            return s_float <= t_float

    # String / generic comparisons
    s_str = str(sample_val) if sample_val is not None else ""
    t_str = str(target_val) if target_val is not None else ""

    if op in ("==", "eq"):
        return sample_val == target_val or s_str == t_str
    elif op in ("!=", "ne"):
        return sample_val != target_val and s_str != t_str
    elif op == "contains":
        return t_str in s_str
    elif op == "startswith":
        return s_str.startswith(t_str)
    elif op == "endswith":
        return s_str.endswith(t_str)
    elif op == "in":
        if isinstance(target_val, (list, tuple, set)):
            return sample_val in target_val
        return s_str in t_str

    # Default fallback equality
    return sample_val == target_val


def _get_channel_samples(samples: List[Dict[str, Any]], channel: Optional[str]) -> List[Dict[str, Any]]:
    """Extract samples matching the target channel, sorted by timestamp."""
    if not channel:
        return sorted(samples, key=lambda s: s.get("t_ms", 0))
    matching = [s for s in samples if s.get("channel") == channel]
    return sorted(matching, key=lambda s: s.get("t_ms", 0))


def _find_hold_activations(
    samples: List[Dict[str, Any]],
    cond: Dict[str, Any],
    max_time_ms: Optional[int] = None,
) -> List[Tuple[int, int]]:
    """Find all time intervals [t_trigger, t_end] where condition held for at least hold_ms.

    Returns list of (t_trigger, t_start) tuples where:
      - t_trigger is the timestamp at which hold_ms was reached
      - t_start is when the condition first became continuously true
    """
    hold_ms = int(cond.get("hold_ms", 0) or 0)
    ch_samples = _get_channel_samples(samples, cond.get("channel"))
    if not ch_samples:
        return []

    activations: List[Tuple[int, int]] = []
    in_true_state = False
    start_t = 0
    triggered = False

    for i, s in enumerate(ch_samples):
        t = int(s.get("t_ms", 0))
        val = s.get("value")
        is_match = matches_condition(val, cond)

        if is_match:
            if not in_true_state:
                in_true_state = True
                start_t = t
                triggered = False

            if not triggered:
                # If hold_ms is 0, triggers immediately
                if hold_ms <= 0:
                    activations.append((t, start_t))
                    triggered = True
                # Check if hold duration reached by current sample timestamp
                elif (t - start_t) >= hold_ms:
                    activations.append((start_t + hold_ms, start_t))
                    triggered = True
                # Check if between current sample and next sample (or trace end), hold_ms is reached
                else:
                    next_t = ch_samples[i + 1].get("t_ms") if i + 1 < len(ch_samples) else max_time_ms
                    if next_t is not None and (next_t - start_t) >= hold_ms:
                        activations.append((start_t + hold_ms, start_t))
                        triggered = True
        else:
            in_true_state = False
            triggered = False

    return activations


def _evaluate_always(trace: Dict[str, Any], monitor: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate an 'always' monitor."""
    test_id = trace.get("test_id", "UNKNOWN")
    monitor_id = monitor.get("monitor_id", "UNKNOWN")
    requirement_id = monitor.get("requirement_id", "UNKNOWN")
    oracle_source = monitor.get("oracle_source", "spec")
    samples = trace.get("samples", [])

    cond = monitor.get("then") or monitor.get("condition")
    when = monitor.get("when")

    # If no condition is provided at all, return INCONCLUSIVE
    if not cond and not when:
        return {
            "test_id": test_id,
            "monitor_id": monitor_id,
            "requirement_id": requirement_id,
            "result": "INCONCLUSIVE",
            "evidence": {"detail": "No condition specified for always monitor"},
            "oracle_source": oracle_source,
        }

    # Case: simple always invariant (no 'when' precondition)
    if cond and not when:
        channel = cond.get("channel")
        ch_samples = _get_channel_samples(samples, channel)

        if not ch_samples:
            return {
                "test_id": test_id,
                "monitor_id": monitor_id,
                "requirement_id": requirement_id,
                "result": "INCONCLUSIVE",
                "evidence": {"detail": f"No samples observed on channel '{channel}' for always monitor"},
                "oracle_source": oracle_source,
            }

        for s in ch_samples:
            val = s.get("value")
            t_ms = s.get("t_ms", 0)
            if not matches_condition(val, cond):
                return {
                    "test_id": test_id,
                    "monitor_id": monitor_id,
                    "requirement_id": requirement_id,
                    "result": "FAIL",
                    "evidence": {
                        "t_ms": t_ms,
                        "channel": channel,
                        "observed": val,
                        "expected": f"{cond.get('op', '==')} {cond.get('value')}",
                        "detail": f"Invariant violated on channel '{channel}': observed {val!r}, expected {cond.get('op', '==')} {cond.get('value')} at {t_ms} ms",
                    },
                    "oracle_source": oracle_source,
                }

        return {
            "test_id": test_id,
            "monitor_id": monitor_id,
            "requirement_id": requirement_id,
            "result": "PASS",
            "evidence": {
                "sample_count": len(ch_samples),
                "detail": f"Invariant held continuously across all {len(ch_samples)} samples on channel '{channel}'",
            },
            "oracle_source": oracle_source,
        }

    # Case: conditional invariant (when -> then)
    return _evaluate_within(trace, monitor, is_immediate=True)


def _evaluate_never(trace: Dict[str, Any], monitor: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a 'never' monitor."""
    test_id = trace.get("test_id", "UNKNOWN")
    monitor_id = monitor.get("monitor_id", "UNKNOWN")
    requirement_id = monitor.get("requirement_id", "UNKNOWN")
    oracle_source = monitor.get("oracle_source", "spec")
    samples = trace.get("samples", [])

    cond = monitor.get("then") or monitor.get("condition") or monitor.get("when")
    if not cond:
        return {
            "test_id": test_id,
            "monitor_id": monitor_id,
            "requirement_id": requirement_id,
            "result": "INCONCLUSIVE",
            "evidence": {"detail": "No condition specified for never monitor"},
            "oracle_source": oracle_source,
        }

    channel = cond.get("channel")
    ch_samples = _get_channel_samples(samples, channel)

    if not ch_samples:
        return {
            "test_id": test_id,
            "monitor_id": monitor_id,
            "requirement_id": requirement_id,
            "result": "PASS",
            "evidence": {
                "sample_count": 0,
                "detail": f"Forbidden condition never occurred (no samples on channel '{channel}')",
            },
            "oracle_source": oracle_source,
        }

    for s in ch_samples:
        val = s.get("value")
        t_ms = s.get("t_ms", 0)
        if matches_condition(val, cond):
            return {
                "test_id": test_id,
                "monitor_id": monitor_id,
                "requirement_id": requirement_id,
                "result": "FAIL",
                "evidence": {
                    "t_ms": t_ms,
                    "channel": channel,
                    "observed": val,
                    "detail": f"Forbidden condition occurred on channel '{channel}': observed {val!r} at {t_ms} ms",
                },
                "oracle_source": oracle_source,
            }

    return {
        "test_id": test_id,
        "monitor_id": monitor_id,
        "requirement_id": requirement_id,
        "result": "PASS",
        "evidence": {
            "sample_count": len(ch_samples),
            "detail": f"Forbidden condition never occurred across {len(ch_samples)} samples on channel '{channel}'",
        },
        "oracle_source": oracle_source,
    }


def _evaluate_eventually(trace: Dict[str, Any], monitor: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate an 'eventually' monitor."""
    test_id = trace.get("test_id", "UNKNOWN")
    monitor_id = monitor.get("monitor_id", "UNKNOWN")
    requirement_id = monitor.get("requirement_id", "UNKNOWN")
    oracle_source = monitor.get("oracle_source", "spec")
    samples = trace.get("samples", [])

    cond = monitor.get("then") or monitor.get("condition")
    if not cond:
        return {
            "test_id": test_id,
            "monitor_id": monitor_id,
            "requirement_id": requirement_id,
            "result": "INCONCLUSIVE",
            "evidence": {"detail": "No condition specified for eventually monitor"},
            "oracle_source": oracle_source,
        }

    channel = cond.get("channel")
    within_ms = monitor.get("within_ms")
    hold_ms = int(cond.get("hold_ms", 0) or 0)

    if hold_ms > 0:
        activations = _find_hold_activations(samples, cond)
        if activations:
            t_first, _ = activations[0]
            if within_ms is not None and t_first > within_ms:
                return {
                    "test_id": test_id,
                    "monitor_id": monitor_id,
                    "requirement_id": requirement_id,
                    "result": "FAIL",
                    "evidence": {
                        "t_ms": t_first,
                        "deadline_ms": within_ms,
                        "detail": f"Condition satisfied at {t_first} ms, but exceeded deadline {within_ms} ms",
                    },
                    "oracle_source": oracle_source,
                }
            return {
                "test_id": test_id,
                "monitor_id": monitor_id,
                "requirement_id": requirement_id,
                "result": "PASS",
                "evidence": {
                    "t_ms": t_first,
                    "detail": f"Condition held for {hold_ms} ms and satisfied at {t_first} ms",
                },
                "oracle_source": oracle_source,
            }
    else:
        ch_samples = _get_channel_samples(samples, channel)
        for s in ch_samples:
            val = s.get("value")
            t_ms = s.get("t_ms", 0)
            if matches_condition(val, cond):
                if within_ms is not None and t_ms > within_ms:
                    return {
                        "test_id": test_id,
                        "monitor_id": monitor_id,
                        "requirement_id": requirement_id,
                        "result": "FAIL",
                        "evidence": {
                            "t_ms": t_ms,
                            "deadline_ms": within_ms,
                            "detail": f"Condition satisfied at {t_ms} ms, but exceeded deadline {within_ms} ms",
                        },
                        "oracle_source": oracle_source,
                    }
                return {
                    "test_id": test_id,
                    "monitor_id": monitor_id,
                    "requirement_id": requirement_id,
                    "result": "PASS",
                    "evidence": {
                        "t_ms": t_ms,
                        "observed": val,
                        "detail": f"Condition eventually satisfied on '{channel}' at {t_ms} ms",
                    },
                    "oracle_source": oracle_source,
                }

    return {
        "test_id": test_id,
        "monitor_id": monitor_id,
        "requirement_id": requirement_id,
        "result": "FAIL",
        "evidence": {
            "channel": channel,
            "expected": f"{cond.get('op', '==')} {cond.get('value')}",
            "detail": f"Condition {cond.get('op', '==')} {cond.get('value')} was never satisfied before end of trace",
        },
        "oracle_source": oracle_source,
    }


def _evaluate_within(trace: Dict[str, Any], monitor: Dict[str, Any], is_immediate: bool = False) -> Dict[str, Any]:
    """Evaluate a 'within' monitor (when [hold_ms] -> then within within_ms)."""
    test_id = trace.get("test_id", "UNKNOWN")
    monitor_id = monitor.get("monitor_id", "UNKNOWN")
    requirement_id = monitor.get("requirement_id", "UNKNOWN")
    oracle_source = monitor.get("oracle_source", "spec")
    samples = trace.get("samples", [])

    when = monitor.get("when")
    then = monitor.get("then") or monitor.get("condition")
    within_ms = 0 if is_immediate else monitor.get("within_ms", 0)

    if not when or not then:
        return {
            "test_id": test_id,
            "monitor_id": monitor_id,
            "requirement_id": requirement_id,
            "result": "INCONCLUSIVE",
            "evidence": {"detail": "Both 'when' and 'then' conditions required for within monitor"},
            "oracle_source": oracle_source,
        }

    # Find total trace max time
    all_times = [s.get("t_ms", 0) for s in samples]
    max_trace_t = max(all_times) if all_times else trace.get("duration_ms", 0)

    activations = _find_hold_activations(samples, when, max_time_ms=max_trace_t)
    if not activations:
        return {
            "test_id": test_id,
            "monitor_id": monitor_id,
            "requirement_id": requirement_id,
            "result": "INCONCLUSIVE",
            "evidence": {"detail": f"Precondition 'when' on channel '{when.get('channel')}' was never triggered in trace"},
            "oracle_source": oracle_source,
        }

    then_samples = _get_channel_samples(samples, then.get("channel"))

    # For each activation of 'when', verify 'then' is satisfied within window
    for trigger_t, start_t in activations:
        deadline_t = trigger_t + within_ms
        satisfied = False
        satisfied_t = None
        satisfied_val = None

        # Look for matching then sample in window [trigger_t, deadline_t]
        for s in then_samples:
            s_t = s.get("t_ms", 0)
            if trigger_t <= s_t <= deadline_t:
                if matches_condition(s.get("value"), then):
                    satisfied = True
                    satisfied_t = s_t
                    satisfied_val = s.get("value")
                    break

        if not satisfied:
            # Check latest observed value on then channel at or before deadline
            observed_val = None
            observed_t = None
            for s in then_samples:
                if s.get("t_ms", 0) <= deadline_t:
                    observed_val = s.get("value")
                    observed_t = s.get("t_ms", 0)

            return {
                "test_id": test_id,
                "monitor_id": monitor_id,
                "requirement_id": requirement_id,
                "result": "FAIL",
                "evidence": {
                    "trigger_t_ms": trigger_t,
                    "deadline_ms": deadline_t,
                    "t_ms": observed_t if observed_t is not None else deadline_t,
                    "observed": observed_val,
                    "expected": f"{then.get('op', '==')} {then.get('value')}",
                    "detail": (
                        f"Channel '{then.get('channel')}' failed to satisfy {then.get('op', '==')} "
                        f"{then.get('value')} by {deadline_t} ms (triggered at {trigger_t} ms; "
                        f"observed {observed_val!r})"
                    ),
                },
                "oracle_source": oracle_source,
            }

    # All activations satisfied
    return {
        "test_id": test_id,
        "monitor_id": monitor_id,
        "requirement_id": requirement_id,
        "result": "PASS",
        "evidence": {
            "activations_checked": len(activations),
            "first_trigger_t_ms": activations[0][0],
            "detail": f"Precondition triggered {len(activations)} time(s); condition on '{then.get('channel')}' satisfied within {within_ms} ms for all",
        },
        "oracle_source": oracle_source,
    }


def evaluate(trace: Dict[str, Any], monitors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Evaluate a list of monitors against an execution trace deterministically.

    Args:
        trace: Dictionary containing test_id, samples, events, end_reason.
        monitors: List of monitor specifications.

    Returns:
        List of Verdict dictionaries with test_id, monitor_id, requirement_id,
        result (PASS / FAIL / INCONCLUSIVE), evidence, oracle_source.
    """
    verdicts = []

    for monitor in monitors:
        kind = monitor.get("kind", "always")

        if kind == "always":
            verdict = _evaluate_always(trace, monitor)
        elif kind == "never":
            verdict = _evaluate_never(trace, monitor)
        elif kind == "eventually":
            verdict = _evaluate_eventually(trace, monitor)
        elif kind == "within":
            verdict = _evaluate_within(trace, monitor)
        else:
            verdict = {
                "test_id": trace.get("test_id", "UNKNOWN"),
                "monitor_id": monitor.get("monitor_id", "UNKNOWN"),
                "requirement_id": monitor.get("requirement_id", "UNKNOWN"),
                "result": "INCONCLUSIVE",
                "evidence": {"detail": f"Unsupported monitor kind '{kind}'"},
                "oracle_source": monitor.get("oracle_source", "spec"),
            }

        verdicts.append(verdict)

    return verdicts