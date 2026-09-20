"""Profile inference engine for firmware intake.

Analyzes static triage output and generates a versioned FirmwareProfile
and IOMap with clear provenance and confidence tracking. Ensures that
unknown firmware does NOT blindly inherit the STM32F4/SI7021 sensor profile.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple


def infer_profile(triage_data: Dict[str, Any], firmware_path: Path | str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Generate firmware profile and I/O map from static triage data.
    
    Returns:
        (firmware_profile, io_map)
    """
    fw_name = Path(firmware_path).name if firmware_path else "unknown"
    sym_data = triage_data.get("symbols", {})
    if isinstance(sym_data, dict):
        symbols = sym_data.get("functions", []) + sym_data.get("objects", [])
    elif isinstance(sym_data, list):
        symbols = sym_data
    else:
        symbols = []
    strings = triage_data.get("strings", [])
    peripherals = triage_data.get("detected_peripherals", {})

    sym_set = set(s.lower() for s in symbols)
    str_set = set(s.lower() for s in strings)

    # 1. Check for STM32F4 / SI7021 signature
    has_si7021_funcs = any("si7021" in s for s in sym_set)
    has_stm32_hal = any(s.startswith("hal_") for s in sym_set)
    has_telemetry_strings = any("humidity:" in s or "temperature:" in s for s in str_set)

    is_si7021_sample = has_si7021_funcs or (has_stm32_hal and has_telemetry_strings)

    if is_si7021_sample:
        provenance = "known_sample" if has_si7021_funcs else "signature_match"
        confidence = 1.0 if has_si7021_funcs else 0.85

        firmware_profile = {
            "profile_id": "stm32f4_si7021",
            "firmware": fw_name,
            "architecture": triage_data.get("architecture", "ARM"),
            "platform": "platforms/boards/stm32f4_discovery-kit.repl",
            "sensor_platform": "sim/si7021_injected.repl",
            "sensor_script": "sim/si7021_injected.py",
            "uart": "sysbus.usart2",
            "provenance": provenance,
            "confidence": confidence,
            "detected_features": {
                "sensor_model": "SI7021",
                "bus": "I2C1 (0x40)",
                "uart": "USART2 (sysbus.usart2)",
            },
            "notes": [
                "Firmware matched STM32F4/SI7021 sensor profile with verified symbol and string signatures.",
                "Sensor responses are injected via sim/si7021_injected.py on I2C1 address 0x40.",
            ],
        }

        io_map = {
            "firmware": fw_name,
            "platform": "platforms/boards/stm32f4_discovery-kit.repl",
            "uart": "sysbus.usart2",
            "inputs": {
                "temp_c": {
                    "kind": "i2c",
                    "peripheral": "sysbus.i2c1",
                    "channel": None,
                    "scale": 1.0,
                    "address": "0x40",
                    "model": "SI7021",
                },
                "humidity_pct": {
                    "kind": "i2c",
                    "peripheral": "sysbus.i2c1",
                    "channel": None,
                    "scale": 1.0,
                    "address": "0x40",
                    "model": "SI7021",
                },
            },
            "outputs": {
                "uart": {
                    "kind": "uart",
                    "pin": "sysbus.usart2",
                }
            },
            "notes": [
                "STM32F4 Discovery with SI7021 sensor attached to I2C1.",
                "Telemetry transmitted over USART2.",
            ],
        }
    else:
        # Unknown or generic firmware: do NOT assume SI7021
        uart_name = "sysbus.usart2"
        if peripherals.get("uart"):
            uart_hints = peripherals["uart"]
            for u in uart_hints:
                if "usart1" in u.lower():
                    uart_name = "sysbus.usart1"
                elif "usart2" in u.lower():
                    uart_name = "sysbus.usart2"
                elif "usart3" in u.lower():
                    uart_name = "sysbus.usart3"

        firmware_profile = {
            "profile_id": "generic_arm_firmware",
            "firmware": fw_name,
            "architecture": triage_data.get("architecture", "ARM"),
            "platform": "platforms/boards/stm32f4_discovery-kit.repl",
            "sensor_platform": None,
            "sensor_script": None,
            "uart": uart_name,
            "provenance": "inferred",
            "confidence": 0.40,
            "detected_features": {
                "detected_uart_symbols": peripherals.get("uart", []),
                "detected_i2c_symbols": peripherals.get("i2c", []),
                "detected_spi_symbols": peripherals.get("spi", []),
            },
            "notes": [
                "Unknown firmware binary: SI7021 sensor profile was NOT applied.",
                "Generic ARM Cortex-M execution environment selected.",
                "Only generic reliability and detected peripheral tests are applicable.",
            ],
        }

        io_map = {
            "firmware": fw_name,
            "platform": "platforms/boards/stm32f4_discovery-kit.repl",
            "uart": uart_name,
            "inputs": {},
            "outputs": {
                "uart": {
                    "kind": "uart",
                    "pin": uart_name,
                }
            },
            "notes": [
                "Generic I/O map: no sensor inputs assumed without evidence.",
                "Monitoring default UART channel for activity and crash detection.",
            ],
        }

    return firmware_profile, io_map

