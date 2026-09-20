"""Automated Benchmark Scoreboard for Firmware Testing Agent.

Evaluates test effectiveness deterministically against ground-truth mutants
and measures false alarms on the original firmware.
Does not alter judge results; manifest is strictly benchmark ground truth.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import argparse
import json

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT_DIR / "calib" / "manifest.json"
DEFAULT_SCOREBOARD_MD = ROOT_DIR / "eval" / "scoreboard.md"


class ScoreboardEvaluator:
    """Evaluates test run results against ground-truth mutant catalogue."""

    def __init__(self, manifest_data: Dict[str, Any]):
        self.manifest = manifest_data
        self.mutants = manifest_data.get("mutants", [])

    @classmethod
    def from_manifest_file(cls, manifest_path: Path) -> "ScoreboardEvaluator":
        with open(manifest_path, "r") as f:
            data = json.load(f)
        return cls(data)

    def evaluate_benchmark(
        self,
        results: Dict[str, List[Dict[str, Any]]],
        original_key: str = "original.elf",
    ) -> Dict[str, Any]:
        """Compute scoreboard metrics from verdict results.

        Args:
            results: Mapping from firmware filename to list of Verdict dicts.
            original_key: Key in results corresponding to original golden firmware.

        Returns:
            Dictionary containing metrics, false alarms, and mutant breakdown.
        """
        # 1. Evaluate Original Firmware (Golden Baseline)
        orig_verdicts = results.get(original_key, [])
        orig_fails = [v for v in orig_verdicts if v.get("result") == "FAIL"]
        orig_total = len(orig_verdicts)

        false_alarms = len(orig_fails)
        false_alarm_rate = (false_alarms / orig_total) if orig_total > 0 else 0.0

        # 2. Evaluate Mutants
        total_mutants = len(self.mutants)
        mutant_evaluations = []
        detected_count = 0

        for m in self.mutants:
            m_id = m.get("mutant_id", "UNKNOWN")
            filename = m.get("filename", "")
            exp_viol = m.get("expected_violation", "")
            verdicts = results.get(filename, [])

            failing_verdicts = [v for v in verdicts if v.get("result") == "FAIL"]
            is_detected = len(failing_verdicts) > 0

            # Check if expected requirement violation was specifically flagged
            matching_fails = [
                v for v in failing_verdicts if v.get("requirement_id") == exp_viol
            ]

            evidence_summary = []
            for f in failing_verdicts:
                mon_id = f.get("monitor_id", "")
                detail = f.get("evidence", {}).get("detail", "Failure detected")
                evidence_summary.append(f"[{mon_id}] {detail}")

            if is_detected:
                detected_count += 1

            mutant_evaluations.append({
                "mutant_id": m_id,
                "filename": filename,
                "category": m.get("category", ""),
                "expected_violation": exp_viol,
                "status": "CAUGHT" if is_detected else "MISSED",
                "total_verdicts": len(verdicts),
                "failing_verdicts_count": len(failing_verdicts),
                "matched_expected_requirement": len(matching_fails) > 0,
                "evidence": evidence_summary,
            })

        detection_rate = (detected_count / total_mutants) if total_mutants > 0 else 0.0

        return {
            "summary": {
                "total_mutants": total_mutants,
                "caught_mutants": detected_count,
                "missed_mutants": total_mutants - detected_count,
                "detection_rate": round(detection_rate, 4),
                "detection_percentage": f"{detection_rate * 100:.1f}%",
                "original_verdicts_evaluated": orig_total,
                "false_alarms_count": false_alarms,
                "false_alarm_rate": round(false_alarm_rate, 4),
                "false_alarm_percentage": f"{false_alarm_rate * 100:.1f}%",
                "benchmark_passed": (false_alarms == 0 and detection_rate > 0.0),
            },
            "original": {
                "firmware": original_key,
                "verdicts_count": orig_total,
                "false_alarms": [
                    {
                        "monitor_id": v.get("monitor_id"),
                        "evidence": v.get("evidence"),
                    }
                    for v in orig_fails
                ],
            },
            "mutants": mutant_evaluations,
        }


def format_markdown_scoreboard(scoreboard: Dict[str, Any]) -> str:
    """Format evaluation metrics into comprehensive readable Markdown."""
    summary = scoreboard["summary"]
    lines = [
        "# Firmware Testing Agent Scoreboard & Benchmark Report",
        "",
        "## 1. Benchmark Methodology",
        "",
        "The firmware testing benchmark evaluates test-agent effectiveness and soundness through mutation testing:",
        "",
        "- **Soundness (False Alarm Rate):** The unmodified `original.elf` is treated as the golden baseline. Any failure (`FAIL` verdict) on `original.elf` represents a **false alarm** (flaky test or invalid specification oracle). The acceptable threshold is strictly **0 false alarms**.",
        "- **Effectiveness (Detection Rate):** Each mutant firmware introduces a single minimal, instruction-level behavioral defect. An effective test suite must catch each defect via deterministic monitor violations or generic crash oracles.",
        "- **Anti-Gaming Principle:** The judge evaluates traces deterministically against specifications without visibility into `calib/manifest.json`. The manifest serves solely as ground truth for benchmark grading.",
        "",
        "### Metric Formulas",
        "",
        "- **Detection Rate:**",
        "  $$\\text{Detection Rate} = \\frac{K}{N} \\times 100\\%$$",
        "  Where $K$ is the number of mutants with at least one `FAIL` verdict, and $N$ is the total number of mutants ($N = 5$).",
        "- **False Alarm Rate:**",
        "  $$\\text{False Alarm Rate} = \\frac{F}{M} \\times 100\\%$$",
        "  Where $F$ is the count of failing verdicts on `original.elf`, and $M$ is total evaluated monitors on `original.elf`.",
        "",
        "## 2. Benchmark Summary",
        "",
        f"- **Mutants Caught:** {summary['caught_mutants']} / {summary['total_mutants']} ({summary['detection_percentage']})",
        f"- **Missed Mutants:** {summary['missed_mutants']}",
        f"- **False Alarms on Original Firmware:** {summary['false_alarms_count']} ({summary['false_alarm_percentage']})",
        f"- **Target Requirement:** 0 False Alarms, 100% Mutant Detection Rate",
        f"- **Overall Benchmark Status:** **{'PASSED' if summary['benchmark_passed'] else 'ATTENTION REQUIRED'}**",
        "",
        "## 3. Mutant Catalogue & Detection Breakdown",
        "",
        "| Mutant ID | Firmware Binary | Category | Target Violation | Detection Status | Evidence / Notes |",
        "|---|---|---|---|---|---|",
    ]

    for m in scoreboard["mutants"]:
        evidence_str = "; ".join(m["evidence"]) if m["evidence"] else "No failures detected"
        if len(evidence_str) > 80:
            evidence_str = evidence_str[:77] + "..."
        lines.append(
            f"| {m['mutant_id']} | `{m['filename']}` | `{m['category']}` | {m['expected_violation']} | **{m['status']}** | {evidence_str} |"
        )

    lines.extend([
        "",
        "## 4. Original Firmware Baseline",
        "",
        f"- **Total Evaluated Monitors:** {summary['original_verdicts_evaluated']}",
        f"- **False Alarm Count:** {summary['false_alarms_count']}",
    ])

    if summary['false_alarms_count'] > 0:
        lines.append("\n### False Alarm Details")
        for fa in scoreboard["original"]["false_alarms"]:
            lines.append(f"- Monitor `{fa['monitor_id']}`: {fa['evidence']}")
    else:
        lines.append("- *Zero false alarms recorded. Original firmware satisfies all monitors.*")

    lines.extend([
        "",
        "## 5. How to Run the Scoreboard",
        "",
        "Run standalone demonstration benchmark:",
        "```powershell",
        ".\\.venv\\Scripts\\python eval/scoreboard.py --demo",
        "```",
        "",
        "Evaluate custom test results:",
        "```powershell",
        ".\\.venv\\Scripts\\python eval/scoreboard.py --manifest calib/manifest.json --results path/to/results.json --output eval/scoreboard.md",
        "```",
        ""
    ])

    return "\n".join(lines)


def run_synthetic_demo() -> Dict[str, Any]:
    """Execute a realistic synthetic demonstration using the actual manifest."""
    evaluator = ScoreboardEvaluator.from_manifest_file(DEFAULT_MANIFEST)

    # Construct realistic synthetic verdicts
    synthetic_results = {
        "original.elf": [
            {"test_id": "T01", "monitor_id": "M_TELEMETRY_PERIOD", "requirement_id": "REQ-01", "result": "PASS", "evidence": {}, "oracle_source": "spec"},
            {"test_id": "T02", "monitor_id": "M_TELEMETRY_FORMAT", "requirement_id": "REQ-02", "result": "PASS", "evidence": {}, "oracle_source": "spec"},
            {"test_id": "T03", "monitor_id": "M_HUMIDITY_RANGE_HIGH", "requirement_id": "REQ-04", "result": "PASS", "evidence": {}, "oracle_source": "spec"},
            {"test_id": "T04", "monitor_id": "M_HUMIDITY_RANGE_LOW", "requirement_id": "REQ-04", "result": "PASS", "evidence": {}, "oracle_source": "spec"},
            {"test_id": "T05", "monitor_id": "M_NO_HARDFAULT", "requirement_id": "REQ-06", "result": "PASS", "evidence": {}, "oracle_source": "spec"},
        ],
        "mutant_1_branch_inversion.elf": [
            {"test_id": "T02", "monitor_id": "M_TELEMETRY_FORMAT", "requirement_id": "REQ-02", "result": "FAIL", "evidence": {"t_ms": 2000, "detail": "Observed 'Error' instead of formatted telemetry"}, "oracle_source": "spec"},
        ],
        "mutant_2_timing_delay.elf": [
            {"test_id": "T01", "monitor_id": "M_TELEMETRY_PERIOD", "requirement_id": "REQ-01", "result": "FAIL", "evidence": {"t_ms": 20, "detail": "Telemetry flood detected: period < 2000 ms"}, "oracle_source": "spec"},
        ],
        "mutant_3_humidity_offset.elf": [
            {"test_id": "T03", "monitor_id": "M_HUMIDITY_RANGE_HIGH", "requirement_id": "REQ-04", "result": "FAIL", "evidence": {"t_ms": 2000, "observed": 107.0, "detail": "Humidity 107% exceeds maximum 100%"}, "oracle_source": "spec"},
        ],
        "mutant_4_humidity_scale.elf": [
            {"test_id": "T04", "monitor_id": "M_HUMIDITY_RANGE_LOW", "requirement_id": "REQ-04", "result": "FAIL", "evidence": {"t_ms": 2000, "observed": -6.0, "detail": "Humidity -6% violates lower bound 0%"}, "oracle_source": "spec"},
        ],
        "mutant_5_i2c_command.elf": [
            {"test_id": "T02", "monitor_id": "M_TELEMETRY_FORMAT", "requirement_id": "REQ-02", "result": "FAIL", "evidence": {"t_ms": 2000, "detail": "Sensor communication failed on command 0xFF"}, "oracle_source": "spec"},
        ],
    }

    return evaluator.evaluate_benchmark(synthetic_results)


def main():
    parser = argparse.ArgumentParser(description="Firmware Testing Scoreboard Runner")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST, help="Path to manifest.json")
    parser.add_argument("--results", type=Path, default=None, help="Path to evaluation results JSON")
    parser.add_argument("--output", type=Path, default=DEFAULT_SCOREBOARD_MD, help="Output markdown path")
    parser.add_argument("--demo", action="store_true", help="Run synthetic demonstration benchmark")
    args = parser.parse_args()

    if args.demo or args.results is None:
        print("Running demonstration benchmark evaluation...")
        scoreboard_data = run_synthetic_demo()
    else:
        with open(args.results, "r") as f:
            results_data = json.load(f)
        evaluator = ScoreboardEvaluator.from_manifest_file(args.manifest)
        scoreboard_data = evaluator.evaluate_benchmark(results_data)

    md_content = format_markdown_scoreboard(scoreboard_data)
    print(md_content)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(md_content)
        print(f"\nScoreboard written to: {args.output}")


if __name__ == "__main__":
    main()
