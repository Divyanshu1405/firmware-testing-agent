import argparse
import json
import jsonschema
import re
from pathlib import Path
import sys

def main():
    parser = argparse.ArgumentParser(description="Score confidence offline.")
    parser.add_argument("--schema", required=True, help="Path to timeline.schema.json")
    parser.add_argument("--testcase", required=True, help="Path to Timeline JSON")
    parser.add_argument("--log", required=True, help="Path to UART capture log (txt)")
    args = parser.parse_args()
    
    schema_path = Path(args.schema)
    testcase_path = Path(args.testcase)
    log_path = Path(args.log)
    
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    timeline = json.loads(testcase_path.read_text(encoding="utf-8"))
    
    try:
        jsonschema.validate(instance=timeline, schema=schema)
    except jsonschema.ValidationError as ve:
        raise RuntimeError(f"Timeline validation failed: {ve}")
        
    log_content = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    checks = []
    
    events = timeline.get("events", [])
    total_checks = 0
    passed_checks = 0
    
    for i, ev in enumerate(events):
        expect = ev.get("expect_uart_contains")
        if expect:
            total_checks += 1
            passed = expect in log_content
            checks.append({
                "event_index": i,
                "at_ms": ev.get("at_ms", 0),
                "expected": expect,
                "found": passed
            })
            if passed: passed_checks += 1
            
    accuracy = (passed_checks / total_checks) if total_checks > 0 else 1.0
    confidence = accuracy
    
    result = {
        "test_id": timeline.get("test_id", "unknown"),
        "checks": checks,
        "accuracy": float(accuracy),
        "confidence": float(confidence)
    }
    
    print(json.dumps(result, indent=2))
    
if __name__ == "__main__":
    main()
