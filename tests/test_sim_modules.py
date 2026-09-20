from pathlib import Path

from sim.fake_backend import FakeBackend
from sim.faults_exec import apply_fault
from sim.lint import lint_timeline
from sim.matrix import run_matrix


def test_lint_rejects_unknown_channel():
    timeline = {
        "duration_ms": 10,
        "events": [{"at_ms": 0, "action": "set", "channel": "bad", "value": 1}],
    }
    assert lint_timeline(timeline, {"inputs": {}})


def test_faults_are_deterministic():
    assert apply_fault("spike", 10, {"action": "spike", "magnitude": 2}) == 12
    assert apply_fault("dropout", 10, {"action": "dropout"}) is None


def test_matrix_reuses_cache(tmp_path):
    case = {
        "firmware": Path("firmware/inputs/firmware1.elf"),
        "timeline": {"test_id": "T", "duration_ms": 1, "events": []},
        "io_map": {},
    }
    first = run_matrix([case], FakeBackend(), tmp_path)
    second = run_matrix([case], FakeBackend(), tmp_path)
    assert first[0]["cached"] is False
    assert second[0]["cached"] is True
