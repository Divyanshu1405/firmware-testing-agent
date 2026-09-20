"""Run a bounded, non-interactive Renode probe for the SI7021 model."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SENSOR = ROOT / "sim" / "si7021.repl"
INJECTED_SENSOR = ROOT / "sim" / "si7021_injected.repl"
DEFAULT_FIRMWARE = ROOT / "firmware" / "inputs" / "firmware1.elf"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--renode", default="renode")
    parser.add_argument("--firmware", type=Path, default=DEFAULT_FIRMWARE)
    parser.add_argument("--injected", action="store_true")
    args = parser.parse_args()
    firmware = args.firmware.resolve()
    uart_log = ROOT / "logs" / "probe_uart.log"
    uart_log.parent.mkdir(parents=True, exist_ok=True)
    uart_log.write_text("")
    try:
        commands = [
            'mach create "probe"',
            "machine LoadPlatformDescription @platforms/boards/stm32f4_discovery-kit.repl",
            f"machine LoadPlatformDescription @{INJECTED_SENSOR if args.injected else SENSOR}",
            f'include "{ROOT / "sim" / "si7021_injected.py"}"' if args.injected else "",
            "setup_si7021 sysbus.i2c1.sensor_si7021" if args.injected else "",
            f"sysbus LoadELF @{firmware}",
            f"usart2 CreateFileBackend @{uart_log}",
            "start",
            "sleep 1",
            "q",
        ]
        command = [args.renode, "--console", "--disable-xwt"]
        for monitor_command in commands:
            if monitor_command:
                command.extend(["--execute", monitor_command])
        print(f"Running firmware probe: {firmware.name}")
        try:
            result = subprocess.run(command, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            print("Renode probe timed out after 30 seconds")
            return 124
        print("--- UART output ---")
        print(uart_log.read_text(errors="replace") if uart_log.exists() else "<none>")
        print(f"Renode exit code: {result.returncode}")
        return result.returncode
    finally:
        uart_log.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())