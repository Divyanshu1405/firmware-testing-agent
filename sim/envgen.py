"""Generate Renode environment files from an IO map."""

from __future__ import annotations

from pathlib import Path
from typing import Any


DEFAULT_BOARD = "platforms/boards/stm32f4_discovery-kit.repl"


def generate_environment(
    io_map: dict[str, Any],
    firmware: Path,
    output_dir: Path,
    uart_log: Path | None = None,
) -> dict[str, Path]:
    """Write a board overlay and Renode script, returning their paths."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    firmware = Path(firmware).resolve()
    uart_log = Path(uart_log or output_dir / "uart.log").resolve()
    overlay_path = output_dir / "io_overlay.repl"
    script_path = output_dir / "run.resc"

    overlay_lines = ["// Generated from profile/io_map.json"]
    needs_si7021 = False
    for channel, mapping in io_map.get("inputs", {}).items():
        peripheral = mapping.get("peripheral")
        address = mapping.get("address")
        if peripheral and address is not None:
            if mapping.get("model") == "SI7021" and peripheral.startswith("sysbus."):
                bus = peripheral.removeprefix("sysbus.")
                overlay_lines.append(
                    f"sensor_si7021: Mocks.DummyI2CSlave @ {bus} {address}"
                )
                needs_si7021 = True
            overlay_lines.append(
                f"// input {channel}: {peripheral} at {address} ({mapping.get('model', 'unknown')})"
            )
    for channel, mapping in io_map.get("outputs", {}).items():
        peripheral = mapping.get("peripheral")
        if peripheral:
            overlay_lines.append(f"// output {channel}: {peripheral}")
    overlay_path.write_text("\n".join(overlay_lines) + "\n")

    platform = io_map.get("platform", DEFAULT_BOARD)
    uart = io_map.get("uart", "sysbus.usart2")
    script_path.write_text(
        "\n".join(
            [
                f'mach create "generated"',
                f"machine LoadPlatformDescription @{platform}",
                f"machine LoadPlatformDescription @{overlay_path.resolve()}",
                *(
                    [
                        f'include "{Path(__file__).with_name("si7021_injected.py").resolve()}"',
                        "setup_si7021 sysbus.i2c1.sensor_si7021",
                    ]
                    if needs_si7021
                    else []
                ),
                f"sysbus LoadELF @{firmware}",
                f"{uart} CreateFileBackend @{uart_log}",
                "start",
                "sleep 1",
                "q",
            ]
        )
        + "\n"
    )
    return {"overlay": overlay_path, "script": script_path}
