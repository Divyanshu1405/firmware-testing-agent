"""Generate input-versus-output plots for failed tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def plot_failure(
    trace: dict[str, Any], timeline: dict[str, Any], output_path: Path
) -> Path:
    """Write a PNG comparing numeric injected inputs and observed outputs."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(9, 4.5))
    input_points: dict[str, list[tuple[float, float]]] = {}
    output_points: dict[str, list[tuple[float, float]]] = {}

    for event in timeline.get("events", []):
        value = event.get("value", event.get("to"))
        numeric = _number(value)
        if numeric is not None and event.get("channel"):
            input_points.setdefault(event["channel"], []).append(
                (event.get("at_ms", 0), numeric)
            )
    for sample in trace.get("samples", []):
        numeric = _number(sample.get("value"))
        if numeric is not None and sample.get("dir") == "out":
            output_points.setdefault(sample.get("channel", "output"), []).append(
                (sample.get("t_ms", 0), numeric)
            )

    for channel, points in input_points.items():
        points.sort()
        axis.plot(*zip(*points), marker="o", linestyle="--", label=f"input:{channel}")
    for channel, points in output_points.items():
        points.sort()
        axis.plot(*zip(*points), marker="x", label=f"output:{channel}")

    axis.set_title(f"Failure trace: {trace.get('test_id', 'unknown')}")
    axis.set_xlabel("Time (ms)")
    axis.set_ylabel("Value")
    axis.grid(True, alpha=0.3)
    if input_points or output_points:
        axis.legend()
    figure.tight_layout()
    figure.savefig(output_path, format="png", dpi=140)
    plt.close(figure)
    return output_path


def plot_failures(
    verdicts: list[dict[str, Any]],
    traces: dict[str, dict[str, Any]],
    timelines: dict[str, dict[str, Any]],
    output_dir: Path,
) -> list[Path]:
    """Generate one PNG for each FAIL verdict with matching trace data."""
    output_dir = Path(output_dir)
    paths = []
    for verdict in verdicts:
        if verdict.get("result", verdict.get("status")) != "FAIL":
            continue
        test_id = verdict.get("test_id")
        if test_id not in traces or test_id not in timelines:
            continue
        paths.append(plot_failure(traces[test_id], timelines[test_id], output_dir / f"{test_id}.png"))
    return paths
