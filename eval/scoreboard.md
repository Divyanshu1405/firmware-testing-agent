# Firmware Testing Agent Scoreboard & Benchmark Report

## 1. Benchmark Methodology

The firmware testing benchmark evaluates test-agent effectiveness and soundness through mutation testing:

- **Soundness (False Alarm Rate):** The unmodified `original.elf` is treated as the golden baseline. Any failure (`FAIL` verdict) on `original.elf` represents a **false alarm** (flaky test or invalid specification oracle). The acceptable threshold is strictly **0 false alarms**.
- **Effectiveness (Detection Rate):** Each mutant firmware introduces a single minimal, instruction-level behavioral defect. An effective test suite must catch each defect via deterministic monitor violations or generic crash oracles.
- **Anti-Gaming Principle:** The judge evaluates traces deterministically against specifications without visibility into `calib/manifest.json`. The manifest serves solely as ground truth for benchmark grading.

### Metric Formulas

- **Detection Rate:**
  $$\text{Detection Rate} = \frac{K}{N} \times 100\%$$
  Where $K$ is the number of mutants with at least one `FAIL` verdict, and $N$ is the total number of mutants ($N = 5$).
- **False Alarm Rate:**
  $$\text{False Alarm Rate} = \frac{F}{M} \times 100\%$$
  Where $F$ is the count of failing verdicts on `original.elf`, and $M$ is total evaluated monitors on `original.elf`.

## 2. Benchmark Summary

- **Mutants Caught:** 5 / 5 (100.0%)
- **Missed Mutants:** 0
- **False Alarms on Original Firmware:** 0 (0.0%)
- **Target Requirement:** 0 False Alarms, 100% Mutant Detection Rate
- **Overall Benchmark Status:** **PASSED**

## 3. Mutant Catalogue & Detection Breakdown

| Mutant ID | Firmware Binary | Category | Target Violation | Detection Status | Evidence / Notes |
|---|---|---|---|---|---|
| MUTANT_01 | `mutant_1_branch_inversion.elf` | `conditional_branch_inversion` | REQ-02 | **CAUGHT** | [M_TELEMETRY_FORMAT] Observed 'Error' instead of formatted telemetry |
| MUTANT_02 | `mutant_2_timing_delay.elf` | `timing_delay_alteration` | REQ-01 | **CAUGHT** | [M_TELEMETRY_PERIOD] Telemetry flood detected: period < 2000 ms |
| MUTANT_03 | `mutant_3_humidity_offset.elf` | `calculation_offset_modification` | REQ-04 | **CAUGHT** | [M_HUMIDITY_RANGE_HIGH] Humidity 107% exceeds maximum 100% |
| MUTANT_04 | `mutant_4_humidity_scale.elf` | `multiplier_scale_zeroing` | REQ-04 | **CAUGHT** | [M_HUMIDITY_RANGE_LOW] Humidity -6% violates lower bound 0% |
| MUTANT_05 | `mutant_5_i2c_command.elf` | `i2c_command_corruption` | REQ-02 | **CAUGHT** | [M_TELEMETRY_FORMAT] Sensor communication failed on command 0xFF |

## 4. Original Firmware Baseline

- **Total Evaluated Monitors:** 5
- **False Alarm Count:** 0
- *Zero false alarms recorded. Original firmware satisfies all monitors.*

## 5. How to Run the Scoreboard

Run standalone demonstration benchmark:
```powershell
.\.venv\Scripts\python eval/scoreboard.py --demo
```

Evaluate custom test results:
```powershell
.\.venv\Scripts\python eval/scoreboard.py --manifest calib/manifest.json --results path/to/results.json --output eval/scoreboard.md
```
