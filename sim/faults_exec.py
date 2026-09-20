"""Deterministic timeline fault transformations."""

from __future__ import annotations

from typing import Any


FAULT_ACTIONS = {
    "dropout",
    "stuck",
    "spike",
    "glitch",
    "drift",
    "uart_write",
    "uart_garbage",
}


def apply_fault(
    action: str,
    value: Any,
    event: dict[str, Any],
    elapsed_ms: int = 0,
    stuck_value: Any = None,
) -> Any:
    """Apply one fault deterministically; ``None`` represents a dropout."""
    if action == "dropout":
        return None
    if action == "stuck":
        return event.get("value", stuck_value if stuck_value is not None else value)
    if action == "spike":
        magnitude = event.get("magnitude", event.get("by", event.get("value", 0)))
        return value + magnitude
    if action == "glitch":
        return event.get("value", 0 if value else 1)
    if action == "drift":
        rate = event.get("rate_per_ms", event.get("rate", 0))
        return value + rate * elapsed_ms
    if action == "uart_write":
        return str(event.get("value", value))
    if action == "uart_garbage":
        length = max(1, int(event.get("length", 4)))
        return "\x00" * length
    raise ValueError(f"unsupported fault action: {action}")


def transform_sample(
    sample: dict[str, Any], event: dict[str, Any], elapsed_ms: int = 0
) -> dict[str, Any]:
    """Return a copied sample with a fault transformation applied."""
    transformed = dict(sample)
    transformed["value"] = apply_fault(
        event["action"],
        sample.get("value"),
        event,
        elapsed_ms=elapsed_ms,
        stuck_value=sample.get("value"),
    )
    return transformed
