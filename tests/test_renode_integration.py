"""Integration test suite for Renode virtual hardware simulation,
trace acquisition, sensor fault injection, profile isolation, and API security.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import uuid

import pytest
from fastapi.testclient import TestClient

from backend.main import app, MAX_UPLOAD_SIZE, RUNS_DIR
from judge.evaluate import evaluate as evaluate_bridge
from profile.infer import infer_profile
from profile.static.triage import analyze_firmware
from sim.backend import RenodeBackend
from sim.runner import simulate
from sim.si7021_injected import (
    SI7021Injected,
    mc_set_sensor_dropout,
    mc_set_sensor_error,
    mc_set_sensor_stuck,
    mc_clear_sensor_stuck,
)


# ── 1. Asciinema Virtual Microsecond Timestamp Parsing ────────────────────────

def test_asciinema_microsecond_parsing(tmp_path: Path):
    """Test that microsecond floating-point timestamps are accurately converted to ms."""
    cast_file = tmp_path / "test.cast"
    cast_file.write_text(
        '{"version": 2, "width": 80, "height": 24, "timestamp": 1000}\n'
        '[0.007123, "o", "Hum"]\n'
        '[0.007500, "o", "idity: 50.0 Temperature: 25.0\\r\\n"]\n'
        '[0.452891, "o", "Humidity: 55.0 Temperature: 26.0\\r\\n"]\n',
        encoding="utf-8",
    )

    samples = RenodeBackend._parse_asciinema(cast_file)
    assert len(samples) == 2
    assert samples[0]["t_ms"] == 7
    assert samples[0]["value"] == "Humidity: 50.0 Temperature: 25.0"
    assert samples[0]["channel"] == "uart"
    assert samples[0]["dir"] == "out"

    assert samples[1]["t_ms"] == 453
    assert samples[1]["value"] == "Humidity: 55.0 Temperature: 26.0"


# ── 2. Zero Silent Mock Fallback on Renode Failure ────────────────────────────

def test_runner_zero_silent_mock_fallback_on_renode_missing(tmp_path: Path):
    """When Renode is missing or fails, real firmware must return INFRASTRUCTURE_ERROR, never silent mock."""
    dummy_elf = tmp_path / "target.elf"
    dummy_elf.write_bytes(b"\x7fELF" + b"\x00" * 100)

    timeline = {"test_id": "T_NO_FALLBACK", "duration_ms": 1000, "events": []}
    io_map = {"firmware": str(dummy_elf), "platform": "platforms/boards/stm32f4_discovery-kit.repl", "inputs": {}, "outputs": {}}

    with patch("sim.runner.find_renode", return_value=None):
        trace = simulate(dummy_elf, timeline, io_map)

    assert trace["end_reason"] == "sim_error"
    assert "INFRASTRUCTURE_ERROR" in trace.get("error_detail", "")
    # Must NOT have generated fake/synthetic telemetry samples
    assert len(trace.get("samples", [])) == 0


def test_verdict_honestly_inconclusive_on_sim_error():
    """Deterministic judge returns INCONCLUSIVE on sim error traces rather than false PASS/FAIL."""
    res = evaluate_bridge(
        {"test_id": "T_ERR", "requirement_ids": ["REQ_01"]},
        {
            "test_id": "T_ERR",
            "firmware": "target.elf",
            "end_reason": "sim_error",
            "error_detail": "INFRASTRUCTURE_ERROR: Renode process crashed",
        },
    )
    verdicts = res["verdicts"]
    assert len(verdicts) >= 1
    assert all(v["result"] == "INCONCLUSIVE" for v in verdicts)
    assert "INFRASTRUCTURE_ERROR" in verdicts[0]["evidence"]["detail"]


def test_reference_firmware_uses_calibration_monitors():
    """The documented firmware1 baseline must use its real gold monitors."""
    result = evaluate_bridge(
        {"test_id": "T_GOLD", "requirement_ids": ["REQ-02"]},
        {
            "test_id": "T_GOLD",
            "firmware": "firmware1.elf",
            "samples": [
                {
                    "t_ms": 100,
                    "dir": "out",
                    "channel": "uart",
                    "value": "Humidity: 50 Temperature: 25",
                }
            ],
            "events": [],
            "end_reason": "duration_reached",
        },
    )
    assert any(m["monitor_id"] == "M_TELEMETRY_FORMAT" for m in result["monitors"])


# ── 3. Sensor Fault Injection Model ──────────────────────────────────────────

class MockPeripheral:
    def __init__(self):
        self.DataReceived = MagicMock()
        self.enqueued = []

    def EnqueueResponseBytes(self, b):
        self.enqueued.append(bytes(b))


def test_sensor_fault_injection_logic():
    """Test SI7021 sensor fault injection: dropout, force_error, and stuck values."""
    mock_periph = MockPeripheral()
    sensor = SI7021Injected(mock_periph)

    # 1. Normal RH read (0xE5)
    mock_periph.enqueued.clear()
    sensor.on_write(bytes([0xE5]))
    assert len(mock_periph.enqueued) == 1
    assert mock_periph.enqueued[0] != bytes([0xFF, 0xFF])

    # 2. Sensor Dropout
    mock_periph.enqueued.clear()
    mc_set_sensor_dropout(1)
    sensor.on_write(bytes([0xE5]))
    assert len(mock_periph.enqueued) == 0  # No response transmitted (NACK/timeout)

    # Clear dropout
    mc_set_sensor_dropout(0)

    # 3. Force Error (0xFF, 0xFF)
    mock_periph.enqueued.clear()
    mc_set_sensor_error(1)
    sensor.on_write(bytes([0xE5]))
    assert len(mock_periph.enqueued) == 1
    assert mock_periph.enqueued[0] == bytes([0xFF, 0xFF])

    # Clear error
    mc_set_sensor_error(0)

    # 4. Stuck Temperature
    mock_periph.enqueued.clear()
    mc_set_sensor_stuck("temp", 42.0)
    sensor.on_write(bytes([0xE3]))
    assert len(mock_periph.enqueued) == 1
    resp_stuck = mock_periph.enqueued[0]

    # Verify that stuck temp remains unchanged even if nominal temp changes
    sensor.temperature_c = -10.0
    mock_periph.enqueued.clear()
    sensor.on_write(bytes([0xE3]))
    assert mock_periph.enqueued[0] == resp_stuck

    mc_clear_sensor_stuck()


# ── 4. Unknown Firmware Profile Isolation ─────────────────────────────────────

def test_unknown_firmware_profile_isolation():
    """Unknown firmware must NOT inherit STM32F4/SI7021 sensor profile."""
    fw_path = Path("firmware/inputs/firmware2.elf")
    assert fw_path.exists(), "firmware2.elf must exist in test inputs"

    triage_data = analyze_firmware(fw_path)
    profile, io_map = infer_profile(triage_data, fw_path)

    assert profile["profile_id"] == "generic_arm_firmware"
    assert profile["sensor_platform"] is None
    assert profile["sensor_script"] is None
    assert "SI7021" not in profile.get("detected_features", {}).get("sensor_model", "")
    assert "temp_c" not in io_map["inputs"]
    assert "humidity_pct" not in io_map["inputs"]


# ── 5. API Upload Validation ──────────────────────────────────────────────────

def test_api_upload_rejects_non_elf():
    """Upload endpoint must reject non-ELF files with HTTP 422."""
    client = TestClient(app)
    response = client.post(
        "/api/upload",
        files={"file": ("malicious.txt", b"Plain text payload not an ELF binary", "text/plain")},
    )
    assert response.status_code == 422
    assert "must be a valid ELF binary" in response.json()["detail"]


def test_api_upload_rejects_oversized_file():
    """Upload endpoint must reject files exceeding MAX_UPLOAD_SIZE with HTTP 413."""
    client = TestClient(app)
    # Simulate an oversized upload by sending content larger than MAX_UPLOAD_SIZE
    oversized_data = b"\x7fELF" + b"\x00" * (MAX_UPLOAD_SIZE + 1024)
    response = client.post(
        "/api/upload",
        files={"file": ("huge.elf", oversized_data, "application/octet-stream")},
    )
    assert response.status_code == 413
    assert "exceeds maximum allowed size" in response.json()["detail"]


def test_api_upload_accepts_valid_elf(tmp_path: Path):
    """Upload endpoint accepts valid ELF binaries."""
    client = TestClient(app)
    valid_elf = b"\x7fELF\x01\x01\x01\x00" + b"\x00" * 64
    response = client.post(
        "/api/upload",
        files={"file": ("valid_test.elf", valid_elf, "application/octet-stream")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "valid_test.elf"
    assert "uploads/valid_test.elf" in data["path"]


# ── 6. API Run Isolation ──────────────────────────────────────────────────────

def test_api_run_isolation():
    """Each pipeline execution creates a unique isolated run directory and artifacts."""
    client = TestClient(app)
    response = client.post(
        "/api/run",
        json={
            "firmware": "dummy_fw.bin",
            "spec_text": "",
            "mode": "offline",
        },
    )
    assert response.status_code == 200
    data = response.json()

    run_id = data["run_id"]
    assert uuid.UUID(run_id)  # Must be a valid UUID string

    run_dir = RUNS_DIR / run_id
    assert run_dir.is_dir()
    assert (run_dir / "report.html").exists()

    # Verify that run report is retrievable via GET /api/runs/{run_id}/report
    report_res = client.get(f"/api/runs/{run_id}/report")
    assert report_res.status_code == 200
    assert "Firmware Test Report" in report_res.text
