"""Run simulator cases with deterministic trace caching."""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any


def _firmware_hash(firmware: Path) -> str:
    digest = hashlib.sha256()
    with Path(firmware).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _case_key(case: dict[str, Any]) -> str:
    firmware = Path(case["firmware"])
    payload = {
        "firmware_sha256": _firmware_hash(firmware),
        "timeline": case["timeline"],
        "io_map": case.get("io_map", {}),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def run_matrix(
    cases: list[dict[str, Any]],
    backend: Any,
    cache_dir: Path,
    parallelism: int = 1,
) -> list[dict[str, Any]]:
    """Run cases and return traces; cached cases are marked with ``cached``."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    def run_case(case: dict[str, Any]) -> dict[str, Any]:
        key = _case_key(case)
        cache_path = cache_dir / f"{key}.json"
        if cache_path.exists():
            trace = json.loads(cache_path.read_text())
            trace["cached"] = True
            return trace
        trace = backend.run(
            Path(case["firmware"]),
            case["timeline"],
            case.get("io_map", {}),
            case.get("timeout_s", 60),
        )
        cache_path.write_text(json.dumps(trace, indent=2, sort_keys=True) + "\n")
        trace["cached"] = False
        return trace

    workers = max(1, int(parallelism))
    if workers == 1:
        return [run_case(case) for case in cases]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(run_case, cases))
