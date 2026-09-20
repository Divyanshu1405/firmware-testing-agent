from judge.judge import evaluate, matches_condition


def test_always_monitor():
    """Existing test: empty condition returns INCONCLUSIVE."""
    trace = {
        "test_id": "T01",
        "samples": [
            {"t_ms": 100, "dir": "in", "channel": "temp_c", "value": 25}
        ]
    }

    monitors = [{
        "monitor_id": "M1",
        "requirement_id": "R1",
        "kind": "always",
        "oracle_source": "spec"
    }]

    result = evaluate(trace, monitors)
    assert result[0]["result"] == "INCONCLUSIVE"


def test_always_pass():
    trace = {
        "test_id": "T02",
        "samples": [
            {"t_ms": 100, "dir": "in", "channel": "temp_c", "value": 25.0},
            {"t_ms": 200, "dir": "in", "channel": "temp_c", "value": 28.5},
            {"t_ms": 300, "dir": "in", "channel": "temp_c", "value": 31.0},
        ]
    }
    monitors = [{
        "monitor_id": "M_SAFE_TEMP",
        "requirement_id": "R_TEMP_LIMIT",
        "kind": "always",
        "then": {"channel": "temp_c", "op": "<", "value": 50.0},
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert len(verdicts) == 1
    assert verdicts[0]["result"] == "PASS"
    assert verdicts[0]["evidence"]["sample_count"] == 3
    assert verdicts[0]["test_id"] == "T02"
    assert verdicts[0]["monitor_id"] == "M_SAFE_TEMP"
    assert verdicts[0]["oracle_source"] == "spec"


def test_always_fail():
    trace = {
        "test_id": "T03",
        "samples": [
            {"t_ms": 100, "dir": "in", "channel": "temp_c", "value": 25.0},
            {"t_ms": 200, "dir": "in", "channel": "temp_c", "value": 55.0},
            {"t_ms": 300, "dir": "in", "channel": "temp_c", "value": 28.0},
        ]
    }
    monitors = [{
        "monitor_id": "M_SAFE_TEMP",
        "requirement_id": "R_TEMP_LIMIT",
        "kind": "always",
        "then": {"channel": "temp_c", "op": "<", "value": 50.0},
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert len(verdicts) == 1
    assert verdicts[0]["result"] == "FAIL"
    assert verdicts[0]["evidence"]["t_ms"] == 200
    assert verdicts[0]["evidence"]["observed"] == 55.0
    assert "violated" in verdicts[0]["evidence"]["detail"].lower()


def test_never_pass():
    trace = {
        "test_id": "T04",
        "samples": [
            {"t_ms": 100, "dir": "out", "channel": "fault_flag", "value": 0},
            {"t_ms": 500, "dir": "out", "channel": "fault_flag", "value": 0},
        ]
    }
    monitors = [{
        "monitor_id": "M_NO_FAULT",
        "requirement_id": "R_NO_ERRORS",
        "kind": "never",
        "then": {"channel": "fault_flag", "op": "==", "value": 1},
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "PASS"
    assert verdicts[0]["evidence"]["sample_count"] == 2


def test_never_fail():
    trace = {
        "test_id": "T05",
        "samples": [
            {"t_ms": 100, "dir": "out", "channel": "fault_flag", "value": 0},
            {"t_ms": 1500, "dir": "out", "channel": "fault_flag", "value": 1},
            {"t_ms": 2000, "dir": "out", "channel": "fault_flag", "value": 0},
        ]
    }
    monitors = [{
        "monitor_id": "M_NO_FAULT",
        "requirement_id": "R_NO_ERRORS",
        "kind": "never",
        "then": {"channel": "fault_flag", "op": "==", "value": 1},
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "FAIL"
    assert verdicts[0]["evidence"]["t_ms"] == 1500
    assert verdicts[0]["evidence"]["observed"] == 1
    assert "forbidden" in verdicts[0]["evidence"]["detail"].lower()


def test_eventually_pass():
    trace = {
        "test_id": "T06",
        "samples": [
            {"t_ms": 500, "dir": "out", "channel": "fan", "value": 0},
            {"t_ms": 2300, "dir": "out", "channel": "fan", "value": 1},
        ]
    }
    monitors = [{
        "monitor_id": "M_FAN_START",
        "requirement_id": "R_FAN",
        "kind": "eventually",
        "then": {"channel": "fan", "op": "==", "value": 1},
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "PASS"
    assert verdicts[0]["evidence"]["t_ms"] == 2300


def test_eventually_fail():
    trace = {
        "test_id": "T07",
        "samples": [
            {"t_ms": 500, "dir": "out", "channel": "fan", "value": 0},
            {"t_ms": 2500, "dir": "out", "channel": "fan", "value": 0},
        ]
    }
    monitors = [{
        "monitor_id": "M_FAN_START",
        "requirement_id": "R_FAN",
        "kind": "eventually",
        "then": {"channel": "fan", "op": "==", "value": 1},
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "FAIL"
    assert "never satisfied" in verdicts[0]["evidence"]["detail"].lower()


def test_eventually_deadline():
    trace = {
        "test_id": "T08",
        "samples": [
            {"t_ms": 500, "dir": "out", "channel": "boot_ok", "value": 0},
            {"t_ms": 4000, "dir": "out", "channel": "boot_ok", "value": 1},
        ]
    }
    monitor_pass = {
        "monitor_id": "M_BOOT_1",
        "requirement_id": "R_BOOT",
        "kind": "eventually",
        "then": {"channel": "boot_ok", "op": "==", "value": 1},
        "within_ms": 5000,
        "oracle_source": "spec"
    }
    monitor_fail = {
        "monitor_id": "M_BOOT_2",
        "requirement_id": "R_BOOT",
        "kind": "eventually",
        "then": {"channel": "boot_ok", "op": "==", "value": 1},
        "within_ms": 3000,
        "oracle_source": "spec"
    }

    verdicts_pass = evaluate(trace, [monitor_pass])
    assert verdicts_pass[0]["result"] == "PASS"
    assert verdicts_pass[0]["evidence"]["t_ms"] == 4000

    verdicts_fail = evaluate(trace, [monitor_fail])
    assert verdicts_fail[0]["result"] == "FAIL"
    assert verdicts_fail[0]["evidence"]["t_ms"] == 4000
    assert verdicts_fail[0]["evidence"]["deadline_ms"] == 3000


def test_within_pass():
    trace = {
        "test_id": "T09",
        "samples": [
            {"t_ms": 1000, "dir": "in", "channel": "temp_c", "value": 25.0},
            {"t_ms": 2000, "dir": "in", "channel": "temp_c", "value": 35.0},
            {"t_ms": 2400, "dir": "out", "channel": "gpio.PA5", "value": 1},
        ]
    }
    monitors = [{
        "monitor_id": "M_OVERTEMP",
        "requirement_id": "R_FAN_TRIGGER",
        "kind": "within",
        "when": {"channel": "temp_c", "op": ">", "value": 30.0},
        "then": {"channel": "gpio.PA5", "op": "==", "value": 1},
        "within_ms": 1000,
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "PASS"
    assert verdicts[0]["evidence"]["activations_checked"] == 1


def test_within_fail():
    trace = {
        "test_id": "T10",
        "samples": [
            {"t_ms": 1000, "dir": "in", "channel": "temp_c", "value": 25.0},
            {"t_ms": 2000, "dir": "in", "channel": "temp_c", "value": 35.0},
            {"t_ms": 2400, "dir": "out", "channel": "gpio.PA5", "value": 0},
            {"t_ms": 3500, "dir": "out", "channel": "gpio.PA5", "value": 0},
        ]
    }
    monitors = [{
        "monitor_id": "M_OVERTEMP",
        "requirement_id": "R_FAN_TRIGGER",
        "kind": "within",
        "when": {"channel": "temp_c", "op": ">", "value": 30.0},
        "then": {"channel": "gpio.PA5", "op": "==", "value": 1},
        "within_ms": 1000,
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "FAIL"
    assert verdicts[0]["evidence"]["trigger_t_ms"] == 2000
    assert verdicts[0]["evidence"]["deadline_ms"] == 3000
    assert verdicts[0]["evidence"]["observed"] == 0


def test_within_with_hold_ms_pass():
    """Condition holds for 2000 ms before trigger, response occurs within 1000 ms."""
    trace = {
        "test_id": "T11",
        "samples": [
            {"t_ms": 1000, "dir": "in", "channel": "temp_c", "value": 32.0},
            {"t_ms": 2000, "dir": "in", "channel": "temp_c", "value": 33.0},
            {"t_ms": 3000, "dir": "in", "channel": "temp_c", "value": 34.0},
            {"t_ms": 3500, "dir": "out", "channel": "fan", "value": 1},
        ]
    }
    monitors = [{
        "monitor_id": "M_HOLD",
        "requirement_id": "R_STABLE_TEMP",
        "kind": "within",
        "when": {"channel": "temp_c", "op": ">", "value": 30.0, "hold_ms": 2000},
        "then": {"channel": "fan", "op": "==", "value": 1},
        "within_ms": 1000,
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "PASS"
    assert verdicts[0]["evidence"]["first_trigger_t_ms"] == 3000


def test_within_with_hold_ms_broken_hold():
    """Condition starts, but drops before hold_ms is reached -> no trigger."""
    trace = {
        "test_id": "T12",
        "samples": [
            {"t_ms": 1000, "dir": "in", "channel": "temp_c", "value": 32.0},
            {"t_ms": 1800, "dir": "in", "channel": "temp_c", "value": 25.0},
            {"t_ms": 3500, "dir": "in", "channel": "temp_c", "value": 24.0},
        ]
    }
    monitors = [{
        "monitor_id": "M_HOLD",
        "requirement_id": "R_STABLE_TEMP",
        "kind": "within",
        "when": {"channel": "temp_c", "op": ">", "value": 30.0, "hold_ms": 2000},
        "then": {"channel": "fan", "op": "==", "value": 1},
        "within_ms": 1000,
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "INCONCLUSIVE"
    assert "never triggered" in verdicts[0]["evidence"]["detail"].lower()


def test_boundary_timing_exact_deadline():
    """Response arrives exactly at trigger_t + within_ms."""
    trace = {
        "test_id": "T13",
        "samples": [
            {"t_ms": 1000, "dir": "in", "channel": "alert", "value": 1},
            {"t_ms": 2000, "dir": "out", "channel": "buzzer", "value": 1},
        ]
    }
    monitors = [{
        "monitor_id": "M_BUZZ",
        "requirement_id": "R_BUZZ",
        "kind": "within",
        "when": {"channel": "alert", "op": "==", "value": 1},
        "then": {"channel": "buzzer", "op": "==", "value": 1},
        "within_ms": 1000,
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "PASS"


def test_boundary_timing_one_ms_late():
    """Response arrives at trigger_t + within_ms + 1 ms."""
    trace = {
        "test_id": "T14",
        "samples": [
            {"t_ms": 1000, "dir": "in", "channel": "alert", "value": 1},
            {"t_ms": 2001, "dir": "out", "channel": "buzzer", "value": 1},
        ]
    }
    monitors = [{
        "monitor_id": "M_BUZZ",
        "requirement_id": "R_BUZZ",
        "kind": "within",
        "when": {"channel": "alert", "op": "==", "value": 1},
        "then": {"channel": "buzzer", "op": "==", "value": 1},
        "within_ms": 1000,
        "oracle_source": "spec"
    }]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "FAIL"
    assert verdicts[0]["evidence"]["deadline_ms"] == 2000


def test_empty_trace():
    trace = {"test_id": "T_EMPTY", "samples": [], "events": []}
    monitors = [
        {"monitor_id": "M1", "requirement_id": "R1", "kind": "always", "then": {"channel": "c", "op": "==", "value": 1}},
        {"monitor_id": "M2", "requirement_id": "R2", "kind": "never", "then": {"channel": "c", "op": "==", "value": 1}},
        {"monitor_id": "M3", "requirement_id": "R3", "kind": "within", "when": {"channel": "c", "op": "==", "value": 1}, "then": {"channel": "d", "op": "==", "value": 1}, "within_ms": 100},
    ]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "INCONCLUSIVE"
    assert verdicts[1]["result"] == "PASS"  # forbidden state never observed
    assert verdicts[2]["result"] == "INCONCLUSIVE"  # precondition never triggered


def test_multiple_concurrent_monitors():
    trace = {
        "test_id": "T_MULTI",
        "samples": [
            {"t_ms": 100, "dir": "in", "channel": "temp_c", "value": 25.0},
            {"t_ms": 200, "dir": "in", "channel": "temp_c", "value": 35.0},
            {"t_ms": 250, "dir": "out", "channel": "fan", "value": 1},
            {"t_ms": 500, "dir": "out", "channel": "alarm", "value": 0},
        ]
    }
    monitors = [
        {
            "monitor_id": "M_SAFE_TEMP",
            "requirement_id": "R1",
            "kind": "always",
            "then": {"channel": "temp_c", "op": "<", "value": 50.0},
            "oracle_source": "spec"
        },
        {
            "monitor_id": "M_NO_ALARM",
            "requirement_id": "R2",
            "kind": "never",
            "then": {"channel": "alarm", "op": "==", "value": 1},
            "oracle_source": "spec"
        },
        {
            "monitor_id": "M_FAN_RESPONSE",
            "requirement_id": "R3",
            "kind": "within",
            "when": {"channel": "temp_c", "op": ">", "value": 30.0},
            "then": {"channel": "fan", "op": "==", "value": 1},
            "within_ms": 500,
            "oracle_source": "spec"
        }
    ]

    verdicts = evaluate(trace, monitors)
    assert len(verdicts) == 3
    assert verdicts[0]["result"] == "PASS"
    assert verdicts[1]["result"] == "PASS"
    assert verdicts[2]["result"] == "PASS"


def test_string_operators():
    trace = {
        "test_id": "T_STR",
        "samples": [
            {"t_ms": 100, "dir": "out", "channel": "uart", "value": "SYSTEM READY: temp=25 fan=0"},
            {"t_ms": 500, "dir": "out", "channel": "uart", "value": "ERROR: sensor disconnected"},
        ]
    }
    monitors = [
        {
            "monitor_id": "M_READY",
            "requirement_id": "R_INIT",
            "kind": "eventually",
            "then": {"channel": "uart", "op": "contains", "value": "SYSTEM READY"},
            "oracle_source": "spec"
        },
        {
            "monitor_id": "M_PREFIX",
            "requirement_id": "R_INIT",
            "kind": "always",
            "then": {"channel": "uart", "op": "startswith", "value": "SYSTEM"},
            "oracle_source": "spec"
        }
    ]

    verdicts = evaluate(trace, monitors)
    assert verdicts[0]["result"] == "PASS"
    assert verdicts[1]["result"] == "FAIL"  # second sample starts with ERROR
    assert verdicts[1]["evidence"]["t_ms"] == 500