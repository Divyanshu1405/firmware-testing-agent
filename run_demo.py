"""Run the offline firmware-testing demo."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from sim.backend import RenodeBackend
from sim.fake_backend import FakeBackend


ROOT = Path(__file__).resolve().parent
DEFAULT_FIRMWARE = ROOT / "firmware" / "inputs" / "firmware1.elf"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true", help="Use the deterministic fake backend")
    parser.add_argument("--firmware", type=Path, default=DEFAULT_FIRMWARE)
    parser.add_argument("--out", type=Path, default=ROOT / "out")
    args = parser.parse_args()

    timeline = json.loads((ROOT / "contracts" / "timeline.json").read_text())
    io_map = json.loads((ROOT / "profile" / "io_map.json").read_text())
    if args.offline:
        backend = FakeBackend()
    else:
        backend = RenodeBackend()
        timeline = {
            "test_id": "REAL_SENSOR_DEMO",
            "duration_ms": 1000,
            "events": [],
        }
    trace = backend.run(args.firmware, timeline, io_map)

    args.out.mkdir(parents=True, exist_ok=True)
    trace_path = args.out / "demo_trace.json"
    report_path = args.out / "report.html"
    trace_path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")
    rows = "".join(
        "<tr><td>{t_ms}</td><td>{channel}</td><td>{value}</td></tr>".format(
            t_ms=html.escape(str(sample.get("t_ms", ""))),
            channel=html.escape(str(sample.get("channel", ""))),
            value=html.escape(str(sample.get("value", ""))),
        )
        for sample in trace.get("samples", [])
    )
    report_path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Firmware demo</title>"
        "<style>body{font-family:system-ui;margin:2rem}table{border-collapse:collapse}"
        "td,th{border:1px solid #ccc;padding:.4rem}</style></head><body>"
        f"<h1>Firmware test demo</h1><p>Backend: {html.escape(trace['sim'])}</p>"
        f"<p>End reason: {html.escape(trace['end_reason'])}</p>"
        "<table><tr><th>Time (ms)</th><th>Channel</th><th>Value</th></tr>"
        f"{rows}</table></body></html>"
    )
    print(f"Trace: {trace_path}")
    print(f"Report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
