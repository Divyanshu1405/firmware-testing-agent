# Firmware Testing Agent: Honest Limitations & System Boundaries

This document provides a transparent, technically rigorous assessment of the design limitations, simulation approximations, and operational boundaries of the Firmware Testing Agent and Judge evaluation framework.

---

## 1. Seeded and Patched Bugs (Mutation Limitations)

The benchmark evaluates test effectiveness using binary-level mutations generated from `original.elf` rather than source-level mutation:

- **Instruction Width & Alignment Constraints:**
  All mutations are strictly constrained to in-place replacements using same-width ARM Thumb/Thumb-2 instructions (16-bit or 32-bit). Because file offsets and section boundaries cannot be shifted without invalidating the ELF segment headers and relocation tables, mutations cannot introduce arbitrary multi-instruction logic blocks.
- **Defect Class Representation:**
  Instruction-level patching excels at modeling:
  - Threshold constant alterations (e.g., modifying comparison immediates)
  - Branch condition inversions (`bne` $\leftrightarrow$ `beq`, `cbz` $\leftrightarrow$ `cbnz`)
  - Arithmetic formula offsets and scaling coefficients (e.g., Si7021 polynomial constants)
  - Protocol command corruption (e.g., invalid I2C opcode transmission)
    However, binary patching **cannot** represent:
  - Multi-threaded synchronization deadlocks and race conditions
  - Memory leak accumulations across complex heap allocations
  - Cache incoherence or DMA buffer descriptor corruption
  - Compiler optimization bugs that span across inlined function boundaries.
- **Relocation & Trampoline Limits:**
  Thumb short conditional branches (`b<cond>.n`) are limited to a $\pm 2\text{ KB}$ range. Jumping to arbitrary error handlers or injecting instrumentation hooks requires long trampolines (`b.w` / `ldr pc`), which cannot fit into 16-bit instruction slots without code displacement.

---

## 2. Simulator Timing Differences vs Bare-Metal Hardware

Renode provides functional execution of ARM Cortex-M4 binaries, but exhibits key physical differences compared to physical silicon:

- **Virtual Time vs Physical Crystal Oscillators:**
  Renode advances simulated virtual time based on instruction count and emulated clock frequencies. Unlike physical STM32F4 silicon running on external crystal resonators (HSE/LSE), virtual time has zero phase noise, temperature-dependent frequency drift, or supply-voltage jitter. Microsecond-level timing races that occur on real silicon due to interrupt latency jitter may not manifest in Renode.
- **Peripheral Bus & Analog Physics:**
  I2C, SPI, and UART communication in Renode is emulated at the packet and register state-machine level. The simulator does not model:
  - Bus capacitance, line rise-time delays, and pull-up resistor degradation
  - Incomplete I2C clock-stretching handshakes
  - Analog noise on ADC lines or floating GPIO pins
  - Power rail transients and brown-out detector (BOD) voltage slopes.
- **Host OS Scheduling Artifacts:**
  When Renode interacts with Python-injected peripheral models (such as `sim/si7021_injected.py`) or external sockets, virtual-to-real-time synchronization can experience jitter depending on host CPU load, background OS tasks, or garbage collection pauses.

---

## 3. Inferred-Oracle Cases vs Formal Specifications

Verdicts depend heavily on the provenance of the evaluation oracle (`oracle_source`):

- **Specification Oracles (`oracle_source: spec`):**
  Derived from human-authored ground truth or unambiguous spec text (e.g., `calib/gold/requirements.json`). These provide high confidence and strict tolerances (e.g., exact 2000 ms periodic reporting, strict 0%–100% RH range).
- **Inferred Oracles (`oracle_source: inferred`):**
  When firmware is tested without specification documentation, the agent infers expected behavior from ELF symbols, string literals, and observed baseline traces. Inferred oracles carry inherent risks:
  - **Tolerance Ambiguity:** The agent may guess a $\pm 5\%$ tolerance band where physical sensor noise requires $\pm 10\%$, leading to potential false positives.
  - **Intentional Feature Misinterpretation:** An intentional power-saving sleep mode or active-low LED output could be classified as an unresponsive peripheral or silence.
- **Generic Oracles (`oracle_source: generic`):**
  Generic oracles (`GENERIC_CRASH`, `GENERIC_HANG`, `GENERIC_SILENCE`) operate unconditionally. While universally applicable, they only catch catastrophic faults (HardFault, infinite loops, total silence), leaving functional logic regressions unflagged.

---

## 4. Fallback Model Quality & API Quota Realities

The agent architecture uses a two-tier LLM router (primary Gemini free tier + fallback local Ollama):

- **Gemini Free-Tier Rate Limits:**
  The free tier enforces requests-per-minute (RPM) and requests-per-day (RPD) ceilings. Under continuous test matrix generation, quota exhaustion triggers automated fallback to local models.
- **Local Model (Ollama / Small LLMs) Precision:**
  Local small models (e.g., 7B–14B parameters) have smaller effective attention context windows and lower reasoning fidelity on complex temporal specifications. Specifically:
  - They may omit critical temporal constraints (e.g., forgetting `hold_ms` or mixing up `within` vs `eventually`).
  - JSON schema adherence can be brittle, requiring automated syntax repair passes via Tenacity retries.
- **Deterministic Judge Firewall:**
  To guarantee that LLM non-determinism never corrupts test integrity, **the LLM is strictly forbidden from issuing pass/fail verdicts**. All verdicts are computed by the deterministic judge engine (`judge/judge.py`), ensuring that model variability only affects test stimulus planning, never evaluation truth.

---

## 5. Replayed LLM Responses & Demo Caching

- **Offline Demonstration Mode:**
  The offline demo mode (`--offline`, `run_demo.py`) replays pre-recorded traces and cached LLM responses (`demo_cache/`). While this guarantees 100% reliability during offline hackathon presentations and Wi-Fi dropouts, it bypasses live prompt synthesis and does not exhibit real-time planner edge cases.
- **Cache Invalidation:**
  Changes to the prompt format or contract schemas immediately invalidate existing cached runs, requiring cache re-recording.

---

## 6. Zero False Alarm Guarantees & Operational Envelopes

- **Baseline Validity Envelope:**
  The guarantee of **0 false alarms** on `original.elf` holds strictly within nominal environmental parameters (ambient temperature $-40^\circ\text{C}$ to $+125^\circ\text{C}$, relative humidity $0\%$ to $100\%$, operating voltage $3.3\text{ V}$).
- **Out-of-Envelope Stimuli:**
  If a test timeline intentionally injects severe out-of-specification stimuli (e.g., physical disconnection of I2C lines), the firmware is expected to report `"Error"`. A test that expects valid numeric telemetry during an intentional fault condition would incorrectly register a false alarm; monitors must therefore always specify appropriate `when` preconditions.
