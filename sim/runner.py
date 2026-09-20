"""Top-level simulation runner dispatching to RenodeBackend or explicit FakeBackend.

Ensures that live simulation never silently falls back to FakeBackend,
preserving honest error reporting and full virtual-time durations.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from profile.infer import infer_profile
from profile.static.triage import analyze_firmware, is_elf_file
from sim.backend import RenodeBackend, find_renode
from sim.fake_backend import FakeBackend

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_firmware_io_map(firmware_path: Path) -> Dict[str, Any]:
    """Retrieve or dynamically infer the I/O map for the target firmware."""
    try:
        if firmware_path.is_file() and is_elf_file(firmware_path):
            triage_data = analyze_firmware(firmware_path)
            _, io_map = infer_profile(triage_data, firmware_path)
            return io_map
    except Exception as exc:
        logger.warning("Failed to infer I/O map for %s: %s", firmware_path, exc)

    # Profiling failure must not make an arbitrary target look like the
    # STM32F4/SI7021 calibration firmware.  Keep the fallback deliberately
    # capability-poor and let planning report unsupported stimuli.
    return {
        "inputs": {},
        "outputs": {
            "uart": {
                "kind": "uart",
                "peripheral": "sysbus.usart2",
            }
        },
        "firmware": firmware_path.name,
        "platform": "platforms/boards/stm32f4_discovery-kit.repl",
        "uart": "sysbus.usart2",
        "notes": ["Generic fallback I/O map; no sensors inferred because profiling failed."],
    }


def simulate(
    firmware_path: str | Path,
    timeline_dict: Dict[str, Any],
    io_map: Optional[Dict[str, Any]] = None,
    sim_mode: str = "renode",
    timeout_s: int = 60,
) -> Dict[str, Any]:
    """Execute a single test timeline against the target firmware.

    Args:
        firmware_path: Path to target firmware binary.
        timeline_dict: Validated timeline event dictionary.
        io_map: Hardware I/O profile for peripheral mapping.
        sim_mode: "renode" (default, virtual hardware) or "fake" (explicit mock fixture).
        timeout_s: Maximum host execution timeout in seconds.

    Returns:
        Trace dictionary strictly compliant with contracts/trace.schema.json.
    """
    fw_path = Path(firmware_path)
    if not fw_path.is_absolute():
        fw_path = (REPO_ROOT / firmware_path).resolve()

    test_id = timeline_dict.get("test_id", "T01")
    seed = int(timeline_dict.get("seed", 0))

    if io_map is None:
        io_map = get_firmware_io_map(fw_path)

    # Explicit Fake fixture mode
    if sim_mode.lower() == "fake":
        fake = FakeBackend()
        trace = fake.run(fw_path, timeline_dict, io_map)
        trace["sim"] = "fake"
        return trace

    # Live Renode simulation path
    renode_bin = find_renode()
    if not renode_bin:
        return {
            "test_id": test_id,
            "firmware": fw_path.name,
            "sim": "renode",
            "seed": seed,
            "samples": [],
            "events": [],
            "end_reason": "sim_error",
            "error_detail": "INFRASTRUCTURE_ERROR: Renode executable not found on host. Cannot execute virtual simulation.",
        }

    if not fw_path.is_file():
        return {
            "test_id": test_id,
            "firmware": fw_path.name,
            "sim": "renode",
            "seed": seed,
            "samples": [],
            "events": [],
            "end_reason": "sim_error",
            "error_detail": f"Target firmware file not found: {fw_path}",
        }

    if not is_elf_file(fw_path):
        return {
            "test_id": test_id,
            "firmware": fw_path.name,
            "sim": "renode",
            "seed": seed,
            "samples": [],
            "events": [],
            "end_reason": "sim_error",
            "error_detail": f"Target firmware '{fw_path.name}' is not a valid ELF binary format.",
        }

    backend = RenodeBackend()
    try:
        # Preserve full duration — do not clamp to 2000 ms
        trace = backend.run(fw_path, timeline_dict, io_map, timeout_s=timeout_s)
    except Exception as exc:
        logger.error("Renode backend execution error: %s", exc)
        return {
            "test_id": test_id,
            "firmware": fw_path.name,
            "sim": "renode",
            "seed": seed,
            "samples": [],
            "events": [],
            "end_reason": "sim_error",
            "error_detail": f"Renode simulation process failed: {exc}",
        }

    # Normalize samples ensuring all fields match trace schema
    for s in trace.get("samples", []):
        if s.get("value") is None:
            s["value"] = 0.0

    trace["samples"].sort(key=lambda s: s.get("t_ms", 0))
    return trace
