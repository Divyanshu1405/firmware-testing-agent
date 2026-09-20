"""Validate timelines against the simulator IO map and frozen action contract."""

from __future__ import annotations

from typing import Any, Dict, List, Set


ALLOWED_ACTIONS = {
    "set",
    "ramp",
    "step",
    "dropout",
    "stuck",
    "spike",
    "glitch",
    "drift",
    "error_reading",
    "uart_write",
    "uart_garbage",
}

CHANNEL_ALIASES = {
    "temperature": "temp_c",
    "temp": "temp_c",
    "humidity": "humidity_pct",
    "humid": "humidity_pct",
    "usart": "uart",
    "usart2": "uart",
    "sensor": "temp_c",
}


def normalize_channel(channel: str, valid_channels: Set[str]) -> str:
    """Normalize common channel aliases to matching profile keys."""
    if channel in valid_channels:
        return channel
    alias = CHANNEL_ALIASES.get(channel.lower())
    if alias and alias in valid_channels:
        return alias
    return channel


def lint_timeline(timeline: Dict[str, Any], io_map: Dict[str, Any]) -> List[str]:
    """Return validation errors; an empty list means the timeline is valid."""
    errors: List[str] = []
    duration_ms = timeline.get("duration_ms")
    if not isinstance(duration_ms, int) or duration_ms < 0:
        errors.append("duration_ms must be a non-negative integer")
        duration_ms = 0

    valid_channels = set(io_map.get("inputs", {})) | set(io_map.get("outputs", {}))
    # Add generic channels if outputs exist
    if "uart" in valid_channels or "sysbus.usart2" in valid_channels:
        valid_channels.add("uart")

    previous_at_ms = -1
    for index, event in enumerate(timeline.get("events", [])):
        action = event.get("action")
        channel = event.get("channel")
        at_ms = event.get("at_ms")
        prefix = f"events[{index}]"

        if action not in ALLOWED_ACTIONS:
            errors.append(f"{prefix}: unsupported action '{action}'")

        if not isinstance(channel, str):
            errors.append(f"{prefix}: channel must be a string")
        else:
            norm_ch = normalize_channel(channel, valid_channels)
            if norm_ch not in valid_channels:
                errors.append(
                    f"{prefix}: unknown channel '{channel}' (not present in firmware I/O map: {sorted(valid_channels)})"
                )

        if not isinstance(at_ms, int) or at_ms < 0:
            errors.append(f"{prefix}: at_ms must be a non-negative integer")
        elif at_ms < previous_at_ms:
            errors.append(f"{prefix}: events must be ordered by at_ms")
        elif at_ms > duration_ms:
            errors.append(f"{prefix}: at_ms ({at_ms} ms) exceeds duration_ms ({duration_ms} ms)")
        else:
            previous_at_ms = at_ms

        for_ms = event.get("for_ms")
        if for_ms is not None and (not isinstance(for_ms, int) or for_ms < 0):
            errors.append(f"{prefix}: for_ms must be a non-negative integer")

        over_ms = event.get("over_ms")
        if over_ms is not None and (not isinstance(over_ms, int) or over_ms < 0):
            errors.append(f"{prefix}: over_ms must be a non-negative integer")

    return errors


def validate_timeline(timeline: Dict[str, Any], io_map: Dict[str, Any]) -> None:
    """Raise ValueError when a timeline is not executable against the IO map."""
    errors = lint_timeline(timeline, io_map)
    if errors:
        raise ValueError("timeline lint failed: " + "; ".join(errors))
