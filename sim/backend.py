"""Contract-compatible Renode execution backend."""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from sim.lint import lint_timeline

REPO_ROOT = Path(__file__).resolve().parent.parent
UART_LINE = re.compile(r"^.*?\b(?P<message>[^\r\n]+)$")


class RenodeBackend:
    """Run a firmware image in Renode and return a trace-shaped dictionary."""

    name = "renode"
    sensor_platform = Path(__file__).with_name("si7021_injected.repl").resolve()
    sensor_script = Path(__file__).with_name("si7021_injected.py").resolve()

    def run(
        self,
        firmware: Path,
        timeline: dict[str, Any],
        io_map: dict[str, Any],
        timeout_s: int = 60,
    ) -> dict[str, Any]:
        firmware = Path(firmware).resolve()
        duration_ms = int(timeline.get("duration_ms", 0))
        trace = {
            "test_id": timeline.get("test_id", "unknown"),
            "firmware": firmware.name,
            "sim": self.name,
            "seed": int(timeline.get("seed", 0)),
            "samples": [],
            "events": [],
            "end_reason": "sim_error",
        }

        if not firmware.is_file():
            trace["events"].append(
                {"t_ms": 0, "kind": "sim_error", "detail": "firmware not found"}
            )
            return trace

        lint_errors = lint_timeline(timeline, io_map)
        if lint_errors:
            trace["events"].append(
                {"t_ms": 0, "kind": "sim_error", "detail": "; ".join(lint_errors)}
            )
            return trace

        input_commands, input_samples, input_error = self._timeline_commands(
            timeline, io_map
        )
        if input_error:
            trace["events"].append(
                {"t_ms": 0, "kind": "sim_error", "detail": input_error}
            )
            return trace
        trace["samples"].extend(input_samples)

        with tempfile.TemporaryDirectory(prefix="firmware-sim-") as run_dir:
            uart_log = Path(run_dir) / "uart.log"
            uart_log.touch()
            command = self._command(firmware, uart_log, duration_ms, input_commands)
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=max(1, timeout_s),
                    check=False,
                )
            except subprocess.TimeoutExpired:
                trace["end_reason"] = "timeout"
                trace["events"].append({"t_ms": 0, "kind": "hang"})
                return trace
            except OSError as error:
                trace["events"].append(
                    {"t_ms": 0, "kind": "sim_error", "detail": str(error)}
                )
                return trace

            trace["samples"].extend(self._uart_samples(uart_log))
            if result.returncode != 0:
                trace["events"].append(
                    {
                        "t_ms": 0,
                        "kind": "sim_error",
                        "detail": result.stderr.strip() or "Renode exited with an error",
                    }
                )
                return trace

        trace["end_reason"] = "duration_reached"
        return trace

    def _command(
        self,
        firmware: Path,
        uart_log: Path,
        duration_ms: int,
        input_commands: list[tuple[int, str]],
    ) -> list[str]:
        commands = [
            "renode",
            "--console",
            "--disable-xwt",
            "--execute",
            'mach create "test"',
            "--execute",
            "machine LoadPlatformDescription @platforms/boards/stm32f4_discovery-kit.repl",
            "--execute",
            f"machine LoadPlatformDescription @{self.sensor_platform}",
            "--execute",
            f'include "{self.sensor_script}"',
            "--execute",
            "setup_si7021 sysbus.i2c1.sensor_si7021",
            "--execute",
            f"sysbus LoadELF @{firmware}",
            "--execute",
            f"usart2 CreateFileBackend @{uart_log}",
            "--execute",
            "start",
        ]
        elapsed_ms = 0
        for at_ms, input_command in input_commands:
            if at_ms < elapsed_ms or at_ms > duration_ms:
                continue
            delay_s = (at_ms - elapsed_ms) / 1000
            if delay_s:
                commands.extend(["--execute", f"sleep {delay_s}"])
            commands.extend(["--execute", input_command])
            elapsed_ms = at_ms
        remaining_s = max(0.001, (duration_ms - elapsed_ms) / 1000)
        commands.extend(["--execute", f"sleep {remaining_s}", "--execute", "q"])
        return commands

    @staticmethod
    def _timeline_commands(
        timeline: dict[str, Any], io_map: dict[str, Any]
    ) -> tuple[list[tuple[int, str]], list[dict[str, Any]], str | None]:
        commands = []
        samples = []
        inputs = io_map.get("inputs", {})
        for event in sorted(timeline.get("events", []), key=lambda item: item["at_ms"]):
            action = event.get("action")
            channel = event.get("channel")
            mapping = inputs.get(channel, {})
            value = event.get("value")
            if value is None:
                value = event.get("to", 25.0)

            command = ""
            if channel in ("temp_c", "temperature"):
                command = f"set_temperature {value}"
            elif channel in ("humidity_pct", "humidity"):
                command = f"set_humidity {value}"
            elif mapping.get("write_address") is not None:
                address = mapping["write_address"]
                try:
                    raw_value = int(value * mapping.get("scale", 1) + mapping.get("offset", 0))
                except (TypeError, ValueError):
                    return [], [], f"input '{channel}' has a non-numeric value"
                width = mapping.get("write_width", 32)
                if width == 32:
                    command = f"sysbus WriteDoubleWord {address} {raw_value}"
                else:
                    return [], [], f"input '{channel}' has unsupported write_width {width}"
            else:
                # Default fallback for simulated channel
                command = f"set_temperature {value}"

            at_ms = int(event.get("at_ms", 0))
            if command:
                commands.append((at_ms, command))
            samples.append(
                {"t_ms": at_ms, "dir": "in", "channel": channel or "temp_c", "value": value}
            )
        return commands, samples, None

    @staticmethod
    def _uart_samples(uart_log: Path) -> list[dict[str, Any]]:
        if not uart_log.exists():
            return []
        samples = []
        for line in uart_log.read_text(errors="replace").splitlines():
            message = line.strip()
            if message:
                samples.append(
                    {"t_ms": 0, "dir": "out", "channel": "uart", "value": message}
                )
        return samples
