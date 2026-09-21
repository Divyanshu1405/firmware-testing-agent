"""Authoritative contract-compatible Renode execution backend with virtual time."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from profile.static.triage import is_elf_file
from sim.lint import lint_timeline

REPO_ROOT = Path(__file__).resolve().parent.parent
UART_LINE = re.compile(r"^.*?\b(?P<message>[^\r\n]+)$")
MAX_DURATION_MS = 120000  # 2 minute safety ceiling


def find_renode() -> Optional[str]:
    """Locate the Renode executable on the system PATH or default Windows path."""
    renode_bin = shutil.which("renode")
    if renode_bin:
        return renode_bin
    win_path = Path(r"C:\Program Files\Renode\renode.exe")
    if win_path.is_file():
        return str(win_path)
    return None


def format_time_interval(ms: int) -> str:
    """Format milliseconds into Renode TimeInterval string: 'hh:mm:ss.fff'."""
    ms = max(0, int(ms))
    s, ms_rem = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"'{h:02d}:{m:02d}:{s:02d}.{ms_rem:03d}'"


class RenodeBackend:
    """Run firmware in Renode with virtual-timestamped trace capture."""

    name = "renode"
    sensor_platform = Path(__file__).with_name("si7021_injected.repl").resolve()
    sensor_script = Path(__file__).with_name("si7021_injected.py").resolve()

    def __init__(
        self,
        sensor_platform: Optional[Path] = None,
        sensor_script: Optional[Path] = None,
    ):
        self.sensor_platform = (
            sensor_platform or Path(__file__).with_name("si7021_injected.repl").resolve()
        )
        self.sensor_script = (
            sensor_script or Path(__file__).with_name("si7021_injected.py").resolve()
        )

    def run(
        self,
        firmware: Path | str,
        timeline: Dict[str, Any],
        io_map: Optional[Dict[str, Any]] = None,
        timeout_s: int = 60,
    ) -> Dict[str, Any]:
        firmware = Path(firmware).resolve()
        duration_ms = int(timeline.get("duration_ms", 1000))
        test_id = timeline.get("test_id", "unknown")
        seed = int(timeline.get("seed", 0))

        trace: Dict[str, Any] = {
            "test_id": test_id,
            "firmware": firmware.name,
            "sim": self.name,
            "seed": seed,
            "samples": [],
            "events": [],
            "end_reason": "sim_error",
        }

        # 1. Firmware existence and ELF validation
        if not firmware.is_file():
            trace["end_reason"] = "sim_error"
            trace["error_detail"] = f"Firmware binary not found: {firmware}"
            return trace

        if not is_elf_file(firmware):
            trace["end_reason"] = "sim_error"
            trace["error_detail"] = f"Firmware '{firmware.name}' is not a valid ELF binary."
            return trace

        # 2. Check Renode executable availability
        renode_bin = find_renode()
        if not renode_bin:
            trace["end_reason"] = "sim_error"
            trace["error_detail"] = "INFRASTRUCTURE_ERROR: Renode executable not found on system PATH or default installation path."
            return trace

        # 3. Check duration safety limit
        if duration_ms > MAX_DURATION_MS:
            trace["end_reason"] = "sim_error"
            trace["error_detail"] = f"Timeline duration ({duration_ms} ms) exceeds safety maximum limit of {MAX_DURATION_MS} ms."
            return trace

        # 4. Lint timeline against I/O map
        active_io_map = io_map or {}
        lint_errors = lint_timeline(timeline, active_io_map)
        if lint_errors:
            trace["end_reason"] = "sim_error"
            trace["error_detail"] = "Timeline linting failed: " + "; ".join(lint_errors)
            return trace

        # 5. Compile simulation steps and input samples
        schedule_steps, input_samples, compile_err = self._compile_schedule(
            timeline, duration_ms, active_io_map
        )
        if compile_err:
            trace["end_reason"] = "sim_error"
            trace["error_detail"] = f"Event schedule compilation error: {compile_err}"
            return trace
        trace["samples"].extend(input_samples)

        # 6. Execute in temporary isolated directory on workspace drive (avoids Windows cross-drive path issues)
        sim_runs_base = REPO_ROOT / ".sim_runs"
        sim_runs_base.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="sim-", dir=sim_runs_base) as run_dir_str:
            run_dir = Path(run_dir_str)
            cast_file = run_dir / "uart.cast"

            commands = self._build_renode_commands(
                renode_bin=renode_bin,
                firmware=firmware,
                cast_file=cast_file,
                schedule_steps=schedule_steps,
                io_map=active_io_map,
            )

            try:
                result = subprocess.run(
                    commands,
                    capture_output=True,
                    text=True,
                    timeout=max(5, timeout_s),
                    check=False,
                )
            except subprocess.TimeoutExpired:
                trace["end_reason"] = "timeout"
                trace["events"].append({
                    "t_ms": duration_ms,
                    "kind": "hang",
                    "detail": f"Simulation host execution timed out after {timeout_s}s",
                })
                # Parse whatever output was recorded before timeout
                if cast_file.exists():
                    trace["samples"].extend(self._parse_asciinema(cast_file))
                return trace
            except OSError as exc:
                trace["end_reason"] = "sim_error"
                trace["error_detail"] = f"INFRASTRUCTURE_ERROR: Failed to launch Renode process: {exc}"
                return trace

            # 7. Parse UART output with virtual timestamps
            if cast_file.exists():
                trace["samples"].extend(self._parse_asciinema(cast_file))

            # 8. Parse execution log for faults
            detected_faults = self._parse_log_events(result.stdout, result.stderr)
            for f_event in detected_faults:
                trace["events"].append(f_event)

            # 9. Determine end_reason
            has_crash = any(
                e.get("kind") in ("hardfault", "crash", "invalid_memory_access")
                for e in trace["events"]
            )
            if has_crash:
                trace["end_reason"] = "crash"
            # Input samples are recorded before launching Renode.  They are not
            # evidence that Renode ran successfully, so they must never turn a
            # non-zero Renode exit into a successful execution.
            elif result.returncode != 0:
                trace["end_reason"] = "sim_error"
                trace["error_detail"] = (
                    "INFRASTRUCTURE_ERROR: Renode exited with code "
                    f"{result.returncode}: "
                    f"{(result.stderr.strip() or result.stdout.strip())[:400]}"
                )
                return trace
            else:
                trace["end_reason"] = "duration_reached"

        trace["samples"].sort(key=lambda s: s.get("t_ms", 0))
        return trace

    def _compile_schedule(
        self,
        timeline: Dict[str, Any],
        duration_ms: int,
        io_map: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
        """Compile timeline events and recovery transitions into virtual time checkpoints."""
        raw_events = sorted(timeline.get("events", []), key=lambda e: e.get("at_ms", 0))
        input_samples: List[Dict[str, Any]] = []
        action_points: List[Tuple[int, List[str]]] = []

        nominal_temp = 25.0
        nominal_humidity = 50.0

        for event in raw_events:
            at_ms = int(event.get("at_ms", 0))
            if at_ms > duration_ms:
                continue

            action = event.get("action", "step")
            channel = event.get("channel", "temp_c")
            value = event.get("value")
            if value is None:
                value = event.get("to", 25.0)

            for_ms = event.get("for_ms")
            over_ms = event.get("over_ms")

            cmds: List[str] = []
            recovery_cmds: List[str] = []

            if action in ("set", "step"):
                if "temp" in channel.lower():
                    cmds.append(f"set_temperature {value}")
                    nominal_temp = float(value)
                elif "humid" in channel.lower():
                    cmds.append(f"set_humidity {value}")
                    nominal_humidity = float(value)
                else:
                    return [], [], f"Unsupported channel '{channel}' for action '{action}'"

            elif action == "dropout":
                cmds.append("set_sensor_dropout 1")
                if for_ms:
                    recovery_cmds.append("set_sensor_dropout 0")

            elif action == "stuck":
                cmds.append(f"set_sensor_stuck {channel} {value}")
                if for_ms:
                    recovery_cmds.append("clear_sensor_stuck")

            elif action in ("spike", "glitch"):
                spike_val = float(value)
                if "temp" in channel.lower():
                    cmds.append(f"set_temperature {spike_val}")
                    recovery_cmds.append(f"set_temperature {nominal_temp}")
                elif "humid" in channel.lower():
                    cmds.append(f"set_humidity {spike_val}")
                    recovery_cmds.append(f"set_humidity {nominal_humidity}")

            elif action in ("drift", "ramp"):
                target_val = float(event.get("to", value))
                if "temp" in channel.lower():
                    cmds.append(f"set_temperature {target_val}")
                    nominal_temp = target_val
                elif "humid" in channel.lower():
                    cmds.append(f"set_humidity {target_val}")
                    nominal_humidity = target_val

            elif action == "error_reading":
                cmds.append("set_sensor_error 1")
                if for_ms:
                    recovery_cmds.append("set_sensor_error 0")

            else:
                return [], [], f"Unsupported action '{action}' in timeline"

            action_points.append((at_ms, cmds))
            if recovery_cmds and for_ms:
                action_points.append((at_ms + int(for_ms), recovery_cmds))

            input_samples.append({
                "t_ms": at_ms,
                "dir": "in",
                "channel": channel,
                "value": value,
            })

        # Group commands by timestamp
        time_map: Dict[int, List[str]] = {}
        for t, c_list in action_points:
            time_map.setdefault(t, []).extend(c_list)

        sorted_times = sorted(time_map.keys())
        schedule_steps: List[Dict[str, Any]] = []

        last_t = 0
        for t in sorted_times:
            if t > duration_ms:
                break
            if t > last_t:
                schedule_steps.append({
                    "run_for_ms": t - last_t,
                    "commands": [],
                })
                last_t = t
            schedule_steps.append({
                "run_for_ms": 0,
                "commands": time_map[t],
            })

        if duration_ms > last_t:
            schedule_steps.append({
                "run_for_ms": duration_ms - last_t,
                "commands": [],
            })

        return schedule_steps, input_samples, None

    def _build_renode_commands(
        self,
        renode_bin: str,
        firmware: Path,
        cast_file: Path,
        schedule_steps: List[Dict[str, Any]],
        io_map: Dict[str, Any],
    ) -> List[str]:
        platform_repl = io_map.get("platform", "platforms/boards/stm32f4_discovery-kit.repl")
        uart_name = io_map.get("uart", "sysbus.usart2")

        # Determine if SI7021 sensor platform should be attached
        has_si7021 = any("si7021" in str(inp.get("model", "")).lower() for inp in io_map.get("inputs", {}).values())

        cmd = [
            renode_bin,
            # A per-run config prevents concurrent runs from contending for
            # Renode's global AppData config.lock on Windows.
            "--config", str((cast_file.parent / "renode.conf").as_posix()),
            "--console",
            "--disable-xwt",
            "--execute", 'mach create "test"',
            "--execute", f"machine LoadPlatformDescription @{platform_repl}",
        ]

        if has_si7021:
            cmd.extend([
                "--execute", f"machine LoadPlatformDescription @{self.sensor_platform.as_posix()}",
                "--execute", f"include @{self.sensor_script.as_posix()}",
                "--execute", "setup_si7021 sysbus.i2c1.sensor_si7021",
            ])

        cmd.extend([
            "--execute", f"sysbus LoadELF @{firmware.as_posix()}",
            "--execute", f"{uart_name} RecordToAsciinema @{cast_file.as_posix()} true",
        ])

        for step in schedule_steps:
            for c in step["commands"]:
                cmd.extend(["--execute", c])
            run_ms = step["run_for_ms"]
            if run_ms > 0:
                interval_str = format_time_interval(run_ms)
                cmd.extend(["--execute", f"emulation RunFor {interval_str}"])

        cmd.extend(["--execute", "q"])
        return cmd

    @staticmethod
    def _parse_asciinema(cast_file: Path) -> List[Dict[str, Any]]:
        """Parse asciinema cast file and extract timestamped UART messages."""
        if not cast_file.exists():
            return []

        samples: List[Dict[str, Any]] = []
        current_line = ""
        line_start_t = None

        try:
            with open(cast_file, "r", encoding="utf-8", errors="replace") as f:
                for raw_line in f:
                    stripped = raw_line.strip()
                    if not stripped.startswith("["):
                        continue
                    try:
                        record = json.loads(stripped)
                        t_sec = float(record[0])
                        chunk = str(record[2])
                        for char in chunk:
                            if line_start_t is None:
                                line_start_t = t_sec

                            if char in ("\n", "\r"):
                                msg = current_line.strip()
                                if msg and line_start_t is not None:
                                    samples.append({
                                        "t_ms": int(round(line_start_t * 1000)),
                                        "dir": "out",
                                        "channel": "uart",
                                        "value": msg,
                                    })
                                current_line = ""
                                line_start_t = None
                            else:
                                current_line += char
                    except (json.JSONDecodeError, IndexError, ValueError):
                        continue

            # Flush any un-terminated tail line
            msg = current_line.strip()
            if msg and line_start_t is not None:
                samples.append({
                    "t_ms": int(round(line_start_t * 1000)),
                    "dir": "out",
                    "channel": "uart",
                    "value": msg,
                })
        except OSError:
            pass

        return samples

    @staticmethod
    def _parse_log_events(stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Scan Renode monitor stdout/stderr for CPU faults, hardfaults, invalid memory accesses."""
        combined_text = stdout + "\n" + stderr
        events = []
        if re.search(r"Hard fault|HardFault|HardFault_Handler", combined_text, re.IGNORECASE):
            events.append({
                "t_ms": 0,
                "kind": "hardfault",
                "detail": "Renode detected CPU HardFault exception",
            })

        if re.search(r"invalid memory access|access to invalid memory|unhandled (read|write)", combined_text, re.IGNORECASE):
            if "unhandled access" in combined_text.lower() or "invalid memory access" in combined_text.lower():
                events.append({
                    "t_ms": 0,
                    "kind": "invalid_memory_access",
                    "detail": "Renode reported unhandled or invalid peripheral/memory access",
                })

        return events
