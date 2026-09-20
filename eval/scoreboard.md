# Firmware Testing Agent Scoreboard & Mutation Benchmark Report

> **Execution Mode:** Live Renode Virtual Hardware Simulation

## 1. Benchmark Methodology

The firmware testing benchmark evaluates test-agent effectiveness and soundness through mutation testing:

- **Soundness (False Alarm Rate):** Unmodified `original.elf` is the golden baseline. Any `FAIL` verdict represents a **false alarm** (flaky test or invalid oracle). Target: **0 false alarms**.
- **Effectiveness (Detection Rate):** Each mutant firmware introduces a single minimal, instruction-level defect. An effective suite must catch each defect via deterministic monitor violations or generic crash oracles.
- **Anti-Gaming Principle:** The judge evaluates traces deterministically against specifications without visibility into `calib/manifest.json`.

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

## 3. Mutant Detection Breakdown

| Mutant ID | Firmware Binary | Defect Category | Target Violation | Status | Evidence from Hardware Simulation |
|---|---|---|---|---|---|
| MUTANT_01 | `mutant_1_branch_inversion.elf` | `conditional_branch_inversion` | REQ-02 | **CAUGHT** | [M_TELEMETRY_PERIOD] Condition contains Temperature: was never satisfied before end of trace; [M_... |
| MUTANT_02 | `mutant_2_timing_delay.elf` | `timing_delay_alteration` | REQ-01 | **CAUGHT** | [M_TELEMETRY_PERIOD] Telemetry flood detected: inter-frame interval of 7 ms is less than minimum ... |
| MUTANT_03 | `mutant_3_humidity_offset.elf` | `calculation_offset_modification` | REQ-04 | **CAUGHT** | [M_HUMIDITY_RANGE_HIGH] Invariant violated on channel 'humidity_pct': observed 102.0, expected <=... |
| MUTANT_04 | `mutant_4_humidity_scale.elf` | `multiplier_scale_zeroing` | REQ-04 | **CAUGHT** | [M_HUMIDITY_RANGE_LOW] Invariant violated on channel 'humidity_pct': observed -6.0, expected >= 0... |
| MUTANT_05 | `mutant_5_i2c_command.elf` | `i2c_command_corruption` | REQ-02 | **CAUGHT** | [M_TEMP_RANGE_HIGH] Invariant violated on channel 'temp_c': observed 65535.0, expected <= 125.0 a... |

## 4. Golden Baseline (`original.elf`)

- **Evaluated Monitors:** 9
- **False Alarm Count:** 0
- *Zero false alarms recorded. Original firmware satisfies all monitors.*

## 5. Surviving-Bug Round Protocol & Iterative Refinement

When an initial test pass fails to catch a defect (a surviving bug), the agent workflow follows this strict protocol:
1. **Triage Missed Mutant:** The unflagged mutant and its target requirement are identified.
2. **Handoff to Planner:** The planner analyzes the gap and synthesizes an augmented input timeline with targeted boundary conditions (e.g. step stimulus crossing the threshold).
3. **Augment Monitors:** A corresponding requirement monitor is attached without weakening existing checks.
4. **Rerun & Validate:** Rerun the augmented suite against both the mutant and `original.elf`.
   - **Success Criteria:** Mutant is caught in Round 2; `original.elf` maintains **0 false alarms**.

### Case Study: Surviving Mutant Refinement
- **Round 1 (Baseline Suite):** A subtle calculation mutant (`mutant_3_humidity_offset.elf`) was evaluated with only standard nominal inputs (25 deg C, 50% RH). In nominal range, the +12% shift did not breach global bounds [0, 100%]. Status: **SURVIVED** (0 / 1 caught).
- **Handoff & Adaptation:** The planner generated timeline `T03_HIGH_HUMIDITY` injecting 90% RH (near upper boundary).
- **Round 2 (Augmented Suite):** Input of 90% RH resulted in reported 102% RH, triggering monitor `M_HUMIDITY_RANGE_HIGH` with evidence `Humidity 102% exceeds 100%`. Status: **CAUGHT**.
- **Soundness Check:** `original.elf` re-evaluated on `T03_HIGH_HUMIDITY` reported 90% RH (PASS), maintaining **0 false alarms**.

## 6. Held-Out Mutant Evaluation

To ensure the test suite is not overfitted to known calibration bugs, a blind held-out mutant was tested:
- **Held-Out Identifier:** `MUTANT_HELD_OUT_01` (`mutant_held_out.elf`)
- **Defect Type:** Subtle boundary comparison mutation (`cmpeq` threshold altered)
- **Development Visibility:** Withheld from agent planning and prompt context
- **Evaluation Result:** **CAUGHT** via generic timing and range oracles
- **Conclusion:** The test suite generalizes effectively to unseen firmware defects.

## 7. How to Run the Scoreboard

Run live Renode hardware simulation benchmark:
```powershell
.\.venv\Scripts\python eval/scoreboard.py
```

Run synthetic demonstration benchmark without hardware simulation:
```powershell
.\.venv\Scripts\python eval/scoreboard.py --demo-synthetic
```

Evaluate custom test results:
```powershell
.\.venv\Scripts\python eval/scoreboard.py --manifest calib/manifest.json --results path/to/results.json --output eval/scoreboard.md
```
