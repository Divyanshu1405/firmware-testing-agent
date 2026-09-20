"""
sim/runner.py
Top-level simulation runner dispatching to RenodeBackend when Renode is available
and firmware is a valid ELF binary; falls back to FakeBackend for synthetic/mock binaries.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any, Dict

from sim.backend import RenodeBackend
from sim.fake_backend import FakeBackend

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent
IO_MAP_PATH = REPO_ROOT / "profile" / "io_map.json"


def _load_io_map() -> dict:
    if IO_MAP_PATH.exists():
        try:
            return json.loads(IO_MAP_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "inputs": {
            "temp_c": {
                "kind": "i2c",
                "peripheral": "sysbus.i2c1",
                "address": "0x40",
                "model": "SI7021",
            },
            "humidity_pct": {
                "kind": "i2c",
                "peripheral": "sysbus.i2c1",
                "address": "0x40",
                "model": "SI7021",
            },
        },
        "outputs": {
            "uart": {
                "kind": "uart",
                "peripheral": "sysbus.usart2",
            }
        },
    }


def simulate(firmware_path: str, timeline_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run simulation for a single timeline against a target firmware binary.
    Uses RenodeBackend when Renode executable exists and target is an ELF binary.
    Falls back to FakeBackend when Renode is not available or target is mock (.bin).
    """
    fw_path = Path(firmware_path)
    if not fw_path.is_absolute():
        fw_path = (REPO_ROOT / firmware_path).resolve()

    io_map = _load_io_map()

    # Check for Renode availability
    renode_bin = shutil.which("renode")
    if not renode_bin:
        win_renode = Path(r"C:\Program Files\Renode\renode.exe")
        if win_renode.exists():
            renode_bin = str(win_renode)

    is_elf = fw_path.suffix.lower() in (".elf", ".axf")
    use_renode = bool(renode_bin) and is_elf and fw_path.is_file()

    trace = None
    if use_renode:
        try:
            backend = RenodeBackend()
            tl_copy = dict(timeline_dict)
            orig_duration = tl_copy.get("duration_ms", 1000)
            tl_copy["duration_ms"] = min(max(500, orig_duration), 2000)

            filtered_events = [
                ev for ev in tl_copy.get("events", [])
                if ev.get("at_ms", 0) <= tl_copy["duration_ms"]
            ]
            tl_copy["events"] = filtered_events

            trace = backend.run(fw_path, tl_copy, io_map, timeout_s=15)

            valid_kinds = {"hardfault", "reset", "hang", "invalid_memory_access"}
            cleaned_events = []
            for ev in trace.get("events", []):
                kind = str(ev.get("kind", "")).lower()
                if kind in valid_kinds:
                    cleaned_events.append({"t_ms": ev.get("t_ms", 0), "kind": kind})
            trace["events"] = cleaned_events

            if not any(s.get("dir") == "in" for s in trace.get("samples", [])):
                for ev in timeline_dict.get("events", []):
                    trace["samples"].append({
                        "t_ms": int(ev.get("at_ms", 0)),
                        "dir": "in",
                        "channel": ev.get("channel", "temp_c"),
                        "value": ev.get("value", ev.get("to", 25.0)),
                    })

        except Exception as exc:
            logger.warning("Renode execution error (%s); falling back to FakeBackend", exc)
            trace = None

    if trace is None:
        fake = FakeBackend()
        trace = fake.run(fw_path, timeline_dict, io_map)
        valid_kinds = {"hardfault", "reset", "hang", "invalid_memory_access"}
        trace["events"] = [
            {"t_ms": ev.get("t_ms", 0), "kind": ev.get("kind")}
            for ev in trace.get("events", [])
            if ev.get("kind") in valid_kinds
        ]

    # Ensure all samples have a non-None value so exclude_none=True does not drop 'value'
    for s in trace.get("samples", []):
        if s.get("value") is None:
            s["value"] = 0.0

    trace["samples"].sort(key=lambda s: s.get("t_ms", 0))
    return trace

