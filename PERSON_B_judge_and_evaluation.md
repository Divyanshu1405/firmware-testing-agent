# Person B: Judge, Test Content and Evaluation Lead

**You decide what counts as a pass or a fail, create the known-bad firmwares, and prove the agent actually catches bugs.**

> **Project:** AI agent that takes a compiled firmware (plus README/spec text), plans tests, builds the Renode environment, runs the tests, judges them and writes a report.
> **Clock:** 20 h total. Code freeze at **H18**. H18 to H20 is rehearsal only.
> **Assumptions:** input is a compiled firmware (ELF preferred; HEX/BIN if needed) for an MCU Renode supports, plus README/spec text. Simulator = Renode. LLM = Gemini free tier (primary) + local Ollama model (fallback). PlatformIO is not used.
> **How the three plans fit together ("easily compiled"):** each person owns separate folders and talks to the others only through the frozen contracts at the bottom of this file. Everyone builds against a **mock** of the other two, so nobody waits.

## Team map

| | Person A | Person B | Person C |
|---|---|---|---|
| Role | Simulator and environment | Judge, test content and evaluation | Agent, LLM and report |
| Name | ________ | ________ | ________ |
| Owns folders | `sim/`, `profile/dynamic/`, `report/plots.py`, `run_demo.py`, `README.md` | `judge/`, `profile/static/`, `calib/`, `faults/`, `eval/` | `agent/`, `contracts/`, `report/`, `demo_cache/` |
| Produces | `RenodeBackend.run()`, `io_map.json`, fault primitives, matrix runner, plots | `judge.evaluate()`, `static.json`, mutants, fault library, scoreboard | requirements, tests, timelines, LLM router, report |
| Main risk | Renode platform match and input injection (first 3 h) | Binary patching and monitor correctness | Free-tier LLM quota and JSON quality |
| Demo role | Runs the live demo terminal | Explains the scoreboard and limitations | Explains the AI agent and LLM fallback |

### Load balance (each person is fully scheduled for all 20 h)

| Category | A | B | C |
|---|---|---|---|
| Build own module | 14 h | 15.5 h | 14 h |
| Wiring into the end-to-end run (H11 to H12.5) | 1.5 h | 0 h | 1.5 h |
| Shared (setup, contracts, wrap-up, rehearsal) | 4.5 h | 4.5 h | 4.5 h |
| Total | 20 h | 20 h | 20 h |

B has 1.5 h more module work but no wiring work. B's mutant task (H9.5 to H12.5) is capped at 3 h and can be handed to whoever finishes first. A carries the most technical risk early (H0 to H3). C carries the most volume in the middle (H3.5 to H12.5). B is steady throughout and fills the gaps by doing the static triage that unblocks A. If someone finishes early, take work from the shared backlog in this order: (1) integration bugs, (2) fresh-clone test, (3) README and limitations list, (4) stretch items.

### Team checkpoints (all three present)

| When | Goal state (must be true) | Check |
|---|---|---|
| **H3.5** | Contracts frozen. Mocks exist for backend, judge and agent | `pytest` green. Mocks run end to end |
| **H8** | A: real backend runs a hand timeline. B: judge passes on synthetic and one real trace. C: router and graph run on mocks | Each person demos in 2 minutes |
| **H12.5** | End-to-end v1 on the original firmware, zero failures on it | `python -m agent.run <firmware>` produces a report |
| **H17** | Scoreboard and report final. Feature freeze candidate | `python eval/scoreboard.py` writes the table |
| **H18** | Freeze. Fresh-clone test passes with Wi-Fi off | README followed on a second machine |

### Git rules

- One branch per person (`a/main`, `b/main`, `c/main`). Only edit your own folders.
- Merge to `main` at every checkpoint and at least every 2 hours. Merge only if `pytest` passes.
- Anything in `contracts/` changes only if all three agree in the group chat first.
- Never commit `.env`. Never commit API keys.

## Frozen contracts (identical in all three files)

**Timeline** (C writes it, A executes it):
```json
{
  "test_id": "T07",
  "requirement_ids": ["R2"],
  "duration_ms": 12000,
  "events": [
    {"at_ms": 0,    "action": "set",     "channel": "temp_c", "value": 25.0},
    {"at_ms": 2000, "action": "ramp",    "channel": "temp_c", "to": 33.0, "over_ms": 4000},
    {"at_ms": 8000, "action": "dropout", "channel": "temp_c", "for_ms": 4000}
  ]
}
```
Allowed actions: `set`, `ramp`, `step`, `dropout`, `stuck`, `spike`, `glitch`, `drift`, `uart_write`, `uart_garbage`.

**Trace** (A produces it, B consumes it):
```json
{
  "test_id": "T07", "firmware": "original.elf", "sim": "renode", "seed": 0,
  "samples": [
    {"t_ms": 1200, "dir": "in",  "channel": "temp_c",   "value": 31.0},
    {"t_ms": 1200, "dir": "out", "channel": "uart",     "value": "t=1200 temp=31 fan=1"},
    {"t_ms": 1210, "dir": "out", "channel": "gpio.PA5", "value": 1}
  ],
  "events": [{"t_ms": 9000, "kind": "hardfault"}],
  "end_reason": "duration_reached"
}
```
`end_reason` is one of `duration_reached`, `timeout`, `crash`, `sim_error`. Event kinds: `hardfault`, `reset`, `hang`, `invalid_memory_access`.

**Monitor** (C or B writes it, B evaluates it):
```json
{
  "monitor_id": "M2", "requirement_id": "R2", "kind": "within",
  "when": {"channel": "temp_c", "op": ">", "value": 30, "hold_ms": 2000},
  "then": {"channel": "gpio.PA5", "op": "==", "value": 1},
  "within_ms": 1000,
  "oracle_source": "spec"
}
```
Kinds: `always`, `never`, `within`, `eventually`. `oracle_source` is `spec`, `inferred` or `generic`.

**Verdict** (B produces it, C reports it):
```json
{
  "test_id": "T07", "monitor_id": "M2", "requirement_id": "R2",
  "result": "FAIL",
  "evidence": {"t_ms": 9100, "detail": "fan still 0 at 9100 ms, expected 1 by 9000 ms"},
  "oracle_source": "spec"
}
```
`result` is `PASS`, `FAIL` or `INCONCLUSIVE`.

**IO map** (A produces it, C and A's linter use it):
```json
{
  "firmware": "original.elf",
  "platform": "platforms/boards/<closest_board>.repl",
  "uart": "sysbus.usart2",
  "inputs":  {"temp_c": {"kind": "adc", "peripheral": "sysbus.adc1", "channel": 0, "scale": null}},
  "outputs": {"fan": {"kind": "gpio", "pin": "gpioa.5"}},
  "notes": []
}
```
`scale` is how physical units map to raw counts. If it is unknown, it stays `null` and is filled from the README (C) and confirmed by experiment (A).

**Function signatures:**
```python
# A:  sim/backend.py
RenodeBackend.run(firmware: Path, timeline: dict, io_map: dict, timeout_s: int = 60) -> dict   # Trace
# B:  judge/judge.py
evaluate(trace: dict, monitors: list[dict]) -> list[dict]                                        # Verdicts
# C:  agent/run.py
python -m agent.run <firmware> [--spec README.md] [--offline]                                    # writes out/report.html
```

**Mocks (each owner ships theirs by H3.5):** `sim/fake_backend.py` returns a canned trace, `judge/fake_judge.py` returns canned verdicts, `agent/fake_agent.py` returns canned timelines and monitors.

**Anti-gaming rules (everyone):**
- The expected behaviour comes from the spec, never from reading what the firmware does.
- The LLM never decides pass or fail. Only the judge does.
- The LLM never sees the mutant manifest (`calib/manifest.json`).
- If there is no spec, label verdicts `inferred` (low confidence).


---

# YOUR PLAN: Person B: Judge, Test Content and Evaluation Lead

## Mission

Own the truth side of the project: the deterministic judge, the generic oracles, the reference requirements and monitors, the fault library, the mutants used to measure effectiveness, and the scoreboard. If your part is solid, every result the demo shows is trustworthy.

## Goal state (what must be true when you are done)

- `judge.evaluate(trace, monitors)` returns evidence-backed verdicts, is fully deterministic, and has unit tests on synthetic traces.
- Generic oracles (hard fault, reset loop, hang, UART silence, invalid memory access) work without any spec.
- A hand-written reference set of requirements and monitors exists (the "gold" set) to grade C's spec extraction.
- `calib/` holds at least 5 mutants of the given firmware, each behaviourally different, plus a hidden manifest.
- `eval/scoreboard.py` prints: caught K of N mutants, false alarms on the original (must be 0), and one surviving-bug round is documented.

## Files and folders you own

| Path | What |
|---|---|
| `judge/judge.py` | Monitor interpreter |
| `judge/generic_oracles.py` | Crash, reset loop, hang, silence oracles |
| `judge/fake_judge.py` | Mock for A and C |
| `profile/static/triage.py` | ELF triage: arch, entry, vector table, sections, symbols, strings, stripped or not, debug info |
| `calib/gold/` | Hand-written requirements and monitors |
| `calib/mutants/`, `calib/manifest.json` | Mutants and hidden bug list |
| `faults/library.json` | Fault templates per input channel |
| `eval/scoreboard.py` | Effectiveness table |

## Your checkpoint goal states

| When | Goal state |
|---|---|
| H2 | `static.json` produced for the given firmware (unblocks A's platform choice) |
| H3.5 | `fake_judge.py` in the repo. Contracts reviewed |
| H8 | Judge passes all unit tests on synthetic traces and works on one real trace from A. Generic oracles done |
| H9.5 | Gold requirements and monitors written |
| H12.5 | At least 5 mutants built and each verified different from the original |
| H14.5 | Fault library complete |
| H17 | Scoreboard table generated automatically, held-out mutant checked |
| H18 | Limitations list written |

## Hour-by-hour plan

| Hours | Task | Output | Done when |
|---|---|---|---|
| H0–0.5 | **Setup.** Install Python deps: `pyelftools`, `capstone`, `pytest` (add `keystone-engine` if you need an assembler) | Imports work | Everyone's checks pass |
| H0.5–2.5 | **Static triage.** `triage.py` reads the given firmware: format, architecture, entry point, vector table, section map, symbols, strings, stripped or not, debug info present. Send the results to A as soon as the header info is ready (~H1.5) | `profile/static/static.json` | Schema-valid. A has used it to choose the platform |
| H2.5–3.5 | **Contracts** with everyone. Then ship `fake_judge.py` | Mock returning valid verdicts | Mock output validates against the Verdict schema |
| H3.5–6.5 | **Judge core.** Interpreter for `always`, `never`, `within`, `eventually`, with `hold_ms` support. Unit tests with hand-made synthetic traces (a passing and a failing trace per kind) | `judge/judge.py`, `tests/test_judge.py` | All tests green. Every FAIL carries timestamp evidence |
| H6.5–8 | **Generic oracles.** Hard-fault event, reset loop, hang (no output for T), UART silence, invalid memory access. All labelled `oracle_source: generic` | `judge/generic_oracles.py` | Each oracle fires on a synthetic trace and stays quiet on a healthy one |
| H8–9.5 | **Gold set.** From the README, hand-write the numbered requirements and their monitors. This is what C's spec extraction is graded against | `calib/gold/requirements.json`, `calib/gold/monitors.json` | Reviewed by C. At least one requirement has an ambiguity noted |
| H9.5–12.5 | **Mutants (calibration set).** With `capstone`, find compare-immediate instructions and conditional branches in the given ELF, and patch bytes (or assemble with `keystone-engine`) to change a threshold, flip a comparison, or remove a check. Write `manifest.json` (bug id, what changed, which requirement it should violate) | `calib/mutants/*.elf`, `calib/manifest.json` | At least 5 mutants, each runs in Renode and behaves differently from the original. Cap this at 3 h. If patching is impractical, use hidden-bug firmwares from the organizers, or build a tiny firmware with `arm-none-eabi-gcc` |
| H12.5–14.5 | **Fault library.** Templates per input channel: stuck-at, dropout, spike, glitch, drift, noise, oscillation around a threshold, truncated or garbage UART frame, long-run timing | `faults/library.json` | Every fault type in the contract has a template. A has confirmed each executes |
| H14.5–17 | **Scoreboard and surviving-bug round.** Run the same suite on the original and every mutant. Table: caught K of N, false alarms on original (must be 0). One surviving-bug round: for each missed mutant, hand the miss to C so the planner adds tests, rerun once. Check one held-out mutant that was not used in development | `eval/scoreboard.py`, `eval/scoreboard.md` | Table generated automatically. Original shows 0 failures |
| H17–18 | **Limitations list + second-machine test.** Write the honest limits: seeded and patched bugs, simulator timing differences, inferred-oracle cases, fallback model quality, replayed LLM responses | `LIMITATIONS.md` | Reviewed by the team |
| H18–20 | **Rehearsal.** You present the scoreboard and limitations | Backup video recorded | Two clean rehearsals |

## What you build against while others are not ready (mocks)

Until the real backend works (H8), test the judge with synthetic traces and A's `fake_backend.py`. Until the mutants exist, use one hand-made variant to sanity-check the scoreboard code.

## If you are blocked or finish early

- **Blocked on patching:** ask A for the memory map or C to search for the instruction encodings. If the ELF is stripped, patch by byte pattern from the disassembly.
- **Finished early:** help C review the gold set against the spec extraction output, then take over the report's scoreboard page, then the shared backlog.

## Risks and fallbacks

| Risk | Fallback |
|---|---|
| Thumb encoding makes patching error-prone | Use `keystone-engine` to assemble replacements. Patch only same-size instructions |
| Mutants crash instead of changing behaviour | Keep only mutants that differ from the original in a controlled way (threshold or comparison), and drop crashers |
| No spec text | Only generic oracles apply. Label verdicts `inferred` and lower expectations in the scoreboard |
| Scoreboard is 100% too easily | Add the held-out mutant and one subtle mutant (off-by-one at exactly the threshold) |

## Do not

- Do not let the LLM decide pass or fail.
- Do not show `calib/manifest.json` to the LLM.
- Do not edit the firmware source, there is none. Only patch copies of the binary.
- Do not change the schemas in `contracts/` on your own.

## Definition of done (tick every box before H18)

- [ ] `static.json` produced and used by A
- [ ] Judge unit tests green for all four monitor kinds
- [ ] Generic oracles tested on healthy and faulty synthetic traces
- [ ] Gold requirements and monitors reviewed by C
- [ ] At least 5 mutants verified, hidden manifest kept out of the LLM's reach
- [ ] Fault library covers every fault type in the contract
- [ ] Scoreboard generated automatically, 0 false alarms on the original
- [ ] One held-out mutant checked
- [ ] `LIMITATIONS.md` written
