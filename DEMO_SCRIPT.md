# Firmware Testing Agent Demo

Welcome to the autonomous firmware testing agent. This demo illustrates how the system deterministically acts on firmware hardware models versus simulated mock environments to validate requirements strictly.

## 1. Simulated Demo Failure (Isolated Bug)
*This command executes a purely simulated edge case (fan failure against thermal threshold mapped to requirement R7) rendering it into `out/demo_fail_report.html` securely. It does not hit the network or run standard graph compilation.*
```bash
python -m agent.run dummy_fw.bin --spec tests/fixtures/sample_spec.md --demo-failure
```

## 2. Standard Offline Execution (Green Path Replay)
*This strictly simulates the end-to-end LangGraph processing timeline (Spec Extraction -> Planning -> Generation -> Mock Judging -> Report) bypassing LLMs via local cache validation. It validates compliance dynamically against frozen schemas.*
```bash
LLM_OFFLINE=1 python -m agent.run dummy_fw.bin --spec tests/fixtures/sample_spec.md
```

## 3. Strict Validation Pychecks
*This executes securely mocked offline graph parsing checks validating reporting templates, timelines bounded deterministic healing, and router fallback capabilities organically.*
```bash
pytest -v
```

> **IMPORTANT:** In this initial iteration (Person C), all backend simulation is executed via simulated placeholders natively. `agent/fake_agent.py` drives the pass/fails transparently. The explicit trace models strictly represent the contracts passed to future hardware simulation suites natively.
