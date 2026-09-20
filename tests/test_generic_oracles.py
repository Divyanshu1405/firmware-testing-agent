from judge.generic_oracles import (
    check_hardfault,
    check_reset_loop,
    check_hang,
    check_uart_silence,
    check_uart_garbage,
    check_invalid_memory_access,
    evaluate_generic_oracles,
)


def test_hardfault_event_fail():
    trace = {
        "test_id": "T_HF_01",
        "events": [{"t_ms": 1450, "kind": "hardfault"}],
        "end_reason": "duration_reached",
        "samples": []
    }
    verdict = check_hardfault(trace)
    assert verdict["result"] == "FAIL"
    assert verdict["oracle_source"] == "generic"
    assert verdict["evidence"]["t_ms"] == 1450
    assert "hardfault" in verdict["evidence"]["detail"].lower()


def test_hardfault_crash_end_reason_fail():
    trace = {
        "test_id": "T_HF_02",
        "events": [],
        "end_reason": "crash",
        "samples": [{"t_ms": 500, "dir": "out", "channel": "uart", "value": "boot"}]
    }
    verdict = check_hardfault(trace)
    assert verdict["result"] == "FAIL"
    assert verdict["evidence"]["end_reason"] == "crash"


def test_hardfault_clean_pass():
    trace = {
        "test_id": "T_HF_03",
        "events": [],
        "end_reason": "duration_reached",
        "samples": [{"t_ms": 100, "dir": "out", "channel": "led", "value": 1}]
    }
    verdict = check_hardfault(trace)
    assert verdict["result"] == "PASS"


def test_reset_loop_fail():
    trace = {
        "test_id": "T_RST_01",
        "events": [
            {"t_ms": 500, "kind": "reset"},
            {"t_ms": 1200, "kind": "reset"},
            {"t_ms": 1900, "kind": "reset"},
        ]
    }
    verdict = check_reset_loop(trace, threshold=2)
    assert verdict["result"] == "FAIL"
    assert verdict["evidence"]["reset_count"] == 3
    assert verdict["evidence"]["timestamps"] == [500, 1200, 1900]
    assert "reset loop" in verdict["evidence"]["detail"].lower()


def test_reset_loop_single_reset_pass():
    trace = {
        "test_id": "T_RST_02",
        "events": [
            {"t_ms": 0, "kind": "reset"}  # Normal power-on reset
        ]
    }
    verdict = check_reset_loop(trace, threshold=2)
    assert verdict["result"] == "PASS"
    assert verdict["evidence"]["reset_count"] == 1


def test_hang_timeout_fail():
    trace = {
        "test_id": "T_HANG_01",
        "events": [],
        "end_reason": "timeout",
        "samples": [{"t_ms": 2000, "dir": "out", "channel": "gpio.PA5", "value": 1}]
    }
    verdict = check_hang(trace)
    assert verdict["result"] == "FAIL"
    assert verdict["evidence"]["end_reason"] == "timeout"


def test_hang_event_fail():
    trace = {
        "test_id": "T_HANG_02",
        "events": [{"t_ms": 3200, "kind": "hang"}],
        "end_reason": "duration_reached",
        "samples": []
    }
    verdict = check_hang(trace)
    assert verdict["result"] == "FAIL"
    assert verdict["evidence"]["t_ms"] == 3200


def test_hang_output_gap_fail():
    trace = {
        "test_id": "T_HANG_03",
        "events": [],
        "end_reason": "duration_reached",
        "samples": [
            {"t_ms": 100, "dir": "out", "channel": "uart", "value": "init"},
            {"t_ms": 1000, "dir": "out", "channel": "uart", "value": "ready"},
            {"t_ms": 7500, "dir": "out", "channel": "uart", "value": "alive"},  # 6500 ms gap
        ]
    }
    verdict = check_hang(trace, hang_threshold_ms=5000)
    assert verdict["result"] == "FAIL"
    assert verdict["evidence"]["gap_ms"] == 6500


def test_hang_trailing_silence_fail():
    trace = {
        "test_id": "T_HANG_04",
        "events": [],
        "end_reason": "duration_reached",
        "samples": [
            {"t_ms": 500, "dir": "out", "channel": "uart", "value": "hello"},
            {"t_ms": 1000, "dir": "out", "channel": "uart", "value": "world"},
            {"t_ms": 8000, "dir": "in", "channel": "temp_c", "value": 25.0},  # input continues, but output stopped at 1000
        ]
    }
    verdict = check_hang(trace, hang_threshold_ms=5000)
    assert verdict["result"] == "FAIL"
    assert verdict["evidence"]["gap_ms"] == 7000


def test_hang_clean_periodic_output_pass():
    trace = {
        "test_id": "T_HANG_05",
        "events": [],
        "end_reason": "duration_reached",
        "samples": [
            {"t_ms": 1000, "dir": "out", "channel": "heartbeat", "value": 1},
            {"t_ms": 2000, "dir": "out", "channel": "heartbeat", "value": 1},
            {"t_ms": 3000, "dir": "out", "channel": "heartbeat", "value": 1},
            {"t_ms": 4000, "dir": "out", "channel": "heartbeat", "value": 1},
        ]
    }
    verdict = check_hang(trace, hang_threshold_ms=5000)
    assert verdict["result"] == "PASS"


def test_uart_silence_fail():
    trace = {
        "test_id": "T_UART_01",
        "samples": [
            {"t_ms": 100, "dir": "out", "channel": "gpio.PA5", "value": 1},
            {"t_ms": 500, "dir": "in", "channel": "temp_c", "value": 25.0},
        ]
    }
    verdict = check_uart_silence(trace)
    assert verdict["result"] == "FAIL"
    assert verdict["evidence"]["uart_sample_count"] == 0
    assert "silence" in verdict["evidence"]["detail"].lower()


def test_uart_silence_pass():
    trace = {
        "test_id": "T_UART_02",
        "samples": [
            {"t_ms": 100, "dir": "out", "channel": "uart", "value": "t=100 temp=25 fan=0"},
        ]
    }
    verdict = check_uart_silence(trace)
    assert verdict["result"] == "PASS"
    assert verdict["evidence"]["uart_sample_count"] == 1


def test_uart_garbage_framing_error_fail():
    trace = {
        "test_id": "T_GARBAGE_01",
        "events": [{"t_ms": 2100, "kind": "uart_framing_error"}],
        "samples": []
    }
    verdict = check_uart_garbage(trace)
    assert verdict["result"] == "FAIL"
    assert verdict["evidence"]["t_ms"] == 2100


def test_uart_garbage_corrupted_characters_fail():
    trace = {
        "test_id": "T_GARBAGE_02",
        "events": [],
        "samples": [
            {"t_ms": 500, "dir": "out", "channel": "uart", "value": "\x00\x01\x02\x03\x04\xff\xfe\x00\x00\x00"},
        ]
    }
    verdict = check_uart_garbage(trace)
    assert verdict["result"] == "FAIL"
    assert "garbled" in verdict["evidence"]["detail"].lower()


def test_uart_clean_pass():
    trace = {
        "test_id": "T_GARBAGE_03",
        "events": [],
        "samples": [
            {"t_ms": 500, "dir": "out", "channel": "uart", "value": "Humidity: 45 Temperature: 23\r\n"},
        ]
    }
    verdict = check_uart_garbage(trace)
    assert verdict["result"] == "PASS"


def test_invalid_memory_access_fail():
    trace = {
        "test_id": "T_MEM_01",
        "events": [
            {"t_ms": 1820, "kind": "invalid_memory_access", "address": 0x20020000}
        ]
    }
    verdict = check_invalid_memory_access(trace)
    assert verdict["result"] == "FAIL"
    assert verdict["evidence"]["t_ms"] == 1820
    assert verdict["evidence"]["address"] == 0x20020000


def test_invalid_memory_access_pass():
    trace = {"test_id": "T_MEM_02", "events": []}
    verdict = check_invalid_memory_access(trace)
    assert verdict["result"] == "PASS"


def test_evaluate_generic_oracles_healthy_trace():
    trace = {
        "test_id": "T_ALL_HEALTHY",
        "end_reason": "duration_reached",
        "events": [{"t_ms": 0, "kind": "reset"}],
        "samples": [
            {"t_ms": 100, "dir": "out", "channel": "uart", "value": "booting ok"},
            {"t_ms": 1500, "dir": "out", "channel": "uart", "value": "temp=25"},
            {"t_ms": 2500, "dir": "out", "channel": "gpio.PA5", "value": 0},
        ]
    }
    verdicts = evaluate_generic_oracles(trace)
    assert len(verdicts) == 6
    assert all(v["result"] == "PASS" for v in verdicts)
    assert all(v["oracle_source"] == "generic" for v in verdicts)


def test_evaluate_generic_oracles_with_faults():
    trace = {
        "test_id": "T_FAULTY",
        "end_reason": "crash",
        "events": [
            {"t_ms": 500, "kind": "reset"},
            {"t_ms": 800, "kind": "reset"},
            {"t_ms": 1000, "kind": "hardfault"},
        ],
        "samples": []
    }
    verdicts = evaluate_generic_oracles(trace)
    verdict_by_id = {v["monitor_id"]: v for v in verdicts}

    assert verdict_by_id["GENERIC_HARDFAULT"]["result"] == "FAIL"
    assert verdict_by_id["GENERIC_RESET_LOOP"]["result"] == "FAIL"
    assert verdict_by_id["GENERIC_UART_SILENCE"]["result"] == "FAIL"
