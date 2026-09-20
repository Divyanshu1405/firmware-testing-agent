"""Trace normalization engine.

Extracts structured output signals (e.g. parsed telemetry, sensor readings, error flags)
from raw UART ASCII streams and formats samples for deterministic monitor evaluation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

# Regex matching standard formatted telemetry: "Humidity: <H> Temperature: <T>"
TELEMETRY_RE = re.compile(
    r"Humidity:\s*(?P<humidity>-?\d+(?:\.\d+)?)\s+Temperature:\s*(?P<temperature>-?\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def normalize_trace(trace: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a raw execution trace by extracting domain channels from UART streams.
    
    Copies the trace and enriches samples with parsed peripheral and telemetry channels.
    """
    normalized = dict(trace)
    samples: List[Dict[str, Any]] = list(trace.get("samples", []))
    new_samples: List[Dict[str, Any]] = []

    for s in samples:
        new_samples.append(dict(s))
        if s.get("channel") == "uart" and s.get("dir") == "out":
            val_str = str(s.get("value", ""))
            t_ms = s.get("t_ms", 0)

            # Check for error indicator
            if "error" in val_str.lower():
                new_samples.append({
                    "t_ms": t_ms,
                    "dir": "out",
                    "channel": "sensor_error",
                    "value": 1,
                })

            # Check for formatted telemetry
            match = TELEMETRY_RE.search(val_str)
            if match:
                raw_h = float(match.group("humidity"))
                raw_t = float(match.group("temperature"))

                new_samples.append({
                    "t_ms": t_ms,
                    "dir": "out",
                    "channel": "humidity_pct",
                    "value": raw_h,
                })

                # Firmware transmits temperature in hundredths of deg C (centi-degrees, e.g. 2499 -> 24.99 C)
                # or raw 65535 on error.
                if raw_t > 500:
                    t_val = raw_t / 100.0 if raw_t < 60000 else raw_t
                else:
                    t_val = raw_t

                new_samples.append({
                    "t_ms": t_ms,
                    "dir": "out",
                    "channel": "temp_c",
                    "value": t_val,
                })

    new_samples.sort(key=lambda item: item.get("t_ms", 0))
    normalized["samples"] = new_samples
    return normalized

