#!/usr/bin/env python3
"""
contracts/validate_examples.py
Validates every *.example.json against its matching *.schema.json.
Exits 0 if all pass, 1 if any fail.
"""
import json
import sys
from pathlib import Path

import jsonschema

CONTRACTS_DIR = Path(__file__).parent


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> int:
    schemas: dict[str, dict] = {}
    for schema_path in CONTRACTS_DIR.glob("*.schema.json"):
        key = schema_path.stem.replace(".schema", "")  # e.g. "timeline"
        schemas[key] = load_json(schema_path)

    all_passed = True
    for example_path in sorted(CONTRACTS_DIR.glob("*.example.json")):
        key = example_path.stem.replace(".example", "")
        if key not in schemas:
            print(f"  SKIP  {example_path.name}  (no matching schema)")
            continue
        instance = load_json(example_path)
        schema = schemas[key]
        try:
            jsonschema.validate(instance=instance, schema=schema)
            print(f"  PASS  {example_path.name}")
        except jsonschema.ValidationError as exc:
            print(f"  FAIL  {example_path.name}: {exc.message}")
            all_passed = False

    if all_passed:
        print("\nAll examples valid.")
        return 0
    else:
        print("\nSome examples FAILED validation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
