"""Validate timelines against the simulator IO map and frozen action contract."""

from __future__ import annotations

from typing import Any


ALLOWED_ACTIONS = {
    "set",
    "ramp",
    "step",
    "dropout",
    "stuck",
    "spike",
    "glitch",
    "drift",
    "uart_write",
    "uart_garbage",
}


def lint_timeline(timeline: dict[str, Any], io_map: dict[str, Any]) -> list[str]:
    """Return validation errors; an empty list means the timeline is valid."""
    errors: list[str] = []
    duration_ms = timeline.get("duration_ms")
    if not isinstance(duration_ms, int) or duration_ms < 0:
        errors.append("duration_ms must be a non-negative integer")
        duration_ms = 0

    channels = set(io_map.get("inputs", {})) | set(io_map.get("outputs", {}))
    previous_at_ms = -1
    for index, event in enumerate(timeline.get("events", [])):
        action = event.get("action")
        channel = event.get("channel")
        at_ms = event.get("at_ms")
        prefix = f"events[{index}]"
        if action not in ALLOWED_ACTIONS:
            errors.append(f"{prefix}: unsupported action '{action}'")
        if not isinstance(channel, str) or channel not in channels:
            errors.append(f"{prefix}: unknown channel '{channel}'")
        if not isinstance(at_ms, int) or at_ms < 0:
            errors.append(f"{prefix}: at_ms must be a non-negative integer")
        elif at_ms < previous_at_ms:
            errors.append(f"{prefix}: events must be ordered by at_ms")
        elif at_ms > duration_ms:
            errors.append(f"{prefix}: at_ms exceeds duration_ms")
        else:
            previous_at_ms = at_ms
    return errors


def validate_timeline(timeline: dict[str, Any], io_map: dict[str, Any]) -> None:
    """Raise ValueError when a timeline is not executable against the IO map."""
    errors = lint_timeline(timeline, io_map)
    if errors:
        raise ValueError("timeline lint failed: " + "; ".join(errors))
