"""Deterministic simulator mock for agent and judge development."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sim.faults_exec import FAULT_ACTIONS, transform_sample

class FakeBackend:
    """Return a stable, contract-shaped trace without launching Renode."""

    name = "fake"

    def run(
        self,
        firmware: Path,
        timeline: dict[str, Any],
        io_map: dict[str, Any] | None = None,
        timeout_s: int = 60,
    ) -> dict[str, Any]:
        del io_map, timeout_s
        samples = []
        for event in timeline.get("events", []):
            sample = {
                "t_ms": int(event.get("at_ms", 0)),
                "dir": "in",
                "channel": event["channel"],
                "value": event.get("value", event.get("to")),
            }
            if event.get("channel"):
                if event.get("action") in FAULT_ACTIONS:
                    sample = transform_sample(sample, event)
                samples.append(sample)
        return {
            "test_id": timeline.get("test_id", "fake-test"),
            "firmware": Path(firmware).name,
            "sim": self.name,
            "seed": int(timeline.get("seed", 0)),
            "samples": samples,
            "events": [],
            "end_reason": "duration_reached",
        }
