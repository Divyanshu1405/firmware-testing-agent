from pathlib import Path
import json
import hashlib
import capstone
from elftools.elf.elffile import ELFFile

from judge.judge import evaluate
from eval.scoreboard import ScoreboardEvaluator

ROOT_DIR = Path(__file__).resolve().parent.parent
GOLD_REQ_PATH = ROOT_DIR / "calib" / "gold" / "requirements.json"
GOLD_MON_PATH = ROOT_DIR / "calib" / "gold" / "monitors.json"
MUTANTS_DIR = ROOT_DIR / "calib" / "mutants"
MANIFEST_PATH = ROOT_DIR / "calib" / "manifest.json"
FAULTS_PATH = ROOT_DIR / "faults" / "library.json"
ORIGINAL_ELF_PATH = ROOT_DIR / "original.elf"


# ==========================================
# 1. Gold Specification Tests
# ==========================================

def test_gold_requirements_schema():
    assert GOLD_REQ_PATH.exists(), "calib/gold/requirements.json missing"
    with open(GOLD_REQ_PATH, "r") as f:
        reqs = json.load(f)

    assert isinstance(reqs, list)
    assert len(reqs) >= 5, "Expected at least 5 requirements"

    req_ids = set()
    for r in reqs:
        assert "id" in r and r["id"].startswith("REQ-")
        assert "title" in r and len(r["title"]) > 0
        assert "description" in r and len(r["description"]) > 0
        assert "source" in r and len(r["source"]) > 0
        assert r["id"] not in req_ids, f"Duplicate requirement ID {r['id']}"
        req_ids.add(r["id"])


def test_gold_monitors_schema():
    assert GOLD_MON_PATH.exists(), "calib/gold/monitors.json missing"
    with open(GOLD_MON_PATH, "r") as f:
        monitors = json.load(f)

    assert isinstance(monitors, list)
    assert len(monitors) >= 5, "Expected at least 5 monitors"

    valid_kinds = {"always", "never", "within", "eventually"}
    for m in monitors:
        assert "monitor_id" in m
        assert "requirement_id" in m
        assert "kind" in m
        assert m["kind"] in valid_kinds, f"Invalid monitor kind {m['kind']}"
        assert m.get("oracle_source") == "spec"
        assert "then" in m or "when" in m, "Monitor missing condition specification"


def test_gold_monitors_judge_compatibility():
    with open(GOLD_MON_PATH, "r") as f:
        monitors = json.load(f)

    # Realistic trace corresponding to normal operation
    trace = {
        "test_id": "T_GOLD_EVAL",
        "duration_ms": 5000,
        "samples": [
            {"t_ms": 100, "dir": "out", "channel": "uart", "value": "Humidity: 45 Temperature: 25\r\n"},
            {"t_ms": 2100, "dir": "out", "channel": "uart", "value": "Humidity: 46 Temperature: 25\r\n"},
            {"t_ms": 100, "dir": "in", "channel": "humidity_pct", "value": 45.0},
            {"t_ms": 2100, "dir": "in", "channel": "humidity_pct", "value": 46.0},
            {"t_ms": 100, "dir": "in", "channel": "temp_c", "value": 25.0},
            {"t_ms": 2100, "dir": "in", "channel": "temp_c", "value": 25.0},
        ],
        "events": [],
        "end_reason": "duration_reached"
    }

    verdicts = evaluate(trace, monitors)
    assert len(verdicts) == len(monitors)
    for v in verdicts:
        assert "test_id" in v
        assert "monitor_id" in v
        assert "requirement_id" in v
        assert "result" in v
        assert v["result"] in ("PASS", "FAIL", "INCONCLUSIVE")
        assert "evidence" in v
        assert "oracle_source" in v


# ==========================================
# 2. Binary Mutants Tests
# ==========================================

def test_mutants_exist_and_count():
    assert MUTANTS_DIR.exists()
    mutant_files = list(MUTANTS_DIR.glob("*.elf"))
    assert len(mutant_files) >= 5, f"Expected at least 5 mutant ELFs, found {len(mutant_files)}"


def test_mutants_differ_from_original():
    with open(ORIGINAL_ELF_PATH, "rb") as f:
        orig_bytes = f.read()

    mutant_files = list(MUTANTS_DIR.glob("*.elf"))
    for mf in mutant_files:
        with open(mf, "rb") as f:
            m_bytes = f.read()
        assert len(m_bytes) == len(orig_bytes), f"Mutant {mf.name} size changed from original"
        assert m_bytes != orig_bytes, f"Mutant {mf.name} is identical to original.elf"

        # Byte diff should be minimal (between 1 and 4 bytes for our instructions)
        diff_count = sum(1 for b1, b2 in zip(orig_bytes, m_bytes) if b1 != b2)
        assert 1 <= diff_count <= 4, f"Mutant {mf.name} has unexpected diff size {diff_count}"


def test_mutants_are_valid_arm_elfs():
    mutant_files = list(MUTANTS_DIR.glob("*.elf"))
    for mf in mutant_files:
        with open(mf, "rb") as f:
            elf = ELFFile(f)
            assert elf.get_machine_arch() == "ARM", f"{mf.name} is not ARM architecture"
            text_sec = elf.get_section_by_name(".text")
            assert text_sec is not None, f"{mf.name} missing .text section"
            assert text_sec["sh_size"] > 0, f"{mf.name} empty .text"


def test_manifest_consistency():
    assert MANIFEST_PATH.exists()
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    mutants = manifest.get("mutants", [])
    assert len(mutants) >= 5

    filenames = set()
    md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

    for m in mutants:
        fn = m["filename"]
        assert fn not in filenames, f"Duplicate filename {fn} in manifest"
        filenames.add(fn)

        mutant_path = MUTANTS_DIR / fn
        assert mutant_path.exists(), f"Mutant file {fn} specified in manifest does not exist"

        addr = int(m["address"], 16)
        with open(mutant_path, "rb") as f:
            elf = ELFFile(f)
            text_sec = elf.get_section_by_name(".text")
            text_addr = text_sec["sh_addr"]
            text_data = text_sec.data()

            ins_bytes = text_data[addr - text_addr : addr - text_addr + len(bytes.fromhex(m["mutated_bytes"]))]
            assert ins_bytes.hex() == m["mutated_bytes"], f"Bytes in {fn} do not match manifest"

            insns = list(md.disasm(ins_bytes, addr))
            assert len(insns) == 1, f"Failed to disassemble instruction in {fn}"
            disasm_str = f"{insns[0].mnemonic} {insns[0].op_str}"
            assert disasm_str == m["mutated_instruction"], f"Disassembly {disasm_str} != manifest {m['mutated_instruction']}"


def test_mutants_are_distinct():
    mutant_files = list(MUTANTS_DIR.glob("*.elf"))
    hashes = set()
    for mf in mutant_files:
        with open(mf, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        assert h not in hashes, f"Duplicate mutant binary detected: {mf.name}"
        hashes.add(h)


# ==========================================
# 3. Fault Library Tests
# ==========================================

def test_fault_library_schema():
    assert FAULTS_PATH.exists()
    with open(FAULTS_PATH, "r") as f:
        lib = json.load(f)

    fault_types = lib.get("fault_types", [])
    assert len(fault_types) >= 8, f"Expected 8 fault categories, found {len(fault_types)}"

    expected_categories = {
        "stuck_at", "dropout", "spike", "glitch", "drift", "noise", "oscillation", "corrupted_uart"
    }
    found_categories = {f["category"] for f in fault_types}
    assert expected_categories.issubset(found_categories), f"Missing categories: {expected_categories - found_categories}"

    valid_actions = {"set", "ramp", "step", "dropout", "stuck", "spike", "glitch", "drift", "uart_write", "uart_garbage", "noise", "oscillation"}
    for f in fault_types:
        assert "id" in f
        assert "name" in f
        assert "action" in f
        assert f["action"] in valid_actions, f"Action {f['action']} not in allowed timeline actions"
        assert "timeline_event_template" in f
        tpl = f["timeline_event_template"]
        assert "at_ms" in tpl
        assert "action" in tpl
        assert "channel" in tpl


# ==========================================
# 4. Scoreboard Tests
# ==========================================

def test_scoreboard_perfect_detection():
    evaluator = ScoreboardEvaluator.from_manifest_file(MANIFEST_PATH)
    results = {
        "original.elf": [
            {"monitor_id": "M1", "result": "PASS", "evidence": {}}
        ],
        "mutant_1_branch_inversion.elf": [{"monitor_id": "M2", "result": "FAIL", "evidence": {}}],
        "mutant_2_timing_delay.elf": [{"monitor_id": "M1", "result": "FAIL", "evidence": {}}],
        "mutant_3_humidity_offset.elf": [{"monitor_id": "M3", "result": "FAIL", "evidence": {}}],
        "mutant_4_humidity_scale.elf": [{"monitor_id": "M4", "result": "FAIL", "evidence": {}}],
        "mutant_5_i2c_command.elf": [{"monitor_id": "M2", "result": "FAIL", "evidence": {}}],
    }

    score = evaluator.evaluate_benchmark(results)
    assert score["summary"]["caught_mutants"] == 5
    assert score["summary"]["missed_mutants"] == 0
    assert score["summary"]["detection_rate"] == 1.0
    assert score["summary"]["false_alarms_count"] == 0
    assert score["summary"]["benchmark_passed"] is True


def test_scoreboard_partial_detection():
    evaluator = ScoreboardEvaluator.from_manifest_file(MANIFEST_PATH)
    results = {
        "original.elf": [
            {"monitor_id": "M1", "result": "PASS", "evidence": {}}
        ],
        "mutant_1_branch_inversion.elf": [{"monitor_id": "M2", "result": "FAIL", "evidence": {}}],
        "mutant_2_timing_delay.elf": [{"monitor_id": "M1", "result": "PASS", "evidence": {}}],  # Missed
        "mutant_3_humidity_offset.elf": [{"monitor_id": "M3", "result": "FAIL", "evidence": {}}],
        "mutant_4_humidity_scale.elf": [{"monitor_id": "M4", "result": "PASS", "evidence": {}}],  # Missed
        "mutant_5_i2c_command.elf": [{"monitor_id": "M2", "result": "FAIL", "evidence": {}}],
    }

    score = evaluator.evaluate_benchmark(results)
    assert score["summary"]["caught_mutants"] == 3
    assert score["summary"]["missed_mutants"] == 2
    assert score["summary"]["detection_rate"] == 0.60
    assert score["summary"]["false_alarms_count"] == 0


def test_scoreboard_zero_detection():
    evaluator = ScoreboardEvaluator.from_manifest_file(MANIFEST_PATH)
    results = {
        "original.elf": [{"monitor_id": "M1", "result": "PASS", "evidence": {}}],
        "mutant_1_branch_inversion.elf": [{"monitor_id": "M2", "result": "PASS", "evidence": {}}],
        "mutant_2_timing_delay.elf": [{"monitor_id": "M1", "result": "PASS", "evidence": {}}],
        "mutant_3_humidity_offset.elf": [{"monitor_id": "M3", "result": "PASS", "evidence": {}}],
        "mutant_4_humidity_scale.elf": [{"monitor_id": "M4", "result": "PASS", "evidence": {}}],
        "mutant_5_i2c_command.elf": [{"monitor_id": "M2", "result": "PASS", "evidence": {}}],
    }

    score = evaluator.evaluate_benchmark(results)
    assert score["summary"]["caught_mutants"] == 0
    assert score["summary"]["missed_mutants"] == 5
    assert score["summary"]["detection_rate"] == 0.0


def test_scoreboard_false_alarm_detection():
    evaluator = ScoreboardEvaluator.from_manifest_file(MANIFEST_PATH)
    results = {
        "original.elf": [
            {"monitor_id": "M1", "result": "PASS", "evidence": {}},
            {"monitor_id": "M2", "result": "FAIL", "evidence": {"detail": "Spurious failure"}},
        ],
        "mutant_1_branch_inversion.elf": [{"monitor_id": "M2", "result": "FAIL", "evidence": {}}],
    }

    score = evaluator.evaluate_benchmark(results)
    assert score["summary"]["false_alarms_count"] == 1
    assert score["summary"]["false_alarm_rate"] == 0.50
    assert score["summary"]["benchmark_passed"] is False


def test_scoreboard_empty_and_missing_handling():
    evaluator = ScoreboardEvaluator.from_manifest_file(MANIFEST_PATH)
    score = evaluator.evaluate_benchmark({})
    assert score["summary"]["caught_mutants"] == 0
    assert score["summary"]["missed_mutants"] == 5
    assert score["summary"]["false_alarms_count"] == 0
    assert score["summary"]["benchmark_passed"] is False
