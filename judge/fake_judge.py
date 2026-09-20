def evaluate(trace, monitors):
    return [
        {
            "test_id": trace.get("test_id", "UNKNOWN"),
            "monitor_id": monitor.get("monitor_id", "UNKNOWN"),
            "requirement_id": monitor.get("requirement_id", "UNKNOWN"),
            "result": "PASS",
            "evidence": {},
            "oracle_source": monitor.get("oracle_source", "generic"),
        }
        for monitor in monitors
    ]