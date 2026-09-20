"""Mock Simulation Backend for Firmware Testing Agent.

Simulates execution of STM32F407 firmware running with a Si7021 I2C sensor
and USART2 telemetry output. Implements realistic behavioral divergence for
original.elf and each mutant binary based on disassembled instruction semantics.
Returns execution traces conforming to the frozen Trace contract.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import math


class FakeBackend:
    """Mock simulation backend implementing realistic sensor & UART dynamics."""

    def __init__(self, name: str = "mock_renode"):
        self.name = name

    def _identify_firmware_variant(self, firmware_path: Path | str) -> str:
        """Identify which mutant or original firmware is being simulated."""
        path_str = str(firmware_path).lower()
        if "mutant_1" in path_str or "branch_inversion" in path_str:
            return "mutant_1_branch_inversion"
        elif "mutant_2" in path_str or "timing_delay" in path_str:
            return "mutant_2_timing_delay"
        elif "mutant_3" in path_str or "humidity_offset" in path_str:
            return "mutant_3_humidity_offset"
        elif "mutant_4" in path_str or "humidity_scale" in path_str:
            return "mutant_4_humidity_scale"
        elif "mutant_5" in path_str or "i2c_command" in path_str:
            return "mutant_5_i2c_command"
        else:
            return "original"

    def _get_env_state_at(
        self,
        t_ms: int,
        timeline_events: List[Dict[str, Any]],
        base_temp: float = 25.0,
        base_humidity: float = 50.0,
    ) -> Dict[str, Any]:
        """Compute environmental stimulus values at a specific timestamp."""
        temp = base_temp
        humidity = base_humidity
        sensor_fault = False

        # Sort timeline events up to current timestamp
        past_events = [e for e in timeline_events if e.get("at_ms", 0) <= t_ms]
        past_events.sort(key=lambda e: e.get("at_ms", 0))

        for ev in past_events:
            ev_at = ev.get("at_ms", 0)
            action = ev.get("action", "")
            channel = ev.get("channel", "")

            # Channel: temp_c
            if channel == "temp_c":
                if action in ("set", "step"):
                    temp = float(ev.get("value", temp))
                elif action == "ramp":
                    to_val = float(ev.get("to", temp))
                    over_ms = float(ev.get("over_ms", 1000) or 1000)
                    progress = min(1.0, max(0.0, (t_ms - ev_at) / over_ms))
                    temp = temp + (to_val - temp) * progress
                elif action == "dropout":
                    for_ms = ev.get("for_ms", 1000)
                    if ev_at <= t_ms <= ev_at + for_ms:
                        sensor_fault = True
                elif action == "spike":
                    for_ms = ev.get("for_ms", 100)
                    if ev_at <= t_ms <= ev_at + for_ms:
                        temp += float(ev.get("amplitude", 20.0))
                elif action == "glitch":
                    for_ms = ev.get("for_ms", 10)
                    if ev_at <= t_ms <= ev_at + for_ms:
                        temp = float(ev.get("value", -99.0))
                elif action == "drift":
                    over_ms = float(ev.get("over_ms", 5000) or 5000)
                    to_val = float(ev.get("to", temp + 20.0))
                    progress = min(1.0, max(0.0, (t_ms - ev_at) / over_ms))
                    temp = temp + (to_val - temp) * progress
                elif action == "oscillation":
                    for_ms = ev.get("for_ms", 5000)
                    if ev_at <= t_ms <= ev_at + for_ms:
                        center = float(ev.get("center_value", temp))
                        amp = float(ev.get("amplitude", 5.0))
                        freq = float(ev.get("freq_hz", 1.0))
                        temp = center + amp * math.sin(2 * math.pi * freq * (t_ms - ev_at) / 1000.0)

            # Channel: humidity_pct
            elif channel == "humidity_pct":
                if action in ("set", "step"):
                    humidity = float(ev.get("value", humidity))
                elif action == "ramp":
                    to_val = float(ev.get("to", humidity))
                    over_ms = float(ev.get("over_ms", 1000) or 1000)
                    progress = min(1.0, max(0.0, (t_ms - ev_at) / over_ms))
                    humidity = humidity + (to_val - humidity) * progress
                elif action == "dropout":
                    for_ms = ev.get("for_ms", 1000)
                    if ev_at <= t_ms <= ev_at + for_ms:
                        sensor_fault = True

            # General fault injection channels
            elif channel in ("sensor_fault", "i2c_bus"):
                if action in ("dropout", "fault"):
                    for_ms = ev.get("for_ms", 1000)
                    if ev_at <= t_ms <= ev_at + for_ms:
                        sensor_fault = True

        return {"temp_c": temp, "humidity_pct": humidity, "sensor_fault": sensor_fault}

    def run(
        self,
        firmware: Path | str,
        timeline: Dict[str, Any],
        io_map: Optional[Dict[str, Any]] = None,
        timeout_s: int = 60,
    ) -> Dict[str, Any]:
        """Execute mock simulation and generate realistic execution trace."""
        fw_path = Path(firmware)
        variant = self._identify_firmware_variant(fw_path)

        test_id = timeline.get("test_id", "T01")
        duration_ms = int(timeline.get("duration_ms", 6000) or 6000)
        timeline_events = timeline.get("events", [])

        samples: List[Dict[str, Any]] = []
        trace_events: List[Dict[str, Any]] = [{"t_ms": 0, "kind": "reset"}]
        end_reason = "duration_reached"

        # Hardware timing parameters derived from original.elf disassembly
        # main() HAL_Init + I2C/UART Init takes ~100ms
        t_current = 100

        # Loop delay:
        # Original: HAL_Delay(2000) at 0x80012f0
        # Mutant 2: HAL_Delay(0) -> loop spins with only CPU/I2C delay (~5ms)
        if variant == "mutant_2_timing_delay":
            loop_period_ms = 5
            max_samples = 150  # Prevent unbounded memory usage
        else:
            loop_period_ms = 2000
            max_samples = 1000

        iteration = 0
        while t_current < duration_ms and iteration < max_samples:
            env = self._get_env_state_at(t_current, timeline_events)
            sensor_fault = env["sensor_fault"]
            in_temp = env["temp_c"]
            in_humidity = env["humidity_pct"]

            # Record stimulus inputs at sample time
            samples.append({
                "t_ms": t_current,
                "dir": "in",
                "channel": "temp_c",
                "value": round(in_temp, 2),
            })
            samples.append({
                "t_ms": t_current,
                "dir": "in",
                "channel": "humidity_pct",
                "value": round(in_humidity, 2),
            })

            # Check for timeline-injected crash/hardfault events
            active_events = [e for e in timeline_events if e.get("at_ms") == t_current]
            for ae in active_events:
                if ae.get("action") == "hardfault":
                    trace_events.append({"t_ms": t_current, "kind": "hardfault"})
                    end_reason = "crash"
                    break

            if end_reason == "crash":
                break

            # Behavioral Simulation per firmware variant:
            if sensor_fault:
                # Sensor hardware failure on I2C bus:
                # Firmware error branch outputs "Error\r\n"
                samples.append({
                    "t_ms": t_current,
                    "dir": "out",
                    "channel": "uart",
                    "value": "Error\r\n",
                })
            else:
                # Sensor hardware functional on I2C bus:
                if variant == "mutant_1_branch_inversion":
                    # Inverted condition check (bne -> beq at 0x80012e0):
                    # Normal successful sensor read jumps to error handling!
                    samples.append({
                        "t_ms": t_current,
                        "dir": "out",
                        "channel": "uart",
                        "value": "Error\r\n",
                    })

                elif variant == "mutant_3_humidity_offset":
                    # subs r0, #6 -> adds r0, #6 in Si7021 formula (+12% RH error)
                    calc_humidity = in_humidity + 12.0
                    calc_temp = in_temp
                    samples.append({
                        "t_ms": t_current,
                        "dir": "out",
                        "channel": "uart",
                        "value": f"Humidity: {int(calc_humidity)} Temperature: {int(calc_temp)}\r\n",
                    })

                elif variant == "mutant_4_humidity_scale":
                    # movs r0, #0 (multiplier zeroed, collapses to -6%)
                    calc_humidity = -6.0
                    calc_temp = in_temp
                    samples.append({
                        "t_ms": t_current,
                        "dir": "out",
                        "channel": "uart",
                        "value": f"Humidity: {int(calc_humidity)} Temperature: {int(calc_temp)}\r\n",
                    })

                elif variant == "mutant_5_i2c_command":
                    # Sent command 0xFF to Si7021 temp read -> command rejected, temp returns 0xFFFF (65535)
                    calc_humidity = in_humidity
                    calc_temp = 65535
                    samples.append({
                        "t_ms": t_current,
                        "dir": "out",
                        "channel": "uart",
                        "value": f"Humidity: {int(calc_humidity)} Temperature: {calc_temp}\r\n",
                    })

                else:
                    # original.elf (or mutant 2 timing delay where data formatting is unchanged)
                    calc_humidity = in_humidity
                    calc_temp = in_temp
                    samples.append({
                        "t_ms": t_current,
                        "dir": "out",
                        "channel": "uart",
                        "value": f"Humidity: {int(calc_humidity)} Temperature: {int(calc_temp)}\r\n",
                    })

            t_current += loop_period_ms
            iteration += 1

        return {
            "test_id": test_id,
            "firmware": fw_path.name,
            "sim": self.name,
            "seed": 0,
            "samples": samples,
            "events": trace_events,
            "end_reason": end_reason,
            "duration_ms": duration_ms,
        }
